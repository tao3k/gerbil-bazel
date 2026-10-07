import unittest

from run_mcp_recipe_batch_cost import batch_control_matches, outcomes, phases


class RecipeBatchCostTest(unittest.TestCase):
    def test_exact_outcomes_retain_failures_and_duplicates(self):
        rows = outcomes('GERBIL-MCP-VERIFY-PASS:a\n'
                        'GERBIL-MCP-VERIFY-FAIL:b\terror\n'
                        'GERBIL-MCP-VERIFY-PASS:a\n')
        self.assertEqual(rows[('PASS', 'a')], 2)
        self.assertEqual(rows[('FAIL', 'b')], 1)

    def test_harness_ok_is_not_a_recipe_outcome(self):
        self.assertFalse(outcomes('HARNESS-OK\nOK\n'))

    def test_empty_and_duplicate_success_are_not_matching_complete_batches(self):
        valid = 'GERBIL-MCP-VERIFY-PASS:a\n'
        self.assertTrue(batch_control_matches(0, valid, 0, valid, ['a']))
        self.assertFalse(batch_control_matches(0, '', 0, '', ['a']))
        self.assertFalse(batch_control_matches(0, valid + valid, 0, valid + valid, ['a']))
        self.assertFalse(batch_control_matches(1, '', 1, '', ['a']))

    def test_known_original_import_failure_is_preserved_not_a_success(self):
        error = 'Syntax Error: cannot find library module'
        self.assertTrue(batch_control_matches(70, error, 70, error, ['a']))
        self.assertFalse(batch_control_matches(70, error, 0, error, ['a']))

    def test_phase_inventory_must_be_exact_and_ordered(self):
        def log(names, count=20):
            return '\n'.join('BATCH-PHASE\t' + name + '\t' + str(i) + '\t' +
                             '\t'.join(['0'] * count)
                for i, name in enumerate(names))
        self.assertEqual(len(phases(log(['start', 'imports', 'checks']))), 3)
        for names in ([], ['start', 'checks'], ['start', 'checks', 'imports'],
                      ['start', 'imports', 'checks', 'checks']):
            with self.assertRaises(ValueError):
                phases(log(names))
        with self.assertRaises(ValueError):
            phases(log(['start', 'imports', 'checks'], count=19))


if __name__ == '__main__':
    unittest.main()
