#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__)
#error Darwin GNU diagnostic only
#endif
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

struct gb_path_stamp { struct rusage usage; struct timespec wall; int valid; };
struct gb_path_cost { unsigned long long calls; double user,system,wall; };
static struct gb_path_cost gb_path_costs[3];
static const char *gb_path_names[3]={"getcwd","normalize","fileInfo"};
static unsigned gb_path_depth,gb_path_dump_pending,gb_path_measurement_failures;

static double gb_path_seconds(struct timeval value) {
  return (double)value.tv_sec+(double)value.tv_usec/1000000.0;
}
static void gb_path_begin(struct gb_path_stamp *stamp) {
  int saved=errno;
  ++gb_path_depth;
  stamp->valid=(getrusage(RUSAGE_SELF,&stamp->usage)==0 &&
                clock_gettime(CLOCK_MONOTONIC,&stamp->wall)==0);
  errno=saved;
}
static void gb_path_dump(void) {
  const char *prefix=getenv("GAMBIT_DARWIN_PATH_COST_PREFIX");
  char path[4096];
  char temporary[4110];
  FILE *file;
  if (!prefix || snprintf(path,sizeof(path),"%s.%s.%ld.json",prefix,GB_PATH_UNIT,
                          (long)getpid())>=(int)sizeof(path)) return;
  snprintf(temporary,sizeof(temporary),"%s.tmp",path);
  file=fopen(temporary,"w");
  if (!file) return;
  fprintf(file,"{\"pid\":%ld,\"unit\":\"%s\",\"partialSnapshot\":true,\"measurementFailures\":%u,\"costs\":[",
          (long)getpid(),GB_PATH_UNIT,gb_path_measurement_failures);
  for (int i=0;i<3;++i)
    fprintf(file,"%s{\"name\":\"%s\",\"calls\":%llu,\"user\":%.9f,\"system\":%.9f,\"wall\":%.9f}",
            i ? "," : "",gb_path_names[i],gb_path_costs[i].calls,
            gb_path_costs[i].user,gb_path_costs[i].system,gb_path_costs[i].wall);
  fprintf(file,"]}\n");
  fclose(file);
  rename(temporary,path);
}
static void gb_path_finish(struct gb_path_stamp *stamp,int slot) {
  struct rusage usage;
  struct timespec wall;
  --gb_path_depth;
  if (!stamp->valid || getrusage(RUSAGE_SELF,&usage)!=0 ||
      clock_gettime(CLOCK_MONOTONIC,&wall)!=0) { ++gb_path_measurement_failures; return; }
  struct gb_path_cost *cost=&gb_path_costs[slot];
  ++cost->calls;
  cost->user+=gb_path_seconds(usage.ru_utime)-gb_path_seconds(stamp->usage.ru_utime);
  cost->system+=gb_path_seconds(usage.ru_stime)-gb_path_seconds(stamp->usage.ru_stime);
  cost->wall+=(double)(wall.tv_sec-stamp->wall.tv_sec)+
              (double)(wall.tv_nsec-stamp->wall.tv_nsec)/1000000000.0;
  if ((cost->calls&63)==0) gb_path_dump_pending=1;
  if (!gb_path_depth && gb_path_dump_pending) {
    gb_path_dump_pending=0;
    gb_path_dump();
  }
}
static void __attribute__((destructor)) gb_path_final_dump(void) {
  gb_path_dump();
}
