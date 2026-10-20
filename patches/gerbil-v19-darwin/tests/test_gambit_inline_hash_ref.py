import unittest

from gambit_inline_hash_ref import inject_live_hash_ref, INLINE_REF

GUARD = ('#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && '
    'defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS)\n')
BLOCK = ('struct gb_trace_native_11_result { ___WORD words[8]; };\n'
    'value = ___GCHASHTABLEREF(gb_t32,gb_in2);\n#endif\n')


class InlineHashRefTest(unittest.TestCase):
    def test_replaces_only_selected_call_inside_original_guard(self):
        code = GUARD + BLOCK + 'other = ___GCHASHTABLEREF(ht,key);\n'
        result = inject_live_hash_ref(code)
        self.assertTrue(result.startswith(GUARD + INLINE_REF))
        self.assertIn('value = gb_live_hash_ref(gb_t32,gb_in2);', result)
        self.assertTrue(result.endswith('other = ___GCHASHTABLEREF(ht,key);\n'))

    def test_rejects_unguarded_or_non_darwin_input(self):
        for guard in ('', GUARD.replace('defined(__APPLE__)', 'defined(__linux__)')):
            with self.assertRaises(ValueError):
                inject_live_hash_ref(guard + BLOCK)

    def test_rejects_duplicate_injection(self):
        with self.assertRaises(ValueError):
            inject_live_hash_ref(inject_live_hash_ref(GUARD + BLOCK))

    def test_preserves_moving_key_fallback_and_live_reads(self):
        self.assertIn('___GCHASHTABLE_FLAG_KEY_MOVED', INLINE_REF)
        self.assertIn('return ___GCHASHTABLEREF(ht,key);', INLINE_REF)
        self.assertIn('___GCHASHTABLE_HASH_STEP(probe2, step2, key, size2 >> 1);', INLINE_REF)
        self.assertNotIn('static ___SCMOBJ', INLINE_REF)


if __name__ == '__main__':
    unittest.main()
