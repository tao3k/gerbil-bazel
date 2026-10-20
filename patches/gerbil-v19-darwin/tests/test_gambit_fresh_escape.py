import unittest

from gambit_fresh_escape import audit, scalarize
from gambit_guarded_trace import Refused, State


class FreshEscapeTest(unittest.TestCase):
    def test_scalarization_drops_only_owned_pair_and_preserves_original_state(self):
        state = State(code=['___WORD gb_t0=(___XCONS(___NUL,gb_in1));',
                            '___WORD gb_t1=(___CAR(gb_t0));'],
                      fresh_pairs={'gb_t0'}, heap_words=3)
        changed, receipt = scalarize(state, '___SET_R1(gb_t1)')
        self.assertEqual(changed.code, ['___WORD gb_t1=(gb_in1);'])
        self.assertEqual(changed.heap_words, 0)
        self.assertEqual(receipt['potentiallyElidableHeapWords'], 3)
        self.assertEqual(state.heap_words, 3)
        self.assertEqual(state.fresh_pairs, {'gb_t0'})

    def test_scalarization_keeps_escaping_nested_container_and_identity_guard(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));',
                            '___WORD gb_t1=(___CONS(gb_t0,___NUL));'],
                      fresh_pairs={'gb_t0', 'gb_t1'}, heap_words=6)
        changed, _ = scalarize(state, '___SET_R1(gb_t1)')
        self.assertEqual(changed.code, state.code)
        state.code.append('if (!(___EQP(gb_t1,gb_in2))) goto GB_TRACE_MISS;')
        changed, _ = scalarize(state, '')
        self.assertEqual(changed.heap_words, 6)

    def test_scalarization_removes_complete_structure_but_keeps_returned_child(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));',
                            '___BEGIN_ALLOC_STRUCTURE(2UL);',
                            '___ADD_STRUCTURE_ELEM(0,___FAL)',
                            '___ADD_STRUCTURE_ELEM(1,gb_t0)',
                            '___END_ALLOC_STRUCTURE(2)',
                            '___WORD gb_t1=(___GET_STRUCTURE(2));',
                            '___WORD gb_t2=(___UNCHECKEDSTRUCTUREREF(gb_t1,___FIX(1L),___FAL,___FAL));'],
                      fresh_pairs={'gb_t0'}, fresh_structures={'gb_t1': ('___FAL', 'gb_t0')}, heap_words=6)
        changed, _ = scalarize(state, '___SET_R1(gb_t2)')
        self.assertEqual(changed.heap_words, 3)
        self.assertEqual(changed.code, [state.code[0], '___WORD gb_t2=(gb_t0);'])
        self.assertEqual(changed.fresh_structures, {})

    def test_scalarization_refuses_unidentifiable_structure_constructor(self):
        state = State(code=['___BEGIN_ALLOC_STRUCTURE(1UL);',
                            '___WORD gb_t0=(___GET_STRUCTURE(1));'],
                      fresh_structures={'gb_t0': ('___FAL',)}, heap_words=2)
        with self.assertRaises(Refused):
            scalarize(state, '')

    def test_returned_object_cannot_be_removed(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));'],
                      fresh_pairs={'gb_t0'}, heap_words=3)
        result = audit(state, '___SET_R1(gb_t0)')
        self.assertEqual(result['retainedHeapWords'], 3)
        self.assertEqual(result['potentiallyElidableHeapWords'], 0)

    def test_owned_pair_reads_can_separate_object_from_returned_field(self):
        for constructor, reader in (('CONS', 'CAR'), ('XCONS', 'CDR')):
            state = State(code=[f'___WORD gb_t0=(___{constructor}(gb_in1,___NUL));',
                                f'___WORD gb_t1=(___{reader}(gb_t0));'],
                          fresh_pairs={'gb_t0'}, heap_words=3)
            self.assertEqual(audit(state, '___SET_R1(gb_t1)')['potentiallyElidableHeapWords'], 3)

    def test_escaping_container_keeps_owned_children(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));',
                            '___WORD gb_t1=(___CONS(gb_t0,___NUL));'],
                      fresh_pairs={'gb_t0', 'gb_t1'}, heap_words=6)
        self.assertEqual(audit(state, '___SET_R1(gb_t1)')['retainedHeapWords'], 6)

    def test_fresh_structure_field_read_preserves_only_observed_child(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));',
                            '___WORD gb_t1=(___GET_STRUCTURE(2));',
                            '___WORD gb_t2=(___UNCHECKEDSTRUCTUREREF(gb_t1,___FIX(1L),___FAL,___FAL));'],
                      fresh_pairs={'gb_t0'}, fresh_structures={'gb_t1': ('___FAL', 'gb_t0')}, heap_words=6)
        result = audit(state, '___SET_R1(gb_t2)')
        self.assertEqual(result['retainedHeapWords'], 3)
        self.assertEqual(result['potentiallyElidableHeapWords'], 3)

    def test_identity_guards_and_scratch_registers_are_not_discarded(self):
        state = State(code=['___WORD gb_t0=(___CONS(gb_in1,___NUL));',
                            'if (!(___EQP(gb_t0,gb_in2))) goto GB_TRACE_MISS;'],
                      fresh_pairs={'gb_t0'}, heap_words=3)
        self.assertEqual(audit(state, '')['retainedHeapWords'], 3)
        state.code.pop()
        self.assertEqual(audit(state, '___SET_R2(gb_t0)')['retainedHeapWords'], 3)

    def test_partial_regions_and_inconsistent_inventory_fail(self):
        for state in (State(heap_words=3), State(effects=1), State(structure_setup=(1, ()))):
            with self.assertRaises(Refused):
                audit(state, '')


if __name__ == '__main__':
    unittest.main()
