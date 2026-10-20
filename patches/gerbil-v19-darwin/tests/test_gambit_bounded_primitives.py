import unittest
from pathlib import Path

from gambit_bounded_primitives import inject, inject_runtime_unit, PREAMBLE


class BoundedPrimitiveTests(unittest.TestCase):
    def test_runtime_region_preserves_original_metadata_and_declarations(self):
        source = 'metadata\n___BEGIN_M_COD\n___JUMPGENSAFE(___SET_NARGS(2),___R3)\n___END_M_COD\ntables\n'
        result, details = inject_runtime_unit(source, Path('_eval.c'))
        self.assertTrue(result.startswith('metadata\n'))
        self.assertTrue(result.endswith('___END_M_COD\ntables\n'))
        self.assertEqual(details['boundedPrimitiveEntrySites'][0]['sites'], 1)
        self.assertIn('GB_BOUNDED_PRIMITIVE_TRY(___R3,2)', result)

    def test_original_primitive_and_live_global_calls_keep_fallback(self):
        body = ('   ___JUMPPRM(___SET_NARGS(1),___PRM__23__23_length)\n'
                'GB_TRACE_INVALIDATE_AT(12);\n'
                '   ___JUMPGLONOTSAFE(___SET_NARGS(1),7,___G_reverse)\n')
        modules = [{'path': Path('a.c'), 'body': body}]
        details = inject(modules)
        result = modules[0]['body']
        self.assertEqual(details['boundedPrimitiveEntrySites'][0]['sites'], 2)
        self.assertIn('GB_BOUNDED_PRIMITIVE_TRY(___PRM__23__23_length,1)', result)
        self.assertIn('GB_BOUNDED_PRIMITIVE_TRY(___GLO(7,___G_reverse),1)', result)
        self.assertLess(result.index('GB_BOUNDED_PRIMITIVE_TRY(___GLO'), result.index('GB_TRACE_INVALIDATE_AT(12)'))
        self.assertIn('___JUMPGLONOTSAFE(___SET_NARGS(1),7,___G_reverse)', result)

    def test_wrong_arity_other_targets_and_nested_macro_arguments_untouched(self):
        body = ('___JUMPPRM(___SET_NARGS(2),___PRM__23__23_length)\n'
                '___JUMPPRM(___SET_NARGS(1),___PRM__23__23_car)\n'
                '___IF_NARGS_EQ(1,___JUMPPRM(___SET_NARGS(1),___PRM__23__23_length))\n')
        modules = [{'path': Path('a.c'), 'body': body}]
        inject(modules)
        self.assertEqual(modules[0]['body'], body)

    def test_structure_primitive_is_two_argument_and_has_bounded_live_reads(self):
        body = '___JUMPPRM(___SET_NARGS(2),___PRM__23__23_structure_2d_instance_2d_of_3f_)\n'
        modules = [{'path': Path('a.c'), 'body': body}]
        inject(modules)
        self.assertIn('GB_BOUNDED_PRIMITIVE_TRY', modules[0]['body'])
        self.assertIn('depth<128', PREAMBLE)
        self.assertIn('___TYPEID(type)', PREAMBLE)
        self.assertIn('___TYPESUPER(type)', PREAMBLE)
        self.assertNotIn('gb_cache', PREAMBLE)

    def test_indirect_primitive_target_with_nested_arguments_is_evaluated_once(self):
        body = '___JUMPGENSAFE(___SET_NARGS(2),___CLO(___R4,1))\n'
        modules = [{'path': Path('a.c'), 'body': body}]
        inject(modules)
        self.assertIn('GB_BOUNDED_PRIMITIVE_TRY(___CLO(___R4,1),2)', modules[0]['body'])
        self.assertIn(body, modules[0]['body'])
        self.assertIn('___WORD gb_primitive=(expression),gb_answer;', PREAMBLE)
        body = '___JUMPGENSAFE(___SET_NARGS(2),effect())\n'
        modules = [{'path': Path('a.c'), 'body': body}]
        inject(modules)
        self.assertEqual(modules[0]['body'], body)

    def test_darwin_gnu_heap_stack_and_list_bounds_are_explicit(self):
        self.assertIn('defined(__APPLE__)', PREAMBLE)
        self.assertIn('!defined(__clang__)', PREAMBLE)
        self.assertIn('size>=64', PREAMBLE)
        self.assertIn('input==___NUL ? size : -1', PREAMBLE)
        self.assertIn('___hp+(3*gb_size)<=___ps->heap_limit', PREAMBLE)
        self.assertIn('(___fp-32)<___ps->stack_trip', PREAMBLE)
        self.assertIn('!defined(___HEARTBEAT_USING_POLL_COUNTDOWN)', PREAMBLE)
        self.assertIn('gb_answer=___CONS(___CAR(gb_input),gb_answer)', PREAMBLE)
        self.assertIn('} while (0);', PREAMBLE)


if __name__ == '__main__':
    unittest.main()
