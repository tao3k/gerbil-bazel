;; Experimental in-process digest bridge; no global backend replacement.
(c-declare #<<c-end
#define main gambit_digest_unused_main
#include "gambit-file-sha256.c"
#undef main
c-end
)

(define generation-native-file-sha
  (let ((digest-into!
         (c-lambda (char-string scheme-object) int
#<<c-end
unsigned char digest[CC_SHA256_DIGEST_LENGTH];
if (file_digest(___arg1, digest) != 0) {
  ___result = errno ? errno : EIO;
} else {
  for (int i = 0; i < CC_SHA256_DIGEST_LENGTH; ++i)
    ___U8VECTORSET(___arg2, ___FIX(i), ___FIX(digest[i]));
  ___result = 0;
}
c-end
)))
   (lambda (path)
  (let* ((bytes (make-u8vector 32 0))
         (status (digest-into! path bytes)))
    (if (not (= status 0)) (error "native generation digest failed" path status))
    (let ((hex "0123456789abcdef") (result (make-string 64 #\0)))
      (let loop ((index 0))
        (if (= index 32) result
            (let ((byte (u8vector-ref bytes index)))
              (string-set! result (* index 2) (string-ref hex (quotient byte 16)))
              (string-set! result (+ (* index 2) 1) (string-ref hex (modulo byte 16)))
              (loop (+ index 1))))))))))
