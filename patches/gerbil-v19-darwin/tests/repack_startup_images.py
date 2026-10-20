"""Reuse locked GNU objects; preserve weak-binding/initializer images byte-exact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

from bazel_host_environment import build_environment
from macho_image_dependencies import dependencies, validate_packed_image_inventory
from macho_packing_semantics import image_semantics, preserve_original_image
from run_parser_native_admission_cost import native_admission_expression, run


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partition_images(rows, maximum_modules=0):
    if type(maximum_modules) is not int or maximum_modules < 0 or maximum_modules == 1:
        raise ValueError('image limit must be zero or an integer of at least two')
    groups = []
    for row in sorted(rows, key=lambda row: row['index']):
        group = next((group for group in groups
                      if (not maximum_modules or len(group) < maximum_modules)
                      and all(item['linkerBasename'] != row['linkerBasename'] for item in group)), None)
        if group is None:
            group = []
            groups.append(group)
        group.append(row)
    return groups


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'image-build', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--system-only', action='store_true',
                        help='preserve every native image with a non-System direct dependency')
    parser.add_argument('--maximum-modules-per-image', type=int, default=0)
    args = parser.parse_args()
    if args.maximum_modules_per_image < 0 or args.maximum_modules_per_image == 1:
        parser.error('image limit must be zero or at least two')
    root = Path(__file__).resolve().parents[3]
    baseline, previous, project, output = [path.resolve() for path in
        (args.baseline, args.image_build, args.project, args.output)]
    if platform.system() != 'Darwin' or not all(path.is_relative_to(root/'.data') for path in (baseline, previous, project, output)):
        parser.error('isolated .data inputs required')
    receipt = previous/'report.json'
    build = json.loads(receipt.read_text())
    home = baseline/'build'
    if (not build.get('qualified') or not build.get('originalGambitMacroInputsUsed')
            or not build.get('officialToolsIncluded') or build.get('scope') !=
            'current-staging-native-preload-image-packing-prototype'):
        parser.error('corrected original-macro official-tool image build required')
    validate_packed_image_inventory(previous/'source/build', build)
    if (digest(home/'bin/gsc') != build['gscSha256'] or digest(home/'include/gambit.h') != build['headerSha256']
            or subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
            != build['projectHead']):
        parser.error('compiler/header/Native project identity changed')
    selected, preserved = [], []
    for row in build['units']:
        original = home/row['path']
        cfile = previous/'units'/str(row['index'])/'module.c'
        if (digest(original) != row['originalSha256'] or digest(original.with_suffix('.scm')) != row['sourceSha256']
                or digest(cfile) != row['generatedCSha256'] or digest(previous/row['object']) != row['objectSha256']):
            raise ValueError('original image/source or reusable GNU object changed')
        excluded = preserve_original_image(image_semantics(original.read_bytes()))
        excluded |= args.system_only and row['dependencies'] != ['/usr/lib/libSystem.B.dylib']
        (preserved if excluded else selected).append(row)
    environment = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    environment['GERBIL_BUILD_CORES'] = str(cores)
    macros = subprocess.check_output([environment['CC'], '-dM', '-E', '-x', 'c', os.devnull],
                                     env=environment, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        parser.error('real GNU GCC 16 required')
    output.mkdir(parents=True, exist_ok=False)
    source = output/'source'
    report = dict(build)
    report.update(qualified=False, performanceQualified=False, units=[], images=[],
                  parentImageReceiptSha256=digest(receipt), candidate=str(source.relative_to(root)),
                  preservedOriginalImages=preserved, packingEligibility='preserve-weak-bindings-and-initializers',
                  rpathSemanticsQualified=False, allUnitsReused=True, cores=cores,
                  maximumModulesPerImage=args.maximum_modules_per_image,
                  systemOnlyPacking=args.system_only, directDependenciesIndependentOfRpath=args.system_only)
    try:
        subprocess.run(['/bin/cp', '-cR', str(baseline), str(source)], check=True, timeout=180)
        groups = partition_images(selected, args.maximum_modules_per_image)
        for row in sorted(selected, key=lambda row: row['index']):
            target = output/row['object']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(previous/row['object'], target)
            cfile = previous/'units'/str(row['index'])/'module.c'
            shutil.copyfile(cfile, target.with_suffix('.c'))
            if digest(target) != row['objectSha256']:
                raise ValueError('GNU object copy changed bytes')
            report['units'].append(row)
        aggregate = source/'build/lib/startup-images'
        aggregate.mkdir()
        for index, group in enumerate(groups):
            image = aggregate/f'group-{index}.o1'
            required = sorted({path for row in group for path in row['dependencies']})
            env = dict(environment, GAMBITDIR_INCLUDE=str(home/'include'), GAMBITDIR_LIB=str(home/'lib'),
                BUILD_DYN_INPUT_FILENAMES_PARAM=' '.join(str(output/row['object']) for row in group),
                BUILD_DYN_OUTPUT_FILENAME_PARAM=str(image),
                BUILD_DYN_LD_OPTIONS_PARAM='-Wl,-undefined,dynamic_lookup '+
                    ' '.join(f'-Wl,-needed_library,{path}' for path in required if path != '/usr/lib/libSystem.B.dylib'))
            run([str(home/'bin/gambuild-C'), 'dyn'], output, env, output/f'link-{index}.log', 180)
            if dependencies(image.read_bytes()) != required or preserve_original_image(image_semantics(image.read_bytes())):
                raise ValueError('ordinary packed image changed dependencies or gained excluded linkage semantics')
            for row in group:
                alias = source/'build'/row['path']
                alias.unlink()
                alias.symlink_to(os.path.relpath(image, alias.parent))
            report['images'].append(dict(path=str(image.relative_to(source/'build')), sha256=digest(image),
                                          aliases=[row['path'] for row in group], dependencies=required))
            print(f'ORDINARY-IMAGE-LINKED index={index} modules={len(group)}', flush=True)
        report['aggregateImageCount'] = len(groups)+len(preserved)
        report['originalImageCount'] = len(selected)+len(preserved)
        validate_packed_image_inventory(source/'build', report)
        report['binaryHashesUnchanged'] = all(digest(home/'bin'/name) == digest(source/'build/bin'/name)
                                             for name in ('gxi', 'gsc'))
        candidate = source/'build'
        env = dict(environment, GERBIL_HOME=str(candidate), GERBIL_PATH=str(project/'.gerbil'),
                   GERBIL_LOADPATH=f"{project/'.gerbil/lib'}:{candidate/'lib'}:{project}",
                   PATH=f"{candidate/'bin'}:{environment['PATH']}",
                   GAMBOPT=f"~~bin={candidate/'bin'},~~lib={candidate/'lib'},~~include={candidate/'include'},max-heap=1G,debug=q")
        report['importRun'] = run([str(candidate/'bin/gxi'), '-e', native_admission_expression(project)],
                                 project, env, output/'import.log', 90, 5)
        if 'NATIVE-ADMISSION-PREFIX-OK\n' not in (output/'import.log').read_text():
            raise ValueError('original Native import marker missing')
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
