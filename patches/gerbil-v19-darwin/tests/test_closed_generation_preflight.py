import subprocess
import tempfile
from pathlib import Path

import pytest


TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[2]


@pytest.mark.parametrize('script', [
    'run_closed_generation_cost.sh', 'check_static_closure_generation_cost.sh',
])
def test_abi_mismatch_is_rejected_before_output_or_native_launch(script):
    with tempfile.TemporaryDirectory(prefix='closed-abi-preflight-', dir=ROOT / '.data') as name:
        root = Path(name)
        original, candidate = root / 'original', root / 'candidate'
        for home, header in [(original, 'single VM'), (candidate, 'multiple VM')]:
            (home / 'bin').mkdir(parents=True)
            (home / 'include').mkdir()
            (home / 'include/gambit.h').write_text(header)
        source, output = root / 'source', root / 'receipt'
        source.mkdir()
        if script == 'run_closed_generation_cost.sh':
            args = [candidate / 'bin', original, source, output]
        else:
            args = [original / 'bin', source, output, candidate / 'bin']
        result = subprocess.run(['bash', str(TESTS / script), *map(str, args)],
                                capture_output=True, text=True, timeout=5)
        assert result.returncode != 0
        assert not output.exists()
