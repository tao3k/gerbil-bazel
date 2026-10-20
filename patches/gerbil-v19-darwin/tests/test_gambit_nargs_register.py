import unittest

from gambit_nargs_register import inject_nargs_register, nargs_macro_definitions, NAMES

HEADER = ''.join('#define '+name+'(n,code) ___ps->na=n;\n' for name in NAMES)
CODE = ('#undef ___MH_PROC\n#define ___MH_PROC gb_coalesced_host\n'
    '#define ___MD_ALL ___D_HEAP\n#define ___MR_ALL ___R_HEAP\n'
    '#define ___MW_ALL ___W_HEAP\n___BEGIN_M_COD\n'
    + 'int read = ___ps->na;\n' * 14 + '___END_M_COD\n')


class NargsRegisterTest(unittest.TestCase):
    def test_preserves_state_boundaries_and_non_darwin_fallback(self):
        code, detail = inject_nargs_register(CODE, HEADER)
        self.assertEqual(detail['stateProtocolDefinitions'], {'D': 1, 'R': 1, 'W': 1})
        self.assertEqual(detail['callerReads'], 14)
        self.assertIn('#define GB_NARGS_R gb_nargs=___ps->na;', code)
        self.assertIn('#define GB_NARGS_W ___ps->na=gb_nargs;', code)
        self.assertIn('#define GB_NARGS_CURRENT ___ps->na', code)
        self.assertIn('defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)', code)
        self.assertEqual(code.count('int read = GB_NARGS_CURRENT;'), 14)

    def test_preserves_multiline_macro_body(self):
        header = HEADER.replace('#define ___GET_REST(n,code) ___ps->na=n;\n',
            '#define ___GET_REST(n,code) \\\n+if (___ps->na>=0) { code; }\n')
        result = nargs_macro_definitions(header)
        self.assertIn('if (gb_nargs>=0) { code; }', result)

    def test_rejects_changed_state_access_or_duplicate_macro(self):
        for header in (HEADER.replace('___ps->na', 'other', 1), HEADER+HEADER):
            with self.assertRaises(ValueError):
                nargs_macro_definitions(header)

    def test_rejects_duplicate_injection_and_raw_write(self):
        result, _ = inject_nargs_register(CODE, HEADER)
        with self.assertRaises(ValueError):
            inject_nargs_register(result, HEADER)
        with self.assertRaises(ValueError):
            inject_nargs_register(CODE.replace('int read = ___ps->na;', '___ps->na=1;', 1), HEADER)


if __name__ == '__main__':
    unittest.main()
