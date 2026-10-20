import unittest

from prepare_source_cost_probe import instrument


class SourceCostProbeTests(unittest.TestCase):
    def original(self):
        return '''(##read-all-as-a-begin-expr-from-psettings
            psettings
            path-or-settings
            (##current-readtable)
            ##wrap-datum
            ##unwrap-datum
            '())
(##top-cte-clone ##interaction-cte)
(##compile-top top-cte
                          (##sourcify src (##make-source #f #f)))
(##compile-top top-cte
                          (##sourcify src (##make-source #f #f)))
(##setup-requirements-and-run c #f)
(##setup-requirements-and-run c #f)
'''

    def test_preserves_original_boundaries_and_unwind(self):
        result = instrument(self.original())
        self.assertIn('(dynamic-wind (lambda () (##gb-source-cost-begin kind))', result)
        self.assertIn('(lambda () (##gb-source-cost-end kind))', result)
        self.assertIn('(c-declare "#include \\"gambit-source-cost-probe.h\\"")', result)
        for kind, expected in enumerate((1, 1, 2, 2)):
            self.assertEqual(result.count(f'(##gb-source-cost {kind} (lambda ()'), expected)
        self.assertEqual(result.count('(##top-cte-clone ##interaction-cte)'), 1)
        self.assertEqual(result.count('(##setup-requirements-and-run c #f)'), 2)

    def test_refuses_changed_original_boundary(self):
        with self.assertRaisesRegex(ValueError, 'boundary changed'):
            instrument(self.original().replace('(##top-cte-clone ##interaction-cte)', '#f'))

    def test_passive_preserves_multiple_values_without_dynamic_wind(self):
        result = instrument(self.original(), passive=True)
        self.assertNotIn('(dynamic-wind', result)
        self.assertIn('(##call-with-values thunk', result)
        self.assertIn('(##apply ##values results)', result)
        self.assertEqual(result.count('(##setup-requirements-and-run c #f)'), 2)


if __name__ == '__main__':
    unittest.main()
