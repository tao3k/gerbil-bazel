(cond-expand
 (darwin-gnu-reader-batch
  (define ##gb-darwin-span-scan
    (c-lambda (scheme-object scheme-object scheme-object scheme-object int) int
#<<c-end
___result = 0;
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
{
  ___SCMOBJ mutex = ___PORT_MUTEX_FIELD(___arg1);
  if (___PRIMITIVETRYLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))) {
    if (___arg5 > 0 && ___arg5 <= 512 &&
        ___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3 && ___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4) {
      int start = ___INT(___arg4), end = ___INT(___PORT_CHAR_RHI_FIELD(___arg1)), n = 0;
      unsigned close = ___ORD(___arg2);
      while (start+n < end && n < ___arg5) {
        unsigned code = ___ORD(___STRINGREF(___arg3,___FIX(start+n)));
        if (code >= 128 || code == close || code == 92 || code == 10) break;
        ++n;
      }
      ___result = n;
    }
    ___PRIMITIVEUNLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))
  }
}
#endif
c-end
))
  (define ##gb-darwin-span-copy
    (c-lambda (scheme-object scheme-object scheme-object scheme-object int scheme-object) bool
#<<c-end
___result = 0;
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
{
  ___SCMOBJ mutex = ___PORT_MUTEX_FIELD(___arg1);
  if (___PRIMITIVETRYLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))) {
    int start = ___INT(___arg4), end = ___INT(___PORT_CHAR_RHI_FIELD(___arg1)), j;
    unsigned close = ___ORD(___arg2);
    if (___arg5 > 0 && ___arg5 <= 512 &&
        ___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3 && ___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4 &&
        start+___arg5 <= end && ___INT(___STRINGLENGTH(___arg6)) == ___arg5) {
      for (j=0; j<___arg5; ++j) {
        unsigned code = ___ORD(___STRINGREF(___arg3,___FIX(start+j)));
        if (code >= 128 || code == close || code == 92 || code == 10) break;
      }
      if (j == ___arg5) {
        for (j=0; j<___arg5; ++j) {
          ___STRINGSET(___arg6,___FIX(j),___STRINGREF(___arg3,___FIX(start+j)))
        }
        ___PORT_CHAR_RLO_FIELD(___arg1) = ___FIX(start+___arg5);
        ___result = 1;
      }
    }
    ___PRIMITIVEUNLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))
  }
}
#endif
c-end
))
  (define (##gb-darwin-buffered-span re close remaining)
    (##declare (not interrupts-enabled))
    (and (##char? close) (##fixnum? remaining) (##fx> remaining 0) (##fx<= remaining 512)
      (let* ((port (macro-readenv-port re))
             (buffer (macro-character-port-rbuf port))
             (start (macro-character-port-rlo port))
             (n (##gb-darwin-span-scan port close buffer start remaining)))
        (and (##fx> n 0)
          (let ((result (##make-string n)))
            (and (##gb-darwin-span-copy port close buffer start n result) result)))))))
 (else))
