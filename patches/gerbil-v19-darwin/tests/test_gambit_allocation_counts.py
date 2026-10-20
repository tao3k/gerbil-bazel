import unittest

from summarize_gambit_allocation_counts import summarize


class AllocationCountsTest(unittest.TestCase):
    def setUp(self):
        self.profile = {'guardedReadOnlyTraces': [dict(module='core', line=10,
            callsRemoved=3, allocationGuardMisses=['!(pair)', 'event'])]}

    def test_first_failures_are_bound_to_conditions_not_cpu(self):
        result = summarize(self.profile, '0 10 2 0\n', '0 0 5\n0 1 1\n')
        self.assertEqual(result['attempts'], 10)
        self.assertEqual(result['successes'], 2)
        self.assertEqual(result['sites'][0]['otherMisses'], 2)
        self.assertEqual(result['sites'][0]['guards'][0]['condition'], '!(pair)')
        self.assertFalse(result['performanceQualified'])

    def test_rejects_duplicate_unknown_and_overcounted_guards(self):
        for failures in ('0 0 1\n0 0 1', '0 2 1', '1 0 1', '0 0 9'):
            with self.assertRaises(ValueError):
                summarize(self.profile, '0 10 2 0', failures)
        for attempts in ('0 1 2 0', '0 10 2 1', '0 10 2 0\n0 10 2 0'):
            with self.assertRaises(ValueError):
                summarize(self.profile, attempts, '')


if __name__ == '__main__':
    unittest.main()
