import unittest

from gambit_trace_selection import select_candidate, self_typed_constructor_guard


class TraceSelectionTests(unittest.TestCase):
    def candidate(self, index, guard, tail=''):
        return index, {'freshStructures': {'fresh': ['descriptor', 'value'],
                                           'second': ['descriptor', 'fresh']}}, {
            'code': [guard, tail]}

    def test_self_typed_path_beats_shorter_rebound_path(self):
        rebound = self.candidate(0, 'if (!(___NOT(___EQP(___TYPEID(descriptor),tag)))) goto GB_TRACE_MISS;')
        typed = self.candidate(1, 'if ((___NOT(___EQP(___TYPEID(descriptor),tag)))) goto GB_TRACE_MISS;', 'longer' * 100)
        self.assertEqual(select_candidate([rebound, typed]), typed)
        self.assertEqual(typed[2]['code'][0], 'if ((___NOT(___EQP(___TYPEID(descriptor),tag)))) goto GB_TRACE_MISS;')

    def test_unrelated_descriptor_not_preferred(self):
        candidate = self.candidate(0, 'if ((___NOT(___EQP(___TYPEID(other),tag)))) goto GB_TRACE_MISS;')
        self.assertFalse(self_typed_constructor_guard(candidate[1], candidate[2]))

    def test_no_descriptor_guard_keeps_length_ranking(self):
        first = self.candidate(0, 'long code')
        second = self.candidate(1, 'short')
        self.assertEqual(select_candidate([first, second]), second)

    def test_empty_candidates_refused(self):
        with self.assertRaises(ValueError):
            select_candidate([])

    def test_single_constructor_retains_original_ranking(self):
        typed = self.candidate(1, 'if ((___NOT(___EQP(___TYPEID(descriptor),tag)))) goto GB_TRACE_MISS;')
        del typed[1]['freshStructures']['second']
        self.assertFalse(self_typed_constructor_guard(typed[1], typed[2]))


if __name__ == '__main__':
    unittest.main()
