(c-declare "#include <stdio.h>\n#include <stdlib.h>")
(c-initialize "{
  const char *path = getenv(\"NATIVE_STAGE_MARKER\");
  FILE *port = path ? fopen(path, \"a\") : NULL;
  if (!port) abort();
  fputs(\"C\\n\", port);
  fclose(port);
}")

(define d1510-native-stage-value
  (begin
    (call-with-output-file
      (list path: (getenv "NATIVE_STAGE_MARKER") append: #t)
      (lambda (port) (display "SCHEME\n" port)))
    (list 'native-stage-value)))
