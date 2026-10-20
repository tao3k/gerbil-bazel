import re
import unittest

from gambit_dynamic_parameter_entry import inject_late_bound_parameter_entry
from gambit_parameter_entry import identity_preamble


class DynamicParameterEntryTest(unittest.TestCase):
    def fixture(self):
        names = re.findall(r'^___IMP_DATA\(___glo_struct,___G_(\w+)\);$',
            identity_preamble(env_lookup=True), re.M)
        bindings = ''.join(f'#define ___GLO_{name} ___GLO({i},___G_{name})\n' for i, name in enumerate(names))
        return bindings+'___BEGIN_M_COD\n___JUMPGLONOTSAFE(___SET_NARGS(0),20,___G_p)\n___END_M_COD\n'

    def test_late_binding_requires_dynamic_and_preserves_original_call(self):
        output, details = inject_late_bound_parameter_entry(self.fixture())
        self.assertEqual(details['parameterSites'], 1)
        self.assertIn('GB_PARAMETER_TRY(___GLO(20,___G_p))\n___JUMPGLONOTSAFE', output)
        self.assertIn(' && defined(___DYNAMIC)', output)
        self.assertIn('#if defined(___DYNAMIC)\n#define ___G_', output)
        self.assertNotIn('___IMP_DATA(___glo_struct', output)
        self.assertNotIn('DYNAMIC-FAST-PATH-HIT', output)

    def test_missing_dependency_is_refused_not_imported_as_static_symbol(self):
        with self.assertRaisesRegex(ValueError, 'undeclared kernel'):
            inject_late_bound_parameter_entry(self.fixture().split('\n', 1)[1])

    def test_repeated_injection_is_refused(self):
        output, _ = inject_late_bound_parameter_entry(self.fixture())
        with self.assertRaisesRegex(ValueError, 'already injected'):
            inject_late_bound_parameter_entry(output)

    def test_optional_hit_marker_is_only_a_diagnostic(self):
        output, details = inject_late_bound_parameter_entry(self.fixture(), diagnostic_hit=True)
        self.assertTrue(details['diagnosticHit'])
        self.assertIn('DYNAMIC-FAST-PATH-HIT', output)
        self.assertIn('!defined(__clang__)', output)

    def test_incomplete_module_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'complete generated module'):
            inject_late_bound_parameter_entry(self.fixture().replace('___END_M_COD', ''))

    def test_safe_calls_are_not_lowered_to_unsafe_getter_transfers(self):
        with self.assertRaisesRegex(ValueError, 'no eligible'):
            inject_late_bound_parameter_entry(self.fixture().replace('JUMPGLONOTSAFE', 'JUMPGLOSAFE'))

    def test_safe_opt_in_keeps_safe_getter_dispatch_and_original_fallback(self):
        fixture = self.fixture().replace('JUMPGLONOTSAFE', 'JUMPGLOSAFE')
        output, details = inject_late_bound_parameter_entry(fixture, include_safe=True)
        self.assertEqual(details['parameterSites'], 1)
        self.assertIn('GB_PARAMETER_TRY_SAFE(___GLO(20,___G_p))\n___JUMPGLOSAFE', output)
        self.assertIn('GB_PARAMETER_TRY_MODE(expression,___JUMPGENSAFE)', output)
        self.assertIn('GB_PARAMETER_TRY_MODE(expression,___JUMPGENNOTSAFE)', output)


if __name__ == '__main__':
    unittest.main()
