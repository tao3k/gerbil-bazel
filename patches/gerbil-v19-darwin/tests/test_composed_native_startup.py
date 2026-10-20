import unittest

from diagnose_composed_native_startup import diagnostic_expression, NATIVE_SOURCE


class StartupDiagnosisTests(unittest.TestCase):
    def test_original_parent_source_is_loaded_without_running_cases(self):
        expression = diagnostic_expression('parent-source')
        self.assertIn(f'(load "{NATIVE_SOURCE}")', expression)
        self.assertIn('NATIVE-PARENT-SOURCE-READY', expression)
        self.assertNotIn('(main ', expression)
        self.assertTrue(expression.endswith('(test-child-process-exit! 0)'))

    def test_stages_do_not_substitute_a_source_load_for_imports(self):
        self.assertNotIn('(load ', diagnostic_expression('runtime'))
        self.assertIn('(import :std/misc/process :std/os/signal)',
                      diagnostic_expression('parent-imports'))
        with self.assertRaises(ValueError):
            diagnostic_expression('unknown')


if __name__ == '__main__':
    unittest.main()
