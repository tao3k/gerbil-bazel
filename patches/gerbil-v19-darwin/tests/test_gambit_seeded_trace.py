import unittest

from gambit_guarded_trace import Program, State
from test_gambit_trace_tree import pure_fixture


class SeededTraceTest(unittest.TestCase):
    def program(self):
        return Program(pure_fixture(), fresh_branches=True, fresh_caller_regions=True)

    def test_default_matches_explicit_default_seed(self):
        program = self.program()
        root = next(program.roots(0))
        default = program.traces(0, root)
        seeded = program.traces(0, root, State(guard_limit=32, predicate_facts={}))
        self.assertEqual([state.code for state in default], [state.code for state in seeded])
        self.assertEqual([state.registers for state in default], [state.registers for state in seeded])

    def test_seed_is_copied_and_used(self):
        program = self.program()
        initial = State(guard_limit=32, predicate_facts={})
        initial.registers[1] = '___FAL'
        snapshot = initial.fork()
        states = program.traces(0, next(program.roots(0)), initial)
        self.assertTrue(states)
        self.assertTrue(any('___FAL' in '\n'.join(state.code) for state in states))
        self.assertEqual(initial, snapshot)

    def test_seeded_effect_is_not_erased(self):
        program = self.program()
        initial = State(effects=1, guard_limit=32, predicate_facts={})
        states = program.traces(0, next(program.roots(0)), initial)
        self.assertTrue(states)
        self.assertTrue(all(state.effects == 1 for state in states))

    def test_unknown_seed_rejected(self):
        program = self.program()
        with self.assertRaises(TypeError):
            program.traces(0, next(program.roots(0)), {})

    def test_explicit_default_path_limit_matches_default(self):
        program = self.program()
        root = next(program.roots(0))
        self.assertEqual(program.traces(0, root), program.traces(0, root, max_paths=64))

    def test_path_limit_is_bounded(self):
        program = self.program()
        root = next(program.roots(0))
        for limit in (0, 1025, True, 1.5):
            with self.assertRaises(ValueError):
                program.traces(0, root, max_paths=limit)
        self.assertLessEqual(len(program.traces(0, root, max_paths=1)), 1)


if __name__ == '__main__':
    unittest.main()
