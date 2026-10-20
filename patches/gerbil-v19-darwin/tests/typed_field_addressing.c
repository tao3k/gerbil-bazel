#include "gambit.h"
#include <stdio.h>

#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || ___WS != 8
#error "field addressing audit requires Darwin GNU 64-bit profile"
#endif

___SCMOBJ gb_pair_car(___SCMOBJ object) { return ___CAR(object); }
___SCMOBJ gb_pair_cdr(___SCMOBJ object) { return ___CDR(object); }
___SCMOBJ gb_vector_first(___SCMOBJ object) { return ___VECTORREF(object, ___FIX(0)); }
___SCMOBJ gb_structure_first(___SCMOBJ object) {
  return ___UNCHECKEDSTRUCTUREREF(object, ___FIX(0), ___FAL, ___FAL);
}
___SCMOBJ gb_generic_first(___SCMOBJ object) { return ___BODY0(object)[0]; }

int main(void) {
  ___WORD pair[3] = {___MAKE_HD_WORDS(2, ___sPAIR), ___FIX(17), ___FIX(29)};
  ___WORD vector[3] = {___MAKE_HD_WORDS(2, ___sVECTOR), ___FIX(31), ___FIX(43)};
  ___WORD structure[3] = {___MAKE_HD_WORDS(2, ___sSTRUCTURE), ___FIX(47), ___FIX(59)};
  ___SCMOBJ p = ___PAIR_FROM_BODY(pair + 1);
  ___SCMOBJ v = ___VECTOR_FROM_BODY(vector + 1, 0);
  ___SCMOBJ s = ___SUBTYPED_FROM_BODY(structure + 1);
  if (gb_pair_car(p) != ___FIX(17) || gb_pair_cdr(p) != ___FIX(29) ||
      gb_vector_first(v) != ___FIX(31) || gb_structure_first(s) != ___FIX(47) ||
      gb_generic_first(p) != ___FIX(17) || gb_generic_first(v) != ___FIX(31))
    return 1;
  puts("FIELD-ADDRESSING-OK 6");
  return 0;
}
