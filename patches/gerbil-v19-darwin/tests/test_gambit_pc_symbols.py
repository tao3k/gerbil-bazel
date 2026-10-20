import unittest

from gambit_pc_symbols import inject
from summarize_gambit_pc_sample import summarize


class PcSymbolsTest(unittest.TestCase):
    def test_landmarks_preserve_original_and_record_exact_owner(self):
        source = ("#define ___PH_PROC ___H_example\n"
                  "___DEF_SLBL(2,___L2_example)\n"
                  "   ___SET_R1(___R2)\n___DEF_GLBL(___L3_example)\n")
        result, rows = inject(source)
        self.assertEqual([row["label"] for row in rows], ["___L2_example", "___L3_example"])
        self.assertEqual(rows[0]["procedure"], "___H_example")
        self.assertEqual(rows[0]["originalLine"], 2)
        self.assertIn("___SET_R1(___R2)", result)
        self.assertIn("_gb_vm_pc_0_%=", result)
        self.assertIn("!defined(__clang__)", result)
        self.assertNotIn("memory", result)

    def test_reject_empty_scope(self):
        with self.assertRaises(ValueError):
            inject("___SET_R1(___R2)\n")

    def test_sample_uses_self_summary_not_inclusive_stack_counts(self):
        generated, rows = inject('#define ___MODULE_NAME "example"\n'
                                 '#define ___PH_PROC ___H_any\n___DEF_GLBL(___L_any)\n')
        sample = ('Call graph:\n  100 gb_vm_pc_0_7 (in gerbil) + 0\n'
                  'Sort by top of stack, same collapsed (when >= 5):\n'
                  '    gb_vm_pc_0_7 (in gerbil) 20\n    some::method(bool) const (in dyld) 8\n'
                  'Binary Images:\n')
        result = summarize(sample, generated, rows)
        self.assertEqual(result['listedSelfSamples'], 28)
        self.assertEqual(result['landmarkSelfSamples'], 20)
        self.assertEqual(result['topProcedures'][0]['module'], 'example')
        self.assertFalse(result['performanceQualified'])

    def test_sample_rejects_foreign_landmark(self):
        generated, rows = inject('#define ___MODULE_NAME "example"\n___DEF_GLBL(___L_any)\n')
        with self.assertRaises(ValueError):
            summarize('Sort by top of stack, same collapsed (when >= 5):\n'
                      'gb_vm_pc_1_2 (in gerbil) 5\nBinary Images:\n', generated, rows)
