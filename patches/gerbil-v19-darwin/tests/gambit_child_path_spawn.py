"""Private Darwin/GNU child-PATH candidate; not a production patch."""

HELPER = r'''
#if defined(USE_DARWIN_POSIX_SPAWN) && defined(__GNUC__) && !defined(__clang__)
#include <paths.h>
static int gb_child_path_spawn(pid_t *pid, const char *name,
                               posix_spawn_file_actions_t *actions,
                               posix_spawnattr_t *attributes,
                               char **argv, char **env)
{
  const char *path = NULL, *start;
  size_t name_length = strlen(name);
  int i, denied = 0, result = ENOENT;
  if (!name_length) return ENOENT;
  for (i = 0; env[i] != NULL; i++)
    if (!strncmp(env[i], "PATH=", 5)) { path = env[i] + 5; break; }
  if (path == NULL) path = _PATH_DEFPATH;
  start = path;
  for (;;)
    {
      const char *end = strchr(start, ':');
      size_t length = end != NULL ? (size_t)(end - start) : strlen(start);
      char *candidate;
      if (length > (size_t)-1 - name_length - 2) return ENAMETOOLONG;
      candidate = ___ALLOC_MEM(length + name_length + 2);
      if (candidate == NULL) return ENOMEM;
      memcpy(candidate, start, length);
      if (length) candidate[length++] = '/';
      memcpy(candidate + length, name, name_length + 1);
      do result = posix_spawn(pid, candidate, actions, attributes, argv, env);
      while (result == EINTR);
      ___FREE_MEM(candidate);
      if (result == 0) return 0;
      if (result == EACCES) denied = 1;
      else if (result != ENOENT && result != ENOTDIR) return result;
      if (end == NULL) break;
      start = end + 1;
    }
  return denied ? EACCES : result;
}
#endif

'''


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('exact original process source anchor required')
    return source.replace(old, new, 1)


def transform(source):
    source = once(source, '___SCMOBJ ___device_stream_setup_from_process\n',
                  HELPER + '___SCMOBJ ___device_stream_setup_from_process\n')
    source = once(source, '''      if (argv[0][n] == 0)
        use_posix_spawn = 0;''', '''      if (argv[0][n] == 0)
        {
#if !defined(__GNUC__) || defined(__clang__)
          use_posix_spawn = 0;
#endif
        }''')
    call = '''                  posix_spawnp (&pid,
                                argv[0],
                                &actions,
                                &attributes,
                                argv,
                                env != NULL ? env : environ);'''
    source = once(source, call, '''#if defined(__GNUC__) && !defined(__clang__)
                  env != NULL && strchr(argv[0], '/') == NULL
                  ? gb_child_path_spawn(&pid, argv[0], &actions, &attributes, argv, env)
                  :
#endif
''' + call)
    source = once(source, '''              if (spawn_errno != 0)
                {''', '''#if defined(__GNUC__) && !defined(__clang__)
              /* Keep execvp's shell fallback and unusual path errors intact. */
              if (env != NULL && strchr(argv[0], '/') == NULL &&
                  (spawn_errno == ENOEXEC || spawn_errno == ENAMETOOLONG))
                goto gb_child_path_fork;
#endif
              if (spawn_errno != 0)
                {''')
    return once(source, '''          else
#endif
          if ((pid = fork ()) < 0)''', '''          else
#endif
#if defined(USE_DARWIN_POSIX_SPAWN) && defined(__GNUC__) && !defined(__clang__)
gb_child_path_fork:
#endif
          if ((pid = fork ()) < 0)''')
