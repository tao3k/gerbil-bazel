import json
from pathlib import Path

from .storage import relative


def protected_paths(root):
    """Follow pinned receipt graphs; protect complete baseline experiment roots."""
    configuration = root / 'tools/bench/retention.json'
    if not configuration.is_file():
        raise ValueError('retention protection configuration required')
    config = json.loads(configuration.read_text())
    protected = {relative(root, path) for path in config['protectedPaths']}
    pending = [relative(root, path) for path in config['protectedReceipts']]
    pending.extend(path for name in config.get('optionalReceipts', [])
                   if (path := relative(root, name)).is_file())
    seen = set()
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(key)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str):
            if value.startswith(str(root) + '/'):
                value = value[len(str(root)) + 1:]
            if value.startswith(('.data/', 'patches/')):
                path = relative(root, value)
                if value.startswith('.data/'):
                    parts = Path(value).parts
                    extent = 4 if len(parts) >= 4 and parts[1:3] == ('bench', 'runs') else 2
                    protected.add(relative(root, '/'.join(parts[:extent])))
                if path.suffix == '.json' and path.is_file() and path not in seen:
                    pending.append(path)
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        if len(seen) > 2048:
            raise ValueError('protection graph limit reached; refuse incomplete protection')
        visit(json.loads(path.read_text()))
    for receipt in (root / '.data/bench/runs').glob('*/receipt.json'):
        protected.update(relative(root, path) for path in json.loads(receipt.read_text())['protectedPaths'])
    return protected


def intersects(path, protected):
    return any(path == entry or path.is_relative_to(entry) or entry.is_relative_to(path)
               for entry in protected)
