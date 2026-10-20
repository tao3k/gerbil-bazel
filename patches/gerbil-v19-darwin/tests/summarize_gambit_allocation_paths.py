#!/usr/bin/env python3
"""Inspect allocation trace coverage in retained C; no build or timing claim."""
import argparse
import hashlib
import json
from pathlib import Path

from gambit_host_coalescing import render


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[3] / '.data'
    profile, output = args.profile.resolve(), args.output.resolve()
    if not all(path.is_relative_to(data) for path in (profile, output)):
        parser.error('retained sources and generation must stay under project .data')
    output.mkdir(parents=True, exist_ok=False)
    names = ('expander/core', 'expander/module', 'expander/compile', 'expander/stx',
             'expander/stxcase', 'runtime/hash', 'runtime/table', 'expander/top',
             'runtime/mop', 'runtime/interface', 'runtime/util')
    paths = [profile / 'source/build/lib/static' / ('gerbil__' + name.replace('/', '__') + '.c')
             for name in names]
    source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    source, details = render(paths, (profile / 'gerbil-link.c').read_text(), output,
                             guarded_readonly_traces=True, guarded_trace_polls=True,
                             guarded_trace_restart_polls=True, guarded_trace_allocations=True)
    (output / 'generated.c').write_text(source)
    details.update(scope='static-allocation-trace-coverage-not-native-performance',
                   qualified=False, performanceQualified=False, sourceHashes=source_hashes)
    (output / 'report.json').write_text(json.dumps(details, indent=2) + '\n')
    print(json.dumps({'sites': len(details['guardedReadOnlyTraces']),
                      'refusals': details['transactionalTraceRefusals'][:12]}, indent=2))


if __name__ == '__main__':
    main()
