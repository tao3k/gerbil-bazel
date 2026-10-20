import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from native_object_manifest import read_manifest, executable_rpaths


class NativeObjectManifestTest(unittest.TestCase):
    def test_executable_literal_rpaths(self):
        paths = ('@loader_path', '/retained/provider/lib')
        commands = b''
        for path in paths:
            raw = path.encode() + b'\0'
            size = (12 + len(raw) + 7) // 8 * 8
            commands += struct.pack('<3I', 0x8000001C, size, 12) + raw.ljust(size - 12, b'\0')
        header = struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 2, 2, len(commands), 0, 0)
        self.assertEqual(executable_rpaths(header + commands), list(paths))
        for data in (header + commands[:-1], header + commands + b'ignored'):
            if data == header + commands + b'ignored':
                self.assertEqual(executable_rpaths(data), list(paths))
            else:
                with self.assertRaises(ValueError):
                    executable_rpaths(data)
        invalid = bytearray(header + commands)
        struct.pack_into('<I', invalid, 40, 0)
        with self.assertRaises(ValueError):
            executable_rpaths(invalid)

    def test_executable_rpaths_reject_other_filetypes(self):
        with self.assertRaises(ValueError):
            executable_rpaths(struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 8, 0, 0, 0, 0))

    def fixture(self, root):
        image = root/'module.o1'
        image.write_bytes(struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 8, 0, 0, 0, 0))
        data = struct.pack('<8I', 0xFEEDFACF, 0x100000C, 0, 1, 0, 0, 0, 0)
        a, b = hashlib.sha256(image.read_bytes()).hexdigest(), hashlib.sha256(data).hexdigest()
        name = image.name+'.gambit-native-objects.'+a+'.'+b
        directory = root/name
        directory.mkdir()
        (directory/'object.o').write_bytes(data)
        reference = root/(image.name+'.gambit-native-objects')
        reference.write_text(f'schema=1\nimage-sha256={a}\nobject-sha256={b}\ndirectory={name}\n')
        return image, reference, directory

    def test_current_object_identity(self):
        with tempfile.TemporaryDirectory() as path:
            image, _, directory = self.fixture(Path(path))
            self.assertEqual(read_manifest(image)['objectPath'], directory/'object.o')

    def test_image_drift_refused(self):
        with tempfile.TemporaryDirectory() as path:
            image, _, _ = self.fixture(Path(path))
            image.write_bytes(image.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                read_manifest(image)

    def test_image_symlink_refused_even_with_matching_bytes(self):
        with tempfile.TemporaryDirectory() as path:
            image, _, _ = self.fixture(Path(path))
            target = image.with_name('same-image.o1')
            image.rename(target)
            image.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'regular native image'):
                read_manifest(image)

    def test_directory_escape_and_duplicate_fields_refused(self):
        for suffix in ('directory=../../outside\n', 'schema=1\n'):
            with tempfile.TemporaryDirectory() as path:
                image, reference, _ = self.fixture(Path(path))
                reference.write_text(reference.read_text()+suffix)
                with self.assertRaises(ValueError):
                    read_manifest(image)

    def test_object_symlink_refused(self):
        with tempfile.TemporaryDirectory() as path:
            image, _, directory = self.fixture(Path(path))
            (directory/'object.o').unlink()
            (directory/'object.o').symlink_to(image)
            with self.assertRaisesRegex(ValueError, 'regular isolated'):
                read_manifest(image)
