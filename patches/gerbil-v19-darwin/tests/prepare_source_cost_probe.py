"""Measure original interpreter boundaries; no cache or source-loader policy change."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shlex
import subprocess

from bazel_host_environment import build_environment


def instrument(text, passive=False):
    preamble = '''
(c-declare "#include \\"gambit-source-cost-probe.h\\"")
(define ##gb-source-cost-begin (c-lambda (int) void "gb_source_begin(___arg1);"))
(define ##gb-source-cost-end (c-lambda (int) void "gb_source_end(___arg1);"))
(define (##gb-source-cost kind thunk)
  (dynamic-wind (lambda () (##gb-source-cost-begin kind))
                thunk
                (lambda () (##gb-source-cost-end kind))))
'''
    if passive:
        preamble = preamble.replace('''  (dynamic-wind (lambda () (##gb-source-cost-begin kind))
                thunk
                (lambda () (##gb-source-cost-end kind))))''', '''  (##gb-source-cost-begin kind)
  (##call-with-values thunk
    (lambda results
      (##gb-source-cost-end kind)
      (##apply ##values results))))''')
    def wrap(expression, kind):
        return f'(##gb-source-cost {kind} (lambda () {expression}))'
    expressions = [
        ('(##read-all-as-a-begin-expr-from-psettings\n'
         '            psettings\n            path-or-settings\n'
         '            (##current-readtable)\n            ##wrap-datum\n'
         "            ##unwrap-datum\n            '())", 0, 1),
        ('(##top-cte-clone ##interaction-cte)', 1, 1),
        ('(##compile-top top-cte\n'
         '                          (##sourcify src (##make-source #f #f)))', 2, 2),
        ('(##setup-requirements-and-run c #f)', 3, 2),
    ]
    for expression, kind, expected in expressions:
        if text.count(expression) != expected:
            raise ValueError(f'original evaluation boundary changed: {kind}')
        text = text.replace(expression, wrap(expression, kind))
    return preamble + text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mcp', type=Path, required=True)
    parser.add_argument('--passive-boundaries', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if platform.system() != 'Darwin' or output.exists() or not all(
            path.is_relative_to(repo / '.data') for path in (baseline, output, args.mcp.resolve())):
        parser.error('fresh isolated Darwin project-data paths required')
    subprocess.run(['/bin/cp', '-cR', str(baseline), str(output)], check=True)
    lib = output / 'src/gambit/lib'
    source = lib / '_eval.scm'
    checker = Path(__file__).with_name('run_gambit_source_check.py')
    def check(stage, syntax=False):
        command = ['python3', str(checker), '--source', str(source), '--baseline', str(baseline),
                   '--mcp', str(args.mcp.resolve()), '--output', str(output / f'{stage}.jsonl')]
        if syntax:
            command.append('--syntax')
        subprocess.run(command, check=True)
    check('before-balance')
    original = source.read_text()
    changed = instrument(original, args.passive_boundaries)
    source.write_text(changed)
    check('after-balance')
    header = Path(__file__).with_name('gambit-source-cost-probe.h')
    (lib / header.name).write_bytes(header.read_bytes())
    report = dict(scope='interpreter-boundary-cost-diagnostic-not-performance',
                  originalSha256=hashlib.sha256(original.encode()).hexdigest(),
                  sourceSha256=hashlib.sha256(changed.encode()).hexdigest(),
                  headerSha256=hashlib.sha256(header.read_bytes()).hexdigest(),
                  sourceLoadPolicyChanged=False, cteIsolationChanged=False, consumerChanged=False,
                  passiveBoundaries=args.passive_boundaries,
                  nonlocalExitCostsValid=not args.passive_boundaries)
    try:
        check('after-syntax', True)
    except subprocess.CalledProcessError:
        report['mcpSyntaxUnavailable'] = True
        print('MCP syntax unavailable; original GSC full macro-context generation required', flush=True)
    env = build_environment()
    home = baseline / 'build'
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    dry = subprocess.check_output(['make', '-n', '-B', '_eval.c'], cwd=lib, env=env, text=True)
    commands = [shlex.split(line) for line in dry.splitlines() if line.startswith('../gsc-boot ')]
    if len(commands) != 1:
        raise RuntimeError('ambiguous official EVAL generation command')
    command = commands[0]
    command[0] = str(home / 'bin/gsc')
    command[1] = f"-:~~bin={home / 'bin'},~~lib={lib},~~include={home / 'include'}"
    report['generationCommand'] = command
    with (output / 'generate-eval.log').open('w') as log:
        subprocess.run(command, cwd=lib, env=env, stdout=log, stderr=subprocess.STDOUT,
                       timeout=300, check=True)
    report['generatedCSha256'] = hashlib.sha256((lib / '_eval.c').read_bytes()).hexdigest()
    report['fullMacroContextGenerationPassed'] = True
    (output / 'source-cost-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('SOURCE-COST-PREPARED original loader/CTE policy; diagnostic only', flush=True)


if __name__ == '__main__':
    main()
