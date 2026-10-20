"""Aggregate actual source-driver objects; not full toolchain or speed admission."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment
from macho_image_dependencies import dependencies
from macho_packing_semantics import compare_group, image_semantics, preserve_original_image
from native_object_manifest import digest, read_manifest
from run_parser_native_admission_cost import run


def admit_group(images):
    originals = {str(image): image_semantics(image.read_bytes()) for image in images}
    if len(originals) != len(images) or len(images) < 2:
        raise ValueError('at least two distinct original images required')
    for image, semantics in originals.items():
        if (preserve_original_image(semantics)
                or dependencies(Path(image).read_bytes()) != ['/usr/lib/libSystem.B.dylib']):
            raise ValueError('capture aggregation preserves weak/initializer/non-System images')
    details = compare_group(originals, next(iter(originals.values())))
    if (details['duplicateDefinitions'] or details['possibleChangedInImageBindings']
            or not details['architectureAndFlagsMatch']):
        raise ValueError('captured inputs introduce duplicate/internal/architecture bindings')
    return originals


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'image-build', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--capture', type=Path, action='append', required=True)
    parser.add_argument('--sample-startup', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, image_build, project, output = [path.resolve() for path in
        (args.baseline, args.image_build, args.project, args.output)]
    captures = [path.resolve() for path in args.capture]
    if not all(path.is_relative_to(root/'.data') for path in
               (baseline, image_build, project, output, *captures)):
        parser.error('isolated .data inputs required')
    home = baseline/'build'
    build = json.loads((image_build/'report.json').read_text())
    if not build.get('qualified') or not build.get('originalGambitMacroInputsUsed'):
        parser.error('qualified original macro-correct inputs required')
    if (digest(home/'bin/gsc') != build['gscSha256']
            or digest(home/'include/gambit.h') != build['headerSha256']):
        parser.error('original compiler/header identity changed')
    if subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip() != build['projectHead']:
        parser.error('original Native harness identity changed')
    rows = {row['module']: row for row in build['units']}
    admitted = []
    modules = set()
    for capture in captures:
        report = json.loads((capture/'report.json').read_text())
        module = report['module']
        row = rows[module]
        image = capture/'captured/module.o1'
        manifest = read_manifest(image)
        if (module in modules or not report.get('qualified')
                or report.get('originalGscSourceDispatch') is not True
                or report['gscSha256'] != build['gscSha256']
                or report['headerSha256'] != build['headerSha256']
                or report['macroInputSha256'] != digest(home/'lib/_gambit#.scm')
                or report['schemeSourceSha256'] != digest(home/'lib'/f'{module}.scm')
                or report['schemeSourceSha256'] != row['sourceSha256']
                or digest(capture/'captured/module.c') != row['generatedCSha256']
                or digest(capture/'captured/module.scm') != row['sourceSha256']
                or digest(capture/'baseline/module.c') != row['generatedCSha256']
                or digest(capture/'baseline/module.o1') != manifest['imageSha256']
                or report['imageSha256'][:2] != [manifest['imageSha256']]*2
                or report['capturedObjectSha256'] != manifest['objectSha256']):
            raise ValueError('actual original-GSC captured input identity changed')
        modules.add(module)
        admitted.append(dict(row=row, image=image, manifest=manifest))
    originals = admit_group([item['image'] for item in admitted])
    environment = build_environment()
    macros = subprocess.check_output([environment['CC'], '-dM', '-E', '-x', 'c', os.devnull],
                                     env=environment, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        parser.error('real GNU GCC 16 required')
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    environment['GERBIL_BUILD_CORES'] = str(cores)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, constructionQualified=False, importQualified=False,
        performanceQualified=False, fullToolchainQualified=False, diagnosticOnly=True,
        scope='actual-source-driver-native-object-aggregation-not-speed-or-full-toolchain',
        hardwareWorkers=cores, modules=sorted(modules), runs=[],
        sharedOriginalExecutable=True,
        startupSampling=args.sample_startup,
        captureReceiptSha256=[digest(path/'report.json') for path in captures],
        originalGscSha256=build['gscSha256'], originalHeaderSha256=build['headerSha256'])
    try:
        candidate = output/'candidate'
        subprocess.run(['/bin/cp', '-cR', str(home), str(candidate)], check=True, timeout=180)
        group = candidate/'lib/startup-captured-images/group.o1'
        group.parent.mkdir()
        env = dict(environment, GAMBITDIR_INCLUDE=str(home/'include'), GAMBITDIR_LIB=str(home/'lib'),
            BUILD_DYN_INPUT_FILENAMES_PARAM=' '.join(str(item['manifest']['objectPath']) for item in admitted),
            BUILD_DYN_OUTPUT_FILENAME_PARAM=str(group),
            BUILD_DYN_LD_OPTIONS_PARAM='-Wl,-undefined,dynamic_lookup', GAMBIT_DARWIN_NATIVE_OBJECTS='0')
        report['linkRun'] = run([str(home/'bin/gambuild-C'), 'dyn'], output, env, output/'link.log', 180)
        semantics = compare_group(originals, image_semantics(group.read_bytes()))
        if (not semantics['architectureAndFlagsMatch'] or not semantics['literalRpathsMatch']
                or semantics['duplicateDefinitions'] or semantics['possibleChangedInImageBindings']
                or semantics['addedDefinitions'] or semantics['removedDefinitions']
                or semantics['packedInitializationHooks']
                or dependencies(group.read_bytes()) != ['/usr/lib/libSystem.B.dylib']):
            raise ValueError('captured aggregate changes admitted native linkage')
        for item in admitted:
            alias = candidate/item['row']['path']
            alias.unlink()
            alias.symlink_to(os.path.relpath(group, alias.parent))
        if any(digest(home/'bin'/name) != digest(candidate/'bin'/name) for name in ('gxi', 'gsc')):
            raise ValueError('aggregation changed original executable')
        report.update(constructionQualified=True, aggregationSha256=digest(group),
            retainedObjectSha256=[item['manifest']['objectSha256'] for item in admitted],
            linkage=semantics, directDependenciesIndependentOfRpath=True,
            fullDyldRpathSemanticsQualified=False, noSchemeOrCRecompilationDuringAggregation=True)
        expression = (f'(current-directory {json.dumps(str(project))}) '
            '(load "t/fixtures/tla-sany-differential/preload.ss") (prefer-native-interfaces!) '
            '(preload-module "std/make") (preload-module "std/build-script") '
            '(preload-module "std/test/unit") '
            '(import :std/make :std/build-script :std/test/unit) '
            '(displayln "CAPTURED-IMAGE-IMPORT-OK") (force-output)')

        def observe(role, native_home):
            env = dict(environment, GERBIL_HOME=str(native_home), GERBIL_PATH=str(project/'.gerbil'),
                GERBIL_LOADPATH=f"{project/'.gerbil/lib'}:{native_home/'lib'}:{project}",
                PATH=f"{native_home/'bin'}:{environment['PATH']}",
                GAMBOPT=f"~~bin={native_home/'bin'},~~lib={native_home/'lib'},~~include={native_home/'include'},max-heap=1G,debug=q")
            sampler = None
            sample_log = None

            def observe_start(pid):
                nonlocal sampler, sample_log
                sample_log = (output/f'{role}-sample.log').open('w')
                sampler = subprocess.Popen(['/usr/bin/sample', str(pid), '3', '1', '-file',
                    str(output/f'{role}-sample.txt')], stdout=sample_log, stderr=subprocess.STDOUT)

            try:
                result = run([str(home/'bin/gxi'), '-e', expression], project, env,
                             output/f'{role}.log', 90, 5,
                             on_start=observe_start if args.sample_startup else None)
                if 'CAPTURED-IMAGE-IMPORT-OK\n' not in (output/f'{role}.log').read_text():
                    raise ValueError('actual compiled-interface import marker missing')
                return dict(role=role, qualified=True, **result)
            except Exception as error:
                return dict(role=role, qualified=False, failure=repr(error))
            finally:
                if sampler is not None:
                    try:
                        sampler.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        sampler.kill()
                        sampler.wait()
                if sample_log is not None:
                    sample_log.close()

        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(observe, role, native_home) for role, native_home in
                       (('original', home), ('captured-packed', candidate))]
            report['runs'] = [future.result() for future in futures]
        report['importQualified'] = all(item['qualified'] for item in report['runs'])
        for item in admitted:
            if read_manifest(item['image']) != item['manifest']:
                raise ValueError('captured image/object changed during aggregation')
        report['qualified'] = report['constructionQualified'] and report['importQualified']
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    if not report['qualified']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
