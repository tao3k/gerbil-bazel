"""Preflight metadata rejection only; Bash owns real native ABI controls."""
import subprocess
import tempfile
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[2]


@pytest.mark.parametrize('control', [
    'missing-source', 'symlink-source', 'missing-header', 'symlink-header',
    'single-vm-header', 'helper-drift',
])
def test_unqualified_abi_is_denied_before_native_launch(control):
    with tempfile.TemporaryDirectory(prefix='frozen-abi-preflight-', dir=ROOT / '.data') as name:
        fixture = Path(name)
        workspace = fixture / 'workspace'
        home = workspace / 'toolchain'
        (home / 'include').mkdir(parents=True)
        (home / 'bin').mkdir()
        source = workspace / 'project/.cache/ascent/native-library/lib/static/gerbil-ascent__core__dependency-graph.c'
        source.parent.mkdir(parents=True)
        source.write_text('int value(void) { return 17; }\n')
        header = home / 'include/gambit.h'
        header.write_text('#define ___MULTIPLE_VMS\n')
        (home / 'bin/gambit-static-object-reuse').write_text('unqualified helper')
        if control == 'missing-source':
            source.unlink()
        elif control == 'symlink-source':
            target = fixture / 'source'
            source.rename(target)
            source.symlink_to(target)
        elif control == 'missing-header':
            header.unlink()
        elif control == 'symlink-header':
            target = fixture / 'header'
            header.rename(target)
            header.symlink_to(target)
        elif control == 'single-vm-header':
            header.write_text('#define ___SINGLE_VM\n')
        elif control == 'helper-drift':
            selected_header = ROOT / '.data/d1510-static-c-snapshot-ascent-v1/toolchain/include/gambit.h'
            if not selected_header.exists():
                pytest.skip('owned qualified Multiple-VM header required')
            header.write_bytes(selected_header.read_bytes())
        receipt = fixture / 'receipt'
        result = subprocess.run(
            ['bash', str(TESTS / 'check_frozen_ascent_abi.sh'), str(workspace), str(receipt)],
            capture_output=True, timeout=5,
        )
        assert result.returncode != 0
        assert not receipt.exists()
