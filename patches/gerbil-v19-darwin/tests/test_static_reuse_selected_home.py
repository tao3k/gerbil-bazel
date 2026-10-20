import subprocess
import tempfile
from pathlib import Path

import pytest


TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[2]
SCRIPTS = [
    'check_static_object_reuse.sh', 'check_static_reuse_identity.sh',
    'check_static_reuse_safety.sh', 'check_static_reuse_toolchain.sh',
]


@pytest.mark.parametrize('script', SCRIPTS)
@pytest.mark.parametrize('header', ['missing', 'symlink'])
def test_invalid_selected_home_is_denied_before_native_launch(script, header):
    # This is a shell preflight test; no Scheme or native test process is started.
    with tempfile.TemporaryDirectory(prefix='static-home-preflight-', dir=ROOT / '.data') as name:
        fixture = Path(name)
        home = fixture / 'home'
        (home / 'include').mkdir(parents=True)
        if header == 'symlink':
            target = fixture / 'target-header'
            target.write_text('not an admitted header')
            (home / 'include/gambit.h').symlink_to(target)
        output = fixture / 'receipt'
        result = subprocess.run(
            ['bash', str(TESTS / script), str(fixture / 'bin'), str(output), str(home)],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode != 0
        assert not output.exists()


@pytest.mark.parametrize('prefix', [[], ['gtimeout', '--signal=TERM', '--kill-after=1', '135s']])
def test_optional_deadline_preserves_argv_under_bash_nounset(prefix):
    # Exercise only shell argv expansion; no consumer or interpreter is launched.
    script = TESTS / 'run_isolated_ascent_static_reuse.sh'
    expansion = '${command_prefix[@]+"${command_prefix[@]}"}'
    assert script.read_text().count(expansion) == 2
    result = subprocess.run(
        ['/bin/bash', '-uc',
         'command_prefix=("$@"); set -- ' + expansion +
         ' just test-native-suite auto; printf "%s\\0" "$@"', 'preflight', *prefix],
        capture_output=True, timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().split('\0')[:-1] == prefix + ['just', 'test-native-suite', 'auto']
