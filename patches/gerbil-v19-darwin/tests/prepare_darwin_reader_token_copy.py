"""Fuse validation and private-string copy without early port state changes."""
from prepare_darwin_reader_whitespace import prepare as prepare_parent


OLD = '''      for (j=0; j<___arg5; ++j) {
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
      }'''
NEW = '''      int newline_count = 0, last_newline = -1;
      for (j=0; j<___arg5; ++j) {
        ___SCMOBJ ch = ___STRINGREF(___arg3,___FIX(start+j));
        unsigned code = ___ORD(ch);
        if (code >= 128 || ___VECTORREF(___arg2,___FIX(code)) != ___FAL) break;
        ___STRINGSET(___arg6,___FIX(___arg7+j),ch)
        if (___CHAREQP(ch,___CHR(10))) {
          ++newline_count;
          last_newline = j;
        }
      }
      if (j == ___arg5) {
        unsigned code = ___ORD(___STRINGREF(___arg3,___FIX(start+j)));
        if (code < 128 && ___VECTORREF(___arg2,___FIX(code)) != ___FAL) {
          if (newline_count) {
            ___PORT_CHAR_RCURLINE_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RCHARS_FIELD(___arg1),___FIX(start+last_newline+1));
            ___PORT_CHAR_RLINES_FIELD(___arg1) = ___FIXADD(___PORT_CHAR_RLINES_FIELD(___arg1),___FIX(newline_count));
          }
          ___PORT_CHAR_RLO_FIELD(___arg1) = ___FIX(start+___arg5);
          ___result = 1;
        }
      }'''


def prepare(text):
    source = prepare_parent(text)
    if source.count(OLD) != 1:
        raise ValueError('frozen token-copy boundary drift')
    return source.replace(OLD, NEW, 1)
