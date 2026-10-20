#include <pthread.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if !defined(__APPLE__) || !defined(__MACH__) || !defined(__GNUC__) || defined(__clang__)
#error "This private protocol probe requires Darwin GNU GCC"
#endif

#define SHIFT 12
#define SIZE ((size_t)1 << SHIFT)
#define MASK (SIZE - 1)
#define ROUNDS 32

typedef uintptr_t word;
typedef struct table {
  struct table *previous;
  size_t capacity;
  word *segments[1];
} table;
typedef struct vm { table *glos; } vm;
typedef struct cache {
  vm *owner;
  size_t index;
  word *segment;
} cache;

/* Same two acquire reads as the current segmented-global accessor. */
static inline word *original_access(vm *v, size_t index) {
  table *t = __atomic_load_n(&v->glos, __ATOMIC_ACQUIRE);
  word *segment = __atomic_load_n(&t->segments[index >> SHIFT], __ATOMIC_ACQUIRE);
  return &segment[index & MASK];
}

static inline word *cached_access(vm *v, size_t index, cache *c) {
  size_t segment_index = index >> SHIFT;
  if (c->owner != v || c->segment == NULL || c->index != segment_index) {
    table *t = __atomic_load_n(&v->glos, __ATOMIC_ACQUIRE);
    word *segment = __atomic_load_n(&t->segments[segment_index], __ATOMIC_ACQUIRE);
    c->owner = v;
    c->index = segment_index;
    c->segment = segment;
  }
  return &c->segment[index & MASK];
}

__attribute__((noinline)) word *original_cell(vm *v, size_t index) {
  return original_access(v, index);
}

__attribute__((noinline)) word *cached_cell(vm *v, size_t index, cache *c) {
  return cached_access(v, index, c);
}

static void require(int condition) {
  if (!condition) abort();
}

static void publish(vm *v, size_t index) {
  table *old = v->glos;
  size_t capacity = old ? old->capacity : 1;
  word *segment = calloc(SIZE, sizeof(*segment));
  require(segment != NULL);
  segment[0] = index + 17;
  if (old && index < old->capacity) {
    require(old->segments[index] == NULL);
    __atomic_store_n(&old->segments[index], segment, __ATOMIC_RELEASE);
    return;
  }
  while (capacity <= index) capacity *= 2;
  table *next = calloc(1, sizeof(*next) + (capacity - 1) * sizeof(word *));
  require(next != NULL);
  next->previous = old;
  next->capacity = capacity;
  for (size_t i = 0; old && i < old->capacity; ++i)
    next->segments[i] = old->segments[i];
  next->segments[index] = segment;
  __atomic_store_n(&v->glos, next, __ATOMIC_RELEASE);
}

static void dispose(vm *v) {
  table *t = v->glos;
  for (size_t i = 0; i < t->capacity; ++i) free(t->segments[i]);
  while (t) {
    table *previous = t->previous;
    free(t);
    t = previous;
  }
  v->glos = NULL;
}

typedef struct concurrent {
  vm v;
  size_t ready;
  size_t done;
} concurrent;

static void *producer(void *argument) {
  concurrent *state = argument;
  for (size_t i = 1; i < ROUNDS; ++i) {
    publish(&state->v, i);
    __atomic_store_n(&state->ready, i, __ATOMIC_RELEASE);
    while (__atomic_load_n(&state->done, __ATOMIC_ACQUIRE) != i) {}
  }
  return NULL;
}

static void progress(const char *name) {
  printf("CASE-OK %s\n", name);
  fflush(stdout);
}

static uint64_t cpu_ns(void) {
  struct timespec now;
  require(clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &now) == 0);
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

/* Inline both accessors, with identical live loads and traversal/checksum work. */
__attribute__((noinline)) static word original_loop(vm *v, size_t iterations) {
  word sum = 0;
  for (size_t i = 0; i < iterations; ++i)
    sum += *(volatile word *)original_access(v, i & MASK);
  return sum;
}

