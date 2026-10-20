import unittest

from native_dwarf_lines import line_intervals, lookup_line
from aggregate_native_cpu_lines import matching_text_layout


HEADER = '''debug_line[0x00000000]
include_directories[  0] = "/data"
file_names[  0]:
           name: "unit.c"
      dir_index: 0
Address            Line   Column File   ISA Discriminator OpIndex Flags
'''


class NativeDwarfLinesTest(unittest.TestCase):
    def test_layout_accepts_index_renumbering_but_rejects_target_or_arch_change(self):
        left = dict(textSha256='text', canonicalRelocationSha256='targets',
                    textBytes=40, relocations=2, cpuType=1, cpuSubtype=2,
                    relocationSha256='raw-a')
        right = dict(left, relocationSha256='raw-b')
        self.assertTrue(matching_text_layout(left, right))
        for field in ('textSha256', 'canonicalRelocationSha256', 'textBytes',
                      'relocations', 'cpuType', 'cpuSubtype'):
            self.assertFalse(matching_text_layout(left, dict(right, **{field: 'changed'})))

    def test_duplicate_rows_and_sequence_end_have_exact_bounds(self):
        ranges, files = line_intervals(HEADER+'''0x10 4 1 0 0 0 0 is_stmt
0x10 5 1 0 0 0 0 is_stmt
0x18 6 1 0 0 0 0 is_stmt
0x20 6 1 0 0 0 0 end_sequence
0x30 9 1 0 0 0 0 is_stmt
0x34 9 1 0 0 0 0 end_sequence
''')
        starts = [row[0] for row in ranges]
        self.assertEqual(files[0], ('/data', 'unit.c'))
        self.assertEqual(lookup_line(ranges, starts, 0x10), (0, 5))
        self.assertEqual(lookup_line(ranges, starts, 0x1c), (0, 6))
        self.assertIsNone(lookup_line(ranges, starts, 0x20))
        self.assertIsNone(lookup_line(ranges, starts, 0x2c))

    def test_unterminated_or_backward_sequence_is_rejected(self):
        for body in ('0x10 4 1 0 0 0 0 is_stmt\n',
                     '0x10 4 1 0 0 0 0 is_stmt\n0x0c 4 1 0 0 0 0 end_sequence\n'):
            with self.assertRaises(ValueError):
                line_intervals(HEADER+body)

    def test_overlapping_sequences_and_unknown_files_are_rejected(self):
        for body in ('0x10 4 1 0 0 0 0 is_stmt\n0x20 4 1 0 0 0 0 end_sequence\n'
                     '0x18 5 1 0 0 0 0 is_stmt\n0x24 5 1 0 0 0 0 end_sequence\n',
                     '0x10 4 1 2 0 0 0 is_stmt\n0x20 4 1 2 0 0 0 end_sequence\n'):
            with self.assertRaises(ValueError):
                line_intervals(HEADER+body)

    def test_multiple_line_tables_are_not_implicitly_merged(self):
        with self.assertRaises(ValueError):
            line_intervals(HEADER+HEADER)


if __name__ == '__main__':
    unittest.main()
