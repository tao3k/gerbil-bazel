import unittest
from unittest.mock import patch
from pathlib import Path

from gambit_guarded_trace import Continuation, Program, Refused, State, inject, macro
from gambit_trace_epoch_cache import prefix, fences, thread_dependency


def procedure(base, body):
    return f"#define ___PH_LBL0 {base}\n___BEGIN_P_SW\n{body}___END_P_SW\n"


def module(index, body, descriptors, controls=None, globals=""):
    original = ("___BEGIN_LBL\n" + "\n".join(descriptors) + "\n___END_LBL\n"
                + globals + body)
    return {"prefix": f"test_m{index}", "offset": 0, "originalBody": body,
            "body": body, "original": original, "controls": controls or {},
            "path": Path(f"module-{index}.c")}


def fixture(effect="", arity=1):
    caller = procedure(0, """___DEF_SLBL(0,___L0_caller)
___IF_NARGS_EQ(1,___NOTHING)
___WRONG_NARGS(0,1,0,0)
___DEF_GLBL(___L_caller)
___SET_STK(1,___R0)
___SET_STK(2,___R1)
___SET_R0(___LBL(1))
___ADJFP(8)
___JUMPGLONOTSAFE(___SET_NARGS(1),0,___G_dispatch)
___DEF_SLBL(1,___L1_caller)
___SET_R0(___STK(-7))
___ADJFP(-8)
___JUMPRET(___R0)
""")
    initializer = procedure(0, f"""___DEF_SLBL(0,___L0_init)
___SET_R1(___LBL(2))
___JUMPRET(___R0)
___DEF_SLBL(2,___L2_init)
___IF_NARGS_EQ({arity},___NOTHING)
___WRONG_NARGS(2,{arity},0,0)
___IF(___STRUCTUREP(___R1))
___GOTO(___L_hot)
___END_IF
___VECTORSET(___R1,___FIX(0L),___FAL)
___JUMPRET(___R0)
___DEF_GLBL(___L_hot)
{effect}
___JUMPRET(___R0)
""")
    dispatch = procedure(10, """___DEF_SLBL(0,___L0_dispatch)
___IF_NARGS_EQ(1,___NOTHING)
___WRONG_NARGS(0,1,0,0)
___DEF_GLBL(___L_dispatch)
___SET_R2(___VECTORREF(___GLO_methods,___FIX(0L)))
___JUMPGENNOTSAFE(___SET_NARGS(1),___R2)
""")
    rows = ["___DEF_LBL_PROC(___host,1,-1)"] * 11
    rows[2] = f"___DEF_LBL_PROC(___host,{arity},-1)"
    return [module(0, caller, rows),
            module(1, initializer + dispatch, rows,
                   {"___GLO_methods": "___GLO(0,___G_methods)"},
                   "___DEF_MOD_GLO(0,___G_dispatch,10)\n")]


