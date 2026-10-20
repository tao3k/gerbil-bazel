"""Private two-word copy specialization; forwarding and scanning are unchanged."""

GUARD = ('defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && '
         '!defined(__clang__) && defined(___SINGLE_VM) && '
         'defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && '
         '(___WS == 8) && !defined(___USE_HANDLES)')


def transform(text):
    original = '''                while (words > 0)
                  {
                    *alloc++ = *body++;
                    words--;
                  }'''
    begin = text.index('___HIDDEN void mark_array\n')
    end = text.index('___HIDDEN void mark_captured_continuation\n', begin)
    body = text[begin:end]
    if body.count(original) != 1 or 'GB_TWO_WORD_COPY' in body:
        raise ValueError('one original movable-object copy loop required')
    replacement = f'''#if {GUARD}
                /* GB_TWO_WORD_COPY: retain sequential read/write ordering. */
                if (words == 2)
                  {{
                    alloc[0] = body[0];
                    alloc[1] = body[1];
                    alloc += 2;
                    body += 2;
                    words = 0;
                  }}
                else
#endif
{original}'''
    return text[:begin] + body.replace(original, replacement) + text[end:]
