from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize('options', [[], ['-:max-heap=1G,debug=q']])
def test_launcher_initializes_compiler_then_overlays_without_losing_options(tmp_path, options):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    image = tmp_path / 'lib/gerbil/compiler/driver~0.o1'
    image.parent.mkdir(parents=True)
    image.write_bytes(b'qualification fixture')
    launcher = bin_dir / 'gxi'
    shutil.copyfile(Path(__file__).with_name('closed_driver_gxi.sh'), launcher)
    native = bin_dir / 'gerbil'
    native.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    native.chmod(0o755)
    result = subprocess.run(['/bin/bash', str(launcher), *options, 'test.ss'],
                            capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    arguments = result.stdout.splitlines()
    assert arguments[:len(options)] == options
    assert arguments[len(options):len(options) + 2] == ['interactive', '-e']
    assert arguments[-1] == 'test.ss'
    assert arguments[-2].startswith('(import :gerbil/compiler) (load ')
