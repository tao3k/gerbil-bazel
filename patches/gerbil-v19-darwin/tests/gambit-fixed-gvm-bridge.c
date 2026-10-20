#include "gambit.h"
#include "gambit-fixed-gvm-state.h"
#include <stdint.h>

struct gb_fixed_slot gb_fixed_hosts[4096];
void gb_fixed_register(___host normal, gb_fixed_host fast) {
  struct gb_fixed_slot *slot = &gb_fixed_hosts[((uintptr_t)normal >> 8) & 4095];
  if (!slot->normal || slot->normal == normal) {
    slot->normal = normal;
    slot->fast = fast;
  }
}

void __attribute__((used)) gb_fixed_start(___processor_state ___ps, gb_fixed_host fast) {
  gb_fixed_pc = ___ps->pc;
  ___fp = ___PSFP;
  ___r0 = ___PSR0; ___r1 = ___PSR1; ___r2 = ___PSR2;
  ___r3 = ___PSR3; ___r4 = ___PSR4;
  ___TAIL_CALL_VOID(fast(___ps));
}

/* One native frame persists across private tail calls, then is popped on exit. */
__asm__(
".text\n.p2align 4\n.globl _gb_fixed_enter\n_gb_fixed_enter:\n"
"sub sp, sp, #96\n"
"stp x19, x20, [sp, #0]\n"
"stp x21, x22, [sp, #16]\n"
"stp x23, x24, [sp, #32]\n"
"stp x25, x26, [sp, #48]\n"
"stp x27, x28, [sp, #64]\n"
"stp x29, x30, [sp, #80]\n"
"bl _gb_fixed_start\n"
"ldp x19, x20, [sp, #0]\n"
"ldp x21, x22, [sp, #16]\n"
"ldp x23, x24, [sp, #32]\n"
"ldp x25, x26, [sp, #48]\n"
"ldp x27, x28, [sp, #64]\n"
"ldp x29, x30, [sp, #80]\n"
"add sp, sp, #96\nret\n"
".p2align 4\n.globl _gb_fixed_leave\n_gb_fixed_leave:\n"
"ldp x19, x20, [sp, #0]\n"
"ldp x21, x22, [sp, #16]\n"
"ldp x23, x24, [sp, #32]\n"
"ldp x25, x26, [sp, #48]\n"
"ldp x27, x28, [sp, #64]\n"
"ldp x29, x30, [sp, #80]\n"
"add sp, sp, #96\nbr x1\n"
);
