import unittest

from run_gambit_startup_cpu import parse_fresh_tree_counts, parse_process_statistics, parse_scalar_elided_words


class ProcessStatisticsTest(unittest.TestCase):
    def test_scalar_elision_counts_are_exact_and_separate_from_allocation_delta(self):
        self.assertEqual(parse_scalar_elided_words('1551\n')['elidedHeapWords'], 1551)
        self.assertEqual(parse_scalar_elided_words('0\n')['elidedHeapWords'], 0)
        for content in ('', '-1', '1.0', '1 2', 'NaN'):
            with self.assertRaises(RuntimeError):
                parse_scalar_elided_words(content)

    def test_fresh_counts_do_not_confuse_readonly_hits_with_allocated_returns(self):
        result = parse_fresh_tree_counts('0 0 0 0\n1 2 6 3\n')
        self.assertEqual(result['allocatedReturns'], 2)
        self.assertEqual(result['committedHeapWords'], 6)
        self.assertEqual(result['rolledBackHeapWords'], 3)

    def test_invalid_fresh_counts_fail_without_repair(self):
        for content in ('0 1 0 0', '0 1 65 0', '256 0 0 0', '-1 0 0 0',
                        '0 0 0 0\n0 0 0 0', '0 1 2', '0 0 1 0'):
            with self.assertRaises(RuntimeError):
                parse_fresh_tree_counts(content)

    def test_layout_uses_actual_kernel_not_consumer_recipe(self):
        content = 'IMPORT-OK\nGAMBIT-PROCESS-STATISTICS (' + ' '.join(map(str, range(20))) + ')\n'
        result = parse_process_statistics(content)
        self.assertEqual(result['gcUserCpuSeconds'], 3)
        self.assertEqual(result['allocatedBytes'], 7)
        self.assertEqual(result['latestGcHeapBytes'], 15)
        self.assertEqual(result['latestGcLiveBytes'], 17)

    def test_missing_duplicate_nonfinite_and_wrong_length_fail(self):
        valid = 'GAMBIT-PROCESS-STATISTICS (' + ' '.join(['0'] * 20) + ')\n'
        for content in ('', valid + valid, valid.replace('0', 'nan', 1),
                        valid.replace('0 ', '', 1)):
            with self.assertRaises(RuntimeError):
                parse_process_statistics(content)
