(cond-expand
 (darwin-gnu-reader-batch
  (define ##gb-darwin-token-scan
    (c-lambda (scheme-object scheme-object scheme-object scheme-object) int
#<<c-end
___result = 0;
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
{
  ___SCMOBJ mutex = ___PORT_MUTEX_FIELD(___arg1);
  if (___PRIMITIVETRYLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))) {
    if (___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3 && ___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4) {
      int start = ___INT(___arg4), end = ___INT(___PORT_CHAR_RHI_FIELD(___arg1)), n = 0;
      while (start+n < end && n < 256) {
        ___SCMOBJ ch = ___STRINGREF(___arg3,___FIX(start+n));
        unsigned code = ___ORD(ch);
        if (code >= 128) break;
        if (___VECTORREF(___arg2,___FIX(code)) != ___FAL) { ___result = n; break; }
        ++n;
      }
    }
    ___PRIMITIVEUNLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))
  }
}
#endif
c-end
))
  (define ##gb-darwin-token-copy
    (c-lambda (scheme-object scheme-object scheme-object scheme-object int scheme-object int) bool
#<<c-end
___result = 0;
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
{
  ___SCMOBJ mutex = ___PORT_MUTEX_FIELD(___arg1);
  if (___PRIMITIVETRYLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))) {
    int start = ___INT(___arg4), end = ___INT(___PORT_CHAR_RHI_FIELD(___arg1)), j;
    if (___arg5 > 0 && ___arg5 < 256 && ___arg7 >= 0 &&
        ___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3 && ___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4 &&
        start+___arg5 < end && ___INT(___STRINGLENGTH(___arg6)) == ___arg7+___arg5) {
      for (j=0; j<___arg5; ++j) {
        unsigned code = ___ORD(___STRINGREF(___arg3,___FIX(start+j)));
        if (code >= 128 || ___VECTORREF(___arg2,___FIX(code)) != ___FAL) break;
      }
      if (j == ___arg5) {
        unsigned code = ___ORD(___STRINGREF(___arg3,___FIX(start+j)));
        if (code < 128 && ___VECTORREF(___arg2,___FIX(code)) != ___FAL) {
          for (j=0; j<___arg5; ++j) {
            ___SCMOBJ ch = ___STRINGREF(___arg3,___FIX(start+j));
            ___STRINGSET(___arg6,___FIX(___arg7+j),ch)
            if (___CHAREQP(ch,___CHR(10))) {
              ___PORT_CHAR_RCURLINE_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RCHARS_FIELD(___arg1),___FIX(start+j+1));
              ___PORT_CHAR_RLINES_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RLINES_FIELD(___arg1),___FIX(1));
            }
          }
          ___PORT_CHAR_RLO_FIELD(___arg1) = ___FIX(start+___arg5);
          ___result = 1;
        }
      }
    }
    ___PRIMITIVEUNLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))
  }
}
#endif
c-end
))
  (define (##gb-darwin-buffered-token re c i)
    (##declare (not interrupts-enabled))
    (and (##fixnum? i) (##fx>= i 0) (##fx<= i 4096)
      (let* ((port (macro-readenv-port re))
             (table (macro-readtable-char-delimiter?-table (macro-readenv-readtable re)))
             (buffer (macro-character-port-rbuf port))
             (start (macro-character-port-rlo port))
             (n (##gb-darwin-token-scan port table buffer start)))
        (and (##fx> n 0)
          (let ((result (make-string (##fx+ i n) c)))
            (and (##gb-darwin-token-copy port table buffer start n result i) result)))))))
 (else))
