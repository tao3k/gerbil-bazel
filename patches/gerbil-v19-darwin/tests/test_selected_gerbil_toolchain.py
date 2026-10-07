import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from selected_gerbil_toolchain import TOOL_ENV, validate_tools


class SelectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.binary = self.root / 'measured'
        self.binary.write_text('measured build')
        self.binary.chmod(0o755)
        self.sha = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        self.env = {'PATH': str(self.root)}
        for name, key in TOOL_ENV.items():
            alias = self.root / name
            alias.symlink_to(self.binary)
            self.env[key] = str(alias)

    def test_exact_selected_aliases_pass(self):
        self.assertEqual(len(validate_tools(self.env, self.binary, self.sha)), 4)

    def test_same_file_hash_is_checked_once_not_five_times(self):
        read = Path.read_bytes
        with patch.object(Path, 'read_bytes', autospec=True, side_effect=read) as mocked:
            self.assertEqual(len(validate_tools(self.env, self.binary, self.sha)), 4)
        self.assertEqual(mocked.call_count, 1)

    def test_binary_mutation_during_hash_is_rejected(self):
        read = Path.read_bytes
        def changed(path):
            data = read(path)
            path.write_text('changed during validation')
            return data
        with patch.object(Path, 'read_bytes', autospec=True, side_effect=changed):
            with self.assertRaises(ValueError):
                validate_tools(self.env, self.binary, self.sha)

    def test_missing_explicit_path_fails(self):
        del self.env['GERBIL_MCP_GXI_PATH']
        with self.assertRaises(ValueError):
            validate_tools(self.env, self.binary, self.sha)

    def test_other_binary_cannot_substitute(self):
        other = self.root / 'other'
        other.write_text('other build')
        self.env['GERBIL_MCP_GXI_PATH'] = str(other)
        with self.assertRaises(ValueError):
            validate_tools(self.env, self.binary, self.sha)

    def test_changed_hash_fails(self):
        with self.assertRaises(ValueError):
            validate_tools(self.env, self.binary, '0' * 64)

    def test_path_resolution_must_also_match(self):
        self.env['PATH'] = ''
        with self.assertRaises(ValueError):
            validate_tools(self.env, self.binary, self.sha)
