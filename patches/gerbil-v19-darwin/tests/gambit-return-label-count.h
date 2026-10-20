/* Diagnostic only: retain exact original returns and count their labels. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || !defined(___SINGLE_HOST)
#error "return label counter requires Darwin/GNU single-host"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
struct gb_return_counter { uint64_t key; uint64_t calls; };
static struct gb_return_counter gb_return_counts[65536];
static void gb_count_return(___WORD value, unsigned source, ___host host) {
  unsigned target = 65535, slot, remaining = 65536;
  uint64_t key;
  if (___LABEL_HOST_GET(value) == host) {
    target = gb_return_target(value);
    if (target >= 65535) abort();
  }
  if (!source || source >= 65536) abort();
  key = ((uint64_t)source << 16) | target;
  slot = (key ^ (key >> 13) ^ (key >> 23)) & 65535;
  while (gb_return_counts[slot].key && gb_return_counts[slot].key != key) {
    if (!--remaining) abort();
    slot = (slot + 1) & 65535;
  }
  gb_return_counts[slot].key = key;
  ++gb_return_counts[slot].calls;
}
static void __attribute__((destructor)) gb_dump_returns(void) {
  const char *directory = getenv("GAMBIT_STRUCTURE_PRIMITIVE_DIR");
  char path[4096];
  int fd;
  FILE *out;
  unsigned i;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-returns.tsv", directory, (long)getpid()) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(out, "source\ttarget\tcalls\n");
  for (i = 0; i < 65536; ++i) {
    if (!gb_return_counts[i].calls) continue;
    fprintf(out, "%u\t%u\t%llu\n", (unsigned)(gb_return_counts[i].key >> 16),
            (unsigned)(gb_return_counts[i].key & 65535),
            (unsigned long long)gb_return_counts[i].calls);
  }
  fclose(out);
}
