#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
#include <libproc.h>
#include <signal.h>
#include <unistd.h>

#ifndef GB_FD_PROBE_CAPACITY
#define GB_FD_PROBE_CAPACITY 256
#endif
#ifndef GB_PROC_PIDINFO
#define GB_PROC_PIDINFO proc_pidinfo
#endif

/* Bind libproc before fork; never use the parent's FD snapshot in the child. */
static pid_t gb_fork_with_fd_probe(void)
{
  (void) GB_PROC_PIDINFO(getpid(), PROC_PIDLISTFDS, 0, NULL, 0);
  return fork();
}

/* Only called in the single-threaded fork child, after interrupt cleanup. */
static int gb_closefrom_fork_child(int start_fd)
{
  struct proc_fdinfo fds[GB_FD_PROBE_CAPACITY];
  sigset_t blocked, previous;
  int bytes, i, count, result, saved_errno;
  if (sigfillset(&blocked) || sigprocmask(SIG_BLOCK, &blocked, &previous))
    return ___closefrom(start_fd);
  bytes = GB_PROC_PIDINFO(getpid(), PROC_PIDLISTFDS, 0, fds, sizeof(fds));
  if (start_fd >= 0 && bytes > 0 && bytes < (int) sizeof(fds) &&
      bytes % sizeof(fds[0]) == 0) {
    count = bytes / sizeof(fds[0]);
    for (i = 0; i < count; ++i) {
      if (fds[i].proc_fd >= start_fd)
        ___close_no_EINTR(fds[i].proc_fd);
    }
    result = 0;
  } else {
    result = ___closefrom(start_fd);
  }
  saved_errno = errno;
  if (sigprocmask(SIG_SETMASK, &previous, NULL)) return -1;
  errno = saved_errno;
  return result;
}
#endif
