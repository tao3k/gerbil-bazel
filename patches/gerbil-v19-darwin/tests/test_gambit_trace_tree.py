import unittest

from gambit_guarded_trace import Program, Refused, State, inject
from gambit_trace_tree import emit, guard_condition
from test_gambit_guarded_trace import module, procedure


def pure_fixture(effect=None):
    caller = procedure(0, '''___DEF_SLBL(0,___L0_caller)
___IF_NARGS_EQ(1,___NOTHING)
___WRONG_NARGS(0,1,0,0)
___DEF_GLBL(___L_caller)
___JUMPGLONOTSAFE(___SET_NARGS(1),0,___G_test)
''')
    callee = procedure(0, '''___DEF_SLBL(0,___L0_test)
___IF_NARGS_EQ(1,___NOTHING)
___WRONG_NARGS(0,1,0,0)
___DEF_GLBL(___L_test)
'''+(effect or '''___IF(___STRUCTUREDIOP(___R1,___SYM_type))
___GOTO(___L_yes)
___END_IF
___SET_R1(___FAL)
___JUMPRET(___R0)
___DEF_GLBL(___L_yes)
___SET_R1(___UNCHECKEDSTRUCTUREREF(___R1,___FIX(1L),___FAL,___FAL))
___JUMPRET(___R0)
'''))
    descriptors = ['___DEF_LBL_PROC(___host,1,-1)']
    return [module(0, caller, descriptors),
            module(1, callee, descriptors, {'___SYM_type': '___SYM(0,___S_type)'},
                   '___DEF_MOD_GLO(0,___G_test,0)\n')]


