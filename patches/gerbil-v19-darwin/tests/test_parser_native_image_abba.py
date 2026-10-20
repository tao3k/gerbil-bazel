import unittest

from run_parser_native_image_abba import validate_batch


class NativeBatchReceiptTest(unittest.TestCase):
    def valid(self):
        return '\n'.join(['CASE-OK real-case']*5 + ['HARNESS-RETURN status=0', 'FINAL-GC-OK',
                                                   'NATIVE-SUITE-OK modules=1', 'OK'])+'\n'

    def test_actual_cases_gc_and_final_exit_are_all_required(self):
        content = self.valid()
        self.assertEqual(validate_batch(content), 5)
        for marker in ('CASE-OK real-case\n', 'HARNESS-RETURN status=0\n', 'FINAL-GC-OK\n',
                       'NATIVE-SUITE-OK modules=1\n', 'OK\n'):
            with self.assertRaises(RuntimeError):
                validate_batch(content.replace(marker, '', 1))

    def test_errors_or_extra_cases_do_not_pass(self):
        for content in ('ERROR real failure\n'+self.valid(), '*** ERROR failure\n'+self.valid(),
                        'CASE-OK extra\n'+self.valid()):
            with self.assertRaises(RuntimeError):
                validate_batch(content)


if __name__ == '__main__':
    unittest.main()
