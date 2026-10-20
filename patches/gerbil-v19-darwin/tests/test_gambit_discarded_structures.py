import unittest
from types import SimpleNamespace

from gambit_discarded_structures import sink, sink_containers, sink_projected_boundary, sink_unobserved
from gambit_guarded_trace import Refused, State


def constructor(name, fields):
    return [f'___BEGIN_ALLOC_STRUCTURE({len(fields)}UL);'] + [
        f'___ADD_STRUCTURE_ELEM({index},{value})' for index, value in enumerate(fields)
    ] + [f'___END_ALLOC_STRUCTURE({len(fields)})',
         f'___WORD {name}=(___GET_STRUCTURE({len(fields)}));']


def fixture():
    first = ('gb_in1', 'gb_in2')
    second = ('gb_in1', 'gb_t0')
    code = constructor('gb_t0', first) + constructor('gb_t1', second)
    code.append('GB_TRACE_POLL_EVENT();\n'
                'if (___EXPECT_FALSE(___fp < ___ps->stack_trip)) {\n'
                '___SET_R1(gb_t1)\n'
                '___JUMPEXTPRM(___NOTHING,___ps->handler_stack_limit)\n}')
    return State(code=code, heap_words=6,
                 fresh_structures={'gb_t0': first, 'gb_t1': second})


class DiscardedStructuresTest(unittest.TestCase):
    def test_nested_materialization_only_inside_existing_poll(self):
        state = fixture()
        before = state.fork()
        code, report = sink(state, discard_result=True, reserved_heap_words=6)
        self.assertEqual(state, before)
        self.assertEqual(len(code), 1)
        self.assertLess(code[0].index('if ('), code[0].index('___BEGIN_ALLOC_STRUCTURE'))
        self.assertLess(code[0].index('___WORD gb_t0='), code[0].index('___WORD gb_t1='))
        self.assertEqual(report['hotStructureAllocationsRemoved'], 2)
        self.assertEqual(report['materializingPollExits'], 1)

    def test_returned_value_cannot_be_dropped(self):
        with self.assertRaises(Refused):
            sink(fixture(), discard_result=False, reserved_heap_words=6)

    def test_heap_reservation_is_not_relaxed(self):
        with self.assertRaises(Refused):
            sink(fixture(), discard_result=True, reserved_heap_words=5)

    def test_visible_address_use_refused(self):
        state = fixture()
        state.code.append('___SET_R2(gb_t0)')
        with self.assertRaises(Refused):
            sink(state, discard_result=True, reserved_heap_words=6)

    def test_cyclic_snapshot_refused(self):
        state = fixture()
        state.fresh_structures['gb_t0'] = ('gb_in1', 'gb_t1')
        state.code[:5] = constructor('gb_t0', state.fresh_structures['gb_t0'])
        with self.assertRaises(Refused):
            sink(state, discard_result=True, reserved_heap_words=6)

    def test_corrupted_constructor_refused(self):
        state = fixture()
        state.code[1] = '___ADD_STRUCTURE_ELEM(0,gb_other)'
        with self.assertRaises(Refused):
            sink(state, discard_result=True, reserved_heap_words=6)

    def test_effectful_or_unrestored_transfer_refused(self):
        for field in ('effects', 'frame'):
            state = fixture()
            setattr(state, field, 1)
            with self.assertRaises(Refused):
                sink(state, discard_result=True, reserved_heap_words=6)


