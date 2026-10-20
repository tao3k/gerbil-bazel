/* Diagnostic only: exact primitive call sites, without changing dispatch. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__)
#error "primitive counter requires Darwin/GNU"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
static uint64_t gambit_primitive_counts[8192];
static const char *gambit_primitive_names[8192];
static void __attribute__((destructor)) gambit_primitive_dump(void) {
  const char *directory = getenv("GAMBIT_STRUCTURE_PRIMITIVE_DIR");
  char path[4096];
  unsigned i;
  int fd;
  FILE *out;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-%s.tsv", directory,
               (long)getpid(), ___MODULE_NAME) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(out, "module\tprimitive\tcalls\n");
  for (i = 0; i < 8192; ++i)
    if (gambit_primitive_counts[i])
      fprintf(out, "%s\t%s\t%llu\n", ___MODULE_NAME,
              gambit_primitive_names[i], (unsigned long long)gambit_primitive_counts[i]);
  fclose(out);
}
#undef ___JUMPPRM
#define ___JUMPPRM(nargs, value) { \
  enum { primitive_site = __COUNTER__ }; \
  _Static_assert(primitive_site < 8192, "primitive site budget exceeded"); \
  gambit_primitive_names[primitive_site] = #value; \
  ++gambit_primitive_counts[primitive_site]; \
  nargs \
  ___JUMP(value) \
}
