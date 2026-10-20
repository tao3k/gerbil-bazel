import unittest
from pathlib import Path

from summarize_native_cpu_profile import first_window_binary


class FirstWindowBinaryTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path('/unit/repo')
        self.binary = self.repo / '.data/native/gerbil'
        self.receipt = dict(actualBuilderChildVerified=True, sampleTarget='build-child',
                            sampledChildBinarySha256='locked', binarySha256={'gxi': 'locked'})

    def test_verified_flat_binary(self):
        self.assertEqual(first_window_binary(self.repo, self.receipt, self.binary), self.binary)

    def test_outer_process_refused(self):
        self.receipt['sampleTarget'] = 'official-parent'
        with self.assertRaises(ValueError):
            first_window_binary(self.repo, self.receipt, self.binary)

    def test_child_digest_mismatch_refused(self):
        self.receipt['sampledChildBinarySha256'] = 'different'
        with self.assertRaises(ValueError):
            first_window_binary(self.repo, self.receipt, self.binary)

    def test_outside_data_refused(self):
        with self.assertRaises(ValueError):
            first_window_binary(self.repo, self.receipt, Path('/unit/other/gerbil'))


if __name__ == '__main__':
    unittest.main()
