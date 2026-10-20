"""Check missing original Gambit macro input, never qualify a speed candidate."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment


def gsc_recipe_command(home, module, target, include_macros=True, original_std_debug=False,
                       native_version=1):
    if type(native_version) is not int or native_version < 1:
        raise ValueError('positive native linker version required')
    command = [str(home/'bin/gsc'), '-c', '-module-ref', Path(module).name,
               '-linker-name', Path(module).name+f'.o{native_version}', '-o', str(target)]
    if original_std_debug and module.startswith('std/'):
        command += ['-debug-source', '-track-scheme', '-cc-options', '-g']
    if include_macros:
        command += ['-e', '(include '+json.dumps(str(home/'lib/_gambit#.scm'))+')',
                    '-e', '(define-cond-expand-feature|gerbil-separate-compilation|)']
    return command + [str(home/'lib'/f'{module}.scm')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if not all(path.is_relative_to(root / '.data') for path in (baseline, output)):
        parser.error('isolated current-input recipe audit required')
    output.mkdir(parents=True, exist_ok=False)
    home = baseline / 'build'
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home/'bin/gsc'), GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f"~~bin={home/'bin'},~~lib={home/'lib'},~~include={home/'include'}")
    modules = ('gerbil/runtime/thread~0', 'std/os/device~0', 'std/format/reader~0')
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='missing-original-gambit-macro-input-source-recipe-audit', cores=cores, runs=[],
                  gscSha256=hashlib.sha256((home/'bin/gsc').read_bytes()).hexdigest(),
                  macroInputSha256=hashlib.sha256((home/'lib/_gambit#.scm').read_bytes()).hexdigest())

    def generate(module):
        index = modules.index(module)
        target = output / f'{index}.c'
        command = gsc_recipe_command(home, module, target)
        with (output/f'{index}.log').open('w') as log:
            status = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60).returncode
        content = (output/f'{index}.log').read_text()
        if status or '*** ERROR' in content or '*** WARNING -- Variable "macro-' in content or not target.is_file():
            raise RuntimeError(f'{module}: original macro-input generation failed')
        print(f'RECIPE-MACRO-OK {module}', flush=True)
        return dict(module=module, exitCode=status,
                    sourceSha256=hashlib.sha256((home/'lib'/f'{module}.scm').read_bytes()).hexdigest(),
                    generatedCSha256=hashlib.sha256(target.read_bytes()).hexdigest())

    try:
        with ThreadPoolExecutor(max_workers=cores) as pool:
            report['runs'] = list(pool.map(generate, modules))
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
