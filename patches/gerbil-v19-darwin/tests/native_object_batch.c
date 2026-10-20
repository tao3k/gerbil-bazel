/* Experimental request coordinator; retain every per-object content check. */
#include "gambit-static-object-base.c"

#include <pthread.h>
#include <limits.h>

struct batch_job {
  char *a[27];
  char *target, *target_proof, *lock, *directory, *pin, *environment;
  char *environment_data;
  char **child_environment;
  char child_environment_sha[65];
  char environment_sha[65], request_tools_sha[65];
  int locked, status;
};

struct batch_queue {
  struct batch_job *jobs;
  size_t count, next;
  pthread_mutex_t mutex;
};

static int copy_regular(const char *source, const char *target) {
  if (!regular_file(source)) return -1;
  FILE *out = fopen(target, "wb");
  if (!out) return -1;
  int failed = append_file(out, source) != 0;
  if (fclose(out) != 0) failed = 1;
  return failed ? -1 : 0;
}

static int canonical_source(const char *path) {
  char resolved[PATH_MAX];
  return path[0] == '/' && regular_file(path) && realpath(path, resolved) &&
         strcmp(path, resolved) == 0;
}

static int canonical_target(const char *path) {
  char resolved[PATH_MAX], *copy = strdup(path);
  if (!copy) return 0;
  char *slash = strrchr(copy, '/');
  int valid = slash && slash != copy && slash[1] &&
              strcmp(slash + 1, ".") && strcmp(slash + 1, "..");
  if (valid) {
    *slash = 0;
    valid = realpath(copy, resolved) && strcmp(copy, resolved) == 0 &&
            regular_or_absent(path);
  }
  free(copy);
  return valid;
}

static int compare_job_targets(const void *left, const void *right) {
  const struct batch_job *const *a = left, *const *b = right;
  return strcmp((*a)->target, (*b)->target);
}

static int same_tool_paths(char **a, char **b) {
  for (int i = 10; i <= 22; ++i)
    if ((i == 10 || i >= 16) && strcmp(a[i], b[i])) return 0;
  return 1;
}

static int compare_environment(const void *left, const void *right) {
  const char *const *a = left, *const *b = right;
  return strcmp(*a, *b);
}

static int environment_text_digest(char **environment, size_t count, char result[65]) {
  char **ordered = malloc((count + 1) * sizeof(*ordered));
  if (!ordered) return -1;
  memcpy(ordered, environment, count * sizeof(*ordered));
  qsort(ordered, count, sizeof(*ordered), compare_environment);
  CC_SHA256_CTX context;
  unsigned char digest[CC_SHA256_DIGEST_LENGTH];
  CC_SHA256_Init(&context);
  for (size_t i = 0; i < count; ++i) {
    CC_SHA256_Update(&context, ordered[i], (CC_LONG)strlen(ordered[i]));
    CC_SHA256_Update(&context, "\n", 1);
  }
  CC_SHA256_Final(digest, &context);
  for (int i = 0; i < CC_SHA256_DIGEST_LENGTH; ++i) sprintf(result + 2 * i, "%02x", digest[i]);
  result[64] = 0;
  free(ordered);
  return 0;
}

static int load_job_environment(struct batch_job *job) {
  if (!canonical_source(job->a[25]) || hex_digest(job->a[25], job->child_environment_sha) != 0) return -1;
  FILE *in = fopen(job->a[25], "rb");
  struct stat status;
  if (!in) return -1;
  if (fstat(fileno(in), &status) != 0 || status.st_size < 1 || status.st_size > 1024 * 1024) {
    fclose(in); return -1;
  }
  size_t size = (size_t)status.st_size;
  job->environment_data = malloc(size);
  if (!job->environment_data) { fclose(in); return -1; }
  int failed = fread(job->environment_data, 1, size, in) != size;
  if (fclose(in) != 0) failed = 1;
  if (failed || !same_digest(job->a[25], job->child_environment_sha)) return -1;
  size_t offset = 0, count = 0;
  while (offset < size) {
    char *entry = job->environment_data + offset;
    char *end = memchr(entry, 0, size - offset);
    if (!end || end == entry || !strchr(entry, '=') || entry[0] == '=' || strpbrk(entry, "\n\r")) return -1;
    char **grown = realloc(job->child_environment, (count + 2) * sizeof(*grown));
    if (!grown) return -1;
    job->child_environment = grown;
    size_t name_length = (size_t)(strchr(entry, '=') - entry);
    for (size_t i = 0; i < count; ++i) {
      size_t prior_length = (size_t)(strchr(grown[i], '=') - grown[i]);
      if (prior_length == name_length && !memcmp(entry, grown[i], name_length)) return -1;
    }
    grown[count++] = entry;
    grown[count] = NULL;
    offset = (size_t)(end - job->environment_data) + 1;
  }
  char expected[65];
  return environment_text_digest(job->child_environment, count, expected) == 0 &&
         !strcmp(expected, job->environment_sha) ? 0 : -1;
}

