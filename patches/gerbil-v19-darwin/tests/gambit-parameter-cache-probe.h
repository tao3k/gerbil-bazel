/* Read-only parameter cache probe. No private cache or VM ABI change. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || \
    !defined(___SINGLE_HOST) || ___MAX_PROCESSORS != 1
#error "parameter probe requires Darwin/GNU single-processor single-host"
#endif
extern ___glo_struct ___G__23__23_current_2d_exception_2d_handler;
extern ___glo_struct ___G__23__23_current_2d_input_2d_port;
extern ___glo_struct ___G__23__23_current_2d_output_2d_port;
extern ___glo_struct ___G__23__23_identity;
static inline int gambit_parameter_cached(___processor_state ___ps, ___WORD parameter, ___WORD *answer) {
  ___WORD ___temp, original, descriptor, cached;
  original = ___PRMCELL(___G__23__23_current_2d_exception_2d_handler.prm);
  if (!___CLOSUREP(original) || !___CLOSUREP(parameter) ||
      ___CLOSURECODE(parameter) != ___CLOSURECODE(original)) return 0;
  if (parameter == ___GLOCELL(___G__23__23_current_2d_exception_2d_handler.val) ||
      parameter == ___GLOCELL(___G__23__23_current_2d_input_2d_port.val) ||
      parameter == ___GLOCELL(___G__23__23_current_2d_output_2d_port.val)) return 1;
  descriptor = ___CLOSUREREF(parameter, ___FIX(1));
  if (!___VECTORP(descriptor) || ___INT(___VECTORLENGTH(descriptor)) < 4 ||
      ___VECTORREF(descriptor, ___FIX(3)) != ___PRMCELL(___G__23__23_identity.prm)) return 1;
  cached = ___THREAD_DENV_CACHE1_FIELD(___CURRENTTHREAD);
  if (!___PAIRP(cached) || ___CAR(cached) != parameter) return 1;
  *answer = ___CDR(cached);
  return 2;
}
#ifdef GB_PARAMETER_COUNT_ONLY
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
static uint64_t gambit_parameter_zero, gambit_parameter_recognized, gambit_parameter_hits;
static void __attribute__((destructor)) gambit_parameter_dump(void) {
  const char *directory = getenv("GAMBIT_PARAMETER_PROBE_DIR");
  char path[4096];
  int fd;
  FILE *out;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-%s.tsv", directory,
               (long)getpid(), ___MODULE_NAME) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(out, "module\tzeroArguments\tparameters\tcache1Hits\n%s\t%llu\t%llu\t%llu\n",
    ___MODULE_NAME, (unsigned long long)gambit_parameter_zero,
    (unsigned long long)gambit_parameter_recognized, (unsigned long long)gambit_parameter_hits);
  fclose(out);
}
#endif
#ifndef GB_PARAMETER_HELPER_ONLY
#undef ___JUMPNOTSAFE
#ifdef GB_PARAMETER_COUNT_ONLY
#define ___JUMPNOTSAFE(nargs, value) { \
  nargs ___SELF = (value); \
  if (___ps->na == 0) { \
    ___WORD parameter_answer; \
    int parameter_status = gambit_parameter_cached(___ps, ___SELF, &parameter_answer); \
    ++gambit_parameter_zero; \
    if (parameter_status) ++gambit_parameter_recognized; \
    if (parameter_status == 2) ++gambit_parameter_hits; \
  } \
  ___JUMP(___LABEL_ENTRY_GET(___SELF)) \
}
#else
#define ___JUMPNOTSAFE(nargs, value) { \
  nargs ___SELF = (value); \
  if (___ps->na == 0) { \
    ___WORD parameter_answer; \
    if (gambit_parameter_cached(___ps, ___SELF, &parameter_answer) == 2) { \
      ___R1 = parameter_answer; \
      ___JUMPRET(___R0) \
    } \
  } \
  ___JUMP(___LABEL_ENTRY_GET(___SELF)) \
}
#endif
#endif