class ProjectedBoundaryTest(unittest.TestCase):
    def region(self):
        state = fixture()
        state.frame = -8
        state.terminal = ('GB_ORIGINAL_EFFECT', 0, (0, 0))
        state.stack[1] = 'gb_t1'
        state.registers[3] = 'gb_t1'
        state.fresh_pairs.add('gb_t2')
        state.fresh_pair_fields['gb_t2'] = ('gb_in1', 'gb_t1')
        state.code.append('___WORD gb_t2=(___CONS(gb_in1,gb_t1));')
        state.heap_words += 3
        program = SimpleNamespace(lines={0: ['___SET_STK(-5,___R1)',
            '___SET_R0(___LBL(3))', '___JUMPGLONOTSAFE(___SET_NARGS(1),7,___G_next)']})
        return program, state

    def test_pair_and_dead_wrappers_removed_with_real_frame_retained(self):
        program, state = self.region()
        original = state.fork()
        code, exported, report = sink_projected_boundary(program, state, reserved_heap_words=9)
        self.assertEqual(state, original)
        self.assertEqual(exported.frame, -8)
        self.assertEqual(exported.registers[1], 'gb_in1')
        self.assertEqual(exported.registers[3], '___VOID')
        self.assertEqual(exported.stack, {})
        self.assertEqual(report['hotPairAllocationsRemoved'], 1)
        self.assertEqual(report['requiredReservedHeapWords'], 9)
        self.assertNotIn('___CONS(', '\n'.join(code))

    def test_live_stack_reference_refused(self):
        program, state = self.region()
        state.stack[-9] = 'gb_t1'
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9)

    def test_ignored_register_cannot_be_read_before_call(self):
        program, state = self.region()
        program.lines[0].insert(0, '___SET_STK(-6,___R3)')
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9)

    def test_safepoint_before_clobber_refused(self):
        program, state = self.region()
        program.lines[0].insert(0, '___POLL(7)')
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9)

    def test_pair_escape_refused(self):
        program, state = self.region()
        state.code.append('___SET_R2(gb_t2)')
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9)

    def test_projected_pair_snapshot_retains_original_caller_proof(self):
        program, state = self.region()
        state.code[-2], state.code[-1] = state.code[-1], state.code[-2]
        state.code[-1] = state.code[-1].replace('___SET_R1(gb_t1)', '___SET_R1(gb_t2)')
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9)
        code, exported, report = sink_projected_boundary(
            program, state, reserved_heap_words=9, pair_snapshots=True)
        self.assertEqual(exported.frame, -8)
        self.assertEqual(report['hotHeapWordsRemoved'], 9)
        self.assertEqual(report['hotPairAllocationsRemoved'], 1)
        self.assertIn('___CONS(gb_in1,gb_t1)', '\n'.join(code))
        self.assertGreater(code[0].index('___CONS'), code[0].index('if ('))

    def test_projected_pair_snapshot_does_not_allow_live_result(self):
        program, state = self.region()
        state.registers[1] = 'gb_t2'
        with self.assertRaises(Refused):
            sink_projected_boundary(program, state, reserved_heap_words=9, pair_snapshots=True)


class ContainerSnapshotsTest(unittest.TestCase):
    def region(self):
        state = fixture()
        state.code.insert(-1, '___WORD gb_t2=(___CONS(gb_t0,gb_t1));')
        state.code.insert(-1, '___WORD gb_t3=(___CONS(gb_t2,gb_t2));')
        state.code[-1] = state.code[-1].replace('___SET_R1(gb_t1)', '___SET_R1(gb_t3)')
        state.fresh_pairs.update(('gb_t2', 'gb_t3'))
        state.fresh_pair_fields.update(gb_t2=('gb_t0', 'gb_t1'), gb_t3=('gb_t2', 'gb_t2'))
        state.heap_words += 6
        return state

    def test_pair_chain_and_shared_dependency_materialize_once_in_poll(self):
        state = self.region()
        before = state.fork()
        code, report = sink_containers(state, discard_result=True, reserved_heap_words=12)
        self.assertEqual(state, before)
        self.assertEqual(len(code), 1)
        self.assertLess(code[0].index('if ('), code[0].index('___CONS'))
        self.assertEqual(code[0].count('___WORD gb_t2='), 1)
        self.assertLess(code[0].index('___WORD gb_t1='), code[0].index('___WORD gb_t2='))
        self.assertLess(code[0].index('___WORD gb_t2='), code[0].index('___WORD gb_t3='))
        self.assertEqual(report['hotPairAllocationsRemoved'], 2)
        self.assertEqual(report['requiredReservedHeapWords'], 12)

    def test_visible_pair_refused(self):
        state = self.region()
        state.code.append('___SET_R2(gb_t3)')
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)


    def test_missing_fields_refused(self):
        state = self.region()
        del state.fresh_pair_fields['gb_t2']
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)

    def test_original_structure_only_entry_still_refuses_pairs(self):
        with self.assertRaises(Refused):
            sink(self.region(), discard_result=True, reserved_heap_words=12)

    def test_corrupted_pair_constructor_refused(self):
        state = self.region()
        state.code[-2] = '___WORD gb_t3=(___CONS(gb_t1,gb_t2));'
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)

    def test_reserved_heap_is_not_reduced(self):
        with self.assertRaises(Refused):
            sink_containers(self.region(), discard_result=True, reserved_heap_words=11)

    def test_pair_cannot_be_replaced_by_structure_constructor(self):
        state = self.region()
        state.code[-2:-1] = constructor('gb_t3', ('gb_t2', 'gb_t2'))
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)

    def test_forward_pair_reference_refused(self):
        state = self.region()
        state.fresh_pair_fields['gb_t2'] = ('gb_t0', 'gb_t3')
        state.code[-3] = '___WORD gb_t2=(___CONS(gb_t0,gb_t3));'
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)

    def test_snapshot_cannot_materialize_after_guard_already_reads_pair(self):
        state = self.region()
        state.code[-1] = state.code[-1].replace(
            '___fp < ___ps->stack_trip', '___PAIRP(gb_t3)')
        with self.assertRaises(Refused):
            sink_containers(state, discard_result=True, reserved_heap_words=12)


