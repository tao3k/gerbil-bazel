"""Fail closed when a test subprocess selects anything but its measured binary."""
import hashlib
from pathlib import Path
import shutil


TOOL_ENV = dict(gxi='GERBIL_MCP_GXI_PATH', gxc='GERBIL_MCP_GXC_PATH',
                gerbil='GERBIL_MCP_GERBIL_PATH', gxpkg='GERBIL_MCP_GXPKG_PATH')


def validate_tools(env, binary, expected_sha256):
    binary = Path(binary).resolve(strict=True)
    result = {}
    for name, key in TOOL_ENV.items():
        value = env.get(key)
        if not value:
            raise ValueError(f'missing explicit {key}')
        explicit = Path(value).resolve(strict=True)
        found = shutil.which(name, path=env.get('PATH', ''))
        if explicit != binary or not found or Path(found).resolve(strict=True) != binary:
            raise ValueError(f'{name} escapes selected build')
        result[name] = dict(sha256=expected_sha256, selectedBuild=True)
    # Every checked alias resolves to this same file, not four different binaries.
    before = binary.stat()
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    after = binary.stat()
    identity = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if actual != expected_sha256 or identity(before) != identity(after):
        raise ValueError('selected binary differs from retained anchor or changed during validation')
    return result
