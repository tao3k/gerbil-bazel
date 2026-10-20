import unittest

from gambit_binding_facts import PAIR, mutation_hooks

HEADER = ('#define ___SET_GLO(i,glo,x)___GLO(i,glo)=x;\n'
    '#define ___GLOBALVARSET(gv,x)___GLOCELL(___GLOBALVARSTRUCT(gv)->val)=x;\n'
    '#define ___GLOBALVARPRIMSET(gv,x)___PRMCELL(___GLOBALVARSTRUCT(gv)->prm)=x;\n')


class BindingFactsTest(unittest.TestCase):
    def test_only_matches_direct_procedure_address_guard(self):
        code = ('___WORD gb_t0=(GB_TRACE_GLO(gb_m3___glotbl,92,___G_class_2d_of));\n'
            'if (!(gb_t0==(gb_m2___lp+(4106*___LABEL_SIZE*___WS)))) goto gb_trace_miss_0;')
        self.assertEqual(len(PAIR.findall(code)), 1)
        self.assertFalse(PAIR.search(code.replace('GB_TRACE_GLO(gb_m3___glotbl,92,___G_class_2d_of)',
            '___UNCHECKEDSTRUCTUREREF(obj,___FIX(1),___FAL,___FAL)')))
        self.assertFalse(PAIR.search(code.replace('gb_m2___lp+(4106*___LABEL_SIZE*___WS)',
            '___TYPEID(type)')))

    def test_all_three_writes_invalidate_after_original_assignment(self):
        code = mutation_hooks(HEADER)
        self.assertEqual(code.count('gb_binding_mask=0;'), 3)
        self.assertIn('___GLO(i,glo)=x; gb_binding_mask=0;', code)
        self.assertIn('___GLOCELL(___GLOBALVARSTRUCT(gv)->val)=x; gb_binding_mask=0;', code)
        self.assertIn('___PRMCELL(___GLOBALVARSTRUCT(gv)->prm)=x; gb_binding_mask=0;', code)
        self.assertEqual(code.count('do {'), 3)

    def test_mutation_shape_drift_is_rejected(self):
        for header in (HEADER.replace('#define ___SET_GLO', '#define missing', 1), HEADER+HEADER):
            with self.assertRaises(ValueError):
                mutation_hooks(header)


if __name__ == '__main__':
    unittest.main()
