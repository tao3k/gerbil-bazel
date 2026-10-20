"""Identity-checked single-object replacement in a retained isolated runtime."""
import argparse
import json
from pathlib import Path

from bazel_host_environment import build_environment
from native_object_manifest import digest, executable_rpaths
from experiment_framework.context import data_path, FROZEN_47_SHA256
from experiment_framework.process import record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--original-object', type=Path, required=True)
    parser.add_argument('--replacement-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    manifest_path = data_path(root, args.manifest)
    original = data_path(root, args.original_object)
    replacement_report = data_path(root, args.replacement_report)
    output = data_path(root, args.output, fresh=True)
    baseline = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())
    candidate = json.loads(replacement_report.read_text())
    replacement = replacement_report.parent / ('diagnostic.a' if original.suffix == '.a' else 'diagnostic.o')
    if (not manifest['qualified'] or manifest['binarySha256'] != FROZEN_47_SHA256
            or digest(baseline / 'gerbil') != FROZEN_47_SHA256
            or not candidate['completed'] or not candidate['inputsUnchanged']
            or digest(replacement) != candidate['artifacts'][replacement.name]):
        raise ValueError('retained runtime and completed candidate identities required')
    identities = {**manifest['frozenObjectHashes'], **manifest['privateRuntimeObjects']}
    if str(original.relative_to(root)) not in manifest['frozenObjectHashes']:
        raise ValueError('replacement must own one frozen native object')
    for path, sha in {**identities, **candidate['inputHashes']}.items():
        if digest(data_path(root, root / path)) != sha:
            raise ValueError('original input drift: ' + path)
    providers = [baseline / f'{i}.o' for i in range(len(manifest['providers']))]
    if any(digest(p) != row['renamedObjectSha256'] for p, row in zip(providers, manifest['providers'])):
        raise ValueError('provider identity drift')
    objects = [root / p for p in manifest['frozenObjectHashes'] if not p.endswith('libgambit.a')]
    archive = [root / p for p in manifest['frozenObjectHashes'] if p.endswith('libgambit.a')]
    if len(archive) != 1 or [*objects, *archive].count(original) != 1:
        raise ValueError('one runtime archive and one owned replacement required')
    backend = baseline / 'os_dyn_embedded.o'
    extra = [root / p for p in manifest['privateRuntimeObjects']]
    inputs = {str(p.relative_to(root)): digest(p) for p in
              [*objects, *providers, backend, *extra, *archive, replacement, baseline / 'gerbil']}
    inputs.update(candidate['inputHashes'])
    gsc = data_path(root, archive[0].parent.parent / 'bin/gsc')
    if digest(gsc) != manifest['gscSha256']:
        raise ValueError('retained GSC identity required')
    inputs[str(gsc.relative_to(root))] = digest(gsc)
    output.mkdir()
    (output / 'control').mkdir()
    env = build_environment()
    # Reproduce literal retained load commands, not changing Homebrew opt targets.
    rpaths = executable_rpaths((baseline / 'gerbil').read_bytes())
    link_flags = ['-nodefaultrpaths', *[f'-Wl,-rpath,{path}' for path in rpaths]]
    report = dict(qualified=False, performanceQualified=False, productionAdmitted=False,
                  diagnosticOnly=candidate.get('diagnosticOnly') is True,
                  scope='single-object-runtime-construction-not-performance-admission',
                  inputHashes=inputs, gscSha256=manifest['gscSha256'], steps=[])
    try:
        for role in ('control', 'candidate'):
            target = output / 'control/gerbil' if role == 'control' else output / 'gerbil'
            chosen = [replacement if role == 'candidate' and p == original else p for p in objects]
            chosen_archive = [replacement if role == 'candidate' and p == original else p for p in archive]
            code = record([env['CC'], *link_flags, '-o', str(target), *map(str, chosen), *map(str, providers),
                           str(backend), *map(str, extra), *map(str, chosen_archive), '-ldl', '-lm'],
                          root, env, output / (role + '-link.log'), timeout=50)
            report['steps'].append(dict(role=role, exitCode=code))
            if code:
                return 1
            if role == 'control':
                report['controlMatchesRetained'] = digest(target) == FROZEN_47_SHA256
                if not report['controlMatchesRetained']:
                    return 1
        (output / 'gxi').symlink_to('gerbil')
        report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
        report['binarySha256'] = digest(output / 'gerbil')
        report['qualified'] = report['inputsUnchanged']
        return 0 if report['qualified'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'inputHashes'}), flush=True)
