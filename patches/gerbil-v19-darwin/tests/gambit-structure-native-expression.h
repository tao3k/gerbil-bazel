/* Expression probe is nonallocating; ABSENT requests original interruptible IR. */
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)
#define ___GB_STRUCTURE_PROBE4(obj,id) \
({ ___WORD gb_obj=(obj), gb_id=(id), gb_descriptor, gb_answer=___FAL, ___temp; \
   unsigned gb_depth; \
   if (___STRUCTUREP(gb_obj)) { \
     gb_descriptor=___STRUCTURETYPE(gb_obj); gb_answer=___ABSENT; \
     for (gb_depth=0; gb_depth<4; ++gb_depth) { \
       if (___EQP(___TYPEID(gb_descriptor),gb_id)) {gb_answer=___TRU; break;} \
       gb_descriptor=___TYPESUPER(gb_descriptor); \
       if (gb_descriptor==___FAL) {gb_answer=___FAL; break;} \
     } \
   } \
   gb_answer; })
#else
#define ___GB_STRUCTURE_PROBE4(obj,id) ((void)(obj),(void)(id),___ABSENT)
#endif
