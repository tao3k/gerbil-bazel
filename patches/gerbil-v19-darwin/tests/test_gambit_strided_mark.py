import unittest
from ctypes import c_int

from gambit_strided_mark import transform


class StridedMarkTest(unittest.TestCase):
    def test_clone_retains_original_marker_and_fallback(self):
        marker = '___HIDDEN void mark_array\n   ARGS\n#endif\n{\n___WORD *cell = start++;\n}\n'
        source = marker + '\n___HIDDEN void mark_captured_continuation\nREST\n' + '''              for (i=words-2; i>=___GCHASHTABLE_KEY0; i-=2)
                mark_array (___PSP body+i, 1); /* mark objects in key fields */
              for (i=words-1; i>=___GCHASHTABLE_VAL0; i-=2)
                mark_array (___PSP body+i, 1); /* mark objects in value fields */'''
        result, report = transform(source)
        self.assertIn(marker.rstrip(), result)
        self.assertTrue(report['originalMarkerPreserved'])
        self.assertIn('start -= 2;', result)
        self.assertIn('i = words-2;', result)
        self.assertIn('i = words-1;', result)
        self.assertIn('!defined(__clang__)', result)
        self.assertIn('!defined(ENABLE_CONSISTENCY_CHECKS)', result)
        self.assertIn('(i-___GCHASHTABLE_KEY0)/2+1', result)
        self.assertIn('(i-___GCHASHTABLE_VAL0)/2+1', result)

    def test_descending_fields_match_original_int_index_including_conversion(self):
        for words in (5, 7, 11, 69, 8197, 2**31 + 5, 2**32 + 11):
            for offset, bound in ((2, 5), (1, 6)):
                first = c_int(words - offset).value
                old = list(range(first, bound - 1, -2)) if first >= bound else []
                count = (first - bound) // 2 + 1 if first >= bound else 0
                batch = [first - 2 * index for index in range(count)]
                self.assertEqual(batch, old)

    def test_unknown_geometry_is_rejected(self):
        with self.assertRaises(ValueError):
            transform('unrelated C source')
