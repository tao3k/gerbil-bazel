"""Branch from the unchanged generated 0018 driver, retaining its loader path."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiled', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated .data output required')
    original = root / '.data/d1510-source-loader-linked/gerbil__compiler__driver.scm'
    text = original.read_text()
    anchor = '(gxc#compile-scm-file__1\n'
    if text.count(anchor) != 1:
        raise ValueError('exact phi call site required')
    text = text.replace(anchor, '(gxc#compile-generated-phi-source\n', 1)
    helper = Path(__file__).with_name('phi_source_helper.scm').read_text()
    if args.compiled:
        helper = helper.split('(define (gxc#compile-generated-phi-source', 1)[0]
        helper += Path(__file__).with_name('compiled_phi_helper.scm').read_text()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + '\n' + helper)
    print(json.dumps(dict(sourcePrepared=True,
                          originalSha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                          helperSha256=hashlib.sha256(helper.encode()).hexdigest())))


if __name__ == '__main__':
    main()
