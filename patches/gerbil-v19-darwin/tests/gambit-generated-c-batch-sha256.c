/* Experimental transport extension; the frozen digest implementation is unchanged. */
#define main single_digest_main
#include "gambit-file-sha256.c"
#undef main

int main(int argc, char **argv) {
  if (argc < 2 || strcmp(argv[1], "--raw-many") != 0)
    return single_digest_main(argc, argv);
  if (argc < 3) return 2;
  for (int index = 2; index < argc; ++index) {
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    if (file_digest(argv[index], digest) != 0) {
      fprintf(stderr, "gambit-file-sha256: %s: %s\n", argv[index], strerror(errno));
      return 2;
    }
    for (int byte = 0; byte < CC_SHA256_DIGEST_LENGTH; ++byte)
      printf("%02x", (unsigned int)digest[byte]);
    putchar('\n');
  }
  return fflush(stdout) == 0 && !ferror(stdout) ? 0 : 2;
}
