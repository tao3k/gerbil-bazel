/* Bounded prototype of _kernel.scm's nonallocating type-chain predicate. */
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && \
    defined(___PRM__23__23_structure_2d_instance_2d_of_3f_)
#ifdef GB_STRUCTURE_COUNT_ONLY
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
static uint64_t gambit_structure_calls;
static void __attribute__((destructor)) gambit_structure_dump(void) {
  const char *directory = getenv("GAMBIT_STRUCTURE_PRIMITIVE_DIR");
  char path[4096];
  FILE *out;
  int fd;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-%s.tsv", directory,
               (long)getpid(), ___MODULE_NAME) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(out, "module\tcalls\n%s\t%llu\n", ___MODULE_NAME,
          (unsigned long long)gambit_structure_calls);
  fclose(out);
}
#else
static inline __attribute__((always_inline)) int gambit_structure_probe
  (___WORD object, ___WORD type_id, ___WORD *answer) {
  ___WORD descriptor, ___temp;
  unsigned depth;
  if (!___STRUCTUREP(object)) { *answer = ___FAL; return 1; }
  descriptor = ___STRUCTURETYPE(object);
  for (depth = 0; depth < 4; ++depth) {
    if (___EQP(___TYPEID(descriptor), type_id)) { *answer = ___TRU; return 1; }
    descriptor = ___TYPESUPER(descriptor);
    if (descriptor == ___FAL) { *answer = ___FAL; return 1; }
  }
  /* Deep or cyclic chains retain the original interruptible Scheme path. */
  return 0;
}
#endif

#ifndef GB_STRUCTURE_HELPER_ONLY
#undef ___JUMPPRM
#ifdef GB_STRUCTURE_COUNT_ONLY
#define ___JUMPPRM(nargs, value) { \
  ___WORD structure_target; \
  nargs \
  structure_target = (value); \
  if (structure_target == ___PRM__23__23_structure_2d_instance_2d_of_3f_ && ___ps->na == 2) \
    ++gambit_structure_calls; \
  ___JUMP(structure_target) \
}
#else
#define ___JUMPPRM(nargs, value) { \
  ___WORD structure_target, structure_answer; \
  nargs \
  structure_target = (value); \
  if (structure_target == ___PRM__23__23_structure_2d_instance_2d_of_3f_ && ___ps->na == 2 && \
      gambit_structure_probe(___R1, ___R2, &structure_answer)) { \
    ___R1 = structure_answer; \
    ___JUMPRET(___R0) \
  } \
  ___JUMP(structure_target) \
}
#endif
#endif
#endif
