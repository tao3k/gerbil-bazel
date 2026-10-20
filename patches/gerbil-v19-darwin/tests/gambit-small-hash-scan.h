/* Opt-in experiment: current key/value reads, no persistent lookup cache. */
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(__aarch64__) && \
    defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && \
    (___WS == 8) && (___SUBTYPED_BODY == 1) && !defined(___USE_HANDLES)
#include <arm_neon.h>
#include <string.h>

#ifndef GB_HASH_SCAN_ENTRY
#define GB_HASH_SCAN_ENTRY() ((void)0)
#endif
#ifndef GB_HASH_SCAN_SELECTED
#define GB_HASH_SCAN_SELECTED(slots) ((void)0)
#endif
#ifndef GB_HASH_SCAN_SIZE
#define GB_HASH_SCAN_SIZE(slots) ((void)0)
#endif
#ifndef GB_HASH_SCAN_HIT
#define GB_HASH_SCAN_HIT() ((void)0)
#endif
#ifndef GB_HASH_SCAN_MISS
#define GB_HASH_SCAN_MISS() ((void)0)
#endif

static ___SCMOBJ __attribute__((noinline,optimize("O3")))
gb_small_hash_scan(___SCMOBJ table, ___SCMOBJ key)
{
  int words, slots, index;
  uint64x2_t needle;
  GB_HASH_SCAN_ENTRY();
  words = ___INT(___GCHASHTABLELENGTH(table)) - ___GCHASHTABLE_KEY0;
  if (words > 0 && !(words & 1)) GB_HASH_SCAN_SIZE(words >> 1);
  if (words <= 0 || (words & 1) || words > 16 ||
      ___EQP(key,___UNUSED) || ___EQP(key,___DELETED) ||
      !___FIXZEROP(___FIXAND(___GCHASHTABLE_FLAGS_FIELD(table),
                            ___FIX(___GCHASHTABLE_FLAG_KEY_MOVED))))
    return ___EXT(___gc_hash_table_ref)(table,key);
  slots = words >> 1;
  GB_HASH_SCAN_SELECTED(slots);
  needle = vdupq_n_u64((uint64_t)key);
  for (index = ___GCHASHTABLE_KEY0; words >= 4; index += 4, words -= 4)
    {
      uint64x2_t first, second, equal;
      /* memcpy avoids imposing a uint64_t alias on Gambit's word typedef. */
      memcpy(&first,___BODY_AS(table,___tWEAK)+index,sizeof(first));
      memcpy(&second,___BODY_AS(table,___tWEAK)+index+2,sizeof(second));
      equal = vceqq_u64(vuzp1q_u64(first,second),needle);
      if (vgetq_lane_u64(equal,0))
        { GB_HASH_SCAN_HIT(); return ___FIELD(WEAK,table,index+1); }
      if (vgetq_lane_u64(equal,1))
        { GB_HASH_SCAN_HIT(); return ___FIELD(WEAK,table,index+3); }
    }
  if (words && ___EQP(___FIELD(WEAK,table,index),key))
    { GB_HASH_SCAN_HIT(); return ___FIELD(WEAK,table,index+1); }
  GB_HASH_SCAN_MISS();
  return ___UNUSED;
}

#undef ___GCHASHTABLEREF
#define ___GCHASHTABLEREF(table,key) gb_small_hash_scan(table,key)
#endif
