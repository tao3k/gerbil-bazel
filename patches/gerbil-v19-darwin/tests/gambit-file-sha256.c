#if !defined(__APPLE__) || !defined(__MACH__) || !defined(__GNUC__) || defined(__clang__)
#error This experimental backend requires Darwin and GNU GCC.
#endif

#include <CommonCrypto/CommonDigest.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int file_digest(const char *path, unsigned char *digest) {
  unsigned char buffer[1024 * 1024];
  CC_SHA256_CTX context;
  struct stat status;
  int file = open(path, O_RDONLY);
  if (file < 0) return -1;
  if (fstat(file, &status) != 0) {
    int saved = errno;
    close(file);
    errno = saved;
    return -1;
  }
  if (!S_ISREG(status.st_mode)) {
    close(file);
    errno = EINVAL;
    return -1;
  }
  if (!CC_SHA256_Init(&context)) {
    close(file);
    errno = EIO;
    return -1;
  }
  for (;;) {
    ssize_t count = read(file, buffer, sizeof(buffer));
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) {
      int saved = errno;
      close(file);
      errno = saved;
      return -1;
    }
    if (count == 0) break;
    if (!CC_SHA256_Update(&context, buffer, (CC_LONG)count)) {
      close(file);
      errno = EIO;
      return -1;
    }
  }
  if (close(file) != 0) return -1;
  if (!CC_SHA256_Final(digest, &context)) {
    errno = EIO;
    return -1;
  }
  return 0;
}

int main(int argc, char **argv) {
  int raw = argc == 3 && strcmp(argv[1], "--raw") == 0;
  int start = raw ? 2 : 1;
  if (argc <= start) return 2;
  for (int index = start; index < argc; ++index) {
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    const char *path = argv[index];
    int escaped = !raw && (strchr(path, '\\') || strchr(path, '\n'));
    if (file_digest(path, digest) != 0) {
      fprintf(stderr, "gambit-file-sha256: %s: %s\n", path, strerror(errno));
      return 2;
    }
    if (escaped) putchar('\\');
    for (int byte = 0; byte < CC_SHA256_DIGEST_LENGTH; ++byte) printf("%02x", (unsigned int)digest[byte]);
    if (!raw) {
      printf("  ");
      for (const char *character = path; *character; ++character) {
        if (*character == '\\') printf("\\\\");
        else if (*character == '\n') printf("\\n");
        else putchar(*character);
      }
    }
    putchar('\n');
  }
  return fflush(stdout) == 0 && !ferror(stdout) ? 0 : 2;
}
