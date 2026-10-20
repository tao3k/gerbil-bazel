/* Diagnostic-only native process intervals; never installed in a release. */
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__)
#error Darwin GNU GCC required
#endif
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <spawn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;
static volatile sig_atomic_t child_pid;

static void forward_signal(int signal_number) {
  if (child_pid > 0) kill((pid_t)child_pid, signal_number);
}

static uint64_t now(void) {
  struct timespec value;
  if (clock_gettime(CLOCK_MONOTONIC, &value) != 0) return 0;
  return (uint64_t)value.tv_sec * 1000000000ULL + (uint64_t)value.tv_nsec;
}

static const char *role(int argc, char **argv) {
  const char *name = strrchr(argv[0], '/');
  name = name ? name + 1 : argv[0];
  if (!strcmp(name, "gsc")) {
    for (int i = 1; i < argc; ++i) {
      if (!strcmp(argv[i], "-link")) return "gsc-link";
      if (!strcmp(argv[i], "-obj")) return "gsc-object";
      if (!strcmp(argv[i], "-c")) return "gsc-codegen";
    }
    return "gsc-other";
  }
  for (int i = 1; i < argc; ++i)
    if (!strncmp(argv[i], "-print-", 7)) return "gcc-query";
  for (int i = 1; i < argc; ++i)
    if (!strcmp(argv[i], "-E")) return "gcc-preprocess";
  for (int i = 1; i < argc; ++i)
    if (!strcmp(argv[i], "-c")) return "gcc-object";
  return "gcc-link";
}

int main(int argc, char **argv) {
  if (argc == 2 && !strcmp(argv[1], "--clock")) {
    uint64_t value = now();
    if (!value) return 125;
    return printf("%llu\n", (unsigned long long)value) > 0 ? 0 : 125;
  }
  char metadata[PATH_MAX], target[PATH_MAX];
  if (argv[0][0] != '/' ||
      snprintf(metadata, sizeof(metadata), "%s.target", argv[0]) >= (int)sizeof(metadata)) return 125;
  int config = open(metadata, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  struct stat state;
  if (config < 0 || fstat(config, &state) != 0 || !S_ISREG(state.st_mode) ||
      state.st_uid != geteuid() || state.st_size < 2 || state.st_size >= PATH_MAX) return 125;
  ssize_t size = read(config, target, sizeof(target) - 1);
  close(config);
  if (size != state.st_size || target[size - 1] != '\n') return 125;
  target[size - 1] = 0;
  if (target[0] != '/' || strchr(target, '\n') || access(target, X_OK) != 0) return 125;
  const char *trace = getenv("GAMBIT_NATIVE_PHASE_TRACE");
  const char *label = role(argc, argv);
  argv[0] = target;
  if (!trace) { execv(target, argv); return 125; }
  int log = open(trace, O_WRONLY | O_APPEND | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0600);
  if (log < 0 || fstat(log, &state) != 0 || !S_ISREG(state.st_mode) ||
      state.st_uid != geteuid()) return 125;
  struct sigaction action;
  memset(&action, 0, sizeof(action));
  action.sa_handler = forward_signal;
  sigemptyset(&action.sa_mask);
  const int signals[] = {SIGTERM, SIGINT, SIGHUP, SIGQUIT};
  for (size_t i = 0; i < sizeof(signals) / sizeof(*signals); ++i)
    if (sigaction(signals[i], &action, NULL) != 0) return 125;
  uint64_t start = now();
  if (!start) return 125;
  sigset_t blocked, previous;
  sigemptyset(&blocked);
  for (size_t i = 0; i < sizeof(signals) / sizeof(*signals); ++i) sigaddset(&blocked, signals[i]);
  if (sigprocmask(SIG_BLOCK, &blocked, &previous) != 0) return 125;
  posix_spawnattr_t attributes;
  if (posix_spawnattr_init(&attributes) != 0) return 125;
  if (posix_spawnattr_setsigmask(&attributes, &previous) != 0 ||
      posix_spawnattr_setflags(&attributes, POSIX_SPAWN_SETSIGMASK) != 0) return 125;
  pid_t child;
  int launched = posix_spawn(&child, target, NULL, &attributes, argv, environ);
  posix_spawnattr_destroy(&attributes);
  if (launched) { sigprocmask(SIG_SETMASK, &previous, NULL); return 125; }
  child_pid = child;
  if (sigprocmask(SIG_SETMASK, &previous, NULL) != 0) { kill(child, SIGKILL); }
  struct rusage usage;
  int status;
  pid_t waited;
  do { waited = wait4(child, &status, 0, &usage); } while (waited < 0 && errno == EINTR);
  child_pid = 0;
  uint64_t end = now();
  if (waited != child || !end) return 125;
  int result = WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
  char row[256];
  int bytes = snprintf(row, sizeof(row), "1\t%d\t%d\t%s\t%llu\t%llu\t%d\t%ld.%06d\t%ld.%06d\n",
      (int)getpid(), (int)getppid(), label, (unsigned long long)start,
      (unsigned long long)end, result, (long)usage.ru_utime.tv_sec,
      (int)usage.ru_utime.tv_usec, (long)usage.ru_stime.tv_sec, (int)usage.ru_stime.tv_usec);
  if (bytes <= 0 || bytes >= (int)sizeof(row) || write(log, row, (size_t)bytes) != bytes) return 125;
  if (close(log) != 0) return 125;
  return result;
}
