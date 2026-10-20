/* C backend prototype: bounded nonallocating walk, original deep fallback. */
#ifndef GB_STRUCTURE_JUMP_EVENT
#define GB_STRUCTURE_JUMP_EVENT(event) ((void)0)
#endif
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)
#define ___GB_STRUCTURE_JUMP4(target) \
{ \
  ___WORD gb_descriptor, gb_answer = ___FAL, ___temp; \
  unsigned gb_depth; \
  int gb_done = 1; \
  GB_STRUCTURE_JUMP_EVENT(0); \
  if (___STRUCTUREP(___R1)) { \
    gb_descriptor = ___STRUCTURETYPE(___R1); \
    gb_done = 0; \
    for (gb_depth = 0; gb_depth < 4; ++gb_depth) { \
      if (___EQP(___TYPEID(gb_descriptor), ___R2)) { \
        gb_answer = ___TRU; gb_done = 1; break; \
      } \
      gb_descriptor = ___TYPESUPER(gb_descriptor); \
      if (gb_descriptor == ___FAL) { gb_done = 1; break; } \
    } \
  } else { GB_STRUCTURE_JUMP_EVENT(1); } \
  if (gb_done) { \
    GB_STRUCTURE_JUMP_EVENT(gb_answer == ___TRU ? 2 : 3); \
    ___SET_R1(gb_answer) \
    ___JUMPRET(___R0) \
  } \
  GB_STRUCTURE_JUMP_EVENT(4); \
  ___JUMPPRM(___SET_NARGS(2),target) \
}
#else
#define ___GB_STRUCTURE_JUMP4(target) ___JUMPPRM(___SET_NARGS(2),target)
#endif
