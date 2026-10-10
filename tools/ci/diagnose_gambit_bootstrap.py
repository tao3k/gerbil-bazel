"""Capture a bounded native bootstrap crash trace after a failed source build."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

source = Path(os.environ['GERBIL_SOURCE_DIRECTORY']) / 'src/gambit'
compiler = source / 'gsc-boot'
output = Path('.ci/receipts').resolve()
output.mkdir(parents=True, exist_ok=True)
if not compiler.is_file() or not os.access(compiler, os.X_OK):
    sys.exit('No executable bootstrap compiler available for diagnosis')
arguments = [str(compiler), '-f', '-c', '-o', str(output / 'bootstrap-probe.c'),
             '-prelude', '(define-cond-expand-feature|enable-smp|)(##include"../lib/header.scm")',
             '_io.scm']
if sys.platform == 'darwin':
    command = ['/usr/bin/lldb', '--batch', '-o', 'run', '-k', 'thread backtrace all', '--']
else:
    command = [shutil.which('gdb') or 'gdb', '--batch', '-ex', 'set pagination off',
               '-ex', 'run', '-ex', 'thread apply all bt 20', '--args']
with (output / 'bootstrap-backtrace.log').open('w') as log:
    child = subprocess.Popen(command + arguments, cwd=source / 'lib', stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True)
    try:
        child.wait(timeout=120)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        log.write('\nBOOTSTRAP-DIAGNOSIS-TIMEOUT\n')
print((output / 'bootstrap-backtrace.log').read_text())
