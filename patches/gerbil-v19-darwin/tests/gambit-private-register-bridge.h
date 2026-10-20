/* Isolated single-processor probe; public host/label/VM layouts are unchanged. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || \
    !defined(___SINGLE_HOST) || !defined(___USE_LABEL_VALUES) || \
    !defined(___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST) || \
    ___NB_GVM_REGS != 5 || ___MAX_PROCESSORS != 1
#error "private bridge requires the qualified Darwin/GNU single-processor profile"
#endif

#include <stdint.h>
typedef void (*gambit_private_host)(___processor_state, ___WORD, ___WORD *,
                                    ___WORD, ___WORD, ___WORD, ___WORD, ___WORD);
struct gambit_private_slot {
  ___host normal;
  gambit_private_host fast;
};
extern struct gambit_private_slot gambit_private_hosts[4096];
extern void gambit_private_register(___host, gambit_private_host);
#ifdef GB_BRIDGE_EDGE_PROBE
extern unsigned long long gambit_private_edges[16][16];
extern unsigned gambit_private_ids[4096];
extern void gambit_private_name(___host, const char *);
static unsigned gambit_private_id;
static inline __attribute__((always_inline)) void gambit_private_trace(___host host) {
  unsigned index = ((uintptr_t)host >> 8) & 4095;
  unsigned target = gambit_private_hosts[index].normal == host ? gambit_private_ids[index] : 0;
  ++gambit_private_edges[gambit_private_id][target];
}
#endif

static inline gambit_private_host gambit_private_lookup(___host host) {
  struct gambit_private_slot *slot =
    &gambit_private_hosts[((uintptr_t)host >> 8) & 4095];
  return slot->normal == host ? slot->fast : 0;
}

#ifdef GB_BRIDGE_HOT_EDGES
#define GB_JOIN_INNER(a,b) a##b
#define GB_JOIN(a,b) GB_JOIN_INNER(a,b)
#define gambit_private_entry GB_JOIN(___HOST_PROC,_private_entry)
#define GB_PRIVATE_STORAGE __attribute__((visibility("hidden")))
#define GB_DECLARE_PEER(peer) \
extern ___host const GB_JOIN(peer,_public_host); \
extern void GB_JOIN(peer,_private_entry)(___processor_state, ___WORD, ___WORD *, \
                                       ___WORD, ___WORD, ___WORD, ___WORD, ___WORD);
#ifdef GB_BRIDGE_HOT1
GB_DECLARE_PEER(GB_BRIDGE_HOT1)
#endif
#ifdef GB_BRIDGE_HOT2
GB_DECLARE_PEER(GB_BRIDGE_HOT2)
#endif
#else
#define GB_PRIVATE_STORAGE static
#endif
GB_PRIVATE_STORAGE void gambit_private_entry(___processor_state, ___WORD, ___WORD *,
                                 ___WORD, ___WORD, ___WORD, ___WORD, ___WORD);
___HIDDEN void __attribute__((aligned(256))) ___HOST_PROC(___processor_state);
#ifdef GB_BRIDGE_HOT_EDGES
GB_PRIVATE_STORAGE ___host const GB_JOIN(___HOST_PROC,_public_host) = ___HOST_PROC;
#endif
static void __attribute__((constructor)) gambit_private_register_module(void) {
  gambit_private_register(___HOST_PROC, gambit_private_entry);
#ifdef GB_BRIDGE_EDGE_PROBE
  gambit_private_name(___HOST_PROC, ___MODULE_NAME);
  gambit_private_id = gambit_private_ids[((uintptr_t)___HOST_PROC >> 8) & 4095];
#endif
}

#undef ___BEGIN_COD
#define ___BEGIN_COD \
___HIDDEN void __attribute__((aligned(256))) ___HOST_PROC (___processor_state ___ps) { \
  ___TAIL_CALL_VOID(gambit_private_entry(___ps, ___ps->pc, ___PSFP, \
                                       ___PSR0, ___PSR1, ___PSR2, ___PSR3, ___PSR4)); \
} \
GB_PRIVATE_STORAGE void ___GNUC_HOST_FUNCTION_ATTRIBUTES gambit_private_entry \
  (___processor_state ___ps, ___WORD bridge_pc, ___WORD *bridge_fp, \
   ___WORD bridge_r0, ___WORD bridge_r1, ___WORD bridge_r2, \
   ___WORD bridge_r3, ___WORD bridge_r4) { \
___WORD ___pc; { ___WORD ___start, ___temp; \
___S32 ___s32_temp; ___U32 ___u32_temp; \
___S64 ___s64_temp; ___U64 ___u64_temp; \
___D_ALL

/* Only the initial entry uses parameters. GC/FFI R_ALL still reloads the VM. */
#undef ___END_HLBL
#define ___END_HLBL \
0}; \
___pc = bridge_pc; ___R_HEAP ___SET_FP(bridge_fp) \
___r0 = bridge_r0; ___r1 = bridge_r1; ___r2 = bridge_r2; \
___r3 = bridge_r3; ___r4 = bridge_r4; \
___start = ___MLBL(___HOST_LBL0); \
if (___EXPECT_FALSE(___pc == ___FIX(0))) { \
  ___ps->pc = ___CAST(___WORD, ___hlbltbl); \
  return; \
}

#undef ___END_COD
#ifdef GB_BRIDGE_EDGE_PROBE
#define GB_TRACE_EDGE(host) gambit_private_trace(host);
#else
#define GB_TRACE_EDGE(host)
#endif
#define GB_TRY_HOT(peer) \
if (bridge_host == GB_JOIN(peer,_public_host)) { \
  ___W_HEAP \
  ___TAIL_CALL_VOID(GB_JOIN(peer,_private_entry)(___ps, ___pc, ___fp, \
                                               ___r0, ___r1, ___r2, ___r3, ___r4)); \
}
#ifdef GB_BRIDGE_HOT1
#define GB_TRY_HOT1 GB_TRY_HOT(GB_BRIDGE_HOT1)
#else
#define GB_TRY_HOT1
#endif
#ifdef GB_BRIDGE_HOT2
#define GB_TRY_HOT2 GB_TRY_HOT(GB_BRIDGE_HOT2)
#else
#define GB_TRY_HOT2
#endif
#define ___END_COD \
{ \
  ___host bridge_host = ___LABEL_HOST_GET(___pc); \
  GB_TRACE_EDGE(bridge_host) \
  ___ps->pc = ___pc; \
  GB_TRY_HOT1 \
  GB_TRY_HOT2 \
  gambit_private_host bridge_next = gambit_private_lookup(bridge_host); \
  if (bridge_next) { \
    ___W_HEAP \
    ___TAIL_CALL_VOID(bridge_next(___ps, ___pc, ___fp, \
                                ___r0, ___r1, ___r2, ___r3, ___r4)); \
  } \
  ___W_ALL \
  ___TAIL_CALL_VOID(bridge_host(___ps)); \
} \
} \
}
