import unittest

from run_mcp_first_window_abba import paired_first_window


class FirstWindowAbbaTests(unittest.TestCase):
    def test_actual_first_lines_are_required_in_original_order(self):
        runs = [dict(role=role, observation=dict(firstCompileSeconds=seconds)) for role, seconds in
                [('baseline', 20), ('candidate', 10), ('candidate', 12), ('baseline', 24)]]
        result = paired_first_window(runs)
        self.assertEqual(result['baselineMeanSeconds'], 22)
        self.assertEqual(result['candidateMeanSeconds'], 11)
        self.assertEqual(result['ratio'], 2)
        with self.assertRaises(ValueError):
            paired_first_window(runs[:-1])
        for value in (None, 0, float('nan'), float('inf'), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                paired_first_window([dict(runs[0], observation=dict(firstCompileSeconds=value))]+runs[1:])


if __name__ == '__main__':
    unittest.main()
