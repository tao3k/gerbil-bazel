"""Private carrier experiment: inline live probing, never cache an answer."""

INLINE_REF = r'''
static inline __attribute__((always_inline)) ___SCMOBJ
gb_live_hash_ref(___SCMOBJ ht, ___SCMOBJ key) {
  ___WORD ___temp;
  int size2, probe2, step2;
  ___SCMOBJ obj;
  if (!___FIXZEROP(___FIXAND(___GCHASHTABLE_FLAGS_FIELD(ht),
                            ___FIX(___GCHASHTABLE_FLAG_KEY_MOVED))))
    return ___GCHASHTABLEREF(ht,key);
  size2 = ___INT(___GCHASHTABLELENGTH(ht)) - ___GCHASHTABLE_KEY0;
  ___GCHASHTABLE_HASH_STEP(probe2, step2, key, size2 >> 1);
  probe2 <<= 1;
  step2 <<= 1;
  obj = ___FIELD(WEAK,ht,probe2 + ___GCHASHTABLE_KEY0);
  if (___EQP(obj,key))
    return ___FIELD(WEAK,ht,probe2 + ___GCHASHTABLE_VAL0);
  if (!___EQP(obj,___UNUSED)) {
    for (;;) {
      probe2 -= step2;
      if (probe2 < 0) probe2 += size2;
      obj = ___FIELD(WEAK,ht,probe2 + ___GCHASHTABLE_KEY0);
      if (___EQP(obj,key))
        return ___FIELD(WEAK,ht,probe2 + ___GCHASHTABLE_VAL0);
      if (___EQP(obj,___UNUSED)) break;
    }
  }
  return ___UNUSED;
}
'''


def inject_live_hash_ref(code):
    entry = 'struct gb_trace_native_11_result { ___WORD words[8]; };'
    start = code.index(entry)
    guard_start = code.rfind('#if ', 0, start)
    guard = code[guard_start:code.index('\n', guard_start)] if guard_start >= 0 else ''
    if not all(token in guard for token in ('defined(__APPLE__)', 'defined(__GNUC__)',
        '!defined(__clang__)', 'defined(___SINGLE_VM)', 'defined(___SINGLE_THREADED_VMS)')):
        raise ValueError('original Darwin/GNU single-VM guard required')
    end = code.index('\n#endif', start)
    block = code[start:end]
    call = '___GCHASHTABLEREF(gb_t32,gb_in2)'
    if block.count(call) != 1 or 'gb_live_hash_ref' in code:
        raise ValueError('original selected context-helper shape required')
    # The helper remains inside the original Darwin/GNU/single-VM guard.
    return code[:start] + INLINE_REF + block.replace(call,
        'gb_live_hash_ref(gb_t32,gb_in2)') + code[end:]
