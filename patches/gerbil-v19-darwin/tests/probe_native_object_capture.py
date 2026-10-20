"""Original current-staging C input through source-owned GCC object capture."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from bazel_host_environment import build_environment
from audit_startup_gsc_recipe import gsc_recipe_command
from macho_packing_semantics import image_semantics
from native_object_manifest import digest, read_manifest, text_section
from run_parser_native_admission_cost import run


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'image-build', 'driver-source', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--gsc-source', action='store_true',
                        help='exercise original GSC source compilation and its actual gambuild dispatch')
    parser.add_argument('--module', default='std/test/unit~0')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, image_build, driver_source, output = [path.resolve() for path in
        (args.baseline, args.image_build, args.driver_source, args.output)]
    if not all(path.is_relative_to(root/'.data') for path in (baseline, image_build, driver_source, output)):
        parser.error('isolated .data inputs required')
    build = json.loads((image_build/'report.json').read_text())
    if build.get('qualified') is not True or build.get('originalGambitMacroInputsUsed') is not True:
        parser.error('qualified corrected current-input C build required')
    rows = [row for row in build['units'] if row['module'] == args.module]
    if len(rows) != 1:
        parser.error('exactly one locked original staging module required')
    row = rows[0]
    source = image_build/'units'/str(row['index'])/'module.c'
    home = baseline/'build'
    if (digest(source) != row['generatedCSha256'] or digest(home/'bin/gsc') != build['gscSha256']
            or digest(home/'include/gambit.h') != build['headerSha256']):
        parser.error('current C/compiler/header identity changed')
    scheme_source = home/'lib'/f"{row['module']}.scm"
    macro_source = home/'lib/_gambit#.scm'
    if digest(scheme_source) != row['sourceSha256']:
        parser.error('original Scheme source identity changed')
    scripts = [driver_source/name for name in ('gambuild-C', 'gambuild-C.unix.in',
        'gambit-native-object-cache', 'gambit-native-object-cache.unix', 'makefile.in')]
    hashes = {path.name: digest(path) for path in scripts}
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env['GERBIL_BUILD_CORES'] = str(cores)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='source-owned-native-object-capture-one-original-staging-unit-not-speed-or-full-toolchain',
                  module=row['module'], generatedCSha256=digest(source), driverSha256=hashes,
                  originalGscSourceDispatch=args.gsc_source,
                  schemeSourceSha256=digest(scheme_source), macroInputSha256=digest(macro_source),
                  gscSha256=build['gscSha256'], headerSha256=build['headerSha256'],
                  hardwareWorkers=cores, runs=[], hostLoadStart=os.getloadavg())
    try:
        def compile(role):
            directory = output/role
            directory.mkdir()
            image = directory/'module.o1'
            native_env = dict(env, GAMBITDIR_INCLUDE=str(home/'include'), GAMBITDIR_LIB=str(home/'lib'),
                BUILD_DYN_INPUT_FILENAMES_PARAM=str(source), BUILD_DYN_META_INFO_FILE_PARAM=str(source),
                BUILD_DYN_OUTPUT_FILENAME_PARAM=str(image), GAMBUILD_VERBOSE='1',
                GAMBIT_DARWIN_NATIVE_OBJECTS='1' if role == 'captured' else '0')
            driver = driver_source/'gambuild-C' if role == 'captured' else home/'bin/gambuild-C'
            command = [str(driver), 'dyn']
            if args.gsc_source:
                for key in tuple(native_env):
                    if key.startswith('BUILD_DYN_'):
                        del native_env[key]
                native_env['GAMBOPT'] = (f"~~bin={driver.parent},~~lib={home/'lib'},"
                                         f"~~include={home/'include'}")
                command = gsc_recipe_command(home, row['module'], image)
                command[1:2] = ['-dynamic', '-keep-temp', '-verbose']
                isolated_source = directory/'module.scm'
                shutil.copyfile(scheme_source, isolated_source)
                command[-1] = str(isolated_source)
            result = run(command, output, native_env, output/f'{role}.log', 180)
            if args.gsc_source:
                generated = image.with_suffix('.c')
                if digest(generated) != row['generatedCSha256']:
                    raise ValueError('GSC-generated C differs from locked original macro-correct input')
                result['generatedCSha256'] = digest(generated)
            result['role'] = role
            return result
        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(compile, role) for role in ('baseline', 'captured')]
            report['runs'] = [future.result() for future in futures]
        captured = output/'captured/module.o1'
        manifest = read_manifest(captured)
        native_env = dict(env, GAMBITDIR_INCLUDE=str(home/'include'), GAMBITDIR_LIB=str(home/'lib'),
            BUILD_DYN_INPUT_FILENAMES_PARAM=str(manifest['objectPath']), BUILD_DYN_META_INFO_FILE_PARAM=str(source),
            BUILD_DYN_OUTPUT_FILENAME_PARAM=str(output/'relinked.o1'), GAMBUILD_VERBOSE='1',
            GAMBIT_DARWIN_NATIVE_OBJECTS='0')
        report['runs'].append(run([str(home/'bin/gambuild-C'), 'dyn'], output, native_env, output/'relink.log', 180))
        images = [output/'baseline/module.o1', captured, output/'relinked.o1']
        texts = [text_section(path.read_bytes()) for path in images]
        semantics = [image_semantics(path.read_bytes()) for path in images]
        if not all(text == texts[0] for text in texts) or not all(item == semantics[0] for item in semantics):
            raise ValueError('captured or relinked native text/linkage differs from original driver')
        if (hashes != {path.name: digest(path) for path in scripts}
                or digest(source) != row['generatedCSha256']
                or digest(scheme_source) != report['schemeSourceSha256']
                or digest(macro_source) != report['macroInputSha256']):
            raise ValueError('driver/source changed during capture')
        report.update(nativeTextByteExact=True, nativeTextSha256=hashlib.sha256(texts[0]).hexdigest(),
                      capturedObjectSha256=manifest['objectSha256'], nativeLinkageMatched=True,
                      imageSha256=[digest(path) for path in images], qualified=True)
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        report['hostLoadEnd'] = os.getloadavg()
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
