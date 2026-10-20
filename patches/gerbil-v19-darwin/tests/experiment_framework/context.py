from dataclasses import dataclass
from pathlib import Path
import subprocess

from native_object_manifest import digest


FROZEN_47_SHA256 = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'


def data_path(root, path, *, fresh=False):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(root / '.data') or (fresh and resolved.exists()):
        raise ValueError('persistent .data path required; outputs must be fresh')
    return resolved


def hardware_workers():
    workers = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    if workers < 1:
        raise ValueError('positive physical worker count required')
    return workers


@dataclass(frozen=True)
class Toolchain:
    binary: Path
    home: Path
    expected_sha256: str | None = None

    def validate(self, root):
        data_path(root, self.binary)
        data_path(root, self.home)
        if not self.binary.is_file() or not (self.home / 'bin/gsc').is_file():
            raise ValueError('isolated runtime and compiler required')
        if self.expected_sha256 and digest(self.binary) != self.expected_sha256:
            raise ValueError('retained binary identity mismatch')
        return self

    def environment(self, base, *, package_home, load_paths, workers, bin_dir=None):
        env = dict(base)
        for key in tuple(env):
            if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')) or key == 'GERBIL_BUILD_PREFIX':
                env.pop(key)
        commands = bin_dir or self.home / 'bin'
        env.update(GERBIL_HOME=str(self.home), GERBIL_PATH=str(package_home),
                   GERBIL_LOADPATH=':'.join(map(str, load_paths)),
                   GERBIL_BUILD_CORES=str(workers), GERBIL_GSC=str(commands / 'gsc'),
                   GAMBOPT=f'~~bin={commands},~~lib={self.home / "lib"},~~include={self.home / "include"}')
        if bin_dir is not None:
            env.update(PATH=str(bin_dir) + ':' + env['PATH'], GERBIL_GXC=str(bin_dir / 'gxc'))
        return env


def retained_47(root, binary=None):
    return Toolchain(
        (binary or root / '.data/d1510-reader-whitespace-native-v2/gerbil').resolve(),
        root / '.data/d1510-mcp-test-source-home-v2/build',
        None if binary is not None else FROZEN_47_SHA256).validate(root)
