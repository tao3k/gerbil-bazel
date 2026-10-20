#include "gambit-fixed-gvm-state.h"
#include <stdint.h>

static void gb_fixed_entry(___processor_state);
___HIDDEN void __attribute__((aligned(256))) ___HOST_PROC(___processor_state);
static void __attribute__((constructor)) gb_fixed_register_module(void) {
  gb_fixed_register(___HOST_PROC, gb_fixed_entry);
}

#undef ___D_FP
#undef ___D_R0
#undef ___D_R1
#undef ___D_R2
#undef ___D_R3
#undef ___D_R4
#define ___D_FP
#define ___D_R0
#define ___D_R1
#define ___D_R2
#define ___D_R3
#define ___D_R4

/* Preserve builtin result type and overflow writes without taking a GPR address. */
#define GB_FIXED_OVERFLOW(op,var,x,y) __extension__ ({ \
  __typeof__(var) gb_result; \
  int gb_overflow = op((x),(y),&gb_result); \
  (var) = gb_result; \
  ___EXPECT_FALSE(gb_overflow); \
})
#undef ___FIXADDP_OVERFLOWS
#undef ___FIXMULP_OVERFLOWS
#undef ___FIXSUBP_OVERFLOWS
#define ___FIXADDP_OVERFLOWS(var,x,y) \
  GB_FIXED_OVERFLOW(__builtin_add_overflow,var,___FW(x),___FW(y))
#define ___FIXMULP_OVERFLOWS(var,x,y) \
  GB_FIXED_OVERFLOW(__builtin_mul_overflow,var,___FW(x),___FW(___INT(y)))
#define ___FIXSUBP_OVERFLOWS(var,x,y) \
  GB_FIXED_OVERFLOW(__builtin_sub_overflow,var,___FW(x),___FW(y))

#undef ___BEGIN_COD
#define ___BEGIN_COD \
___HIDDEN void __attribute__((aligned(256))) ___HOST_PROC(___processor_state ___ps) { \
  ___TAIL_CALL_VOID(gb_fixed_enter(___ps, gb_fixed_entry)); \
} \
static void ___GNUC_HOST_FUNCTION_ATTRIBUTES gb_fixed_entry(___processor_state ___ps) { \
  { ___WORD ___start, ___temp; \
  ___S32 ___s32_temp; ___U32 ___u32_temp; \
  ___S64 ___s64_temp; ___U64 ___u64_temp; \
  ___D_ALL

#define ___pc gb_fixed_pc
#undef ___END_HLBL
#define ___END_HLBL \
0}; \
___R_HEAP \
___start = ___MLBL(___HOST_LBL0); \
if (___EXPECT_FALSE(___pc == ___FIX(0))) { \
  ___ps->pc = ___CAST(___WORD, ___hlbltbl); \
  return; \
}

#undef ___END_COD
#define ___END_COD \
{ \
  ___host gb_host = ___LABEL_HOST_GET(___pc); \
  struct gb_fixed_slot *gb_slot = &gb_fixed_hosts[((uintptr_t)gb_host >> 8) & 4095]; \
  ___ps->pc = ___pc; \
  if (gb_slot->normal == gb_host && gb_slot->fast) { \
    ___W_HEAP \
    ___TAIL_CALL_VOID(gb_slot->fast(___ps)); \
  } \
  ___W_ALL \
  ___TAIL_CALL_VOID(gb_fixed_leave(___ps, gb_host)); \
} \
} \
}
