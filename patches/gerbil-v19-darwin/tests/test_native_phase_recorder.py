"""Tests utility delegation, not Scheme compilation or test supervision."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / '.data/d1510-native-phase-recorder-v1/recorder'
pytestmark = pytest.mark.skipif(not BINARY.exists(), reason='owned Darwin GNU recorder required')


def recorder(tmp_path, target, trace=True):
    command = tmp_path / 'gsc'
    shutil.copyfile(BINARY, command)
    command.chmod(0o700)
    Path(str(command) + '.target').write_text(target + '\n')
    env = dict(os.environ)
    env.pop('GAMBIT_NATIVE_PHASE_TRACE', None)
    if trace:
        env['GAMBIT_NATIVE_PHASE_TRACE'] = str(tmp_path / 'trace')
    return command, env


@pytest.mark.parametrize('trace', [False, True])
@pytest.mark.parametrize('target,status', [('/usr/bin/true', 0), ('/usr/bin/false', 1)])
def test_exit_propagation(tmp_path, trace, target, status):
    command, env = recorder(tmp_path, target, trace)
    result = subprocess.run([str(command), '-obj'], env=env, capture_output=True, timeout=3)
    assert result.returncode == status
    assert result.stdout == result.stderr == b''
    if trace:
        row = (tmp_path / 'trace').read_text().strip().split('\t')
        assert len(row) == 9 and row[0] == '1' and row[3] == 'gsc-object'
        assert int(row[5]) >= int(row[4]) > 0
        assert int(row[6]) == status
    else:
        assert not (tmp_path / 'trace').exists()


def test_arguments_and_stdout_preserved(tmp_path):
    command, env = recorder(tmp_path, '/bin/echo')
    result = subprocess.run([str(command), 'two words', 'literal$'], env=env,
                            capture_output=True, timeout=3)
    assert result.returncode == 0 and result.stdout == b'two words literal$\n'


def test_symlink_trace_denied_without_execution(tmp_path):
    command, env = recorder(tmp_path, '/usr/bin/true')
    foreign = tmp_path / 'foreign'
    foreign.write_text('unchanged')
    (tmp_path / 'trace').symlink_to(foreign)
    assert subprocess.run([str(command)], env=env, timeout=3).returncode == 125
    assert foreign.read_text() == 'unchanged'


def test_termination_forwarded_and_recorded(tmp_path):
    command, env = recorder(tmp_path, '/bin/sh')
    ready = tmp_path / 'ready'
    process = subprocess.Popen([str(command), '-c',
        'printf ready > "$1"; exec /bin/sleep 30', 'ready-marker', str(ready)], env=env)
    try:
        deadline = time.monotonic() + 3
        while not ready.exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=3) == 143
        assert (tmp_path / 'trace').read_text().split('\t')[6] == '143'
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
