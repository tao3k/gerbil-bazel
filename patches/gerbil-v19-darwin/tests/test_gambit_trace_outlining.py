import unittest

from gambit_guarded_trace import State
from gambit_trace_outlining import outline


class TraceOutliningTests(unittest.TestCase):
    def test_terminal_target_is_exported_even_outside_live_registers(self):
        state = State(effects=1)
        state.effect_snapshot = (0, 0, state.fork())
        state.code = ['___WORD gb_t9=gb_in0;']
        state.terminal = ('GB_ORIGINAL_RET_TO', 0, 'gb_t9')
        helper, caller = outline(None, state, 0, 'defined(__APPLE__)')
        self.assertIn('out->words[0]=gb_t9;', helper)
        self.assertIn('___WORD gb_t9;', caller)
        self.assertIn('gb_t9=gb_native_result.words[0];', caller)

    def test_live_type_loop_receives_native_processor_and_frame(self):
        state = State(effects=1)
        state.effect_snapshot = (0, 0, state.fork())
        state.code = [
            'struct gb_type_chain_result result=gb_trace_type_chain(___ps,___fp,gb_in1,gb_in2);',
            'if (!result.complete) goto GB_TRACE_EFFECT_MISS;',
            '___WORD gb_t2=result.answer;',
        ]
        state.registers[1] = 'gb_t2'
        helper, caller = outline(None, state, 0, 'defined(__APPLE__)')
        self.assertIn('___processor_state ___ps', helper)
        self.assertIn('___WORD *___fp', helper)
        self.assertIn('gb_in1,gb_in2,___ps,___fp,&gb_native_result', caller)
        self.assertIn('return -1;', helper)
        self.assertIn('return 0;', helper)
        self.assertIn('gb_native_status < 0', caller)


if __name__ == '__main__':
    unittest.main()
