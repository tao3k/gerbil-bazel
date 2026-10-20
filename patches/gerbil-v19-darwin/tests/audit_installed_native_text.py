"""Compare captured native text with installed originals; never infer speedup."""
import argparse
import hashlib
import json
from pathlib import Path

from native_object_manifest import digest, text_section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--capture', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    paths = [args.baseline, args.output, *args.capture]
    if not all(path.resolve().is_relative_to(root/'.data') for path in paths):
        parser.error('isolated project-data inputs and output required')
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for directory in args.capture:
        receipt_path = directory/'report.json'
        receipt = json.loads(receipt_path.read_text())
        if not receipt.get('qualified') or not receipt.get('originalGscSourceDispatch'):
            raise ValueError('actual successful original-GSC capture required')
        original = args.baseline/'build/lib'/f"{receipt['module']}.o1"
        captured = directory/'captured/module.o1'
        if digest(captured) != receipt['imageSha256'][1]:
            raise ValueError('captured image differs from its receipt')
        texts = [text_section(path.read_bytes()) for path in (original, captured)]
        rows.append(dict(module=receipt['module'],
                         captureReceiptSha256=digest(receipt_path),
                         installedImageSha256=digest(original),
                         capturedImageSha256=digest(captured),
                         textBytes=[len(text) for text in texts],
                         textSha256=[hashlib.sha256(text).hexdigest() for text in texts],
                         nativeTextByteExact=texts[0] == texts[1]))
    report = dict(scope='installed-versus-regenerated-native-text-comparison',
                  performanceQualified=False, semanticEquivalenceProven=False,
                  allNativeTextByteExact=all(row['nativeTextByteExact'] for row in rows),
                  mismatchIsNotProofOfRegression=True, rows=rows)
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    for row in rows:
        print(f"INSTALLED-TEXT {row['module']} exact={row['nativeTextByteExact']} "
              f"bytes={row['textBytes']}", flush=True)


if __name__ == '__main__':
    main()