class GuardedTraceTest(unittest.TestCase):
    def test_structure_region_commits_only_complete_fixed_fields(self):
        setup = '''___BEGIN_ALLOC_STRUCTURE(3UL)
___ADD_STRUCTURE_ELEM(0,___R2)
___ADD_STRUCTURE_ELEM(1,___R1)
___ADD_STRUCTURE_ELEM(2,___FAL)
___END_ALLOC_STRUCTURE(3)
___SET_R1(___GET_STRUCTURE(3))
'''
        modules = fixture(effect=setup)
        report = inject(modules, allow_polls=True, restart_polls=True, transactional_allocations=True)
        self.assertTrue(report['guardedReadOnlyTraces'])
        self.assertEqual(report['guardedReadOnlyTraces'][0]['transactionalHeapWords'], 4)
        self.assertEqual(report['guardedReadOnlyTraces'][0]['transactionalFreshStructures'], 1)
        for invalid in (setup.replace('___ADD_STRUCTURE_ELEM(1,___R1)\n', ''),
                        setup.replace('___ADD_STRUCTURE_ELEM(1,___R1)', '___ADD_STRUCTURE_ELEM(0,___R1)'),
                        setup.replace('___R1)\n___ADD_STRUCTURE_ELEM(2', '___CONS(___R1,___NUL))\n___ADD_STRUCTURE_ELEM(2'),
                        setup.replace('___END_ALLOC_STRUCTURE(3)', '___END_ALLOC_STRUCTURE(2)')):
            rejected = inject(fixture(effect=invalid), allow_polls=True, restart_polls=True,
                              transactional_allocations=True)
            self.assertFalse(rejected['guardedReadOnlyTraces'])

    def test_known_wide_global_calls_preserve_native_argument_layout(self):
        for arity in (4, 6, 16):
            modules = fixture(effect='''___BEGIN_ALLOC_STRUCTURE(1UL)
___ADD_STRUCTURE_ELEM(0,___R1)
___END_ALLOC_STRUCTURE(1)
___SET_R1(___GET_STRUCTURE(1))
''')
            for row in modules:
                for key in ('original', 'body', 'originalBody'):
                    row[key] = row[key].replace('___IF_NARGS_EQ(1,', f'___IF_NARGS_EQ({arity},')
                    row[key] = row[key].replace('___SET_NARGS(1)', f'___SET_NARGS({arity})')
                    row[key] = row[key].replace('___DEF_LBL_PROC(___host,1,-1)', f'___DEF_LBL_PROC(___host,{arity},-1)')
                    row[key] = row[key].replace(
                        f'___JUMPGENNOTSAFE(___SET_NARGS({arity}),___R2)',
                        f'___JUMPGLONOTSAFE(___SET_NARGS({arity}),1,___G_ctor)')
                row['original'] += '\n___DEF_MOD_GLO(1,___G_ctor,2)\n' if row is modules[1] else ''
            report = inject(modules, allow_polls=True, restart_polls=True, transactional_allocations=True)
            self.assertTrue(report['guardedReadOnlyTraces'], arity)
            self.assertEqual(report['guardedReadOnlyTraces'][0]['transactionalHeapWords'], 2)

    def test_static_label_procedure_predicate_keeps_native_check(self):
        program = Program(fixture(), transactional_allocations=True)
        state = State()
        position = program.entries[1, 2]
        checked = program.expression('___PROCEDUREP(___LBL(2))', 1, position, state)
        self.assertEqual(checked, '___PROCEDUREP(' + program.descriptor(1, 2) + ')')
        with self.assertRaises(Refused):
            program.expression('___CAR(___LBL(2))', 1, position, state)

    def test_fresh_closure_setup_requires_complete_owned_fields(self):
        setup = '''___SET_R1(___ALLOC_CLO(2UL))
___BEGIN_SETUP_CLO(2,___R1,2)
___ADD_CLO_ELEM(0,___R2)
___ADD_CLO_ELEM(1,___R3)
___END_SETUP_CLO(2)
'''
        modules = fixture(effect=setup)
        report = inject(modules, allow_polls=True, restart_polls=True, transactional_allocations=True)
        self.assertTrue(report['guardedReadOnlyTraces'])
        self.assertEqual(report['guardedReadOnlyTraces'][0]['transactionalHeapWords'], 4)
        code = modules[0]['body']
        self.assertIn('___ALLOC_CLO(2UL)', code)
        self.assertIn('___LABEL_ENTRY_OR_DESCR]=(test_m1___lp+', code)
        self.assertIn('(___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0)', code)
        for invalid in (setup.replace('___ADD_CLO_ELEM(1,___R3)\n', ''),
                        setup.replace('___ADD_CLO_ELEM(1,___R3)', '___ADD_CLO_ELEM(0,___R3)'),
                        setup.replace('___BEGIN_SETUP_CLO(2,___R1,2)', '___BEGIN_SETUP_CLO(2,___R2,2)'),
                        setup.replace('___END_SETUP_CLO(2)', '')):
            rejected = inject(fixture(effect=invalid), allow_polls=True, restart_polls=True,
                              transactional_allocations=True)
            self.assertFalse(rejected['guardedReadOnlyTraces'])

    def test_closure_type_facts_do_not_allow_incomplete_field_reads(self):
        program = Program(fixture(), transactional_allocations=True)
        state = State()
        closure = program.expression('___ALLOC_CLO(1UL)', 0, 1, state)
        state.registers[1] = closure
        self.assertEqual(program.expression('___PROCEDUREP(___R1)', 0, 1, state), '1')
        self.assertEqual(program.expression('___PAIRP(___R1)', 0, 1, state), '0')
        with self.assertRaises(Refused):
            program.expression('___CLO(___R1,1)', 0, 1, state)
        branch = state.fork()
        branch.initialized_closures.add(closure)
        self.assertNotIn(closure, state.initialized_closures)
        self.assertEqual(program.expression('___CLO(___R1,1)', 0, 1, branch), f'___CLO({closure},1)')
        for size in ('17UL', '___R1'):
            with self.assertRaises(Refused):
                program.expression(f'___ALLOC_CLO({size})', 0, 1, state)

    def test_fresh_pair_predicates_prune_impossible_allocation_paths(self):
        program = Program(fixture(), transactional_allocations=True)
        state = State()
        pair = program.expression('___CONS(___R1,___NUL)', 0, 1, state)
        state.registers[1] = pair
        self.assertEqual(program.expression('___PAIRP(___R1)', 0, 1, state), '1')
        for predicate in ('NULLP', 'STRUCTUREP', 'SYMBOLP', 'BOXP'):
            self.assertEqual(program.expression(f'___{predicate}(___R1)', 0, 1, state), '0')
        self.assertEqual(program.expression('___NOT(___NULLP(___R1))', 0, 1, state), '1')
        boolean = state.capture(program.expression('___BOOLEAN(___PAIRP(___R1))', 0, 1, state))
        state.registers[2] = boolean
        self.assertEqual(program.expression('___NOTFALSEP(___R2)', 0, 1, state), '1')
        branch = state.fork()
        branch.fresh_pairs.clear()
        branch.boolean_values.clear()
        self.assertIn(pair, state.fresh_pairs)
        self.assertIn(boolean, state.boolean_values)
        ordinary = Program(fixture())
        self.assertEqual(ordinary.expression('___PAIRP(___R1)', 0, 1, state), f'___PAIRP({pair})')
        with self.assertRaises(Refused):
            ordinary.expression('___NULLP(___R1)', 0, 1, state)

    def test_fresh_pair_cannot_take_null_branch(self):
        modules = fixture(effect='''___SET_R1(___CONS(___R1,___NUL))
___IF(___NULLP(___R1))
___GOTO(___L_impossible)
___END_IF
___JUMPRET(___R0)
___DEF_GLBL(___L_impossible)
___VECTORSET(___R1,___FIX(0L),___FAL)
''')
        report = inject(modules, allow_polls=True, restart_polls=True, transactional_allocations=True)
        self.assertTrue(report['guardedReadOnlyTraces'])
        inserted = modules[0]['body'].split('#if', 1)[1].split('#endif', 1)[0]
        self.assertNotIn('___NULLP(', inserted)
        self.assertIn('!defined(___DEBUG_HEAP_LIMIT)', inserted)

    def test_terminal_static_procedure_label_is_emitted_as_native_descriptor(self):
        modules = fixture()
        program = Program(modules)
        target = Continuation(1, program.entries[1, 2])
        state = State(heap_words=3, terminal=('JUMPGENNOTSAFE', 1, target))
        with patch.object(Program, 'roots', return_value=[1]), \
             patch.object(Program, 'traces', return_value=[state]):
            inject(modules, allow_polls=True, restart_polls=True, transactional_allocations=True)
        self.assertNotIn('Continuation(', modules[0]['body'])
        self.assertIn('___JUMPGENNOTSAFE(___SET_NARGS(1),(test_m1___lp+', modules[0]['body'])

    def test_transactional_pair_reserves_heap_and_rolls_back_every_guard_miss(self):
        modules = fixture(effect='___SET_R1(___CONS(___R1,___NUL))\n___CHECK_HEAP(2,4096)')
        report = inject(modules, allow_polls=True, restart_polls=True,
                        transactional_allocations=True)
        self.assertTrue(report['guardedReadOnlyTraces'])
        self.assertEqual(report['guardedReadOnlyTraces'][0]['transactionalHeapWords'], 3)
        code = modules[0]['body']
        self.assertIn('___hp+3>___ps->heap_limit', code)
        self.assertIn('gb_trace_allocation_miss_0:;\n___hp=gb_heap_checkpoint;', code)
        self.assertIn('goto gb_trace_allocation_miss_0;', code)
        self.assertIn('___SET_R1(gb_t', code)
        self.assertIn('!defined(___USE_HANDLES)', code)
        self.assertTrue(report['guardedReadOnlyTraces'][0]['allocationGuardMisses'])
        self.assertIn('GB_TRACE_GUARD_MISS(0,0)', code)

    def test_allocation_accounting_is_path_local_and_rejects_nested_or_unbounded_pairs(self):
        program = Program(fixture(), transactional_allocations=True)
        state = State()
        program.expression('___CONS(___R1,___NUL)', 0, 1, state)
        self.assertEqual(state.heap_words, 3)
        branch = state.fork()
        program.expression('___XCONS(___R1,___NUL)', 0, 1, branch)
        self.assertEqual(state.heap_words, 3)
        self.assertEqual(branch.heap_words, 6)
        with self.assertRaises(Refused):
            program.expression('___CONS(___CONS(___R1,___NUL),___NUL)', 0, 1, state)
        state.heap_words = 63
        with self.assertRaises(Refused):
            program.expression('___CONS(___R1,___NUL)', 0, 1, state)

    def test_transactional_heap_cannot_cross_external_effects_or_coalesced_polls(self):
        for options in ({}, {'restart_polls': True, 'coalesce_polls': True},
                        {'restart_polls': True, 'primitive_boundary': True}):
            with self.assertRaises(Refused):
                inject(fixture(), transactional_allocations=True, **options)

    def test_thread_cache_fences_preserve_uncertain_and_matching_field_reads(self):
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___VECTORREF(gb_in1,___FIX(25L)));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___UNCHECKEDSTRUCTUREREF(gb_in1,___FIX(27L),___FAL,___FAL));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___VECTORREF(gb_in1,gb_in2));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___CLO(gb_in1,24));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___VECTORREF(gb_in1,___FIX(-1L)));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___UNKNOWNREAD(gb_in1));']), '1')

    def test_thread_cache_low_field_proof_checks_nested_reads_and_type_bounds(self):
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___UNCHECKEDSTRUCTUREREF(gb_in1,___FIX(8L),___FAL,___FAL));']), '0')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___TYPE(gb_in1));',
            '___WORD gb_t1=(___VECTORREF(GB_TRACE_GLO(table,0,name),gb_t0));']), '0')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___SUBTYPE(gb_in1));',
            '___WORD gb_t1=(___VECTORREF(gb_in2,gb_t0));']), '1')
        self.assertEqual(thread_dependency(['___WORD gb_t0=(___VECTORREF(___VECTORREF(gb_in1,___FIX(26L)),___FIX(1L)));']), '1')

    def test_epoch_cache_keys_all_read_inputs_but_not_fresh_query_key(self):
        state = State()
        state.code = ["___WORD gb_t0=(___STRUCTURETYPE(gb_in1));",
                      "if (!(gb_t0==gb_in3)) goto GB_TRACE_MISS;",
                      "if (!(___MEMALLOCATEDP(gb_in2))) goto GB_TRACE_MISS;"]
        result = prefix(state, "___SET_R1(gb_t0); ___SET_R2(gb_in2);", "miss")
        self.assertIn("keys[2]", result)
        self.assertIn("gb_slot->keys[0]==gb_in1", result)
        self.assertIn("gb_slot->keys[1]==gb_in3", result)
        self.assertNotIn("==gb_in2", result)
        self.assertLess(result.index("MEMALLOCATEDP"), result.index("gb_slot->epoch"))
        self.assertIn("gb_slot->epoch==gb_trace_epoch", result)
        state.code.append("___WORD gb_t1=(___STK(-2));")
        self.assertIsNone(prefix(state, "gb_t0", "miss"))

    def test_epoch_fences_unknown_effects_and_global_heap_writes(self):
        modules = fixture()
        program = Program(modules)
        operations = {program.lines[mi][pos].strip() for mi, pos in fences(program, {"STRUCTUREP", "VECTORREF", "FIX"})}
        self.assertIn("___VECTORSET(___R1,___FIX(0L),___FAL)", operations)
        self.assertNotIn("___SET_STK(1,___R0)", operations)
        self.assertNotIn("___WRONG_NARGS(0,1,0,0)", operations)
        self.assertNotIn("___END_IF", operations)
        self.assertNotIn("___SET_R2(___VECTORREF(___GLO_methods,___FIX(0L)))", operations)

    def test_epoch_fence_never_splits_multiline_macro_arguments(self):
        body = procedure(0, "___DEF_SLBL(0,___L0_x)\n___OPAQUE(___R1,\n___R2) ___SET_R1(___STK(-5)\n)\n___JUMPRET(___R0)\n")
        program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
        edits = fences(program, set())
        self.assertEqual(len(edits), 1)
        self.assertTrue(program.lines[0][edits[0][1]].startswith("___OPAQUE("))

    def test_fresh_pair_and_complete_owned_closure_fences_are_distinct(self):
        body = procedure(0, '''___DEF_SLBL(0,___L0_x)
___SET_R1(___CONS(___R1,___NUL))
___SET_STK(1,___ALLOC_CLO(2UL))
___BEGIN_SETUP_CLO(2,___STK(1),0)
___ADD_CLO_ELEM(0,___R1)
___ADD_CLO_ELEM(1,___R2)
___END_SETUP_CLO(2)
___BEGIN_SETUP_CLO(1,___R2,0)
___ADD_CLO_ELEM(0,___R1)
___END_SETUP_CLO(1)
___SET_R1(___BOOLEAN(___NULLP(___R1)))
___SET_R1(___FIXASHL(___R1,___FIX(1L)))
___JUMPRET(___R0)
''')
        program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
        edits = fences(program, {"BOOLEAN", "FIX"})
        fresh = {program.lines[mi][pos].strip() for mi, pos in program.fresh_epoch_fences}
        ordinary = {program.lines[mi][pos].strip() for mi, pos in edits if (mi, pos) not in program.fresh_epoch_fences}
        self.assertIn('___SET_R1(___CONS(___R1,___NUL))', fresh)
        self.assertIn('___SET_STK(1,___ALLOC_CLO(2UL))', fresh)
        self.assertIn('___ADD_CLO_ELEM(1,___R2)', fresh)
        self.assertIn('___BEGIN_SETUP_CLO(1,___R2,0)', ordinary)
        self.assertNotIn('___SET_R1(___FIXASHL(___R1,___FIX(1L)))', ordinary)

    def test_fresh_closure_proof_rejects_interruption_duplicate_fields_and_effects(self):
        fragments = [
            '___POLL(0)\n___BEGIN_SETUP_CLO(1,___R1,0)\n___ADD_CLO_ELEM(0,___R2)\n___END_SETUP_CLO(1)\n',
            '___BEGIN_SETUP_CLO(2,___R1,0)\n___ADD_CLO_ELEM(0,___R2)\n___ADD_CLO_ELEM(0,___R3)\n___END_SETUP_CLO(2)\n',
        ]
        for fragment in fragments:
            body = procedure(0, '___DEF_SLBL(0,___L0_x)\n___SET_R1(___ALLOC_CLO(2UL))\n' + fragment + '___JUMPRET(___R0)\n')
            program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
            fences(program, set())
            self.assertFalse(program.fresh_epoch_fences)
        body = procedure(0, '___DEF_SLBL(0,___L0_x)\n___SET_R1(___CONS(effect(),___NUL))\n___JUMPRET(___R0)\n')
        program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
        fences(program, set())
        self.assertFalse(program.fresh_epoch_fences)

    def test_global_only_prefix_still_checks_live_epoch(self):
        state = State()
        state.code = ["___WORD gb_t0=(GB_TRACE_GLO(table,0,glo));",
                      "if (!(gb_t0==descriptor)) goto GB_TRACE_MISS;"]
        result = prefix(state, "___SET_R4(gb_t0);", "miss", 7)
        self.assertIn("gb_trace_epoch && gb_slot->epoch==gb_trace_epoch", result)
        self.assertIn("GB_TRACE_CACHE_SITE(7)", result)
        self.assertIn("gb_t0=gb_slot->values[0]", result)

    def test_pure_predicates_do_not_invalidate_but_heap_write_does(self):
        body = procedure(0, "___DEF_SLBL(0,___L0_x)\n___SET_R1(___BOOLEAN(___SYMBOLP(___R1)))\n___IF(___FIXPOSITIVEP(___R2))\n___GOTO(___L_hot)\n___END_IF\n___DEF_GLBL(___L_hot)\n___UNCHECKEDSTRUCTURESET(___R1,___R2,___FIX(1L),___FAL,___FAL)\n___JUMPRET(___R0)\n")
        program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
        edits = fences(program, {"BOOLEAN", "FIX"})
        self.assertEqual(len(edits), 1)
        self.assertTrue(program.lines[0][edits[0][1]].startswith("___UNCHECKEDSTRUCTURESET("))

    def test_inlined_lookup_has_precise_post_effect_resume(self):
        modules = fixture(effect="___SET_R1(___GCHASHTABLEREF(___R1,___R2))")
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True,
                        primitive_boundary=True, inline_lookup=True)
        self.assertTrue(report["guardedReadOnlyTraces"])
        site = report["guardedReadOnlyTraces"][0]
        self.assertEqual(site["inlinedLookups"], 1)
        self.assertEqual(site["terminal"], "GB_ORIGINAL_RETURN")
        code = modules[0]["body"]
        self.assertIn("!defined(___DYNAMIC)", code)
        self.assertIn("gb_trace_effect_miss_0", code)
        self.assertEqual(code.count("___GCHASHTABLEREF("), 1)
        point = modules[1]["originalBody"].splitlines().index("___SET_R1(___GCHASHTABLEREF(___R1,___R2))") + 1
        self.assertIn(f"goto gb_trace_resume_1_{point};", code)
        self.assertIn(f"gb_trace_resume_1_{point}:;", modules[1]["body"])

    def test_native_helper_has_distinct_pre_and_post_lookup_misses(self):
        modules = fixture(effect="___SET_R1(___GCHASHTABLEREF(___R1,___R2))")
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True,
                        primitive_boundary=True, inline_lookup=True, outline_lookup=True)
        helper = report["nativeTraceHelpers"]
        self.assertIn('noinline,optimize("O3")', helper)
        self.assertIn("gb_native_effect_miss", helper)
        self.assertIn("return -1;", helper)
        self.assertIn("return 0;", helper)
        self.assertEqual(helper.count("___GCHASHTABLEREF("), 1)
        self.assertIn("gb_native_status < 0", modules[0]["body"])
        self.assertNotIn("___GCHASHTABLEREF(", modules[0]["body"])

    def test_lookup_return_branch_exports_actual_return_word(self):
        modules = fixture(effect="___SET_R1(___GCHASHTABLEREF(___R1,___R2))")
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True,
                        primitive_boundary=True, inline_lookup=True, lookup_return_branches=True)
        self.assertEqual(report['guardedReadOnlyTraces'][0]['terminal'], 'GB_ORIGINAL_RET_TO')
        self.assertEqual(modules[0]['body'].count('___GCHASHTABLEREF('), 1)
        self.assertIn('___JUMPRET(gb_in0)', modules[0]['body'])
        self.assertIn('gb_trace_effect_miss_0', modules[0]['body'])

    def test_lookup_loop_reentry_keeps_one_effect_and_exact_native_frame(self):
        modules = fixture(effect="___SET_R1(___GCHASHTABLEREF(___R1,___R2))")
        caller = modules[0]
        original = caller['body']
        changed = original.replace('___SET_R0(___STK(-7))\n___ADJFP(-8)\n___JUMPRET(___R0)',
                                   '___IF(___NOTFALSEP(___R1))\n___GOTO(___L_return)\n___END_IF\n'
                                   '___SET_R0(___STK(-7))\n___SET_R1(___STK(-6))\n___ADJFP(-8)\n'
                                   '___GOTO(___L_caller)\n___DEF_GLBL(___L_return)\n'
                                   '___SET_R0(___STK(-7))\n___ADJFP(-8)\n___JUMPRET(___R0)')
        caller['body'] = caller['originalBody'] = changed
        caller['original'] = caller['original'].replace(original, changed)
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True,
                        primitive_boundary=True, inline_lookup=True, lookup_return_branches=True)
        site = report['guardedReadOnlyTraces'][0]
        self.assertEqual(site['terminal'], 'GB_ORIGINAL_REENTRY')
        self.assertEqual(site['frameDelta'], 0)
        self.assertEqual(caller['body'].count('___GCHASHTABLEREF('), 1)
        self.assertIn('gb_trace_effect_miss_0', caller['body'])

    def test_lookup_return_branch_requires_precise_effect_fallback(self):
        with self.assertRaises(Refused):
            inject(fixture(), lookup_return_branches=True)

    def test_return_outline_keeps_return_and_effect_fallback_in_caller(self):
        modules = fixture(effect="___SET_R1(___GCHASHTABLEREF(___R1,___R2))")
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True,
                        primitive_boundary=True, inline_lookup=True, outline_lookup=True,
                        lookup_return_branches=True, outline_return_traces=True)
        self.assertEqual(report['guardedReadOnlyTraces'][0]['terminal'], 'GB_ORIGINAL_RET_TO')
        self.assertIn('___GCHASHTABLEREF(', report['nativeTraceHelpers'])
        self.assertNotIn('___GCHASHTABLEREF(', modules[0]['body'])
        self.assertIn('___JUMPRET(gb_in0)', modules[0]['body'])
        self.assertIn('gb_native_status < 0', modules[0]['body'])
        self.assertIn('gb_trace_effect_miss_0', modules[0]['body'])

    def test_return_outline_requires_both_existing_modes(self):
        for options in ({}, {'outline_lookup': True}, {'lookup_return_branches': True}):
            with self.subTest(options=options), self.assertRaises(Refused):
                inject(fixture(), outline_return_traces=True, **options)

    def test_return_branch_guard_budget_is_bounded_and_preserved_on_fork(self):
        state = State(guard_limit=24)
        for _ in range(20):
            state.require('gb_in1==gb_in2')
        branch = state.fork()
        self.assertEqual(branch.guard_limit, 24)
        for _ in range(4):
            branch.require('gb_in1==gb_in2')
        with self.assertRaises(Refused):
            branch.require('gb_in1==gb_in2')
        self.assertEqual(State().guard_limit, 16)

    def test_success_only_equal_words_do_not_leak_to_cold_snapshot(self):
        state = State()
        state.require("___FIXEQ(___FIX(0L),gb_t2)")
        self.assertEqual(state.resolved_word("gb_t2"), "___FIX(0L)")
        cold = state.fork()
        state.require("gb_t3==(test_m0___lp+(2*___LABEL_SIZE*___WS))")
        self.assertEqual(cold.resolved_word("gb_t3"), "gb_t3")
        self.assertEqual(state.resolved_word("gb_t3"), "(test_m0___lp+(2*___LABEL_SIZE*___WS))")
        state.require("___EQP(gb_t4,gb_t5)", False)
        self.assertEqual(state.resolved_word("gb_t4"), "gb_t4")

    def test_rest_parameter_else_is_preserved_without_extra_statement(self):
        body = procedure(0, "___DEF_SLBL(0,___L0_x)\n___IF_NARGS_EQ(0,___SET_R1(___NUL))\n___GET_REST(0,0,0,0)\n___JUMPRET(___R0)\n")
        program = Program([module(0, body, ["___DEF_LBL_PROC(___host,0,-1)"])])
        self.assertEqual(fences(program, {"NUL"}), [])

    def test_epoch_cache_rejects_embedded_c_control_and_callbacks(self):
        for code in ("if (x)\n___OPAQUE(___R1)\nelse\n___OPAQUE(___R2)\n", "___CFUN_SELECT(a,b)\n"):
            body = procedure(0, "___DEF_SLBL(0,___L0_x)\n" + code)
            program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
            with self.assertRaises(ValueError):
                fences(program, set())

    def test_constant_embedded_result_is_readonly_but_function_call_rejected(self):
        for value, accepted in (("___FIX(___TB)", True), ("foreign_callback()", False)):
            body = procedure(0, "___DEF_SLBL(0,___L0_x)\n{ ___SCMOBJ ___RESULT;\n___RESULT = " + value + ";\n___SET_R1(___RESULT)\n}\n___JUMPRET(___R0)\n")
            program = Program([module(0, body, ["___DEF_LBL_PROC(___host,1,-1)"])])
            if accepted:
                self.assertEqual(fences(program, set()), [])
            else:
                with self.assertRaises(ValueError):
                    fences(program, set())

    def test_static_chain_is_guarded_without_named_consumer_policy(self):
        modules = fixture()
        original = modules[0]["body"]
        report = inject(modules)
        self.assertEqual(len(report["guardedReadOnlyTraces"]), 1)
        self.assertEqual(report["guardedReadOnlyTraces"][0]["callsRemoved"], 2)
        rewritten = modules[0]["body"]
        self.assertIn("defined(___SINGLE_THREADED_VMS)", rewritten)
        self.assertIn("(___NB_ARG_REGS == 3)", rewritten)
        self.assertIn("GB_TRACE_GLO(test_m0___glotbl,0,___G_dispatch)", rewritten)
        self.assertIn("___PROCEDUREP(", rewritten)
        self.assertLess(rewritten.index("___PROCEDUREP("), rewritten.index("___LABEL_ENTRY_GET("))
        self.assertIn("test_m1___lp+(2*___LABEL_SIZE*___WS)", rewritten)
        self.assertIn("___JUMPRET(gb_in0)", rewritten)
        self.assertIn("___SET_R1(gb_in1)", rewritten)
        self.assertNotIn("___SET_STK(", rewritten[rewritten.index("#if"):rewritten.index("#endif")])
        self.assertIn(original.split("___DEF_GLBL(___L_caller)\n")[1], rewritten)

    def test_poll_heap_write_allocation_and_opaque_call_refuse_hot_path(self):
        for effect in ("___POLL(1)", "___VECTORSET(___R1,___FIX(0L),___TRU)",
                       "___CHECK_HEAP(1)", "___SET_R1(___MAKEVECTOR(___FIX(1L),___FAL))",
                       "___OPAQUE(___R1)"):
            with self.subTest(effect=effect):
                modules = fixture(effect)
                original = modules[0]["body"]
                self.assertEqual(inject(modules)["guardedReadOnlyTraces"], [])
                self.assertEqual(modules[0]["body"], original)

    def test_wrong_arity_and_ambiguous_binding_use_original(self):
        self.assertEqual(inject(fixture(arity=2))["guardedReadOnlyTraces"], [])
        modules = fixture()
        modules[0]["original"] += "___DEF_MOD_GLO(1,___G_dispatch,0)\n"
        self.assertEqual(inject(modules)["guardedReadOnlyTraces"], [])

    def test_register_aliases_and_continuations_are_not_host_mutations(self):
        modules = fixture()
        modules[0]["body"] = modules[0]["originalBody"] = modules[0]["body"].replace(
            "___SET_STK(2,___R1)", "___SET_STK(2,___R1)\n___SET_R3(___R1)")
        report = inject(modules)
        self.assertEqual(report["guardedReadOnlyTraces"][0]["frameDelta"], 0)
        self.assertIn("___WORD gb_in3=___R3;", modules[0]["body"])
        self.assertIn("___SET_R3(gb_in1)", modules[0]["body"])

    def test_parser_handles_nested_arguments(self):
        self.assertEqual(macro("___IF(___EQP(___STK(-4),___TYPEID(___R1)))"),
                         ("IF", ["___EQP(___STK(-4),___TYPEID(___R1))"]))

    def test_vector_initializer_labels_are_static_candidates(self):
        modules = fixture()
        modules[1]["body"] = modules[1]["originalBody"] = modules[1]["body"].replace(
            "___SET_R1(___LBL(2))", "___ADD_VECTOR_ELEM(0,___LBL(2))")
        self.assertEqual(len(inject(modules)["guardedReadOnlyTraces"]), 1)

    def test_poll_checkpoints_restore_original_descriptors_and_exclude_countdowns(self):
        modules = fixture("___POLL(2)")
        report = inject(modules, allow_polls=True)
        self.assertEqual(report["guardedReadOnlyTraces"][0]["polls"], 1)
        rewritten = modules[0]["body"]
        self.assertIn("!defined(___HEARTBEAT_USING_POLL_COUNTDOWN)", rewritten)
        self.assertIn("!defined(___DEBUG_STACK_LIMIT)", rewritten)
        self.assertIn("___ps->temp1=(test_m1___lp+(2*___LABEL_SIZE*___WS))", rewritten)
        self.assertIn("___ps->handler_stack_limit", rewritten)

    def test_internal_arity_does_not_overwrite_actual_parameter_state(self):
        state = State(nargs=2, actual_nargs="1")
        checkpoint = Program(fixture()).materialize(state)
        self.assertIn("___SET_NARGS(1)", checkpoint)
        self.assertNotIn("___SET_NARGS(2)", checkpoint)

    def test_empty_branch_does_not_add_a_false_path_guard(self):
        baseline = inject(fixture())["guardedReadOnlyTraces"][0]
        modules = fixture("___IF(___NOTFALSEP(___R2))\n___GOTO(___L_noop)\n___END_IF\n___DEF_GLBL(___L_noop)")
        result = inject(modules)["guardedReadOnlyTraces"][0]
        self.assertEqual(result["conditions"], baseline["conditions"])

    def test_readonly_poll_restart_does_not_commit_partial_state(self):
        modules = fixture("___POLL(2)")
        report = inject(modules, allow_polls=True, restart_polls=True)
        self.assertEqual(report["guardedReadOnlyTraces"][0]["polls"], 1)
        fast = modules[0]["body"].split("#if", 1)[1].split("#endif", 1)[0]
        self.assertIn("< ___ps->stack_trip)) goto gb_trace_miss_0", fast)
        self.assertNotIn("___ps->temp1", fast)
        self.assertNotIn("___ps->handler_stack_limit", fast)

    def test_coalesced_checks_cover_peak_virtual_stack_at_both_boundaries(self):
        modules = fixture("___ADJFP(4)\n___POLL(2)\n___ADJFP(-4)\n___POLL(2)")
        report = inject(modules, allow_polls=True, restart_polls=True, coalesce_polls=True)
        site = report["guardedReadOnlyTraces"][0]
        self.assertEqual(site["polls"], 2)
        self.assertEqual(site["peakFrame"], 12)
        fast = modules[0]["body"].split("#if", 1)[1].split("#endif", 1)[0]
        check = "if (___EXPECT_FALSE((___fp-(12)) < ___ps->stack_trip))"
        self.assertEqual(fast.count(check), 2)
        self.assertLess(fast.index(check), fast.index("___WORD gb_in0"))
        self.assertGreater(fast.rindex(check), fast.index("___LABEL_ENTRY_GET("))
        self.assertLess(fast.rindex(check), fast.index("___SET_R0("))

    def test_cross_module_primitive_handoff_keeps_original_effect_instruction(self):
        modules = fixture()
        effect = "___SET_R1(___GCHASHTABLEREF(___GLO(0,___G_table),___R1))"
        body = procedure(0, "___DEF_SLBL(0,___L0_effect)\n"
            "___IF_NARGS_EQ(1,___NOTHING)\n___WRONG_NARGS(0,1,0,0)\n"
            "___DEF_GLBL(___L_effect)\n" + effect + "\n___JUMPRET(___R0)\n")
        modules.append(module(2, body, ["___DEF_LBL_PROC(___host,1,-1)"]))
        report = inject(modules, primitive_boundary=True)
        self.assertEqual(report["guardedReadOnlyTraces"][0]["terminal"], "GB_ORIGINAL_EFFECT")
        self.assertIn("test_m2___lp+(0*___LABEL_SIZE*___WS)", modules[0]["body"])
        self.assertIn("goto gb_trace_resume_2_", modules[0]["body"])
        self.assertNotIn("___GCHASHTABLEREF", modules[0]["body"])
        self.assertEqual(modules[2]["body"].count(effect), 1)
        self.assertLess(modules[2]["body"].index("gb_trace_resume_2_"),
                        modules[2]["body"].index(effect))


if __name__ == "__main__":
    unittest.main()
