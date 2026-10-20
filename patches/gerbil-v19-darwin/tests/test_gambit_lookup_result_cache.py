import unittest

from gambit_lookup_result_cache import CACHE, WRITES, inject, write_hooks


class LookupCacheTests(unittest.TestCase):
    def header(self):
        return '\n'.join('#define ___'+name+'(x,y,z) original_'+name+'(x,y,z);'
                         for name in WRITES)

    def test_all_known_writes_preserve_expression_before_marker(self):
        hooks = write_hooks(self.header())
        for name in WRITES:
            line = next(line for line in hooks.splitlines()
                        if line.startswith('#define ___'+name+'('))
            self.assertEqual(line.count('original_'+name+'(x,y,z)'), 1)
            self.assertLess(line.index('original_'), line.index('GB_LOOKUP_RESET'))

    def test_missing_or_duplicate_original_shape_refused(self):
        with self.assertRaises(ValueError):
            write_hooks('')
        with self.assertRaises(ValueError):
            write_hooks(self.header()+'\n#define ___STORE_WORD(x,y,z) changed(x,y,z)')

    def test_lazy_rehash_precedes_result_reuse(self):
        self.assertLess(CACHE.index('___GCHASHTABLE_FLAG_KEY_MOVED'),
                        CACHE.index('slot->epoch==gb_lookup_generation'))
        self.assertIn('gb_lookup_dirty=1;\n    GB_LOOKUP_EVENT(site,2);\n'
                      '    return ___GCHASHTABLEREF(table,key);', CACHE)

    def test_opaque_foreign_body_refused(self):
        with self.assertRaisesRegex(ValueError, 'opaque foreign'):
            inject('___BEGIN_M_COD\n___BEGIN_CFUN\n___END_M_COD', self.header())

    def test_reinjection_refused(self):
        with self.assertRaisesRegex(ValueError, 'already injected'):
            inject('gb_lookup_cached', self.header())


if __name__ == '__main__':
    unittest.main()
