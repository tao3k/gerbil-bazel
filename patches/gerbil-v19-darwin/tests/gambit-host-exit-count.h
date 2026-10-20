/* Diagnostic only: identify destinations omitted by the private bridge graph. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || \
    !defined(___SINGLE_HOST) || ___MAX_PROCESSORS != 1
#error "host exit counter requires Darwin/GNU single-processor single-host"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <string.h>
struct gambit_host_counter { ___host host; uint64_t calls; char *image; uintptr_t offset; };
static struct gambit_host_counter gambit_host_exits[512];
static inline void gambit_count_host_exit(___host host) {
  uintptr_t value = (uintptr_t)host;
  unsigned slot = ((value >> 4) ^ (value >> 12)) & 511;
  unsigned remaining = 512;
  while (gambit_host_exits[slot].host && gambit_host_exits[slot].host != host) {
    if (!--remaining) abort();
    slot = (slot + 1) & 511;
  }
  if (!gambit_host_exits[slot].host) {
    Dl_info info;
    /* Capture while the image is loaded; VM cleanup may unload it before exit. */
    int mapped = dladdr((void *)host, &info);
    gambit_host_exits[slot].image = strdup(mapped ? info.dli_fname : "<unmapped>");
    if (!gambit_host_exits[slot].image) abort();
    gambit_host_exits[slot].offset = value - (mapped ? (uintptr_t)info.dli_fbase : 0);
    gambit_host_exits[slot].host = host;
  }
  ++gambit_host_exits[slot].calls;
}
static void __attribute__((destructor)) gambit_host_exit_dump(void) {
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
  fprintf(out, "module\timage\toffset\tcalls\n");
  for (i = 0; i < 512; ++i) {
    if (!gambit_host_exits[i].calls) continue;
    fprintf(out, "%s\t%s\t%llx\t%llu\n", ___MODULE_NAME, gambit_host_exits[i].image,
      (unsigned long long)gambit_host_exits[i].offset,
      (unsigned long long)gambit_host_exits[i].calls);
  }
  fclose(out);
}
#undef ___END_COD
#define ___END_COD \
gambit_count_host_exit(___LABEL_HOST_GET(___pc)); \
___ps->pc = ___pc; \
___W_ALL } \
___EXIT_HOST(); \
}
