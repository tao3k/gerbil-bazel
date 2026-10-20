"""Private Darwin/GNU RTS candidate; no lookup cache or new probe policy."""

GUARD = 'defined(__APPLE__) && defined(__aarch64__) && defined(__GNUC__) && (__GNUC__ >= 16) && !defined(__clang__)'


def transform(text):
    moved = '''  if (!___FIXZEROP(___FIXAND(___GCHASHTABLE_FLAGS_FIELD(ht),
                             ___FIX(___GCHASHTABLE_FLAG_KEY_MOVED))))
    gc_hash_table_rehash_in_situ (ht);'''
    for name, args in [('ref', 'ht, key'), ('set', 'ht, key, val')]:
        begin = text.index('___SCMOBJ ___gc_hash_table_' + name + '\n')
        end = text.index('\n}\n', begin) + 3
        function = text[begin:end]
        if function.count(moved) != 1:
            raise ValueError('exact original hash rehash boundary required')
        parameters = '___SCMOBJ ht, ___SCMOBJ key' + (', ___SCMOBJ val' if name == 'set' else '')
        helper = 'gb_gc_hash_' + name + '_moved'
        declaration = f'''#if {GUARD}
static ___SCMOBJ __attribute__((noinline, cold)) {helper}({parameters});
#endif

'''
        replacement = moved.replace('    gc_hash_table_rehash_in_situ (ht);',
            f'''    {{
#if {GUARD}
      __attribute__((musttail)) return {helper}({args});
#else
      gc_hash_table_rehash_in_situ (ht);
#endif
    }}''')
        definition = f'''
#if {GUARD}
static ___SCMOBJ __attribute__((noinline, cold))
{helper}({parameters})
{{
  gc_hash_table_rehash_in_situ (ht);
  __attribute__((musttail)) return ___gc_hash_table_{name}({args});
}}
#endif
'''
        text = text[:begin] + declaration + function.replace(moved, replacement) + definition + text[end:]
    return text
