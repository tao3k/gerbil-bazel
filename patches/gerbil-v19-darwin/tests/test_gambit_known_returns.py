import unittest
from gambit_known_returns import inject


def procedure(base, body):
    return f"#define ___PH_LBL0 {base}\n___BEGIN_P_SW\n{body}___END_P_SW\n"


class KnownReturnsTest(unittest.TestCase):
    def test_local_boolean_subroutine_has_no_return_fallthrough(self):
        source = procedure(21, """___DEF_SLBL(0,___L0_caller)
   ___SET_R0(___LBL(2))
   ___ADJFP(1)
   ___GOTO(___L_predicate)
___DEF_GLBL(___L_predicate)
   ___IF(___NOT(___STRUCTUREP(___R1)))
   ___GOTO(___L_false)
   ___END_IF
   ___SET_R1(___TRU)
   ___JUMPRET(___R0)
___DEF_GLBL(___L_false)
   ___SET_R1(___FAL)
   ___JUMPRET(___R0)
___DEF_SLBL(2,___L2_caller)
   ___SET_R0(___STK(1))
   ___JUMPRET(___R0)
""")
        rewritten, report = inject(source)
        self.assertEqual(report["microReturnSites"], 2)
        self.assertEqual(report["returnSites"], 2)
        self.assertEqual(rewritten.count("___R0==___MLBL(23)"), 2)
        self.assertEqual(rewritten.count("___JUMPRET(___R0)"), 3)
        _, blocked = inject(source.replace("___SET_R1(___TRU)", "___SET_R0(___FAL)"))
        self.assertEqual(blocked["microReturnSites"], 0)

    def test_internal_caller_uses_caller_descriptor_base(self):
        caller = procedure(21, """___DEF_SLBL(0,___L0_caller)
   ___SET_R0(___LBL(2))
   ___JUMPINT(___SET_NARGS(1),___PRC(40),___L_callee)
___DEF_SLBL(2,___L2_caller)
   ___JUMPRET(___R0)
""")
        callee = procedure(40, """___DEF_SLBL(0,___L0_callee)
___DEF_GLBL(___L_callee)
   ___SET_R1(___TRU)
   ___JUMPRET(___R0)
""")
        rewritten, report = inject(caller + callee)
        self.assertEqual(report["returnSites"], 1)
        self.assertIn("___R0==___MLBL(23)", rewritten)
        self.assertNotIn("___R0==___MLBL(42)", rewritten)
        self.assertEqual(rewritten.count("___JUMPRET(___R0)"), 2)
        self.assertIn("#if defined(__APPLE__)", rewritten)


if __name__ == "__main__":
    unittest.main()
