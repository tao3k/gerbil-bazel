"""Check original std debug recipe against installed native text, not speed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from audit_startup_gsc_recipe import gsc_recipe_command
from bazel_host_environment import build_environment
from native_object_manifest import digest, text_section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if not all(path.is_relative_to(root/'.data') for path in (baseline, output)):
        parser.error('isolated original toolchain and fresh output required')
    output.mkdir(parents=True, exist_ok=False)
    home = baseline/'build'
    env = build_environment()
    for key in tuple(env):
        if key.startswith('BUILD_DYN_'):
            del env[key]
    env.update(GERBIL_HOME=str(home),
               GAMBOPT=f"~~bin={home/'bin'},~~lib={home/'lib'},~~include={home/'include'}")
    workers = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    modules = ('std/test/unit~0', 'std/make~0', 'std/build-script~0')
    report = dict(scope='original-std-debug-recipe-construction-diagnostic',
                  performanceQualified=False, semanticEquivalenceProven=False,
                  hardwareWorkers=workers, originalGscSha256=digest(home/'bin/gsc'), rows=[])

    def compile_module(module):
        directory = output/module.replace('/', '_')
        directory.mkdir()
        source = home/'lib'/f'{module}.scm'
        local_source = directory/'module.scm'
        shutil.copyfile(source, local_source)
        image = directory/'module.o1'
        command = gsc_recipe_command(home, module, image, original_std_debug=True)
        command[1:2] = ['-dynamic', '-keep-temp', '-verbose']
        command[-1] = str(local_source)
        with (directory/'compile.log').open('w') as log:
            result = subprocess.run(command, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=180)
        if result.returncode or not image.is_file() or '*** ERROR' in (directory/'compile.log').read_text():
            raise RuntimeError(f'{module}: original debug recipe compilation failed')
        original = home/'lib'/f'{module}.o1'
        texts = [text_section(path.read_bytes()) for path in (original, image)]
        row = dict(module=module, schemeSourceSha256=digest(source),
                   generatedCSha256=digest(directory/'module.c'),
                   installedImageSha256=digest(original), generatedImageSha256=digest(image),
                   textBytes=[len(text) for text in texts],
                   textSha256=[hashlib.sha256(text).hexdigest() for text in texts],
                   nativeTextByteExact=texts[0] == texts[1])
        print(f"DEBUG-RECIPE {module} exact={row['nativeTextByteExact']} bytes={row['textBytes']}", flush=True)
        return row

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            report['rows'] = list(pool.map(compile_module, modules))
        report['allNativeTextByteExact'] = all(row['nativeTextByteExact'] for row in report['rows'])
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
