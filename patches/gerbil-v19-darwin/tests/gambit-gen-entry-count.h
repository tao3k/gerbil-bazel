/* Diagnostic only: map native entry addresses without changing VM state. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || !defined(___SINGLE_HOST) || !defined(___USE_LABEL_VALUES)
#error "generic entry counter requires Darwin/GNU label values"
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
struct gb_gen_label { ___WORD entry; unsigned index; };
struct gb_gen_counter { uint64_t key; uint64_t calls; };
static struct gb_gen_label gb_gen_labels[65536];
static struct gb_gen_counter gb_gen_counts[65536];
static int gb_gen_labels_ready;
static unsigned gb_gen_label_aliases;
static unsigned gb_gen_slot(___WORD entry) {
  uintptr_t value = (uintptr_t)entry;
  return ((value >> 2) ^ (value >> 17)) & 65535;
}
static void gb_register_gen_label(___WORD entry, unsigned index) {
  unsigned slot = gb_gen_slot(entry), remaining = 65536;
  if (!entry || index >= 65534) abort();
  while (gb_gen_labels[slot].entry && gb_gen_labels[slot].entry != entry) {
    if (!--remaining) abort();
    slot = (slot + 1) & 65535;
  }
  if (gb_gen_labels[slot].entry) {
    ++gb_gen_label_aliases;
    return;
  }
  gb_gen_labels[slot].entry = entry;
  gb_gen_labels[slot].index = index;
}
static void gb_count_gen(___WORD value, unsigned source, ___host host) {
  ___WORD ___temp;
  unsigned target = 65535, slot, remaining = 65536;
  uint64_t key;
  if (___PROCEDUREP(value)) {
    ___WORD label = ___LABEL_ENTRY_GET(value);
    target = 65534;
    if (___LABEL_HOST_GET(label) == host) {
      ___WORD entry = (___WORD)___LABEL_HOST_LABEL_GET(label);
      slot = gb_gen_slot(entry);
      while (gb_gen_labels[slot].entry) {
        if (gb_gen_labels[slot].entry == entry) {
          target = gb_gen_labels[slot].index;
          break;
        }
        if (!--remaining) abort();
        slot = (slot + 1) & 65535;
      }
      if (target == 65534) abort();
    }
  }
  if (!source || source >= 65534) abort();
  key = ((uint64_t)source << 16) | target;
  slot = (key ^ (key >> 13) ^ (key >> 23)) & 65535;
  remaining = 65536;
  while (gb_gen_counts[slot].key && gb_gen_counts[slot].key != key) {
    if (!--remaining) abort();
    slot = (slot + 1) & 65535;
  }
  gb_gen_counts[slot].key = key;
  ++gb_gen_counts[slot].calls;
}
static void __attribute__((destructor)) gb_dump_gen(void) {
  const char *directory = getenv("GAMBIT_STRUCTURE_PRIMITIVE_DIR");
  char path[4096];
  int fd;
  FILE *out;
  unsigned i;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-gen.tsv", directory, (long)getpid()) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fprintf(stderr, "GEN-LABEL-ALIASES %u\n", gb_gen_label_aliases);
  fprintf(out, "source\ttarget\tcalls\n");
  for (i = 0; i < 65536; ++i) {
    if (!gb_gen_counts[i].calls) continue;
    fprintf(out, "%u\t%u\t%llu\n", (unsigned)(gb_gen_counts[i].key >> 16),
            (unsigned)(gb_gen_counts[i].key & 65535),
            (unsigned long long)gb_gen_counts[i].calls);
  }
  fclose(out);
}
