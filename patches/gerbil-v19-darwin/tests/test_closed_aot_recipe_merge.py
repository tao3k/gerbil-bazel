"""Native AST controls for recipe-only merges, not consumer timing tests."""
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / '.data/d1510-reader-whitespace-native-v2/gxi'
TRANSFORM = Path(__file__).with_name('prepare_closed_link_aot_driver.scm')
BASE = ['gxc#open-compile-executor', 'gxc#add-compile-output-job!__%',
        'gxc#add-compile-output-job!__0', 'gxc#add-compile-output-job!']
ADDED = ['gxc#add-compile-output-job!__1', 'gxc#current-compile-output-recipe']
DRIVER = ['gxc#compile-executable-module/separate', 'gxc#gsc-compile-file',
          'gxc#compile-scm-file__%']


@pytest.mark.skipif(not BINARY.exists(), reason='retained native AST reader required')
@pytest.mark.parametrize('module,mutation', [
    ('base', 'none'), ('driver', 'none'), ('base', 'missing'),
    ('base', 'duplicate'), ('base', 'preexisting-added'),
    ('base', 'disabled'),
])
def test_recipe_merge_preserves_unselected_forms(tmp_path, module, mutation):
    names = BASE if module == 'base' else DRIVER
    additions = ADDED if module == 'base' else []
    original, donor, output = [tmp_path / name for name in ('old.scm', 'donor.scm', 'out.scm')]
    old_names = names + (ADDED[:1] if mutation == 'preexisting-added' else [])
    new_names = names + additions
    if mutation == 'missing':
        new_names = new_names[:-1]
    elif mutation == 'duplicate':
        new_names = new_names + new_names[:1]
    original.write_text('(begin (define untouched 7) ' +
                        ' '.join(f'(define {name} 1)' for name in old_names) + ')\n')
    donor.write_text('(begin (define untouched 999) ' +
                     ' '.join(f'(define {name} 2)' for name in new_names) + ')\n')
    home = ROOT / '.data/d1391-runtime-object-source/build'
    env = dict(os.environ, GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               CLOSED_DRIVER_BASE=str(original), CLOSED_DRIVER_DONOR=str(donor),
               CLOSED_DRIVER_OUTPUT=str(output), CLOSED_DRIVER_MODULE=module,
               CLOSED_DRIVER_RECIPE='0' if mutation == 'disabled' else '1')
    result = subprocess.run([str(BINARY), '-e', f'(load "{TRANSFORM}")'],
                            env=env, capture_output=True, text=True, timeout=10)
    if mutation != 'none':
        assert result.returncode != 0
        assert not output.exists()
        return
    assert result.returncode == 0, result.stderr
    text = output.read_text()
    assert '(define untouched 7)' in text
    assert '999' not in text
    for name in names + additions:
        assert text.count(f'(define {name} 2)') == 1
    assert 'frozen-remainder-preserved' in result.stdout
