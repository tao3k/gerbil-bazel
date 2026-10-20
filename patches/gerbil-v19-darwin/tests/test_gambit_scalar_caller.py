import unittest

from gambit_scalar_caller import inject
from gambit_guarded_trace import Continuation, Program, Refused, State, inject as inject_carrier
from gambit_fresh_escape import audit, scalarize
from gambit_scalar_boundary import inject as inject_boundary
from test_gambit_trace_tree import pure_fixture


class ScalarCallerTest(unittest.TestCase):
    def test_static_procedure_facts_require_original_proc_metadata(self):
        modules = pure_fixture()
        program = Program(modules, fresh_branches=True, fresh_caller_regions=True)
        state = State()
        state.registers[1] = program.descriptor(0, 0)
        self.assertEqual(program.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')
        state.registers[1] = 'gb_in1'
        self.assertNotEqual(program.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')
        state.registers[1] = program.descriptor(0, 1)
        self.assertNotEqual(program.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')
        state.registers[1] = Continuation(0, program.entries[0, 0])
        self.assertEqual(program.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')
        modules[0]['original'] = modules[0]['original'].replace('___DEF_LBL_PROC(___host,1,-1)',
                                                              '___DEF_LBL_RET(___host,0,0)')
        return_only = Program(modules, fresh_branches=True, fresh_caller_regions=True)
        state.registers[1] = return_only.descriptor(0, 0)
        self.assertNotEqual(return_only.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')
        default = Program(pure_fixture(), fresh_branches=True)
        state.registers[1] = default.descriptor(0, 0)
        self.assertNotEqual(default.expression('___PROCEDUREP(___R1)', 0, 0, state), '1')

    def test_prefix_refuses_cross_module_reads_of_an_absent_host_register(self):
        modules = pure_fixture('''___SET_R2(___CONS(___R3,___NUL))
___IF(___PAIRP(___R1))
___GOTO(___L_yes)
___END_IF
___SET_R1(___CAR(___R2))
___SET_R2(___FAL)
___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)
___DEF_GLBL(___L_yes)
___SET_R1(___CDR(___R2))
___SET_R2(___FAL)
___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)
''')
        modules[0]['controls']['___MD_ALL'] = '___D_R0 ___D_R1 ___D_R2 ___D_R4'
        self.assertEqual(inject_boundary(modules)['supplementaryPureTrees'], [])

    def test_prefix_codegen_keeps_original_host_register_declarations(self):
        modules = self.fixture()
        for module in modules:
            module['controls']['___MD_ALL'] = '___D_R0 ___D_R1 ___D_R2 ___D_R4'
            module['body'] = module['body'].replace('___JUMPRET(___R0)',
                '___SET_R2(___FAL)\n___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)')
            module['originalBody'] = module['body']
        original = modules[1]['body']
        details = inject_boundary(modules)
        self.assertEqual(len(details['supplementaryPureTrees']), 1)
        self.assertIn('___WORD gb_in3=___PSR3;', modules[0]['body'])
        self.assertNotIn('___SET_R3(gb_in3)', modules[0]['body'])
        self.assertIn('gb_scalar_boundary_1_', modules[1]['body'])
        self.assertIn('___G_unknown', modules[1]['body'])
        self.assertEqual(modules[1]['body'].count('___G_unknown'), original.count('___G_unknown'))
        base = self.fixture()
        for module in base:
            module['body'] = module['body'].replace('___JUMPRET(___R0)',
                '___SET_R2(___FAL)\n___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)')
            module['originalBody'] = module['body']
        originals = [module['body'] for module in base]
        planned = inject_boundary(base, apply=False)
        self.assertEqual([module['body'] for module in base], originals)
        self.assertTrue(planned['nativeScalarEdits'])
        carrier = inject_carrier(base, scalar_boundary_labels=['___L_caller'])
        self.assertEqual(len(carrier['scalarBoundaryTrees']), 1)
        self.assertIn('gb_scalar_boundary_1_', base[1]['body'])
        with self.assertRaises(Refused):
            inject_carrier(self.fixture(), scalar_boundary_labels=['___L_caller'],
                           scalar_caller_labels=['___L_caller'])

    def test_boundary_audit_preserves_pending_stores_and_never_executes_unknown_call(self):
        modules = pure_fixture('''___SET_R2(___CONS(___R1,___NUL))
___SET_R1(___CAR(___R2))
___SET_R2(___FAL)
___SET_STK(3,___R1)
___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)
''')
        ordinary = Program(modules, fresh_branches=True, fresh_caller_regions=True)
        self.assertEqual(ordinary.traces(0, ordinary.labels[0]['___L_caller']), [])
        program = Program(modules, fresh_branches=True, fresh_caller_regions=True,
                          fresh_caller_boundaries=True)
        states = program.traces(0, program.labels[0]['___L_caller'])
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(state.terminal[0], 'GB_ORIGINAL_EFFECT')
        owner, point = state.terminal[2]
        self.assertIn('___G_unknown', program.lines[owner][point])
        final = program.materialize(state)
        self.assertIn('___SET_STK(3,', final)
        changed, findings = scalarize(state, final)
        self.assertEqual(findings['potentiallyElidableHeapWords'], 3)
        self.assertEqual(changed.heap_words, 0)
        self.assertNotIn('___G_unknown', '\n'.join(changed.code))

    def test_boundary_pending_fresh_object_store_keeps_allocation(self):
        modules = pure_fixture('''___SET_R2(___CONS(___R1,___NUL))
___SET_STK(3,___R2)
___SET_R1(___CAR(___R2))
___SET_R2(___FAL)
___JUMPGLONOTSAFE(___SET_NARGS(1),1,___G_unknown)
''')
        program = Program(modules, fresh_branches=True, fresh_caller_regions=True,
                          fresh_caller_boundaries=True)
        state = program.traces(0, program.labels[0]['___L_caller'])[0]
        self.assertEqual(audit(state, program.materialize(state))['potentiallyElidableHeapWords'], 0)
        with self.assertRaises(Refused):
            Program(modules, fresh_caller_boundaries=True)

    def fixture(self):
        return pure_fixture('''___SET_R2(___CONS(___R1,___NUL))
___IF(___PAIRP(___R1))
___GOTO(___L_yes)
___END_IF
___SET_R1(___CDR(___R2))
___JUMPRET(___R0)
___DEF_GLBL(___L_yes)
___SET_R1(___CAR(___R2))
___JUMPRET(___R0)
''')

    def test_explicit_scalarization_preserves_original_fallback_and_darwin_gnu_guard(self):
        modules = self.fixture()
        original = modules[0]['body']
        details = inject(modules)
        self.assertEqual(len(details['supplementaryPureTrees']), 1)
        selection = details['supplementaryPureTrees'][0]
        self.assertEqual(selection['maximumHeapWords'], 0)
        self.assertEqual(selection['minimumElidedWords'], 3)
        body = modules[0]['body']
        self.assertIn('defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)', body)
        self.assertIn('GB_SCALAR_ELIDED_WORDS(3)', body)
        self.assertIn('___hp=gb_heap_checkpoint;', body)
        self.assertIn(original.split('___DEF_GLBL(___L_caller)\n')[1], body)

    def test_explicit_labels_do_not_rewrite_unselected_callers(self):
        modules = self.fixture()
        originals = [module['body'] for module in modules]
        details = inject(modules, labels=['___L_nonexistent'])
        self.assertEqual(details['supplementaryPureTrees'], [])
        self.assertEqual([module['body'] for module in modules], originals)

    def test_scalar_plan_merges_into_carrier_without_changing_legacy_selection(self):
        original = inject_carrier(self.fixture())
        modules = self.fixture()
        candidate = inject_carrier(modules, scalar_caller_labels=['___L_caller'])
        self.assertEqual(candidate['guardedReadOnlyTraces'], original['guardedReadOnlyTraces'])
        self.assertEqual(len(candidate['scalarCallerTrees']), 1)
        self.assertIn('GB_SCALAR_ELIDED_WORDS(3)', modules[0]['body'])
        with self.assertRaises(Refused):
            inject_carrier(self.fixture(), supplementary_fresh_branches=True,
                           scalar_caller_labels=['___L_caller'])


if __name__ == '__main__':
    unittest.main()
