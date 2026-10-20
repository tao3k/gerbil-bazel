"""Prototype late-bound parameter entry using generated module dependencies."""
import re

from gambit_parameter_entry import identity_preamble


def late_bound_parameter_preamble(include_safe=False):
    preamble = identity_preamble(env_lookup=True)
    preamble = re.sub(r'^___IMP_DATA\(___glo_struct,___G_\w+\);\n', '', preamble, flags=re.M)
    if preamble.count(' && !defined(___DYNAMIC)') != 1:
        raise ValueError('original static helper guard changed')
    preamble = preamble.replace(' && !defined(___DYNAMIC)', ' && defined(___DYNAMIC)')
    if include_safe:
        branch = '___JUMPGENNOTSAFE(___SET_NARGS(1),gb_getter)'
        boundary = '\n#else\n#define GB_PARAMETER_TRY(expression) ((void)0);'
        if preamble.count(branch) != 1 or preamble.count(boundary) != 1:
            raise ValueError('original getter transfer changed')
        preamble = preamble.replace('#define GB_PARAMETER_TRY(expression)',
            '#define GB_PARAMETER_TRY_MODE(expression,gb_transfer)', 1)
        preamble = preamble.replace(branch, 'gb_transfer(___SET_NARGS(1),gb_getter)')
        preamble = preamble.replace(boundary,
            '\n#define GB_PARAMETER_TRY(expression) GB_PARAMETER_TRY_MODE(expression,___JUMPGENNOTSAFE)'
            '\n#define GB_PARAMETER_TRY_SAFE(expression) GB_PARAMETER_TRY_MODE(expression,___JUMPGENSAFE)'
            +boundary+'\n#define GB_PARAMETER_TRY_SAFE(expression) ((void)0);')
    return preamble


def inject_late_bound_parameter_entry(code, diagnostic_hit=False, include_safe=False):
    if 'GB_PARAMETER_TRY' in code or 'gb_parameter_lookup' in code:
        raise ValueError('parameter entry already injected')
    if code.count('___BEGIN_M_COD') != 1 or code.count('___END_M_COD') != 1:
        raise ValueError('one complete generated module required')
    rows = re.findall(r'^#define ___GLO_(\w+) ___GLO\((\d+),(___G_\w+)\)$', code, re.M)
    bindings = {}
    for name, index, identifier in rows:
        if identifier != '___G_'+name or name in bindings:
            raise ValueError('ambiguous generated global bindings')
        bindings[name] = int(index)
    preamble = identity_preamble(env_lookup=True)
    needed = re.findall(r'^___IMP_DATA\(___glo_struct,___G_(\w+)\);$', preamble, re.M)
    missing = [name for name in needed if name not in bindings]
    if missing:
        raise ValueError('undeclared kernel binding dependencies: '+', '.join(missing))
    preamble = late_bound_parameter_preamble(include_safe=include_safe)
    aliases = '#if defined(___DYNAMIC)\n'+''.join(
        f'#define ___G_{name} ___GLOSTRUCT({bindings[name]},___G_{name})\n' for name in needed)+'#endif\n'
    counter = ''
    if diagnostic_hit:
        counter = ('#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___DYNAMIC)\n'
            'static unsigned long gb_dynamic_parameter_hits;\n'
            '#define GB_PARAMETER_HIT() do { if (!gb_dynamic_parameter_hits++) '
            'fputs("DYNAMIC-FAST-PATH-HIT\\n",stderr); } while (0)\n#endif\n')
    mode = r'(NOT)?' if include_safe else r'(NOT)'
    pattern = re.compile(r'___JUMPGLO'+mode+r'SAFE\(___SET_NARGS\(0\),(\d+),(___G_\w+)\)')
    sites = len(pattern.findall(code))
    if not sites:
        raise ValueError('no eligible generated zero-argument global calls')
    def call(match):
        macro = 'GB_PARAMETER_TRY' if match[1] else 'GB_PARAMETER_TRY_SAFE'
        return macro+'(___GLO('+match[2]+','+match[3]+'))\n'+match[0]
    output = pattern.sub(call, code)
    output = output.replace('___BEGIN_M_COD', aliases+counter+preamble+'\n___BEGIN_M_COD')
    undefs = '#if defined(___DYNAMIC)\n'+''.join(f'#undef ___G_{name}\n' for name in needed)+'#endif\n'
    output = output.replace('___END_M_COD', undefs+'___END_M_COD')
    return output, dict(parameterSites=sites,
        lateBoundDependencies={name: bindings[name] for name in needed}, diagnosticHit=diagnostic_hit)
