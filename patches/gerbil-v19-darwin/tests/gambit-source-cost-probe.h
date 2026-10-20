#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

struct gb_source_clock { double user, sys, wall; };
struct gb_source_frame { int kind; struct gb_source_clock start, children; };
static struct gb_source_frame gb_source_stack[1024];
static struct gb_source_clock gb_source_inclusive[4], gb_source_exclusive[4];
static unsigned long gb_source_calls[4], gb_source_errors, gb_source_finished;
static unsigned gb_source_depth;

static struct gb_source_clock gb_source_now(void) {
  struct rusage usage;
  struct timespec time;
  struct gb_source_clock result = {0,0,0};
  if (getrusage(RUSAGE_SELF,&usage) || clock_gettime(CLOCK_MONOTONIC,&time)) {
    ++gb_source_errors;
    return result;
  }
  result.user=usage.ru_utime.tv_sec+usage.ru_utime.tv_usec*1e-6;
  result.sys=usage.ru_stime.tv_sec+usage.ru_stime.tv_usec*1e-6;
  result.wall=time.tv_sec+time.tv_nsec*1e-9;
  return result;
}

static void gb_source_dump(void) {
  const char *prefix=getenv("GAMBIT_DARWIN_SOURCE_COST_PREFIX");
  char path[4096], temporary[4096];
  if (!prefix) return;
  if (snprintf(path,sizeof(path),"%s.%ld.json",prefix,(long)getpid()) >= sizeof(path) ||
      snprintf(temporary,sizeof(temporary),"%s.tmp",path) >= sizeof(temporary)) {
    ++gb_source_errors; return;
  }
  FILE *file=fopen(temporary,"w");
  if (!file) { ++gb_source_errors; return; }
  fprintf(file,"{\"pid\":%ld,\"openFrames\":%u,\"errors\":%lu,\"phases\":[",
          (long)getpid(),gb_source_depth,gb_source_errors);
  for (int i=0;i<4;++i) {
    fprintf(file,"%s{\"kind\":%d,\"calls\":%lu,\"inclusiveUser\":%.9f,"
                 "\"inclusiveSystem\":%.9f,\"inclusiveWall\":%.9f,"
                 "\"exclusiveUser\":%.9f,\"exclusiveSystem\":%.9f,\"exclusiveWall\":%.9f}",
            i ? "," : "",i,gb_source_calls[i],
            gb_source_inclusive[i].user,gb_source_inclusive[i].sys,gb_source_inclusive[i].wall,
            gb_source_exclusive[i].user,gb_source_exclusive[i].sys,gb_source_exclusive[i].wall);
  }
  fprintf(file,"]}\n");
  if (fclose(file) || rename(temporary,path)) ++gb_source_errors;
}

static void gb_source_begin(int kind) {
  int saved=errno;
  if (kind<0 || kind>=4 || gb_source_depth>=1024) ++gb_source_errors;
  else {
    struct gb_source_frame *frame=&gb_source_stack[gb_source_depth++];
    frame->kind=kind;
    frame->children=(struct gb_source_clock){0,0,0};
    frame->start=gb_source_now();
  }
  errno=saved;
}

static void gb_source_end(int kind) {
  int saved=errno;
  struct gb_source_clock end=gb_source_now();
  if (!gb_source_depth || gb_source_stack[gb_source_depth-1].kind!=kind) ++gb_source_errors;
  else {
    struct gb_source_frame *frame=&gb_source_stack[--gb_source_depth];
    struct gb_source_clock delta={end.user-frame->start.user,end.sys-frame->start.sys,
                                  end.wall-frame->start.wall};
    ++gb_source_calls[kind];
#define GB_SOURCE_ADD(field) do { \
  gb_source_inclusive[kind].field+=delta.field; \
  gb_source_exclusive[kind].field+=delta.field-frame->children.field; \
  if (gb_source_depth) gb_source_stack[gb_source_depth-1].children.field+=delta.field; \
} while (0)
    GB_SOURCE_ADD(user); GB_SOURCE_ADD(sys); GB_SOURCE_ADD(wall);
#undef GB_SOURCE_ADD
    if (!(++gb_source_finished%64) && !gb_source_depth) gb_source_dump();
  }
  errno=saved;
}
static void __attribute__((destructor)) gb_source_final(void) { gb_source_dump(); }
#else
static void gb_source_begin(int kind) { (void)kind; }
static void gb_source_end(int kind) { (void)kind; }
#endif
