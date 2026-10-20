"""Explicit state export for owned producer trees; no GVM transfer inside C helpers."""
import re

from gambit_guarded_trace import Refused, macro


def outline(code, name, guard):
    if not re.fullmatch(r'gb_whole_[A-Za-z0-9_]+', name):
        raise Refused('owned whole-producer helper name required')
    if '___STK(' in code:
        raise Refused('original stack reads require a separately proved shadow mapping')
    declarations = ''.join(f'___WORD gb_in{i}=gb_inputs[{i}],gb_r{i}=gb_inputs[{i}];\n'
                           for i in range(5))
    export = ''.join(f'out->r[{i}]=gb_r{i};\n' for i in range(5))
    export += 'out->nargs=gb_nargs; out->fp=___fp; out->hp=___hp;\n'
    lines, normal, polls = [], 0, 0
    for line in code.splitlines():
        if line.startswith('___SET_R'):
            operation, args = macro(line)
            match = re.fullmatch(r'SET_R([0-4])', operation)
            if not match or len(args) != 1:
                raise Refused('only five recorded GVM register exports supported')
            lines.append(f'gb_r{match[1]}=({args[0]});')
        elif line.startswith('___SET_NARGS('):
            operation, args = macro(line)
            if len(args) != 1:
                raise Refused('exact nargs export required')
            lines.append(f'gb_nargs=({args[0]});')
        elif line.startswith('___SET_STK('):
            operation, args = macro(line)
            if len(args) != 2 or not re.fullmatch(r'-?\d+', args[0]):
                raise Refused('constant recorded stack export required')
            lines.append('if (out->stack_count>=32) goto gb_whole_miss;\n'
                         + f'out->stack[out->stack_count].address=&___STK({args[0]});\n'
                         + f'out->stack[out->stack_count].value=({args[1]});\n'
                         + 'out->stack_count++;')
        elif line.startswith('___ps->temp1='):
            lines.append(line.replace('___ps->temp1=', 'gb_poll_resume=', 1))
        elif line.startswith('___JUMPRET('):
            operation, args = macro(line)
            if len(args) != 1:
                raise Refused('exact original return target required')
            lines.append(export + f'out->target=___CAST(___WORD,{args[0]});\nreturn 1;')
            normal += 1
        elif line.startswith('___JUMPEXTPRM('):
            operation, args = macro(line)
            if args != ['___NOTHING', '___ps->handler_stack_limit']:
                raise Refused('only original stack-limit poll transfer supported')
            lines.append(export + 'out->target=gb_poll_resume;\nreturn 2;')
            polls += 1
        elif re.search(r'___JUMP|___SET_GLO|___ps->\w+\s*=(?!=)', line):
            raise Refused('unclassified transfer or shared-state write')
        else:
            lines.append(line)
    if not normal or not polls:
        raise Refused('normal and original poll exports both required')
    body = '\n'.join(lines).replace('GB_TRACE_MISS', 'gb_whole_miss')
    result = ('#if ' + guard + '\n'
        + f'static int __attribute__((noinline,optimize("O3"))) {name}(const ___WORD *gb_inputs,\n'
        'int gb_in_nargs,___processor_state ___ps,___WORD *___fp,___WORD *___hp,\n'
        'struct gb_whole_result *out) {\n___WORD ___temp,gb_poll_resume=___FAL;\n'
        'int gb_nargs=gb_in_nargs; out->stack_count=0;\n' + declarations + body
        + '\ngb_whole_miss:;\nreturn 0;\n}\n#endif\n')
    return result, dict(normalExports=normal, pollExports=polls,
                        sharedNargsWritesInHelper=False, sharedResumeWritesInHelper=False)
