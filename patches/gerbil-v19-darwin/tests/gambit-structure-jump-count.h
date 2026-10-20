/* Diagnostic only, forced into each generated C translation unit. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__)
#error "native structure jump counter requires Darwin/GNU"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
static uint64_t gb_structure_jump_counts[5];
#define GB_STRUCTURE_JUMP_EVENT(event) (++gb_structure_jump_counts[event])
static void __attribute__((destructor)) gb_dump_structure_jumps(void) {
  const char *directory = getenv("GAMBIT_STRUCTURE_PRIMITIVE_DIR");
  const char *file = strrchr(__BASE_FILE__, '/');
  char path[4096];
  FILE *out;
  int fd;
  unsigned i;
  if (!directory || !gb_structure_jump_counts[0]) return;
  file = file ? file + 1 : __BASE_FILE__;
  if (snprintf(path, sizeof(path), "%s/%ld-%s-jumps.tsv", directory, (long)getpid(), file) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(out, "event\tcalls\n");
  for (i = 0; i < 5; ++i) fprintf(out, "%u\t%llu\n", i, (unsigned long long)gb_structure_jump_counts[i]);
  fclose(out);
}
