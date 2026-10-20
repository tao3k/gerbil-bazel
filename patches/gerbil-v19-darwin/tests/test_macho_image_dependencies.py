import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from macho_image_dependencies import dependencies, validate_packed_image_inventory


def fixture(name='/usr/lib/libSystem.B.dylib', kind=0xC):
    raw = name.encode()+b'\0'
    size = (24+len(raw)+7)//8*8
    command = struct.pack('<6I', kind, size, 24, 0, 0, 0)+raw
    command += b'\0'*(size-len(command))
    return struct.pack('<8I', 0xFEEDFACF, 0, 0, 8, 1, size, 0, 0)+command


class MachoImageDependenciesTest(unittest.TestCase):
    def test_original_absolute_strong_dependencies(self):
        self.assertEqual(dependencies(fixture()), ['/usr/lib/libSystem.B.dylib'])

    def test_unsupported_semantics_and_malformed_input_refused(self):
        for data in (fixture('@loader_path/libfoo.dylib'), fixture(kind=0x80000018),
                     fixture(kind=0x8000001F), fixture()[:40], b''):
            with self.assertRaises(ValueError):
                dependencies(data)

    def test_alias_and_image_hash_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            data = fixture()
            (home/'packed.o1').write_bytes(data)
            (home/'module.o1').symlink_to('packed.o1')
            receipt = dict(units=[dict(path='module.o1')], images=[dict(path='packed.o1',
                sha256=hashlib.sha256(data).hexdigest(), dependencies=dependencies(data), aliases=['module.o1'])])
            self.assertTrue(validate_packed_image_inventory(home, receipt))
            (home/'packed.o1').write_bytes(data+b'changed')
            with self.assertRaisesRegex(ValueError, 'hash/dependencies'):
                validate_packed_image_inventory(home, receipt)

    def test_missing_inventory_refused(self):
        with self.assertRaisesRegex(ValueError, 'inventory'):
            validate_packed_image_inventory(Path('.'), {})

    def test_preserved_original_images_remain_byte_exact_and_not_aliased(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            data = fixture()
            for name in ('packed.o1', 'original.o1'):
                (home/name).write_bytes(data)
            (home/'module.o1').symlink_to('packed.o1')
            receipt = dict(units=[dict(path='module.o1')], images=[dict(path='packed.o1',
                sha256=hashlib.sha256(data).hexdigest(), dependencies=dependencies(data), aliases=['module.o1'])],
                preservedOriginalImages=[dict(path='original.o1', originalSha256=hashlib.sha256(data).hexdigest(),
                                              dependencies=dependencies(data))])
            self.assertTrue(validate_packed_image_inventory(home, receipt))
            (home/'original.o1').unlink()
            (home/'original.o1').symlink_to('packed.o1')
            with self.assertRaisesRegex(ValueError, 'preserved original'):
                validate_packed_image_inventory(home, receipt)


if __name__ == '__main__':
    unittest.main()