class PureTraceTreeTest(unittest.TestCase):
    def test_caller_owned_structure_guards_observe_fields_not_container_identity(self):
        program = Program(pure_fixture(), fresh_branches=True, fresh_caller_regions=True)
        state = State(fresh_structures={'gb_t0': ('gb_in2', 'gb_in1', '___FAL')})
        state.registers[1] = 'gb_t0'
        self.assertEqual(program.expression('___UNCHECKEDSTRUCTUREREF(___R1,___FIX(1L),___FAL,___FAL)', 0, 0, state), 'gb_in1')
        self.assertEqual(program.expression('___STRUCTUREDIOP(___R1,___TRU)', 0, 0, state), '___EQP(___TYPEID(gb_in2),___TRU)')
        default = Program(pure_fixture(), fresh_branches=True)
        self.assertIn('gb_t0', default.expression('___STRUCTUREDIOP(___R1,___TRU)', 0, 0, state))

    def test_caller_predicate_facts_reject_structure_contradictions_without_affecting_default(self):
        state = State(predicate_facts={})
        state.require('___STRUCTUREDIOP(gb_in1,___SYM_type)')
        branch = state.fork()
        branch.require('___NOT(___STRUCTUREP(gb_in1))')
        self.assertTrue(branch.infeasible)
        self.assertFalse(state.infeasible)
        default = State()
        default.require('___STRUCTUREDIOP(gb_in1,___SYM_type)')
        default.require('___NOT(___STRUCTUREP(gb_in1))')
        self.assertFalse(default.infeasible)

    def test_caller_type_facts_follow_readonly_ssa_but_not_negative_type_tests(self):
        state = State(predicate_facts={})
        state.require('___STRUCTUREDIOP(gb_in1,___SYM_type)')
        owner = state.capture('___STRUCTURETYPE(gb_in1)')
        identity = state.capture('___TYPEID('+owner+')')
        state.require('___EQP('+identity+',___SYM_type)', False)
        self.assertTrue(state.infeasible)
        negative = State(predicate_facts={})
        negative.require('___STRUCTUREDIOP(gb_in1,___SYM_type)', False)
        negative.require('___STRUCTUREP(gb_in1)')
        self.assertFalse(negative.infeasible)

    def test_source_caller_conditional_goto_keeps_both_guarded_paths(self):
        program = Program(pure_fixture('''___IF_GOTO(___PAIRP(___R1),___L_yes)
___SET_R1(___FAL)
___JUMPRET(___R0)
___DEF_GLBL(___L_yes)
___SET_R1(___TRU)
___JUMPRET(___R0)
'''), fresh_branches=True, fresh_caller_regions=True)
        states = program.traces(0, next(program.roots(0)))
        self.assertEqual(len(states), 2)
        self.assertTrue(all(state.terminal is None for state in states))
        self.assertTrue(any('if ((___PAIRP(' in '\n'.join(state.code) for state in states))
        self.assertTrue(any('if (!(___PAIRP(' in '\n'.join(state.code) for state in states))

    def test_source_caller_exact_local_label_call_checks_callee_arity(self):
        body = '''___SET_STK(1,___R0)
___SET_R0(___LBL(1))
___JUMPGENNOTSAFE(___SET_NARGS(1),___LBL(2))
___DEF_SLBL(1,___L1_return)
___JUMPRET(___STK(1))
___DEF_SLBL(2,___L2_local)
___IF_NARGS_EQ(1,___NOTHING)
___WRONG_NARGS(2,1,0,0)
___SET_R1(___CONS(___R1,___NUL))
___JUMPRET(___R0)
'''
        for nargs, expected in ((1, 1), (2, 0)):
            program = Program(pure_fixture(body.replace('___SET_NARGS(1)', f'___SET_NARGS({nargs})')),
                              fresh_branches=True, fresh_caller_regions=True)
            states = program.traces(0, next(program.roots(0)))
            completed = [state for state in states if state.terminal is None or state.terminal[0] == 'GB_INPUT_STACK_RETURN']
            self.assertEqual(len(completed), expected)
            if completed:
                self.assertEqual(completed[0].heap_words, 3)

    def test_source_caller_owned_pair_fields_are_path_local_and_end_known_list(self):
        program = Program(pure_fixture(), fresh_branches=True, fresh_caller_regions=True)
        state = State()
        nil = state.capture('___NUL')
        state.registers[3] = nil
        pair = program.expression('___XCONS(___R3,___R1)', 0, 0, state)
        state.registers[2] = pair
        self.assertEqual(program.expression('___CAR(___R2)', 0, 0, state), 'gb_in1')
        self.assertEqual(program.expression('___CDR(___R2)', 0, 0, state), nil)
        self.assertEqual(program.expression('___NULLP(___CDR(___R2))', 0, 0, state), '1')
        self.assertEqual(program.expression('___NOT(___PAIRP(___CDR(___R2)))', 0, 0, state), '1')
        branch = state.fork()
        branch.fresh_pair_fields.clear()
        self.assertIn(pair, state.fresh_pair_fields)
        default = Program(pure_fixture(), fresh_branches=True)
        original = State()
        default.expression('___CONS(___R1,___NUL)', 0, 0, original)
        self.assertEqual(original.fresh_pair_fields, {})

    def test_supplementary_tree_emission_is_darwin_guarded_and_off_by_default(self):
        default = pure_fixture()
        old = [item['body'] for item in default]
        ordinary = inject(default)
        self.assertEqual(ordinary['supplementaryPureTrees'], [])
        self.assertEqual([item['body'] for item in default], old)
        modules = pure_fixture()
        generated = inject(modules, supplementary_pure_branches=True)
        self.assertEqual(len(generated['supplementaryPureTrees']), 1)
        body = modules[0]['body']
        self.assertIn('defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)', body)
        self.assertIn('GB_PURE_TREE_ENTRY(0)', body)
        self.assertEqual(body.count('GB_TRACE_GLO('), 1)
        self.assertIn('gb_pure_tree_miss_0:;', body)
        self.assertIn('___JUMPRET(gb_in0)', body)

    def test_pure_walk_stops_before_preexisting_optimized_entry(self):
        program = Program(pure_fixture(), pure_branches=True)
        point = program.entries[1, 0]
        program.preserved_points.add((1, point))
        states = program.traces(0, next(program.roots(0)))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].terminal, ('GB_ORIGINAL_EFFECT', 0, (1, point)))
        self.assertNotIn('___STRUCTUREDIOP', '\n'.join(states[0].code))

    def test_candidates_cover_both_computed_results_without_changing_default(self):
        modules = pure_fixture()
        self.assertEqual(list(Program(modules).roots(0)), [])
        program = Program(modules, pure_branches=True)
        roots = list(program.roots(0))
        self.assertEqual(len(roots), 1)
        states = program.traces(0, roots[0])
        self.assertEqual(len(states), 2)
        self.assertTrue(all(state.effects == state.heap_words == state.frame == 0 for state in states))
        self.assertIn('___FAL', '\n'.join('\n'.join(state.code) for state in states))
        self.assertEqual(len({tuple(state.code) for state in states}), 2)
        self.assertTrue(any('___UNCHECKEDSTRUCTUREREF' in '\n'.join(state.code) for state in states))

    def test_allocation_and_write_resume_at_original_effect_without_executing_it(self):
        for effect in ('___SET_R1(___CONS(___R1,___NUL))\n___JUMPRET(___R0)\n',
                       '___VECTORSET(___R1,___FIX(0L),___FAL)\n___JUMPRET(___R0)\n'):
            program = Program(pure_fixture(effect), pure_branches=True)
            root = next(program.roots(0))
            states = program.traces(0, root)
            self.assertEqual(len(states), 1)
            state = states[0]
            self.assertEqual(state.terminal[0], 'GB_ORIGINAL_EFFECT')
            self.assertEqual(state.effects, 0)
            self.assertEqual(state.heap_words, 0)
            self.assertEqual(state.registers[1], 'gb_in1')
            self.assertNotIn('___CONS', '\n'.join(state.code))
            self.assertNotIn('___VECTORSET', '\n'.join(state.code))

    def test_stack_copy_snapshots_input_before_overlapping_destination_is_restored(self):
        program = Program(pure_fixture('''___SET_STK(0,___STK(-1))
___SET_STK(-1,___R1)
___JUMPRET(___R0)
'''), pure_branches=True)
        states = program.traces(0, next(program.roots(0)))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertRegex(state.stack[0], r'^gb_t\d+$')
        self.assertIn(f'___WORD {state.stack[0]}=(___STK(-1));', '\n'.join(state.code))
        restored = program.materialize(state, live_only=True)
        self.assertIn('___SET_STK(-1,gb_in1)', restored)
        self.assertIn(f'___SET_STK(0,{state.stack[0]})', restored)
        self.assertNotIn('___SET_STK(0,___STK(-1))', restored)

    def test_effect_resumption_preserves_pending_stack_writes_before_frame_adjustment(self):
        modules = pure_fixture('''___SET_STK(1,___R0)
___IF(___PAIRP(___R1))
___GOTO(___L_yes)
___END_IF
___SET_R1(___FAL)
___BEGIN_ALLOC_STRUCTURE(2UL)
___DEF_GLBL(___L_yes)
___SET_R1(___TRU)
___BEGIN_ALLOC_STRUCTURE(2UL)
''')
        details = inject(modules, supplementary_pure_branches=True)
        self.assertEqual(len(details['supplementaryPureTrees']), 1)
        self.assertEqual(modules[0]['body'].count('___SET_STK(1,gb_in0)'), 2)

    def test_pure_analysis_cannot_mix_with_effectful_lookup_or_allocation(self):
        for flags in ({'transactional_allocations': True}, {'inline_lookup': True},
                      {'lookup_return_branches': True}):
            with self.assertRaises(Refused):
                Program(pure_fixture(), pure_branches=True, **flags)

    def test_tree_shares_prefix_and_uses_both_complementary_arms(self):
        yes = State(code=['___WORD gb_t0=(gb_in1);',
                          'if (!(condition)) goto GB_TRACE_MISS;', '___WORD gb_t2=(___TRU);'])
        no = State(code=['___WORD gb_t0=(gb_in1);',
                         'if ((condition)) goto GB_TRACE_MISS;', '___WORD gb_t2=(___FAL);'])
        result, info = emit([yes, no], lambda state: 'RESULT(gb_t2);')
        self.assertEqual(result.count('___WORD gb_t0='), 1)
        self.assertIn('if (condition)', result)
        self.assertIn('} else {', result)
        self.assertIn('(___TRU)', result)
        self.assertIn('(___FAL)', result)
        self.assertEqual(info['paths'], 2)

    def test_fresh_completed_branches_keep_allocation_and_tail_frame_adjustment(self):
        program = Program(pure_fixture('''___IF(___PAIRP(___R1))
___GOTO(___L_yes)
___END_IF
___SET_R1(___CONS(___R1,___NUL))
___ADJFP(-1)
___JUMPRET(___R0)
___DEF_GLBL(___L_yes)
___SET_R1(___CONS(___R1,___FAL))
___ADJFP(-1)
___JUMPRET(___R0)
'''), fresh_branches=True)
        states = program.traces(0, next(program.roots(0)))
        self.assertEqual(len(states), 2)
        self.assertTrue(all(state.heap_words == 3 and state.frame == -1 for state in states))
        self.assertTrue(all(state.terminal is None and state.effects == 0 for state in states))
        with self.assertRaises(Refused):
            emit(states, lambda state: 'DONE;')
        code, details = emit(states, lambda state: program.materialize(state), allow_fresh=True)
        self.assertEqual(details['paths'], 2)
        self.assertIn('___ADJFP(-1)', code)

    def test_fresh_allocations_cannot_resume_at_external_write_or_partial_setup(self):
        for effect in ('''___SET_R1(___CONS(___R1,___NUL))
___VECTORSET(___R2,___FIX(0L),___R1)
___JUMPRET(___R0)
''', '''___BEGIN_ALLOC_STRUCTURE(2UL)
___ADD_STRUCTURE_ELEM(0,___R1)
___JUMPRET(___R0)
'''):
            program = Program(pure_fixture(effect), fresh_branches=True)
            self.assertEqual(program.traces(0, next(program.roots(0))), [])

    def test_fresh_mode_rejects_other_trace_execution_modes(self):
        for flag in ('pure_branches', 'transactional_allocations', 'inline_lookup',
                     'lookup_return_branches', 'primitive_boundary', 'restart_polls'):
            with self.assertRaises(Refused):
                Program(pure_fixture(), fresh_branches=True, **{flag: True})

    def test_caller_mode_returns_exact_input_stack_snapshot_not_assumed_r0(self):
        modules = pure_fixture('''___SET_R1(___CONS(___R1,___NUL))
___ADJFP(-1)
___JUMPRET(___STK(2))
''')
        ordinary = Program(modules, fresh_branches=True)
        self.assertEqual(ordinary.traces(0, next(ordinary.roots(0))), [])
        caller = Program(modules, fresh_branches=True, fresh_caller_regions=True)
        states = caller.traces(0, next(caller.roots(0)))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].terminal[0], 'GB_INPUT_STACK_RETURN')
        target = states[0].terminal[2]
        self.assertIn(f'___WORD {target}=(___STK(1));', states[0].code)
        self.assertNotEqual(target, 'gb_in0')
        self.assertEqual(states[0].frame, -1)

    def test_single_result_mode_is_opt_in_and_does_not_change_canonical_materialization(self):
        program = Program(pure_fixture(), fresh_branches=True)
        state = State(registers={0: 'gb_in0', 1: 'gb_in1', 2: 'gb_in2', 3: 'gb_in3', 4: 'gb_in4'})
        full = program.materialize(state)
        single = program.materialize(state, result_only=True)
        self.assertIn('___SET_R4(gb_in4)', full)
        self.assertIn('___SET_R1(gb_in1)', single)
        self.assertNotIn('___SET_R2(', single)
        state.terminal = ('GB_ORIGINAL_EFFECT', 0, (0, 1))
        with self.assertRaises(Refused):
            program.materialize(state, result_only=True)
        with self.assertRaises(Refused):
            Program(pure_fixture(), fresh_caller_regions=True)

    def test_fresh_emitter_reserves_maximum_heap_and_rolls_back_late_guard_misses(self):
        modules = pure_fixture('''___SET_R2(___CONS(___R1,___NUL))
___IF(___PAIRP(___R1))
___GOTO(___L_yes)
___END_IF
___SET_R1(___R2)
___JUMPRET(___R0)
___DEF_GLBL(___L_yes)
___SET_R1(___CONS(___R2,___FAL))
___JUMPRET(___R0)
''')
        report = inject(modules, supplementary_fresh_branches=True)
        trees = report['supplementaryPureTrees']
        self.assertEqual(len(trees), 1)
        self.assertTrue(trees[0]['freshAllocationTree'])
        self.assertEqual(trees[0]['maximumHeapWords'], 6)
        self.assertEqual(trees[0]['allocatedReturnPaths'], 2)
        emitted = modules[0]['body']
        self.assertIn('___hp+6>___ps->heap_limit', emitted)
        self.assertIn('gb_fresh_tree_rollback_0:;', emitted)
        self.assertIn('___hp=gb_heap_checkpoint;', emitted)
        self.assertIn('GB_FRESH_TREE_ROLLBACK(0,___hp-gb_heap_checkpoint)', emitted)
        self.assertIn('(___WS == 8)', emitted)
        with self.assertRaises(Refused):
            inject(pure_fixture(), supplementary_pure_branches=True,
                   supplementary_fresh_branches=True)

    def test_fresh_fuser_rejects_invalid_heap_budget_and_incomplete_closures(self):
        base = State(code=['if (!(x)) goto GB_TRACE_MISS;'])
        for invalid in (State(code=base.code, heap_words=-1),
                        State(code=base.code, heap_words=65),
                        State(code=base.code, effects=1),
                        State(code=base.code, fresh_closures={'uninitialized': None})):
            with self.assertRaises(Refused):
                emit([base, invalid], lambda state: 'DONE;', allow_fresh=True)

    def test_effects_or_ambiguous_prefixes_are_not_fused(self):
        normal = State(code=['if (!(x)) goto GB_TRACE_MISS;'])
        with self.assertRaises(Refused):
            emit([normal, State(code=normal.code, effects=1)], lambda state: 'DONE;')
        with self.assertRaises(Refused):
            emit([State(code=['same;']), State(code=['same;', 'different;'])], lambda state: 'DONE;')

    def test_guard_decoding_preserves_nested_predicate_and_rejects_other_control_flow(self):
        self.assertEqual(guard_condition('if (!(___NOT(x))) goto GB_TRACE_MISS;'), ('___NOT(x)', True))
        self.assertIsNone(guard_condition('if (x) system("command");'))
        with self.assertRaises(Refused):
            guard_condition('if (!()x()) goto GB_TRACE_MISS;')


if __name__ == '__main__':
    unittest.main()
