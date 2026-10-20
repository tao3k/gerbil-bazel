"""Utility-only wrapper argument checks; never starts a Scheme interpreter."""
import os
from pathlib import Path
import subprocess

import pytest


WRAPPER = Path(__file__).with_name('retained_entry_gxi.sh')


@pytest.mark.parametrize('arguments', [
    ['-:max-heap=1G,debug=q', 'entry.ss', 'test-file', 'path with spaces.ss'],
    ['-e', '(displayln "native")'],
    [],
])
def test_runtime_options_precede_injection_and_arguments_are_preserved(tmp_path, arguments):
    home = tmp_path / 'home'
    (home / 'bin').mkdir(parents=True)
    delegate = home / 'bin/gxi'
    delegate.write_text('#!/bin/sh\nprintf "%s\\0" "$@"\n')
    delegate.chmod(0o755)
    overlay = tmp_path / 'driver.o1'
    overlay.write_bytes(b'utility fixture only')
    env = dict(os.environ, GERBIL_HOME=str(home), GAMBIT_DARWIN_DRIVER_OVERLAY=str(overlay))
    result = subprocess.run(['bash', str(WRAPPER), *arguments], env=env,
                            capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    values = result.stdout.decode().split('\0')[:-1]
    leading = arguments[:1] if arguments and arguments[0].startswith('-:') else []
    assert values[:len(leading)] == leading
    assert values[len(leading)] == '-e'
    assert '(load (getenv "GAMBIT_DARWIN_DRIVER_OVERLAY"))' in values[len(leading) + 1]
    assert values[len(leading) + 2:] == arguments[len(leading):]


def test_overlay_symlink_is_rejected_before_delegate(tmp_path):
    target = tmp_path / 'target'
    target.write_bytes(b'fixture')
    overlay = tmp_path / 'driver.o1'
    overlay.symlink_to(target)
    env = dict(os.environ, GERBIL_HOME=str(tmp_path), GAMBIT_DARWIN_DRIVER_OVERLAY=str(overlay))
    result = subprocess.run(['bash', str(WRAPPER)], env=env, capture_output=True, timeout=5)
    assert result.returncode != 0
