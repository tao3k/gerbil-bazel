import unittest

from gambit_intern_string_compare import GUARD, transform


class InternStringCompareTests(unittest.TestCase):
    def source(self):
        return '''___SCMOBJ ___find_symkey_from_scheme_string
{
          for (i=0; i<n; i++)
            if (___STRINGREF(str,___FIX(i)) != ___STRINGREF(name,___FIX(i)))
              goto next;
}
'''

    def test_guarded_original_fallback_and_byte_count(self):
        result = transform(self.source())
        self.assertIn('#if ' + GUARD, result)
        self.assertIn('___CAST(___SIZE_T,n) * ___CS', result)
        self.assertIn('#else\n          for (i=0; i<n; i++)', result)
        self.assertEqual(result.count('memcmp('), 1)

    def test_reject_repeat(self):
        with self.assertRaises(ValueError):
            transform(transform(self.source()))

    def test_reject_missing_loop(self):
        with self.assertRaises(ValueError):
            transform(self.source().replace('i<n', 'i<=n'))
