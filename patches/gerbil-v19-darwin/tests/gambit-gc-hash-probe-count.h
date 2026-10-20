#include <stdio.h>
#include <stdlib.h>

static unsigned long long gb_gc_probe_calls, gb_gc_probe_steps;
static unsigned long long gb_gc_probe_hits, gb_gc_probe_misses, gb_gc_probe_rehashes;
static unsigned long long gb_gc_probe_hist[32], gb_gc_probe_max;
static unsigned long long gb_gc_probe_empty_calls, gb_gc_probe_empty_hits;
static unsigned long long gb_gc_probe_nonempty_misses;

static void gb_gc_probe_record(unsigned steps, int hit, int count)
{
  unsigned bin = steps > 32 ? 31 : steps - 1;
  ++gb_gc_probe_calls;
  gb_gc_probe_steps += steps;
  ++gb_gc_probe_hist[bin];
  if (hit) ++gb_gc_probe_hits; else ++gb_gc_probe_misses;
  if (steps > gb_gc_probe_max) gb_gc_probe_max = steps;
  if (count == 0) {
    ++gb_gc_probe_empty_calls;
    if (hit) ++gb_gc_probe_empty_hits;
  } else if (!hit) ++gb_gc_probe_nonempty_misses;
}

#define GB_GC_PROBE_RETURN(value,hit) \
  do { gb_gc_probe_record(gb_probe_steps,hit,gb_probe_count); return (value); } while (0)

static void __attribute__((destructor)) gb_gc_probe_dump(void)
{
  const char *path = getenv("GAMBIT_GC_HASH_PROBE_FILE");
  unsigned i;
  FILE *out;
  if (!path || !*path) return;
  out = fopen(path,"w");
  if (!out) return;
  fprintf(out,"{\"calls\":%llu,\"steps\":%llu,\"hits\":%llu,\"misses\":%llu,"
              "\"lazyRehashes\":%llu,\"maxSteps\":%llu,\"emptyCalls\":%llu,"
              "\"emptyHits\":%llu,\"nonemptyMisses\":%llu,\"stepHistogram\":[",
          gb_gc_probe_calls,gb_gc_probe_steps,gb_gc_probe_hits,gb_gc_probe_misses,
          gb_gc_probe_rehashes,gb_gc_probe_max,gb_gc_probe_empty_calls,
          gb_gc_probe_empty_hits,gb_gc_probe_nonempty_misses);
  for (i=0;i<32;++i) fprintf(out,"%s%llu",i ? "," : "",gb_gc_probe_hist[i]);
  fprintf(out,"]}\n");
  fclose(out);
}
