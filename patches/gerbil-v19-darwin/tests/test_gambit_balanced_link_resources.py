"""Patch shape and native preprocessor guards for the independent side patch."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / '0017-gambit-darwin-balanced-link-resources.patch'
TEXT = PATCH.read_text()


class BalancedLinkResourceTests(unittest.TestCase):
    def test_patch_applies_to_its_original_context(self):
        lines = TEXT.split('@@', 2)[2].splitlines()[1:]
        original = '\n'.join(line[1:] for line in lines if line.startswith((' ', '-'))) + '\n'
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / 'gsc/_t-c-1.scm'
            source.parent.mkdir()
            source.write_text('\n' * 530 + original)
            subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=directory, check=True,
                           capture_output=True)

    def test_reverse_precedence_and_portable_fold_are_retained(self):
        self.assertIn('(reverse list-of-rsrc)', TEXT)
        self.assertIn('(targ-union-list-of-rsrc-portable list-of-rsrc)', TEXT)
        self.assertIn('(targ-union-rsrc (car lst) table)', TEXT)
        self.assertNotIn('set-cdr!', TEXT)
        self.assertNotIn('reverse!', TEXT)

    def test_native_guard_selects_only_darwin_gnu(self):
        compiler = os.environ.get('GAMBIT_TEST_CC')
        if not compiler:
            self.skipTest('set GAMBIT_TEST_CC to the GNU compiler for native guard checks')
        literal = next(line[1:].strip().removesuffix('))') for line in TEXT.splitlines()
                       if line.startswith('+    "#if'))
        body = json.loads(literal).replace('___return', 'return')
        for apple, mach, gnu, clang, expected in (
                (True, True, True, False, 1), (False, False, True, False, 0),
                (True, True, True, True, 0), (True, True, False, False, 0),
                (True, False, True, False, 0)):
            with self.subTest(apple=apple, mach=mach, gnu=gnu, clang=clang):
                flags = []
                for name, enabled in [('__APPLE__', apple), ('__MACH__', mach),
                                      ('__GNUC__', gnu), ('__clang__', clang)]:
                    flags.append('-U' + name)
                    if enabled:
                        flags.append('-D' + name + '=1')
                result = subprocess.run([compiler, '-E', '-P', '-x', 'c', *flags, '-'],
                                        input='int selected(void) {\n' + body + '\n}\n',
                                        capture_output=True, text=True, check=True)
                self.assertIn(f'return({expected});', result.stdout)


if __name__ == '__main__':
    unittest.main()
