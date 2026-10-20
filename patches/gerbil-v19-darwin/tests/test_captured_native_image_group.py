from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pack_captured_native_images import admit_group
from test_macho_packing_semantics import fixture


class CapturedGroupTest(unittest.TestCase):
    def check(self, left, right, dependency='/usr/lib/libSystem.B.dylib'):
        with tempfile.TemporaryDirectory() as directory:
            images = [Path(directory)/name for name in ('a.o1', 'b.o1')]
            for image, data in zip(images, (left, right)):
                image.write_bytes(data)
            with patch('pack_captured_native_images.dependencies', return_value=[dependency]):
                return admit_group(images)

    def test_distinct_ordinary_system_only_inputs(self):
        result = self.check(fixture(), fixture().replace(b'_fun', b'_bar'))
        self.assertEqual(len(result), 2)

    def test_duplicate_native_definitions_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.check(fixture(), fixture())

    def test_new_internal_symbol_provider_refused(self):
        with self.assertRaisesRegex(ValueError, 'bindings'):
            self.check(fixture(), fixture(kind=1, descriptor=0xFE00, value=0))

    def test_weak_and_external_library_inputs_remain_original(self):
        for left, library in ((fixture(descriptor=0x80), '/usr/lib/libSystem.B.dylib'),
                              (fixture(), '/external/libcrypto.dylib')):
            with self.assertRaisesRegex(ValueError, 'preserves'):
                self.check(left, fixture().replace(b'_fun', b'_bar'), library)

    def test_mismatched_architecture_refused(self):
        other = bytearray(fixture().replace(b'_fun', b'_bar'))
        other[8:12] = (1).to_bytes(4, 'little')
        with self.assertRaisesRegex(ValueError, 'architecture'):
            self.check(fixture(), bytes(other))


if __name__ == '__main__':
    unittest.main()
