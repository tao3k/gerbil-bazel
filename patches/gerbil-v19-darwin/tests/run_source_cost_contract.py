"""Qualify observation paths and value semantics without qualifying performance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, output = (p.resolve() for p in (args.baseline, args.candidate, args.output))
    if not all(p.is_relative_to(root / '.data') for p in (baseline, candidate, output)):
        parser.error('isolated project-data paths required')
    output.mkdir(parents=True, exist_ok=False)
    fixture = output / 'source.scm'
    fixture.write_text('(displayln "SOURCE-CONTRACT-OK")\n')
    home = baseline / 'build'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_PATH=str(output / 'empty-user'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    report = dict(qualified=False, performanceQualified=False,
                  scope='native-observer-path-and-value-contract', runs=[])
    report['candidateBinarySha256'] = hashlib.sha256((candidate / 'build/bin/gxi').read_bytes()).hexdigest()
    expected = 'SOURCE-CONTRACT-OK\nVALUES-CONTRACT-OK\nCONTRACT-RETURN-OK\n'
    for role, source in (('baseline', baseline), ('candidate', candidate)):
        cost = '(lambda (kind thunk) (thunk))' if role == 'baseline' else '##gb-source-cost'
        expression = f'''(##load {json.dumps(str(fixture))} (lambda args #f) #t #t #f #t)
(let* ((cost {cost})
       (result (##call-with-values (lambda () (cost 3 (lambda () (##values 11 23)))) list)))
  (unless (equal? result '(11 23)) (error "observer changed values" result))
  (displayln "VALUES-CONTRACT-OK"))
(displayln "CONTRACT-RETURN-OK")'''
        process_env = dict(env, GAMBIT_DARWIN_SOURCE_COST_PREFIX=str(output / role))
        result = subprocess.run([str(source / 'build/bin/gxi'), '-e', expression],
                                env=process_env, text=True, capture_output=True, timeout=90)
        (output / f'{role}.log').write_text(result.stdout + result.stderr)
        report['runs'].append(dict(role=role, exitCode=result.returncode))
        if result.returncode or result.stdout != expected or result.stderr:
            raise RuntimeError(f'{role} source/value contract failed')
    paths = list(output.glob('candidate.*.json'))
    if len(paths) != 1:
        raise RuntimeError('exactly one native observation file required')
    costs = json.loads(paths[0].read_text())
    if (costs['errors'] or costs['openFrames']
            or [p['kind'] for p in costs['phases']] != list(range(4))
            or any(p['calls'] <= 0 for p in costs['phases'])):
        raise RuntimeError('all four native boundaries must execute and close')
    report['nativeCosts'] = costs
    report['qualified'] = True
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('SOURCE-COST-CONTRACT-OK original/candidate outputs and multiple values match', flush=True)


if __name__ == '__main__':
    main()
