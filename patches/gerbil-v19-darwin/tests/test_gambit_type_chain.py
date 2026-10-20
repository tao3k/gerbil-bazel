import unittest

from gambit_guarded_trace import Program, State
from gambit_type_chain import lower, PREAMBLE
from test_gambit_guarded_trace import module, procedure


BODY = '''___DEF_SLBL(0,___L0_entry)
___GOTO(___L_test)
___DEF_GLBL(___L_next)
___SET_R1(___TYPESUPER(___R1))
___IF(___NOT(___NOTFALSEP(___R1)))
___GOTO(___L_false)
___END_IF
___POLL(1)
___DEF_SLBL(1,___L1_poll)
___DEF_GLBL(___L_test)
___SET_R2(___TYPEID(___R1))
___IF(___NOT(___EQP(___R2,___R3)))
___GOTO(___L_next)
___END_IF
___SET_R1(___TRU)
___JUMPRET(___R0)
___DEF_GLBL(___L_false)
___SET_R1(___FAL)
___JUMPRET(___R0)
'''


def model(body=BODY):
    program = Program([module(0, procedure(0, body), ['___DEF_LBL_PROC(___host,1,-1)'])])
    return program, program.labels[0]['___L_test']


class TypeChainTests(unittest.TestCase):
    def test_exact_loop_exports_boolean_and_actual_last_id(self):
        program, point = model()
        state = State(effects=1, guard_limit=24)
        self.assertEqual(lower(program, 0, point, state), point + 5)
        self.assertEqual(state.type_chain_loops, 1)
        self.assertIn('.answer', '\n'.join(state.code))
        self.assertIn('.last_id', '\n'.join(state.code))
        self.assertIn('GB_TRACE_EFFECT_MISS', '\n'.join(state.code))
        self.assertEqual(state.frame, 0)
        self.assertEqual(state.polls, 1)
        self.assertEqual(state.fork().type_chain_loops, 1)

    def test_unknown_effect_changed_return_or_mutating_target_is_refused(self):
        for body in (BODY.replace('___POLL(1)', '___VECTORSET(___R4,___FIX(0),___R1)'),
                     BODY.replace('___SET_R1(___FAL)', '___SET_R1(___TRU)'),
                     BODY.replace('___EQP(___R2,___R3)', '___EQP(___R2,___R1)')):
            program, point = model(body)
            state = State(effects=1, guard_limit=24)
            self.assertIsNone(lower(program, 0, point, state))
            self.assertFalse(state.code)

    def test_helper_bounds_live_reads_and_original_poll_failure(self):
        self.assertIn('depth<128', PREAMBLE)
        self.assertIn('result.last_id=___TYPEID(type)', PREAMBLE)
        self.assertIn('type=___TYPESUPER(type)', PREAMBLE)
        self.assertIn('___fp<___ps->stack_trip', PREAMBLE)
        self.assertIn('GB_TRACE_POLL_EVENT()', PREAMBLE)
        self.assertNotIn('cache', PREAMBLE)

    def test_seventh_poll_is_bounded_and_preserved(self):
        program, point = model()
        state = State(effects=1, guard_limit=24, polls=6)
        self.assertIsNotNone(lower(program, 0, point, state))
        self.assertEqual(state.polls, 7)
        refused = State(effects=1, guard_limit=24, polls=7)
        self.assertIsNone(lower(program, 0, point, refused))
        self.assertFalse(refused.code)


if __name__ == '__main__':
    unittest.main()
