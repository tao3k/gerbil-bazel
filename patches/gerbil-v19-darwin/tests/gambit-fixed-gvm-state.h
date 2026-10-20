#if !defined(__APPLE__) || !defined(__aarch64__) || !defined(__GNUC__) || \
    defined(__clang__) || !defined(___SINGLE_THREADED_VMS) || \
    !defined(___SINGLE_VM) || !defined(___SINGLE_HOST) || \
    !defined(___USE_LABEL_VALUES) || \
    !defined(___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST) || \
    ___NB_GVM_REGS != 5 || ___MAX_PROCESSORS != 1
#error "fixed GVM state requires the isolated Darwin GNU ARM64 profile"
#endif

/* Only private GVM hosts assign these; public entry/exit saves the native ABI. */
register ___WORD gb_fixed_pc __asm__("x20");
register ___WORD *___fp __asm__("x21");
register ___WORD ___r0 __asm__("x22");
register ___WORD ___r1 __asm__("x23");
register ___WORD ___r2 __asm__("x24");
register ___WORD ___r3 __asm__("x25");
register ___WORD ___r4 __asm__("x26");

typedef void (*gb_fixed_host)(___processor_state);
struct gb_fixed_slot { ___host normal; gb_fixed_host fast; };
extern struct gb_fixed_slot gb_fixed_hosts[4096];
extern void gb_fixed_register(___host, gb_fixed_host);
extern void gb_fixed_enter(___processor_state, gb_fixed_host);
extern void gb_fixed_leave(___processor_state, ___host);
