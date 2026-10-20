import hashlib
from pathlib import Path
import tempfile
import unittest

from aggregate_native_cpu_lines import matching_image


class NativeImageIdentityTests(unittest.TestCase):
    def test_copy_is_bound_by_uuid_and_actual_bytes_not_path_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory)/'copied-runtime'
            copied.write_bytes(b'original-native-image')
            native = dict(uuid='UUID', sha256=hashlib.sha256(copied.read_bytes()).hexdigest())
            summary = dict(images={str(copied): dict(native)})
            self.assertEqual(matching_image(summary, native), str(copied))
            copied.write_bytes(b'changed-native-image')
            with self.assertRaises(ValueError):
                matching_image(summary, native)
            with self.assertRaises(ValueError):
                matching_image(dict(images={}), native)


if __name__ == '__main__':
    unittest.main()
