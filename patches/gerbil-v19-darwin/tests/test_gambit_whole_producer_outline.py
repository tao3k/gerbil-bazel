import unittest

from gambit_guarded_trace import Refused
from gambit_whole_producer_outline import outline


class OutlineTests(unittest.TestCase):
    def code(self):
        return '\n'.join(['if (!(gb_in1)) goto GB_TRACE_MISS;',
                          '___SET_R1(gb_in1)', '___SET_NARGS(2)',
                          'if (___fp < ___ps->stack_trip) {',
                          '___SET_STK(1,gb_in0)', '___ADJFP(1)',
                          '___ps->temp1=gb_in0;',
                          '___JUMPEXTPRM(___NOTHING,___ps->handler_stack_limit)',
                          '}', '___JUMPRET(gb_in0)'])

    def test_exports_original_return_and_poll_separately(self):
        result, facts = outline(self.code(), 'gb_whole_test', 'defined(__APPLE__)')
        self.assertEqual(facts['normalExports'], 1)
        self.assertEqual(facts['pollExports'], 1)
        self.assertIn('gb_r1=(gb_in1);', result)
        self.assertIn('gb_nargs=(2);', result)
        self.assertIn('gb_poll_resume=gb_in0;', result)
        self.assertIn('out->stack[out->stack_count].address=&___STK(1);', result)
        self.assertIn('out->stack[out->stack_count].value=(gb_in0);', result)
        self.assertNotIn('___SET_STK', result)
        self.assertIn('___ADJFP(1)', result)
        self.assertIn('out->fp=___fp; out->hp=___hp;', result)
        self.assertIn('gb_whole_miss:;\nreturn 0;', result)
        self.assertNotIn('___SET_NARGS', result)
        self.assertNotIn('___JUMP', result)
        self.assertNotIn('___ps->temp1=', result)

    def test_unknown_transfer_refused(self):
        with self.assertRaises(Refused):
            outline(self.code().replace('___ps->handler_stack_limit', '___ps->handler_heap_limit'),
                    'gb_whole_test', '1')

    def test_shared_state_write_refused(self):
        with self.assertRaises(Refused):
            outline('___ps->na=2;\n' + self.code(), 'gb_whole_test', '1')

    def test_register_outside_original_abi_refused(self):
        with self.assertRaises(Refused):
            outline(self.code().replace('___SET_R1', '___SET_R5'), 'gb_whole_test', '1')

    def test_stack_reads_without_shadow_mapping_refused(self):
        with self.assertRaises(Refused):
            outline('___WORD word=___STK(1);\n' + self.code(), 'gb_whole_test', '1')


if __name__ == '__main__':
    unittest.main()
