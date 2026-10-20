/* Diagnostic only: count kernel entries without changing GVM state. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || !defined(___SINGLE_HOST)
#error "kernel label count requires Darwin GNU single-host"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static uint64_t gb_kernel_labels[___LBLCOUNT];
static uint64_t gb_rest_shapes[65][65];
static void __attribute__((destructor)) gb_kernel_labels_dump(void) {
  const char *directory = getenv("GAMBIT_KERNEL_LABEL_DIR");
  char path[4096];
  FILE *out;
  unsigned i;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld.tsv", directory, (long)getpid()) >= sizeof(path)) abort();
  out = fopen(path, "wx");
  if (!out) abort();
  fputs("label\tcalls\n", out);
  for (i = 0; i < ___LBLCOUNT; ++i)
    if (gb_kernel_labels[i]) fprintf(out, "%u\t%llu\n", i, (unsigned long long)gb_kernel_labels[i]);
  if (fclose(out)) abort();
  if (snprintf(path, sizeof(path), "%s/%ld-rest.csv", directory, (long)getpid()) >= sizeof(path)) abort();
  out = fopen(path, "wx");
  if (!out) abort();
  fputs("parameters,arguments,calls\n", out);
  for (i = 0; i < 65; ++i) {
    unsigned j;
    for (j = 0; j < 65; ++j)
      if (gb_rest_shapes[i][j]) fprintf(out, "%u,%u,%llu\n", i, j, (unsigned long long)gb_rest_shapes[i][j]);
  }
  if (fclose(out)) abort();
}
#undef ___BEGIN_SW
#define ___BEGIN_SW \
___REGISTER_HOST_ENTRY \
do { \
  intptr_t gb_delta = (intptr_t)___pc - (intptr_t)___lp; \
  intptr_t gb_index = gb_delta / (___LABEL_SIZE * ___WS); \
  if (gb_index < 0 || gb_index >= ___LBLCOUNT || gb_delta % (___LABEL_SIZE * ___WS)) abort(); \
  ++gb_kernel_labels[gb_index]; \
  if (___pc == ___ps->handler_get_rest) { \
    ___WORD gb_np = ___PRD_NBPARMS(___SUBTYPED_HEADER(___ps->temp1)); \
    ___WORD gb_na = ___ps->na; \
    if (gb_np < 0 || gb_na < 0) abort(); \
    ++gb_rest_shapes[gb_np < 64 ? gb_np : 64][gb_na < 64 ? gb_na : 64]; \
  } \
} while (0); \
goto *___LABEL_HOST_LABEL_GET(___pc);
