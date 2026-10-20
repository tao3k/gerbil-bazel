"""Experimental host-local procedure-binding facts, never table/type results."""
import re

GUARD = ('defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && '
    'defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && '
    'defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && '
    '(___NB_ARG_REGS == 3) && !defined(___DYNAMIC) && '
    '!defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)')
PAIR = re.compile(
    r'___WORD (gb_t\d+)=\((GB_TRACE_GLO\(\w+,\d+,___G_\w+\))\);\n'
    r'if \(!\(\1==(\(gb_m\d+___lp\+\(\d+\*___LABEL_SIZE\*___WS\)\))\)\) '
    r'goto (gb_native_miss|gb_trace_miss_\d+);')


def mutation_hooks(header):
    rows = []
    for name in ('___SET_GLO', '___GLOBALVARSET', '___GLOBALVARPRIMSET'):
        found = re.findall(r'^#define '+name+r'(\([^\n]+)$', header, re.M)
        if len(found) != 1 or found[0].endswith('\\'):
            raise ValueError('single-line original binding mutation required: '+name)
        parameters, body = found[0].split(')', 1)
        rows.append('#undef '+name+'\n#define '+name+parameters+') '
            'do { '+body+' gb_binding_mask=0; } while (0);\n')
    return ''.join(rows)


def inject_binding_facts(code, header, diagnostic=False):
    if 'GB_BIND_VALUE' in code:
        raise ValueError('already injected')
    anchor = '#undef ___MH_PROC\n#define ___MH_PROC gb_coalesced_host'
    if code.count(anchor) != 1 or code.count('___BEGIN_M_COD') != 1 or code.count('___END_M_COD') != 1:
        raise ValueError('one original coalesced host required')
    if '___BEGIN_CFUN' in code or '___CFUN_OOL' in code:
        raise ValueError('opaque foreign bodies need separate admission')
    guards = []
    def transform(block, mask):
        def replace(match):
            index = len(guards)
            if index >= 64:
                raise ValueError('binding fact capacity exceeded')
            guards.append(dict(index=index, expression=match[2], expected=match[3], miss=match[4]))
            return ('___WORD '+match[1]+'=GB_BIND_VALUE('+mask+','+str(index)+','
                +match[2]+','+match[3]+');\n'+match[0].split('\n', 1)[1])
        return PAIR.sub(replace, block)
    for site in (7, 11):
        start = code.index('static int __attribute__((noinline,optimize("O3"))) gb_trace_native_'+str(site)+'(')
        end = code.index('\n}\n#endif', start)+2
        block = transform(code[start:end], '(*gb_binding_mask)')
        param = 'struct gb_trace_native_'+str(site)+'_result *out) {'
        if block.count(param) != 1:
            raise ValueError('original native helper signature changed')
        block = block.replace(param, param.replace(') {', ',unsigned long long *gb_binding_mask) {'))
        code = code[:start]+block+code[end:]
        pattern = re.compile(r'(int gb_native_status=gb_trace_native_'+str(site)+r'\([^\n]+,&gb_native_result)\);')
        code, count = pattern.subn(r'\1,&gb_binding_mask);', code)
        if count != 1:
            raise ValueError('one native caller required')
    code = transform(code, 'gb_binding_mask')
    if len(guards) < 14:
        raise ValueError('selected guarded-trace binding envelope required')
    for kind in ('D', 'R'):
        pattern = re.compile(r'^(#define ___M'+kind+r'_ALL [^\n]*)$', re.M)
        code, count = pattern.subn(r'\1 GB_BIND_'+kind, code)
        if count != 23:
            raise ValueError('all 23 original state definitions required')
    event = ('extern unsigned long long gb_diag_attempts[16],gb_diag_hits[16];\n'
        '#define GB_BIND_EVENT(hit) (++gb_diag_attempts[0],gb_diag_hits[0]+=(hit))\n'
        if diagnostic else '#define GB_BIND_EVENT(hit) ((void)0)\n')
    prefix = ('\n#if '+GUARD+'\n'+event+
        '#define GB_BIND_D unsigned long long gb_binding_mask=0;\n'
        '#define GB_BIND_R gb_binding_mask=0;\n'
        '#define GB_BIND_VALUE(mask,index,expression,expected) ({ '
        'unsigned long long gb_bit=1ULL<<(index); '
        '___WORD gb_value=(expected); '
        'GB_BIND_EVENT(((mask)&gb_bit)!=0); '
        'if (!((mask)&gb_bit)) { gb_value=(expression); '
        'if (gb_value==(expected)) (mask)|=gb_bit; } gb_value; })\n'
        +mutation_hooks(header)+
        '#else\n#define GB_BIND_D\n#define GB_BIND_R\n'
        '#define GB_BIND_VALUE(mask,index,expression,expected) (expression)\n#endif\n')
    # Native helpers precede the host: declare macros before their definitions.
    insertion = code.index('struct gb_trace_native_7_result')
    guard_start = code.rfind('#if ', 0, insertion)
    code = code[:guard_start]+prefix+code[guard_start:]
    return code, dict(guards=guards, factCount=len(guards), diagnosticOnly=diagnostic,
        scope='single-host-procedure-address-facts-not-general-cache-qualification')
