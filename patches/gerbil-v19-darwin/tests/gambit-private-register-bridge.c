#include "gambit.h"
#include <stdint.h>
#ifdef GB_BRIDGE_EDGE_PROBE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#endif

typedef void (*gambit_private_host)(___processor_state, ___WORD, ___WORD *,
                                    ___WORD, ___WORD, ___WORD, ___WORD, ___WORD);
struct gambit_private_slot {
  ___host normal;
  gambit_private_host fast;
};
struct gambit_private_slot gambit_private_hosts[4096];
#ifdef GB_BRIDGE_EDGE_PROBE
unsigned long long gambit_private_edges[16][16];
unsigned gambit_private_ids[4096];
static const char *gambit_private_names[16] = {"unregistered-or-legacy"};
static unsigned gambit_private_count;
void gambit_private_name(___host host, const char *name) {
  unsigned index = ((uintptr_t)host >> 8) & 4095;
  if (gambit_private_hosts[index].normal == host) {
    unsigned id = ++gambit_private_count;
    if (id >= 16) abort();
    gambit_private_ids[index] = id;
    gambit_private_names[id] = name;
  }
}
static void __attribute__((destructor)) gambit_private_dump(void) {
  const char *directory = getenv("GAMBIT_PRIVATE_EDGE_DIR");
  char path[4096];
  unsigned from, to;
  int fd;
  FILE *out;
  if (!directory) return;
  if (snprintf(path, sizeof(path), "%s/%ld-edges.tsv", directory, (long)getpid()) >= sizeof(path)) abort();
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) abort();
  out = fdopen(fd, "w");
  if (!out) abort();
  fputs("from\tto\tcount\n", out);
  for (from = 0; from <= gambit_private_count; ++from)
    for (to = 0; to <= gambit_private_count; ++to)
      if (gambit_private_edges[from][to])
        fprintf(out, "%s\t%s\t%llu\n", gambit_private_names[from],
                gambit_private_names[to], gambit_private_edges[from][to]);
  fclose(out);
}
#endif

void gambit_private_register(___host normal, gambit_private_host fast) {
  struct gambit_private_slot *slot =
    &gambit_private_hosts[((uintptr_t)normal >> 8) & 4095];
  /* A collision retains the public path; never redirect another host. */
  if (!slot->normal || slot->normal == normal) {
    slot->normal = normal;
    slot->fast = fast;
  }
}
