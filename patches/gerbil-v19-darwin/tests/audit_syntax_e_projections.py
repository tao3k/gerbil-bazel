"""Find immediate projection consumers; never remove producer side effects."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from gambit_known_returns import PROC

LABEL = re.compile(r'___DEF_SLBL\((\d+),(___\w+)\)')
CALL = re.compile(
    r'___SET_R0\(___LBL\((\d+)\)\)\s*'
    r'(?:___ADJFP\(-?\d+\)\s*)?'
    r'___JUMPGLONOTSAFE\(___SET_NARGS\(1\),\d+,___G_gx_23_syntax_2d_e\)')
PROJECTION = re.compile(r'\s*___SET_R1\(___(CAR|CDR)\(___R1\)\)')


def projections(content):
    sites = []
    for procedure in PROC.finditer(content):
        body = procedure[2]
        labels = {}
        for label in LABEL.finditer(body):
            index = int(label[1])
            if index in labels:
                raise ValueError('ambiguous continuation label')
            labels[index] = label
        for call in CALL.finditer(body):
            continuation = labels.get(int(call[1]))
            if continuation is None:
                continue
            projection = PROJECTION.match(body, continuation.end())
            if projection:
                offset = procedure.start(2) + call.start()
                sites.append(dict(line=content.count('\n', 0, offset) + 1,
                                  continuation=continuation[2], field=projection[1],
                                  producerSideEffectsProvenRemovable=False))
    return sites


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/'
                     'd1510-source-loader-49-baseline.json').read_text())
    sites, inputs = [], {}
    for relative, expected in lock['inputHashes'].items():
        path = root / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'retained input changed: {relative}')
        inputs[relative] = actual
        sites.extend(dict(path=relative, **site) for site in projections(path.read_text()))
    result = dict(scope='retained-input-projection-opportunities-not-transform-or-speedup',
                  inputHashes=inputs, siteCount=len(sites),
                  carSites=sum(s['field'] == 'CAR' for s in sites),
                  cdrSites=sum(s['field'] == 'CDR' for s in sites), sites=sites)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('scope', 'siteCount', 'carSites', 'cdrSites')}))


if __name__ == '__main__':
    main()
