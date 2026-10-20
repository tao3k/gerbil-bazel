import unittest
from gambit_micro_clones import inject
from test_gambit_known_returns import procedure


BODY = """___DEF_SLBL(0,___L0_caller)
   ___SET_R0(___LBL(2))
   ___ADJFP(1)
   ___GOTO(___L_test)
___DEF_GLBL(___L_test)
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
   ___ADJFP(-1)
   ___JUMPRET(___R0)
"""


class MicroClonesTest(unittest.TestCase):
    def test_deferred_frame_materializes_before_original_cold_continuation(self):
        body = BODY.replace("   ___SET_R0(___LBL(2))", "   ___SET_STK(1,___R0)\n   ___SET_STK(2,___R1)\n"
                            "   ___SET_R1(___STRUCTURETYPE(___R1))\n   ___SET_R0(___LBL(2))")
        body = body.replace("___ADJFP(1)", "___ADJFP(8)")
        body = body.replace("___DEF_SLBL(2,___L2_caller)\n", "___DEF_SLBL(2,___L2_caller)\n"
                            "   ___IF(___NOTFALSEP(___R1))\n   ___GOTO(___L_hot)\n   ___END_IF\n"
                            "   ___SET_R1(___STK(-6))\n   ___SET_R0(___STK(-7))\n"
                            "   ___ADJFP(-8)\n   ___POLL(2)\n   ___JUMPRET(___R0)\n"
                            "___DEF_GLBL(___L_hot)\n   ___SET_R1(___STK(-6))\n")
        body = body.replace("___STK(1)", "___STK(-7)").replace("___ADJFP(-1)", "___ADJFP(-8)")
        text, report = inject(procedure(21, body), 0, defer_frames=True)
        self.assertEqual(report["deferredFrames"], 1)
        self.assertIn("&& (___MAX_PROCESSORS == 1)", text)
        self.assertIn("gb_saved_0_0=___R1;", text)
        self.assertIn("___SET_STK(1,___R0)\n___SET_STK(2,gb_saved_0_0)\n"
                      "___SET_R0(___LBL(2))\n___ADJFP(8)\n___GOTO(___L2_caller)", text)
        _, refused = inject(procedure(21, body.replace("___SET_R1(___TRU)", "___POLL(2)")), 0, defer_frames=True)
        self.assertEqual(refused["deferredFrames"], 0)

    def test_native_only_returns_preserve_original_frames_and_fallback(self):
        text, report = inject(procedure(21, BODY), 7)
        self.assertEqual(report["callsiteCopies"], 1)
        self.assertEqual(report["directReturns"], 2)
        self.assertEqual(text.count("___JUMPRET(___R0)"), 3)
        self.assertEqual(text.count("___GOTO(___L2_caller)"), 2)
        self.assertEqual(text.count("___SET_R0(___LBL(2))"), 1)
        self.assertEqual(text.count("___ADJFP(1)"), 1)
        self.assertEqual(text.count("___ADJFP(-1)"), 1)
        self.assertIn("#else\n___GOTO(___L_test)", text)
        self.assertIn("gb_micro_7_0_", text)

    def test_poll_frame_root_and_opaque_effects_are_not_specialized(self):
        for effect in ("___POLL(1)", "___ADJFP(1)", "___SET_R0(___FAL)",
                       "___SET_R1(___R0)", "___CHECK_HEAP(1)", "___SET_STK(1,___R1)"):
            with self.subTest(effect=effect):
                source = procedure(21, BODY.replace("___SET_R1(___TRU)", effect))
                text, report = inject(source, 0)
                self.assertEqual(report["callsiteCopies"], 0)
                self.assertEqual(text, source)

    def test_fallthrough_and_backedge_are_explicit_in_copy(self):
        body = BODY.replace("   ___SET_R1(___TRU)\n   ___JUMPRET(___R0)",
                            "___DEF_GLBL(___L_loop)\n   ___SET_R1(___TYPESUPER(___R1))\n"
                            "   ___IF(___NOTFALSEP(___R1))\n   ___GOTO(___L_test)\n   ___END_IF")
        text, report = inject(procedure(21, body), 1)
        self.assertEqual(report["callsiteCopies"], 1)
        self.assertEqual(report["directReturns"], 1)
        copy = text[text.index("gb_micro_1_0_1:"):]
        self.assertNotIn("___GOTO(___L_test)", copy)
        self.assertIn("___GOTO(gb_micro_1_0_", copy)


if __name__ == "__main__":
    unittest.main()
