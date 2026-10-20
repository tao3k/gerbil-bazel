import unittest

from prepare_gc_mark_probe import PREAMBLE, array_census, inject


class GcMarkProbeTest(unittest.TestCase):
    def source(self):
        return '''#ifdef ENABLE_CONSISTENCY_CHECKS

#define mark_array(start,n) ORIGINAL
___HIDDEN void mark_array
ARGS
{
  ___WORD *limit = alloc_heap_limit;
        ___WORD obj = *cell;
            head_typ = ___HD_TYP(head);
                ___SIZE_TS words = ___HD_WORDS(head);
  ORIGINAL_COPY_AND_FORWARD;
}


___HIDDEN void mark_captured_continuation
UNCHANGED
'''

    def test_only_adds_hooks_to_original_algorithm(self):
        source = self.source()
        changed = inject(source)
        without_hooks = changed.replace(PREAMBLE + '\n', '', 1)
        for hook in ('\n  GB_GC_CALL(n);', '\n        GB_GC_VISIT();',
                     '\n            GB_GC_HEAD(head_typ);',
                     '\n                GB_GC_COPY(subtype,words);'):
            self.assertEqual(without_hooks.count(hook), 1)
            without_hooks = without_hooks.replace(hook, '', 1)
        self.assertEqual(source, without_hooks)

    def test_platform_guard_and_no_scheme_roots(self):
        self.assertIn('defined(__APPLE__)', PREAMBLE)
        self.assertIn('!defined(__clang__)', PREAMBLE)
        self.assertIn('(___WS == 8)', PREAMBLE)
        self.assertIn('unsigned long gb_gc_heads[8]', PREAMBLE)
        self.assertIn('GAMBIT_GC_MARK_PROBE_FILE', PREAMBLE)
        self.assertNotIn('___WORD', PREAMBLE)

    def test_rejects_unknown_or_already_instrumented_marker(self):
        with self.assertRaises(ValueError):
            inject('unknown')
        with self.assertRaises(ValueError):
            inject(self.source().replace('___WORD obj = *cell;', 'different;'))

    def test_array_census_is_separate_from_tail_visits(self):
        self.assertIn('long gb_signed_n=(n);', PREAMBLE)
        self.assertIn('gb_signed_n>0 ? (unsigned long)gb_signed_n : 0', PREAMBLE)
        self.assertIn('gb_n>4 ? gb_n-4 : 0', PREAMBLE)
        self.assertIn('arrayLengthBucketCalls', PREAMBLE)
        self.assertIn('arrayLengthBucketCells', PREAMBLE)
        changed = inject(self.source())
        self.assertEqual(changed.count('GB_GC_CALL(n);'), 1)
        self.assertEqual(changed.count('GB_GC_VISIT();'), 1)

    def census(self):
        return dict(calls=8, singleCalls=1, visits=185,
                    arrayLengthBucketCalls=[1] * 8,
                    arrayLengthBucketCells=[0, 1, 2, 3, 8, 9, 33, 129],
                    fourAheadSlots=163, negativeLengthCalls=1)

    def test_complete_census_and_empty_negative_scan(self):
        result = array_census(self.census())
        self.assertEqual(result['arrayCells'], 185)
        self.assertEqual(result['fourAheadSlots'], 163)
        self.assertFalse(result['performanceQualified'])

    def test_rejects_rollover_and_inconsistent_census(self):
        for key, value in (('arrayLengthBucketCells', [0, 1, 2, 3, 8, 9, 33, 9]),
                           ('arrayLengthBucketCalls', [True] * 8),
                           ('fourAheadSlots', 164), ('negativeLengthCalls', 2),
                           ('visits', 184), ('calls', 9)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                array_census(dict(self.census(), **{key: value}))


if __name__ == '__main__':
    unittest.main()
