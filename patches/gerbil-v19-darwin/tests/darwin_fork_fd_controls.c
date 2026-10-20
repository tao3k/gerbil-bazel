#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int failure_mode;
static unsigned long close_attempts;

static int probe_pidinfo(int pid, int flavor, uint64_t arg, void *buffer, int size)
{
  if (buffer && failure_mode == 1) return 0;
  if (buffer && failure_mode == 2) return 1;
  return proc_pidinfo(pid, flavor, arg, buffer, size);
}

static int ___close_no_EINTR(int fd)
{
  int result;
  ++close_attempts;
  do { result = close(fd); } while (result < 0 && errno == EINTR);
  return result;
}

static int ___closefrom(int start)
{
  int fd, max = sysconf(_SC_OPEN_MAX);
  for (fd = start; fd < max; ++fd) ___close_no_EINTR(fd);
  return 0;
}

#define GB_PROC_PIDINFO probe_pidinfo
#include "darwin_fork_fd_probe.h"

struct result { int passed; unsigned long attempts; double seconds; };

static double now(void)
{
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts)) _exit(80);
  return ts.tv_sec + ts.tv_nsec / 1e9;
}

static int run_case(const char *name, int candidate, int dense, int high, int failure)
{
  int channel[2], status;
  struct result result;
  pid_t pid;
  ssize_t bytes;
  if (pipe(channel)) return 0;
  failure_mode = failure;
  pid = candidate ? gb_fork_with_fd_probe() : fork();
  if (pid < 0) return 0;
  if (pid == 0) {
    int nullfd, pair[2], i, start = channel[1] + 1;
    struct proc_fdinfo remaining[512];
    sigset_t mask, before_mask, after_mask;
    double began;
    sigfillset(&mask);
    if (sigprocmask(SIG_SETMASK, &mask, NULL)) _exit(81);
    if (sigprocmask(SIG_BLOCK, NULL, &before_mask)) _exit(89);
    close(channel[0]);
    nullfd = open("/dev/null", O_RDONLY);
    if (nullfd < 0) _exit(82);
    if (nullfd < start) {
      int newfd = fcntl(nullfd, F_DUPFD, start);
      if (newfd < start) _exit(83);
      close(nullfd);
      nullfd = newfd;
    }
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair)) _exit(84);
    for (i = 0; i < dense; ++i)
      if (fcntl(nullfd, F_DUPFD, start) < start) _exit(85);
    if (high && dup2(nullfd, 4096) != 4096) _exit(86);
    close_attempts = 0;
    began = now();
    if (candidate && gb_closefrom_fork_child(start) < 0) _exit(90);
    else if (candidate) { /* already closed by the candidate */ }
    else ___closefrom(start);
    result.seconds = now() - began;
    result.attempts = close_attempts;
    result.passed = fcntl(channel[1], F_GETFD) >= 0;
    if (sigprocmask(SIG_BLOCK, NULL, &after_mask) || before_mask != after_mask) result.passed = 0;
    errno = 0;
    if (fcntl(nullfd, F_GETFD) >= 0 || errno != EBADF) result.passed = 0;
    if (high) {
      errno = 0;
      if (fcntl(4096, F_GETFD) >= 0 || errno != EBADF) result.passed = 0;
    }
    bytes = proc_pidinfo(getpid(), PROC_PIDLISTFDS, 0, remaining, sizeof(remaining));
    if (bytes <= 0 || bytes >= (ssize_t) sizeof(remaining) || bytes % sizeof(remaining[0])) result.passed = 0;
    for (i = 0; bytes > 0 && i < (int) (bytes / sizeof(remaining[0])); ++i)
      if (remaining[i].proc_fd >= start) result.passed = 0;
    if (candidate && (dense || failure) && result.attempts < 100000) result.passed = 0;
    if (candidate && !dense && !failure && result.attempts > 16) result.passed = 0;
    if (write(channel[1], &result, sizeof(result)) != sizeof(result)) _exit(87);
    _exit(result.passed ? 0 : 88);
  }
  close(channel[1]);
  bytes = read(channel[0], &result, sizeof(result));
  close(channel[0]);
  if (waitpid(pid, &status, 0) != pid) return 0;
  if (bytes != sizeof(result) || !WIFEXITED(status) || WEXITSTATUS(status) || !result.passed) {
    fprintf(stderr, "CASE-FAIL %s status=%d bytes=%ld\n", name, status, (long) bytes);
    return 0;
  }
  printf("CASE-OK %s attempts=%lu closeSeconds=%.9f\n", name, result.attempts, result.seconds);
  fflush(stdout);
  return 1;
}

int main(void)
{
  if (!run_case("original sparse", 0, 0, 0, 0) ||
      !run_case("candidate sparse", 1, 0, 0, 0) ||
      !run_case("original high fd", 0, 0, 1, 0) ||
      !run_case("candidate high fd", 1, 0, 1, 0) ||
      !run_case("original dense", 0, 300, 0, 0) ||
      !run_case("candidate full-buffer fallback", 1, 300, 0, 0) ||
      !run_case("candidate permission/error fallback", 1, 0, 0, 1) ||
      !run_case("candidate malformed-result fallback", 1, 0, 0, 2)) return 1;
  puts("OK");
  return 0;
}
