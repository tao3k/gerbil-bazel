"""Prototype caching of na through the existing GVM D/R/W state protocol."""
import re

GUARD = ('defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && '
    'defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && '
    'defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && '
    '!defined(___DYNAMIC) && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && '
    '!defined(___DEBUG_STACK_LIMIT)')
NAMES = ('___SET_NARGS', '___IF_NARGS_EQ', '___GET_REST', '___GET_KEY',
    '___GET_REST_KEY', '___GET_KEY_REST')


def nargs_macro_definitions(header):
    result = []
    lines = header.splitlines(keepends=True)
    for name in NAMES:
        starts = [i for i, line in enumerate(lines) if line.startswith('#define '+name+'(')]
        if len(starts) != 1:
            raise ValueError('exact original arity macro required: '+name)
        index = starts[0]
        macro = lines[index]
        while lines[index].rstrip().endswith('\\'):
            index += 1
            macro += lines[index]
        if macro.count('___ps->na') != 1:
            raise ValueError('original arity state access changed: '+name)
        result.append('#undef '+name+'\n'+macro.replace('___ps->na', 'gb_nargs'))
    return ''.join(result)


def inject_nargs_register(code, header):
    anchor = '#undef ___MH_PROC\n#define ___MH_PROC gb_coalesced_host'
    if code.count(anchor) != 1 or code.count('___BEGIN_M_COD') != 1 or code.count('___END_M_COD') != 1:
        raise ValueError('one selected coalesced host required')
    if 'gb_nargs' in code:
        raise ValueError('already injected')
    begin = code.index('___BEGIN_M_COD')
    end = code.index('___END_M_COD', begin)
    body = code[begin:end]
    direct_reads = len(re.findall(r'___ps->na\b', body))
    if direct_reads != 14 or re.search(r'___ps->na\s*=', body):
        raise ValueError('original 14 caller reads with no raw writes required')
    # Only experimental source is changed. Other platforms keep original accesses.
    body = re.sub(r'___ps->na\b', 'GB_NARGS_CURRENT', body)
    code = code[:begin] + body + code[end:]
    counts = {}
    for kind in ('D', 'R', 'W'):
        pattern = re.compile(r'^(#define ___M'+kind+r'_ALL [^\n]*)$', re.M)
        code, counts[kind] = pattern.subn(r'\1 GB_NARGS_'+kind, code)
        if not counts[kind]:
            raise ValueError('missing existing state protocol: '+kind)
    prefix = ('\n#if '+GUARD+'\n'
        '#define GB_NARGS_D ___WORD gb_nargs;\n'
        '#define GB_NARGS_R gb_nargs=___ps->na;\n'
        '#define GB_NARGS_W ___ps->na=gb_nargs;\n'
        '#define GB_NARGS_CURRENT gb_nargs\n'
        +nargs_macro_definitions(header)+
        '#else\n#define GB_NARGS_D\n#define GB_NARGS_R\n#define GB_NARGS_W\n'
        '#define GB_NARGS_CURRENT ___ps->na\n#endif\n')
    return code.replace(anchor, prefix+anchor, 1), dict(stateProtocolDefinitions=counts,
        callerReads=direct_reads, scope='nargs-register-state-protocol-envelope-not-admitted')