static int dump_environment(const char *raw_path, const char *text_path) {
  if (!canonical_target(raw_path) || !canonical_target(text_path) || !strcmp(raw_path, text_path)) return 2;
  int raw = open(raw_path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
  if (raw < 0) return 2;
  int text = open(text_path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
  if (text < 0) { close(raw); unlink(raw_path); return 2; }
  FILE *a = fdopen(raw, "wb"), *b = fdopen(text, "wb");
  if (!a || !b) {
    if (a) fclose(a); else close(raw);
    if (b) fclose(b); else close(text);
    unlink(raw_path); unlink(text_path); return 2;
  }
  size_t count = 0;
  while (environ[count]) ++count;
  char **ordered = malloc((count + 1) * sizeof(*ordered));
  if (!ordered) { fclose(a); fclose(b); return 2; }
  memcpy(ordered, environ, count * sizeof(*ordered));
  qsort(ordered, count, sizeof(*ordered), compare_environment);
  int failed = 0;
  for (size_t i = 0; i < count; ++i) {
    if (strpbrk(ordered[i], "\n\r")) { failed = 1; break; }
    size_t bytes = strlen(ordered[i]);
    if (fwrite(ordered[i], 1, bytes + 1, a) != bytes + 1 || fprintf(b, "%s\n", ordered[i]) < 0) {
      failed = 1; break;
    }
  }
  free(ordered);
  if (fclose(a) != 0) failed = 1;
  if (fclose(b) != 0) failed = 1;
  if (failed) { unlink(raw_path); unlink(text_path); }
  return failed ? 2 : 0;
}

static int batch_recipe_supported(char **a) {
  const char *denied[] = {" -M", " -B", " -save-temps", " -fprofile", " --coverage",
    " -g", " -fplugin", " -wrapper", " -specs", " --specs", " -fdump", " -fopt-info",
    " -S ", " -E ", " -o ", " @", " -ffile-prefix-map=", " -fmacro-prefix-map=",
    " -fdebug-prefix-map="};
  char *flags = NULL;
  if (asprintf(&flags, " %s %s %s %s %s ", a[11], a[12], a[13], a[14], a[24]) < 0) return 0;
  int supported = plain_flags(flags);
  for (size_t i = 0; i < sizeof(denied) / sizeof(*denied); ++i)
    if (strstr(flags, denied[i])) supported = 0;
  free(flags);
  char cwd[PATH_MAX], source[PATH_MAX], *spelled = NULL;
  if (!realpath(a[8], cwd) || strcmp(cwd, a[8]) ||
      asprintf(&spelled, "%s/%s", a[8], a[26]) < 0) return 0;
  int same_source = realpath(a[26][0] == '/' ? a[26] : spelled, source) && !strcmp(source, a[2]);
  free(spelled);
  return supported && same_source;
}

static int requested_tool_path(struct batch_job *job, const char *name, const char *expected, const char *phase) {
  char *label = NULL;
  if (asprintf(&label, "%s.%s", phase, name) < 0) return -1;
  char *out = child_path(job->directory, label), *err = NULL;
  free(label);
  if (asprintf(&err, "%s.stderr", out ? out : "") < 0 || !out) { free(out); free(err); return -1; }
  char *arguments[512], *option = NULL;
  int count = 0;
  if (!strcmp(name, "apple-as")) {
    arguments[count++] = "/usr/bin/xcrun";
    arguments[count++] = "--find";
    arguments[count++] = "as";
  } else {
    arguments[count++] = job->a[10];
    if (add_flags(arguments, &count, job->a[24], 0) != 0 ||
        asprintf(&option, "-print-prog-name=%s", name) < 0) { free(out); free(err); return -1; }
    arguments[count++] = option;
  }
  arguments[count] = NULL;
  int result = compile_object(arguments, out, err);
  if (result == 0 && empty_file(err)) {
    FILE *in = fopen(out, "rb");
    char path[PATH_MAX];
    if (!in || !fgets(path, sizeof(path), in)) result = -1;
    else {
      size_t bytes = strlen(path);
      if (bytes && path[bytes - 1] == '\n') path[--bytes] = 0;
      if (fgetc(in) != EOF) result = -1;
      else if (!strchr(path, '/')) {
        const char *search = NULL;
        for (char **entry = job->child_environment; *entry; ++entry)
          if (!strncmp(*entry, "PATH=", 5)) search = *entry + 5;
        result = -1;
        if (search) {
          char *copy = strdup(search), *state = NULL;
          for (char *part = copy ? strtok_r(copy, ":", &state) : NULL; part;
               part = strtok_r(NULL, ":", &state)) {
            /* Relative PATH lookup is not qualified by this protocol. */
            if (part[0] != '/') break;
            char *candidate = child_path(part, path);
            if (candidate && access(candidate, X_OK) == 0) {
              result = strcmp(candidate, expected) ? -1 : 0;
              free(candidate); break;
            }
            free(candidate);
          }
          free(copy);
        }
      } else result = strcmp(path, expected) ? -1 : 0;
    }
    if (in) fclose(in);
  } else result = -1;
  free(option); free(out); free(err);
  return result;
}

static int verify_request_tool_paths(struct batch_job *jobs, size_t count, const char *phase) {
  for (size_t i = 0; i < count; ++i) {
    size_t prior = 0;
    while (prior < i && !(same_tool_paths(jobs[prior].a, jobs[i].a) &&
           !strcmp(jobs[prior].a[8], jobs[i].a[8]) &&
           !strcmp(jobs[prior].a[24], jobs[i].a[24]) &&
           !strcmp(jobs[prior].child_environment_sha, jobs[i].child_environment_sha))) ++prior;
    if (prior < i) continue;
    gambit_static_compile_environment = jobs[i].child_environment;
    gambit_static_compile_directory = jobs[i].a[8];
    int valid = requested_tool_path(&jobs[i], "cc1", jobs[i].a[16], phase) == 0 &&
                requested_tool_path(&jobs[i], "as", jobs[i].a[17], phase) == 0 &&
                requested_tool_path(&jobs[i], "apple-as", jobs[i].a[18], phase) == 0;
    gambit_static_compile_environment = NULL;
    gambit_static_compile_directory = NULL;
    if (!valid) return -1;
  }
  return 0;
}

static void *batch_worker(void *data) {
  struct batch_queue *queue = data;
  for (;;) {
    pthread_mutex_lock(&queue->mutex);
    size_t index = queue->next++;
    pthread_mutex_unlock(&queue->mutex);
    if (index >= queue->count) return NULL;
    gambit_static_compile_environment = queue->jobs[index].child_environment;
    gambit_static_compile_directory = queue->jobs[index].a[8];
    gambit_static_source_display = queue->jobs[index].a[26];
    queue->jobs[index].status = capture(25, queue->jobs[index].a);
    gambit_static_compile_environment = NULL;
    gambit_static_compile_directory = NULL;
    gambit_static_source_display = NULL;
  }
}

static int capture_batch(const char *manifest, const char *directory, int workers) {
  int result = 2, descriptor = -1;
  char *buffer = NULL, manifest_sha[65];
  struct batch_job *jobs = NULL, **ordered = NULL;
  size_t count = 0;
  if (workers < 1 || workers > 256 || !canonical_source(manifest) ||
      hex_digest(manifest, manifest_sha) != 0) return 2;
  descriptor = open(manifest, O_RDONLY | O_NOFOLLOW);
  struct stat status;
  if (descriptor < 0 || fstat(descriptor, &status) != 0 || status.st_size < 1 ||
      status.st_size > 16 * 1024 * 1024) goto done;
  size_t size = (size_t)status.st_size, offset = 0;
  buffer = malloc(size);
  if (!buffer) goto done;
  while (offset < size) {
    ssize_t bytes = read(descriptor, buffer + offset, size - offset);
    if (bytes < 0 && errno == EINTR) continue;
    if (bytes <= 0) goto done;
    offset += (size_t)bytes;
  }
  close(descriptor); descriptor = -1;
  const char old_magic[] = "gambit-native-object-batch-v1";
  if (size >= sizeof(old_magic) && !memcmp(buffer, old_magic, sizeof(old_magic))) {
    result = 77; goto done;
  }
  const char v2_magic[] = "gambit-native-object-batch-v2";
  if (size >= sizeof(v2_magic) && !memcmp(buffer, v2_magic, sizeof(v2_magic))) {
    result = 77; goto done;
  }
  const char magic[] = "gambit-native-object-batch-v3";
  if (size <= sizeof(magic) || memcmp(buffer, magic, sizeof(magic))) goto done;
  offset = sizeof(magic);
  while (offset < size) {
    if (count >= 4096) goto done;
    struct batch_job *grown = realloc(jobs, (count + 1) * sizeof(*jobs));
    if (!grown) goto done;
    jobs = grown;
    struct batch_job *job = &jobs[count++];
    memset(job, 0, sizeof(*job));
    for (int i = 0; i < 27; ++i) {
      char *end = memchr(buffer + offset, 0, size - offset);
      if (!end) goto done;
      job->a[i] = buffer + offset;
      offset = (size_t)(end - buffer) + 1;
    }
    if (strcmp(job->a[1], "--capture") || !batch_recipe_supported(job->a) || !canonical_source(job->a[2]) ||
        !canonical_target(job->a[3]) || !canonical_source(job->a[9]) ||
        strlen(job->a[6]) != 64 || !same_digest(job->a[2], job->a[6])) goto done;
    job->target = job->a[3];
    job->environment = job->a[9];
    if (hex_digest(job->environment, job->environment_sha) != 0) goto done;
    if (load_job_environment(job) != 0) goto done;
    if (asprintf(&job->target_proof, "%s.gambit-static-proof", job->target) < 0 ||
        asprintf(&job->lock, "%s.gambit-static-lock", job->target) < 0 ||
        !regular_or_absent(job->target_proof)) goto done;
  }
  if (!count || !same_digest(manifest, manifest_sha)) goto done;
  ordered = malloc(count * sizeof(*ordered));
  if (!ordered) goto done;
  for (size_t i = 0; i < count; ++i) ordered[i] = &jobs[i];
  qsort(ordered, count, sizeof(*ordered), compare_job_targets);
  for (size_t i = 1; i < count; ++i)
    if (!strcmp(ordered[i - 1]->target, ordered[i]->target)) goto done;
  for (size_t i = 0; i < count; ++i) {
    if (!strcmp(jobs[i].target, manifest)) goto done;
    for (size_t j = 0; j < count; ++j) {
      if (!strcmp(jobs[i].target, jobs[j].a[2]) ||
          !strcmp(jobs[i].target, jobs[j].a[9]) ||
          !strcmp(jobs[i].target, jobs[j].a[25]) ||
          !strcmp(jobs[i].target_proof, jobs[j].target)) goto done;
      for (int k = 10; k <= 22; ++k)
        if ((k == 10 || k >= 16) && !strcmp(jobs[i].target, jobs[j].a[k])) goto done;
    }
  }
  /* The same ordering is used even when two callers supply reverse manifests. */
  for (size_t i = 0; i < count; ++i) {
    for (int attempt = 0; mkdir(ordered[i]->lock, 0700) != 0; ++attempt) {
      if (errno != EEXIST || attempt >= 999) goto done;
      struct timespec delay = {0, 10000000};
      nanosleep(&delay, NULL);
    }
    ordered[i]->locked = 1;
  }
  if (mkdir(directory, 0700) != 0) goto done;
  for (size_t i = 0; i < count; ++i) {
    struct batch_job *job = &jobs[i];
    char *object = NULL, *proof = NULL, *environment = NULL;
    if (asprintf(&job->directory, "%s/job-%zu", directory, i) < 0 ||
        mkdir(job->directory, 0700) != 0 ||
        asprintf(&job->pin, "%s.gambit-batch.XXXXXX", job->a[2]) < 0) goto done;
    int pin = mkstemp(job->pin);
    if (pin < 0) goto done;
    close(pin);
    object = child_path(job->directory, "selected.o");
    environment = child_path(job->directory, "environment");
    if (!object || asprintf(&proof, "%s.gambit-static-proof", object) < 0) goto done;
    if (!environment || copy_regular(job->environment, environment) != 0 ||
        !same_digest(environment, job->environment_sha)) goto done;
    if (regular_file(job->target) && copy_regular(job->target, object) != 0) goto done;
    if (regular_file(job->target_proof) && copy_regular(job->target_proof, proof) != 0) goto done;
    job->a[3] = object;
    job->a[4] = job->directory;
    job->a[5] = job->pin;
    job->a[9] = environment;
    free(proof);
  }
  /* Discovery must use the same explicit environment as the actual compiler. */
  if (verify_request_tool_paths(jobs, count, "resolve") != 0) goto done;
  struct batch_queue queue = {jobs, count, 0, PTHREAD_MUTEX_INITIALIZER};
  pthread_t threads[256];
  pthread_attr_t attributes;
  if (pthread_attr_init(&attributes) != 0) goto done;
  /* The retained digest implementation uses a 1 MiB stack buffer. */
  if (pthread_attr_setstacksize(&attributes, 4 * 1024 * 1024) != 0) {
    pthread_attr_destroy(&attributes); goto done;
  }
  int launched = 0, launch_failed = 0;
  for (; launched < workers && (size_t)launched < count; ++launched)
    if (pthread_create(&threads[launched], &attributes, batch_worker, &queue) != 0) {
      launch_failed = 1; break;
    }
  pthread_attr_destroy(&attributes);
  for (int i = 0; i < launched; ++i) pthread_join(threads[i], NULL);
  pthread_mutex_destroy(&queue.mutex);
  if (launch_failed || !same_digest(manifest, manifest_sha)) goto done;
  if (verify_request_tool_paths(jobs, count, "final") != 0) goto done;
  /* No public target is changed by a partial compile failure. */
  size_t tool_sets = 0;
  for (size_t i = 0; i < count; ++i) {
    struct batch_job *job = &jobs[i];
    if (job->status != 0 || !same_digest(job->a[2], job->a[6]) ||
        !canonical_target(job->target) || !regular_or_absent(job->target_proof) ||
        !same_digest(job->environment, job->environment_sha) ||
        !same_digest(job->a[25], job->child_environment_sha) ||
        !same_digest(job->a[9], job->environment_sha)) goto done;
    char *after = child_path(job->directory, "tools.request-complete");
    char *before = child_path(job->directory, "tools.before");
    char *tools[] = {job->a[10], job->a[16], job->a[17], job->a[18],
                    job->a[19], job->a[20], job->a[21], job->a[22]};
    char expected[65];
    if (!after || !before || hex_digest(before, expected) != 0) goto done;
    size_t prior = 0;
    while (prior < i && !same_tool_paths(jobs[prior].a, job->a)) ++prior;
    if (prior < i) memcpy(job->request_tools_sha, jobs[prior].request_tools_sha, 65);
    else {
      if (tools_digest(after, tools) != 0 || hex_digest(after, job->request_tools_sha) != 0) goto done;
      ++tool_sets;
    }
    if (strcmp(expected, job->request_tools_sha)) goto done;
    free(after); free(before);
  }
  for (size_t i = 0; i < count; ++i) {
    struct batch_job *job = &jobs[i];
    char *proof = NULL;
    if (asprintf(&proof, "%s.gambit-static-proof", job->a[3]) < 0 ||
        rename(job->a[3], job->target) != 0 || rename(proof, job->target_proof) != 0) {
      free(proof); goto done;
    }
    free(proof);
  }
  puts("GAMBIT-STATIC-OBJECT-BATCH-COMMIT");
  printf("GAMBIT-STATIC-OBJECT-BATCH-TOOL-SETS %zu\n", tool_sets);
  result = 0;
done:
  if (descriptor >= 0) close(descriptor);
  for (size_t i = 0; i < count; ++i) {
    if (jobs[i].pin) unlink(jobs[i].pin);
    if (jobs[i].locked) rmdir(jobs[i].lock);
    free(jobs[i].target_proof); free(jobs[i].lock);
    free(jobs[i].directory); free(jobs[i].pin);
    free(jobs[i].child_environment); free(jobs[i].environment_data);
  }
  free(ordered); free(jobs); free(buffer);
  if (result != 0) fputs("GAMBIT-STATIC-OBJECT-BATCH-DENY\n", stderr);
  return result;
}

int main(int argc, char **argv) {
  if (argc == 4 && !strcmp(argv[1], "--dump-environment")) {
    const char *enabled = getenv("GAMBIT_DARWIN_NATIVE_OBJECT_BATCH");
    if (!enabled || strcmp(enabled, "1")) return 77;
    return dump_environment(argv[2], argv[3]);
  }
  if (argc > 1 && !strcmp(argv[1], "--batch")) {
    const char *enabled = getenv("GAMBIT_DARWIN_NATIVE_OBJECT_BATCH");
    if (argc != 5 || !enabled || strcmp(enabled, "1")) return 77;
    char *end;
    long workers = strtol(argv[4], &end, 10);
    if (*end || workers < 1 || workers > 256) return 2;
    return capture_batch(argv[2], argv[3], (int)workers);
  }
  return capture_single_main(argc, argv);
}
