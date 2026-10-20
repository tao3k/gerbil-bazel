"""Bind a compiled module overlay without changing its underlying runtime."""
import hashlib
from pathlib import Path


def module_overlay_identity(library, module):
    parts = module.split('/')
    if not all(part and all(c.isalnum() or c in '_-' for c in part) for part in parts):
        raise ValueError('invalid overlay module')
    if library.resolve() != library.absolute():
        raise ValueError('overlay path must not traverse symlinks')
    stem = Path(*parts)
    directory = library / stem.parent
    if directory.is_symlink():
        raise ValueError('overlay module directory symlink')
    files = sorted(path for path in directory.iterdir()
                   if (path.name.startswith(stem.name + '.') or path.name.startswith(stem.name + '~'))
                   and not (path.name.endswith('.dSYM') and path.is_dir() and not path.is_symlink()))
    files.append(library / 'static' / ('__'.join(parts) + '.scm'))
    if not (library / stem.with_suffix('.ssi')).is_file() or not any(path.suffix == '.o1' for path in files):
        raise ValueError('compiled overlay interface and image required')
    result = {}
    for path in files:
        if path.is_symlink() or not path.is_file() or path.resolve() != path.absolute():
            raise ValueError('regular non-symlink overlay file required')
        result[str(path.relative_to(library))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