class SelectiveSnapshotsTest(unittest.TestCase):
    def region(self, final='___SET_R1(gb_t1)'):
        state = ContainerSnapshotsTest().region()
        program = SimpleNamespace(materialize=lambda *args, **kwargs: final)
        return program, state

    def test_returned_structures_stay_allocated_pair_chain_moves_into_poll(self):
        program, state = self.region()
        before = state.fork()
        code, final, report = sink_unobserved(program, state, reserved_heap_words=12)
        self.assertEqual(state, before)
        self.assertEqual(report['discardedNodes'], ['gb_t2', 'gb_t3'])
        self.assertEqual(report['hotHeapWordsRemoved'], 6)
        self.assertEqual(report['normalRetainedHeapWords'], 6)
        self.assertEqual('\n'.join(code).count('___GET_STRUCTURE'), 2)
        self.assertNotIn('___CONS', '\n'.join(code[:-1]))
        self.assertIn('___CONS', code[-1])
        self.assertEqual(final, '___SET_R1(gb_t1)___JUMPRET(gb_in0)')

    def test_returned_pair_retains_its_full_dependency_graph(self):
        program, state = self.region('___SET_R1(gb_t3)')
        code, _, report = sink_unobserved(program, state, reserved_heap_words=12)
        self.assertEqual(report['hotHeapWordsRemoved'], 0)
        self.assertEqual(report['discardedNodes'], [])
        self.assertEqual(code, state.code)

    def test_live_stack_pair_is_not_removed(self):
        program, state = self.region('___SET_STK(-9,gb_t2)___SET_R1(gb_t1)')
        _, _, report = sink_unobserved(program, state, reserved_heap_words=12)
        self.assertEqual(report['discardedNodes'], ['gb_t3'])
        self.assertEqual(report['hotHeapWordsRemoved'], 3)

    def test_unrewritten_normal_field_read_is_refused(self):
        program, state = self.region()
        state.code.insert(-1, '___WORD gb_t4=(___CAR(gb_t2));')
        with self.assertRaises(Refused):
            sink_unobserved(program, state, reserved_heap_words=12)

    def test_effect_or_unknown_transfer_is_refused(self):
        for field, value in (('effects', 1), ('terminal', ('GB_ORIGINAL_EFFECT', 0, (0, 0)))):
            program, state = self.region()
            setattr(state, field, value)
            with self.assertRaises(Refused):
                sink_unobserved(program, state, reserved_heap_words=12)


if __name__ == '__main__':
    unittest.main()
