import unittest

from summarize_native_cpu_profile import classify_native_pc
from run_mcp_native_cpu_profile import candidate_provenance_valid, native_admission_receipt_valid
from audit_embedded_host_distance import control_transfer_sites


class NativeCpuProfileTest(unittest.TestCase):
    def test_complete_indirect_branch_audit(self):
        report = control_transfer_sites(
            '1000: d61f0000 br x0\n1004: d63f0200 blr x16\n'
            '1008: 14000001 b 0x100c\n100c: d65f03c0 ret\n', 0x1000, 0x1010)
        self.assertEqual(report['indirectBranchCount'], 1)
        self.assertEqual(report['indirectCallCount'], 1)
        self.assertEqual([site['register'] for site in report['indirectSites']], [0, 16])
        self.assertFalse(report['dynamicTransferCountMeasured'])

    def test_incomplete_or_out_of_order_native_extent_rejected(self):
        for text in ('1000: d61f0000 br x0\n',
                     '1004: d61f0000 br x0\n1000: d61f0000 br x0\n',
                     '1000: d61f0000 br x0\n1000: d61f0000 br x0\n'):
            with self.assertRaises(ValueError):
                control_transfer_sites(text, 0x1000, 0x1008)

    def setUp(self):
        self.native = dict(textStart=0x1000, textEnd=0x1200,
                           starts=[0x1010, 0x1100],
                           names={0x1010: {'host'}, 0x1100: {'other'}},
                           executableSections=[(0x1000, 0x1200, '__text'),
                                               (0x1200, 0x1230, '__stubs')])

    def test_actual_function_start_and_end_bounds(self):
        self.assertEqual(classify_native_pc(self.native, 0x1010, 'host'),
                         ('host', 'validatedNativeCycles'))
        self.assertEqual(classify_native_pc(self.native, 0x10fc, 'host'),
                         ('host', 'validatedNativeCycles'))
        self.assertEqual(classify_native_pc(self.native, 0x1100, 'host'),
                         ('NATIVE_FUNCTION@0x1100', 'unresolvedNativeCycles'))

    def test_stubs_are_not_assigned_to_previous_function(self):
        self.assertEqual(classify_native_pc(self.native, 0x1200, 'DYLD-STUB$$write'),
                         ('NATIVE_SECTION:__stubs', 'nonFunctionNativeCycles'))

    def test_outside_sections_and_before_first_function_stay_unknown(self):
        self.assertEqual(classify_native_pc(self.native, 0x1230, 'other'),
                         ('UNKNOWN_NATIVE_PC', 'outsideExecutableNativeCycles'))
        self.assertEqual(classify_native_pc(self.native, 0x100c, 'host'),
                         ('UNKNOWN_NATIVE_PC', 'outsideFunctionNativeCycles'))

    def test_deduplicated_name_is_not_a_scheme_procedure(self):
        self.assertEqual(classify_native_pc(self.native, 0x1014, '<deduplicated_symbol>'),
                         ('NATIVE_FUNCTION@0x1010', 'unresolvedNativeCycles'))

    def test_candidate_provenance_requires_all_explicit_boundaries(self):
        runtime = dict(qualified=True, diagnosticOnly=False, gscUnchanged=True,
                       consumerFlagsChanged=False, runtimeAbiChanged=False,
                       binaryHashes={'gxi': 'binary', 'gsc': 'compiler'})
        self.assertTrue(candidate_provenance_valid(runtime, 'binary', 'compiler'))
        for key in ('qualified', 'diagnosticOnly', 'gscUnchanged',
                    'consumerFlagsChanged', 'runtimeAbiChanged', 'binaryHashes'):
            incomplete = dict(runtime)
            incomplete.pop(key)
            self.assertFalse(candidate_provenance_valid(incomplete, 'binary', 'compiler'))
        self.assertFalse(candidate_provenance_valid(runtime, 'changed', 'compiler'))
        self.assertFalse(candidate_provenance_valid(runtime, 'binary', 'changed'))

    def test_native_prefix_receipt_does_not_admit_failed_or_full_suite_claims(self):
        receipt = dict(qualified=True, diagnosticOnly=True, performanceQualified=False,
                       scope='referenced-native-batch-preload-prefix-not-case-or-full-suite',
                       projectHead='f35b14193db7cfc89444b0f9a82b81c3862bc795', nativeExitPolicy=True,
                       wallBudgetSeconds=90, silenceBudgetSeconds=5,
                       runs=[dict(name='baseline', exitCode=0), dict(name='observer', exitCode=0)])
        self.assertTrue(native_admission_receipt_valid(receipt))
        for key in receipt:
            missing = dict(receipt)
            missing.pop(key)
            self.assertFalse(native_admission_receipt_valid(missing))
        self.assertFalse(native_admission_receipt_valid(dict(receipt, silenceBudgetSeconds=10)))
        self.assertFalse(native_admission_receipt_valid(dict(receipt, nativeExitPolicy=False)))
        self.assertFalse(native_admission_receipt_valid(dict(receipt, performanceQualified=True)))
        self.assertFalse(native_admission_receipt_valid(dict(receipt, runs=[dict(name='baseline', exitCode=0)])))


if __name__ == '__main__':
    unittest.main()
