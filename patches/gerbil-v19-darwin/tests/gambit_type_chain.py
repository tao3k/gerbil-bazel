"""Recognize the original pure TYPEID/TYPESUPER GVM loop, never a class cache."""
import re


def lower(program, mi, point, state):
    from gambit_guarded_trace import macro, Refused, LABEL
    lines = program.lines[mi]
    if state.conditions >= state.guard_limit or state.polls >= 7:
        return None

    def operation(index):
        return macro(lines[index].strip())

    try:
        while LABEL.fullmatch(lines[point].strip()):
            point += 1
        name, args = operation(point)
        if not re.fullmatch('SET_R[1-4]', name) or len(args) != 1:
            return None
        id_reg = int(name[-1])
        read, values = macro(args[0])
        if read != 'TYPEID' or len(values) != 1 or not re.fullmatch('___R[1-4]', values[0]):
            return None
        type_reg = int(values[0][-1])
        if type_reg == id_reg:
            return None
        name, args = operation(point + 1)
        if name != 'IF':
            return None
        name, args = macro(args[0])
        if name != 'NOT':
            return None
        name, args = macro(args[0])
        if name != 'EQP' or len(args) != 2 or args[0] != f'___R{id_reg}':
            return None
        wanted = args[1]
        if re.search(f'___R[{type_reg}{id_reg}]\\b', wanted):
            return None
        name, args = operation(point + 2)
        if name != 'GOTO' or lines[point + 3].strip() != '___END_IF':
            return None
        advance = program.labels[mi][args[0]]
        if operation(point + 4) != (f'SET_R{type_reg}', ['___TRU']):
            return None
        name, returns = operation(point + 5)
        if name != 'JUMPRET':
            return None
        if operation(advance) != (f'SET_R{type_reg}', [f'___TYPESUPER(___R{type_reg})']):
            return None
        if operation(advance + 1) != ('IF', [f'___NOT(___NOTFALSEP(___R{type_reg}))']):
            return None
        name, args = operation(advance + 2)
        if name != 'GOTO' or lines[advance + 3].strip() != '___END_IF':
            return None
        absent = program.labels[mi][args[0]]
        if operation(absent) != (f'SET_R{type_reg}', ['___FAL']) or operation(absent + 1) != ('JUMPRET', returns):
            return None
        name, args = operation(advance + 4)
        if name != 'POLL' or len(args) != 1 or not args[0].isdigit():
            return None
        loop = advance + 5
        while LABEL.fullmatch(lines[loop].strip()):
            loop += 1
        if loop != point or len(returns) != 1:
            return None
        indices = [*range(point, point + 6), *range(advance, advance + 5), absent, absent + 1]
        base = program.scopes[mi, point][0]
        if any(program.scopes[mi, index][0] != base for index in indices):
            return None
        source = program.value(state.registers[type_reg])
        target = program.value(program.expression(wanted, mi, point, state))
        token = f'gb_type_chain_{len(state.code)}'
        state.code.append(f'struct gb_type_chain_result {token}=gb_trace_type_chain(___ps,___fp-({state.frame}),{source},{target});')
        state.require(f'{token}.complete')
        state.registers[type_reg] = state.capture(f'{token}.answer')
        state.registers[id_reg] = state.capture(f'{token}.last_id')
        state.polls += 1
        state.peak_frame = max(state.peak_frame, state.frame)
        state.type_chain_loops += 1
        return point + 5
    except (Refused, KeyError, IndexError, ValueError):
        return None


PREAMBLE = r'''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && (___NB_ARG_REGS == 3) && !defined(___DYNAMIC) && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)
struct gb_type_chain_result { ___WORD answer,last_id; int complete; };
static struct gb_type_chain_result __attribute__((noinline,optimize("O3")))
gb_trace_type_chain(___processor_state ___ps,___WORD *___fp,___WORD type,___WORD wanted) {
  ___WORD ___temp;
  struct gb_type_chain_result result={___FAL,___FAL,0};
  for (int depth=0; depth<128; ++depth) {
    if (!___STRUCTUREP(type) || ___INT(___STRUCTURELENGTH(type))<5) return result;
    result.last_id=___TYPEID(type);
    if (___EQP(result.last_id,wanted)) {
      result.answer=___TRU;
      result.complete=1;
      return result;
    }
    type=___TYPESUPER(type);
    if (type==___FAL) { result.complete=1; return result; }
    GB_TRACE_POLL_EVENT();
    if (___EXPECT_FALSE(___fp<___ps->stack_trip)) return result;
  }
  return result;
}
#endif
'''