__attribute__((noinline)) static word cached_loop(vm *v, size_t iterations) {
  cache local = {0};
  word sum = 0;
  for (size_t i = 0; i < iterations; ++i)
    sum += *(volatile word *)cached_access(v, i & MASK, &local);
  return sum;
}

static void ideal_hit_cost(vm *v) {
  const size_t iterations = SIZE * 2048;
  word *segment = original_cell(v, 0);
  word expected = 0;
  for (size_t i = 0; i < SIZE; ++i) {
    segment[i] = i + 1;
    expected += i + 1;
  }
  expected *= iterations / SIZE;
  const int roles[] = {0, 1, 1, 0, 0, 1};
  for (size_t i = 0; i < sizeof(roles) / sizeof(roles[0]); ++i) {
    uint64_t start = cpu_ns();
    word sum = roles[i] ? cached_loop(v, iterations) : original_loop(v, iterations);
    uint64_t elapsed = cpu_ns() - start;
    require(sum == expected && elapsed > 0);
    printf("IDEAL-HIT-COST %s %zu %" PRIu64 " %" PRIuPTR "\n",
           roles[i] ? "cached" : "original", iterations, elapsed, sum);
    fflush(stdout);
  }
}

int main(int argc, char **argv) {
  require(argc == 1 || (argc == 2 && strcmp(argv[1], "--ideal-hit-cost") == 0));
  vm a = {0}, b = {0};
  cache c = {0};
  publish(&a, 0);
  publish(&b, 0);
  require(cached_cell(&a, 0, &c) == original_cell(&a, 0));
  progress("initial-pointer-identity");
  *original_cell(&a, 23) = 91;
  require(*cached_cell(&a, 23, &c) == 91);
  *cached_cell(&a, 23, &c) = 103;
  require(*original_cell(&a, 23) == 103);
  progress("live-cell-read-write");
  require(cached_cell(&a, MASK, &c) == original_cell(&a, MASK));
  progress("last-cell-boundary");
  require(cached_cell(&b, 23, &c) == original_cell(&b, 23));
  require(*cached_cell(&b, 23, &c) == 0);
  require(*cached_cell(&a, 23, &c) == 103);
  progress("vm-isolation-and-return");
  word *first = cached_cell(&a, 23, &c);
  for (size_t i = 1; i < ROUNDS; ++i) publish(&a, i);
  require(first == cached_cell(&a, 23, &c));
  require(first == original_cell(&a, 23));
  progress("old-segment-stable-across-root-growth");
  for (size_t i = 0; i < ROUNDS; ++i) {
    require(cached_cell(&a, i * SIZE, &c) == original_cell(&a, i * SIZE));
    require(*cached_cell(&a, i * SIZE, &c) == i + 17);
  }
  progress("segment-misses-and-in-capacity-publication");
  concurrent state = {0};
  publish(&state.v, 0);
  cache local = {0};
  word *stable = cached_cell(&state.v, 0, &local);
  pthread_t thread;
  require(pthread_create(&thread, NULL, producer, &state) == 0);
  for (size_t i = 1; i < ROUNDS; ++i) {
    while (__atomic_load_n(&state.ready, __ATOMIC_ACQUIRE) != i) {}
    require(cached_cell(&state.v, 0, &local) == stable);
    require(cached_cell(&state.v, i * SIZE, &local) == original_cell(&state.v, i * SIZE));
    require(*cached_cell(&state.v, i * SIZE, &local) == i + 17);
    __atomic_store_n(&state.done, i, __ATOMIC_RELEASE);
  }
  require(pthread_join(thread, NULL) == 0);
  progress("concurrent-publication-with-stable-hit");
  if (argc == 2) ideal_hit_cost(&a);
  dispose(&state.v);
  dispose(&a);
  dispose(&b);
  puts("PROTOCOL-OK");
  return 0;
}
