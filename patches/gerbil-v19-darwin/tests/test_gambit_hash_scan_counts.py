import unittest

from run_gambit_startup_cpu import parse_hash_scan_counts


class HashScanCountsTest(unittest.TestCase):
    def test_valid_and_zero_selected_coverage(self):
        self.assertEqual(parse_hash_scan_counts('538 530 201 329 532 6 0 0 0')['hits'], 201)
        self.assertEqual(parse_hash_scan_counts('2 0 0 0 0 2 0 0 0')['selected'], 0)

    def test_inconsistent_or_malformed_receipts_fail(self):
        for content in ('', '0 0 0 0 0 0 0 0 0', '2 3 1 2 2 0 0 0 0',
                        '2 2 1 0 2 0 0 0 0', '2 2 1 1 1 0 0 0 0',
                        '2 2 1 1 -2 4 0 0 0'):
            with self.subTest(content=content), self.assertRaises(RuntimeError):
                parse_hash_scan_counts(content)


if __name__ == '__main__':
    unittest.main()
