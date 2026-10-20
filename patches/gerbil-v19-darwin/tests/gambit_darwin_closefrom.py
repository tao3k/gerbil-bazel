"""Private Darwin FD enumeration candidate; retain the original fallback."""

GUARD = 'defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)'
ANCHOR = '\nint ___closefrom\n'
BRANCH = '''#else

  int max_fds;
  int fd;
'''
HELPER = '''
#if GUARD
#include <libproc.h>
#include <sys/proc_info.h>

static __attribute__((noinline)) int ___gb_darwin_close_open_fds (int start_fd)
{
  struct proc_fdinfo fds[4096];
  int bytes;
  int count;
  int i;

  if (start_fd < 0) return 0;
  bytes = proc_pidinfo (getpid (), PROC_PIDLISTFDS, 0, fds, sizeof (fds));
  /* A full buffer might omit descriptors. Never accept a partial inventory. */
  if (bytes <= 0 || bytes >= sizeof (fds) || bytes % sizeof (fds[0]) != 0)
    return 0;
  count = bytes / sizeof (fds[0]);
  for (i=0; i<count; i++)
    if (fds[i].proc_fd < 0) return 0;
  for (i=0; i<count; i++)
    if (fds[i].proc_fd >= start_fd)
      ___close_no_EINTR (fds[i].proc_fd);
  return 1;
}
#endif
'''.replace('GUARD', GUARD)


def transform(text):
    if text.count(ANCHOR) != 1 or '___gb_darwin_close_open_fds' in text:
        raise ValueError('one original closefrom boundary required')
    start = text.index(ANCHOR)
    end = text.index('\nint ___dup_no_EINTR', start)
    body = text[start:end]
    if body.count(BRANCH) != 1:
        raise ValueError('one original descriptor-scan fallback required')
    replacement = BRANCH + '\n#if ' + GUARD + '''
  if (___gb_darwin_close_open_fds (start_fd)) return 0;
#endif
'''
    return text[:start] + HELPER + body.replace(BRANCH, replacement, 1) + text[end:]
