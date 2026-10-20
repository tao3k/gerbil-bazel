import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / '.data/d1510-reader-whitespace-native-v2/gxi'


@pytest.mark.skipif(not BINARY.exists(), reason='private native source-transform control')
@pytest.mark.parametrize('platform,enabled', [(False, True), (True, False), (True, True)])
def test_final_link_only_and_platform_fallback(tmp_path, platform, enabled):
    source, output = tmp_path / 'input.scm', tmp_path / 'output.scm'
    source.write_text('''(define (gxc#gerbil-gcc) "gcc-16")
(define (gxc#darwin-gnu-source-loader-platform?) ''' + ('#t' if platform else '#f') + ''')
(define (gxc#invoke__% flag absent1 absent2 compiler args) (write args) (newline))
(gxc#invoke__% #f #f #f (gxc#gerbil-gcc) (list "first.o" "-lgambit"))
(gxc#invoke__% #f #f #f (gxc#gerbil-gcc) (list "second.o" "-lgambit"))
(gxc#invoke__% #f #f #f (gxc#gerbil-gcc) (list "-c" "module.c"))
''')
    home = ROOT / '.data/d1391-runtime-object-source/build'
    env = dict(os.environ, GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               FD_DRIVER_INPUT=str(source), FD_DRIVER_OUTPUT=str(output))
    obj = str(tmp_path / 'runtime object.o')
    if enabled:
        env['GAMBIT_DARWIN_RUNTIME_OBJECT'] = obj
    else:
        env.pop('GAMBIT_DARWIN_RUNTIME_OBJECT', None)
    transform = Path(__file__).with_name('prepare_fd_final_driver.scm')
    subprocess.run([str(BINARY), '-e', '(load ' + json.dumps(str(transform)) + ')'],
                   env=env, check=True, capture_output=True, timeout=10)
    result = subprocess.check_output([str(BINARY), '-e', '(load ' + json.dumps(str(output)) + ')'],
                                     env=env, text=True, timeout=10).splitlines()
    prefix = json.dumps(obj) + ' ' if platform and enabled else ''
    assert result == ['(' + prefix + '"first.o" "-lgambit")',
                      '(' + prefix + '"second.o" "-lgambit")',
                      '("-c" "module.c")']
