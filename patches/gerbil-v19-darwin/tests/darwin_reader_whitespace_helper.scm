(cond-expand
 (darwin-gnu-reader-batch
  (define ##gb-darwin-whitespace-skip
    (c-lambda (scheme-object scheme-object scheme-object) int
#<<c-end
___result = 0;
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
{
  ___SCMOBJ mutex = ___PORT_MUTEX_FIELD(___arg1);
  if (___PRIMITIVETRYLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))) {
    ___SCMOBJ buffer = ___PORT_CHAR_RBUF_FIELD(___arg1);
    ___SCMOBJ start = ___INT(___PORT_CHAR_RLO_FIELD(___arg1));
    ___SCMOBJ end = ___INT(___PORT_CHAR_RHI_FIELD(___arg1));
    int n = 0;
    while (start+n < end && n < 4096) {
      unsigned code = ___ORD(___STRINGREF(buffer,___FIX(start+n)));
      if (code >= 128 || ___VECTORREF(___arg2,___FIX(code)) != ___arg3) break;
      ++n;
      if (code == 10) {
        ___PORT_CHAR_RCURLINE_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RCHARS_FIELD(___arg1),___FIX(start+n));
        ___PORT_CHAR_RLINES_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RLINES_FIELD(___arg1),___FIX(1));
      }
    }
    ___PORT_CHAR_RLO_FIELD(___arg1) = ___FIX(start+n);
    ___result = n;
    ___PRIMITIVEUNLOCK(mutex,___FIX(___OBJ_LOCK1),___FIX(___OBJ_LOCK2))
  }
}
#endif
c-end
))
  (define (##gb-darwin-buffered-whitespace re)
    (##declare (not interrupts-enabled))
    (##gb-darwin-whitespace-skip
     (macro-readenv-port re)
     (macro-readtable-char-handler-table (macro-readenv-readtable re))
     ##read-whitespace)))
 (else))
