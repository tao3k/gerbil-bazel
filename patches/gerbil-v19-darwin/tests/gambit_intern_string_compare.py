"""Private fixed-width string equality experiment, without intern-table changes."""

GUARD = ('defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && '
         '!defined(__clang__) && defined(___SINGLE_VM) && '
         'defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1)')


def transform(text):
    begin = text.index('___SCMOBJ ___find_symkey_from_scheme_string\n')
    end = text.index('\n}\n', begin) + 3
    function = text[begin:end]
    original = '''          for (i=0; i<n; i++)
            if (___STRINGREF(str,___FIX(i)) != ___STRINGREF(name,___FIX(i)))
              goto next;'''
    if function.count(original) != 1 or 'memcmp' in function:
        raise ValueError('exact original fixed-width string loop required')
    replacement = f'''#if {GUARD}
          if (memcmp(___BODY_AS(str,___tSTRING),
                     ___BODY_AS(name,___tSTRING),
                     ___CAST(___SIZE_T,n) * ___CS) != 0)
            goto next;
#else
{original}
#endif'''
    return text[:begin] + function.replace(original, replacement) + text[end:]
