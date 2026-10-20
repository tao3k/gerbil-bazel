import unittest
from pathlib import Path

from gambit_parameter_entry import inject, PREAMBLE, identity_preamble


class ParameterEntryTest(unittest.TestCase):
    def test_epoch_composition_invalidates_slot_swaps_before_any_getter(self):
        candidate = identity_preamble(coherent_epoch=True)
        fence = candidate.index('if (gb_answer.slot>=2) GB_TRACE_THREAD_INVALIDATE_AT(65535);')
        self.assertLess(fence, candidate.index('___WORD gb_getter=gb_answer.getter;'))
        self.assertIn('result->slot=gb_slot;', candidate)
        self.assertNotIn('GB_TRACE_INVALIDATE_AT', identity_preamble())

    def test_environment_lookup_is_bounded_live_and_preserves_collision_order(self):
        candidate = identity_preamble(coherent_epoch=True, env_lookup=True)
        self.assertIn('gb_depth>=128', candidate)
        self.assertIn('!___EQP(gb_other,gb_param)', candidate)
        self.assertIn('gb_env=___ENV_RIGHT_FIELD(gb_env)', candidate)
        self.assertIn('gb_env=___ENV_LEFT_FIELD(gb_env)', candidate)
        self.assertIn('___GLOCELL(___G__23__23_env_2d_lookup.val)!=___PRMCELL', candidate)
        self.assertIn('result->slot=0;', candidate)
        self.assertIn('gb_slot=4;', candidate)
        self.assertNotIn('static ___WORD', candidate)

    def test_identity_return_is_opt_in_and_preserves_vm_state_and_custom_getter(self):
        candidate = identity_preamble()
        self.assertNotIn('GB_PARAMETER_IDENTITY_HIT', PREAMBLE)
        self.assertIn('gb_getter==___PRMCELL(___G__23__23_identity.prm)', candidate)
        self.assertIn('gb_getter==___PRMCELL(___G_identity.prm)', candidate)
        self.assertNotIn('gb_getter==___GLOCELL', candidate)
        self.assertIn('___SELF=gb_getter;', candidate)
        self.assertIn('___SET_NARGS(1)', candidate)
        self.assertIn('___JUMPRET(___R0)', candidate)
        self.assertIn('___JUMPGENNOTSAFE(___SET_NARGS(1),gb_getter)', candidate)
        self.assertIn('___CLO(gb_param,2)!=gb_param', candidate)

    def test_zero_argument_calls_keep_original_fallback_and_no_consumer_names(self):
        original = "___JUMPGLOSAFE(___SET_NARGS(0),3,___G_any)\n___JUMPGLONOTSAFE(___SET_NARGS(1),4,___G_other)\n"
        module = {"body": original, "path": Path("generic.c")}
        report = inject([module])
        self.assertEqual(report["parameterEntrySites"][0]["sites"], 1)
        self.assertIn("GB_PARAMETER_TRY(___GLO(3,___G_any))", module["body"])
        self.assertIn(original, module["body"])
        self.assertNotIn("GB_PARAMETER_TRY(___GLO(4", module["body"])

    def test_fastpath_checks_exact_closure_global_and_stack_then_runs_getter(self):
        self.assertIn("!defined(__clang__)", PREAMBLE)
        self.assertIn("!defined(___DYNAMIC)", PREAMBLE)
        self.assertIn("___GLOCELL(___G__23__23_dynamic_2d_ref.val)!=___PRMCELL", PREAMBLE)
        self.assertIn("___LABEL_ENTRY_GET(gb_param)!=", PREAMBLE)
        self.assertIn("___CLO(gb_param,2)!=gb_param", PREAMBLE)
        self.assertIn("(___fp-8) < ___ps->stack_trip", PREAMBLE)
        self.assertIn("___JUMPGENNOTSAFE(___SET_NARGS(1),gb_getter)", PREAMBLE)
        self.assertNotIn("static ___WORD", PREAMBLE)


if __name__ == "__main__":
    unittest.main()
