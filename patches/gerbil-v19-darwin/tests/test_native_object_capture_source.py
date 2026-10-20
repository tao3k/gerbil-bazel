import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PATCH = Path(__file__).resolve().parents[1]/'0014-gambit-darwin-native-object-capture.patch'


class NativeObjectCaptureSourceTest(unittest.TestCase):
    def install_helper(self, root):
        subprocess.run(['git', 'apply', '--include=bin/gambit-native-object-cache.unix', str(PATCH)],
                       cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return root/'bin/gambit-native-object-cache.unix'

    def test_linker_arguments_exit_and_input_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            helper = self.install_helper(root)
            capture = root/'capture'
            capture.mkdir()
            obj = root/'module with spaces.o'
            obj.write_bytes(b'original assembler object')
            collect2 = root/'collect2'
            collect2.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$ARG_RECEIPT"\nexit 37\n')
            collect2.chmod(0o755)
            arguments = ['-bundle', str(obj), '-o', str(root/'module.o1')]
            env = dict(os.environ, GAMBIT_NATIVE_CAPTURE_DIRECTORY=str(capture),
                       ARG_RECEIPT=str(root/'arguments'))
            result = subprocess.run(['sh', str(helper), str(collect2), *arguments], env=env)
            self.assertEqual(result.returncode, 37)
            self.assertEqual((root/'arguments').read_text().splitlines(), arguments)
            self.assertEqual((capture/'link-input-0.o').read_bytes(), obj.read_bytes())

    def test_non_darwin_marker_retains_original_command_and_status(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            helper = self.install_helper(root)
            compiler = root/'compiler'
            compiler.write_text('#!/bin/sh\nexit 0\n')
            compiler.chmod(0o755)
            script = root/'driver'
            script.write_text('GAMBIT_NATIVE_OBJECT_DRIVER_LOADING=yes\n. "$HELPER"\n'
                              'C_COMPILER=$COMPILER\nBUILD_DYN_CMD="exit 29"\n'
                              'gambuild_dyn_with_native_object_cache\n')
            result = subprocess.run(['sh', str(script)], env=dict(os.environ, HELPER=str(helper),
                                    COMPILER=str(compiler)), cwd=root)
            self.assertEqual(result.returncode, 29)
            self.assertEqual(list(root.glob('*.gambit-native-*')), [])

    def test_new_helper_is_syntax_valid_and_installed_by_source_makefile(self):
        with tempfile.TemporaryDirectory() as path:
            helper = self.install_helper(Path(path))
            subprocess.run(['sh', '-n', str(helper)], check=True)
        patch = PATCH.read_text()
        self.assertIn('+core-post: gambit-native-object-cache ', patch)
        self.assertIn('+gambit-native-object-cache: makefile $(srcdirpfx)gambit-native-object-cache.unix', patch)
        self.assertIn('+    if test "${GAMBIT_DARWIN_NATIVE_OBJECTS-}" = 1;', patch)


if __name__ == '__main__':
    unittest.main()
