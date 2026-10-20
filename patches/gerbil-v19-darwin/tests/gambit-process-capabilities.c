#include <dlfcn.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
  struct rlimit limit;
  if (getrlimit(RLIMIT_NOFILE, &limit) != 0) return 1;
  printf("openMax=%ld softLimit=%llu hardLimit=%llu closefromSymbol=%s",
         sysconf(_SC_OPEN_MAX), (unsigned long long)limit.rlim_cur,
         (unsigned long long)limit.rlim_max,
         dlsym(RTLD_DEFAULT, "closefrom") ? "present" : "absent");
#ifdef SYS_close_range
  printf(" SYS_close_range=present");
#else
  printf(" SYS_close_range=absent");
#endif
#ifdef F_CLOSEM
  printf(" F_CLOSEM=present\n");
#else
  printf(" F_CLOSEM=absent\n");
#endif
  return 0;
}
