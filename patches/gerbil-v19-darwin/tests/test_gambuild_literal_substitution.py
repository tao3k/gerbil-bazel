"""Portable contracts for the exact helper shipped by the Darwin driver patch."""
import os
from pathlib import Path
import re
import subprocess
import unittest

PATCH = Path(__file__).resolve().parents[1] / '0015-gambit-darwin-literal-build-substitution.patch'
TEXT = PATCH.read_text()
HELPER = '\n'.join(line[1:] for line in re.search(
    r'^\+replace_literal\(\)\n\+\{\n.*?^\+\}', TEXT, re.M | re.S).group().splitlines())
BLOCK = '\n'.join(line[1:] for line in TEXT[TEXT.index('+# This experiment'):].splitlines()
                  if line.startswith('+')) + '\n}\n'


class LiteralSubstitutionTests(unittest.TestCase):
    def replace(self, text, key, value):
        env = os.environ.copy()
        env.update(INPUT=text, KEY=key, VALUE=value)
        result = subprocess.run(['/bin/sh', '-c', HELPER + '''
GAMBUILD_EXPANDED="$INPUT"
replace_literal "$KEY" "$VALUE"
printf '%s' "$GAMBUILD_EXPANDED"
'''], env=env, capture_output=True, check=True)
        return result.stdout.decode()

    def test_all_occurrences_and_no_recursive_expansion(self):
        self.assertEqual(self.replace('x${A}${A}y', '${A}', '${A}z'), 'x${A}z${A}zy')

    def test_literal_metacharacters(self):
        for value in ("a'b", 'a&b/c\\d', '[$*?];"', '', 'line1\nline2'):
            with self.subTest(value=value):
                self.assertEqual(self.replace('a${K}b', '${K}', value), 'a' + value + 'b')

    def test_absent_key_and_literal_glob_key(self):
        self.assertEqual(self.replace('plain', '${K}', 'x'), 'plain')
        self.assertEqual(self.replace('a*?b*?', '*?', 'x'), 'axbx')

    def dispatch(self, platform, compiler, value):
        prefix = '''
uname() { printf '%s' "$PLATFORM"; }
substitute_obj_portable() { printf 'portable'; }
substitute_dyn_portable() { printf 'portable'; }
substitute_exe_portable() { printf 'portable'; }
shell_quote() { printf '%s' "$1"; }
GAMBUILD_NL='
'
BUILD_FEATURE_C_COMP="$COMPILER"
BUILD_OBJ_CC_OPTIONS_PARAM="$VALUE"
'''
        env = os.environ.copy()
        env.update(PLATFORM=platform, COMPILER=compiler, VALUE=value)
        return subprocess.check_output(['/bin/sh', '-c', prefix + BLOCK +
                                        "\nsubstitute_obj '${BUILD_OBJ_CC_OPTIONS_PARAM}'"],
                                       env=env, text=True)

    def test_darwin_and_gnu_guard(self):
        self.assertEqual(self.dispatch('Linux', 'gcc', 'value'), 'portable')
        self.assertEqual(self.dispatch('Darwin', 'clang', 'value'), 'portable')
        self.assertEqual(self.dispatch('Darwin', 'gcc', 'value'), 'value')

    def test_newline_and_sed_delimiter_fall_back(self):
        self.assertEqual(self.dispatch('Darwin', 'gcc', 'a\nb'), 'portable')
        self.assertEqual(self.dispatch('Darwin', 'gcc', 'a\030b'), 'portable')


if __name__ == '__main__':
    unittest.main()
