"""Factor compatible pure trace guards into a bounded, non-replaying C tree."""
import re

from gambit_guarded_trace import Refused


def guard_condition(statement):
    match = re.fullmatch(r'if \((!?)\((.*)\)\) goto GB_TRACE_MISS;', statement)
    if not match:
        return None
    depth = 0
    for char in match[2]:
        depth += (char == '(')-(char == ')')
        if depth < 0:
            raise Refused('malformed pure tree condition')
    if depth:
        raise Refused('malformed pure tree condition')
    return match[2], bool(match[1])


def emit(states, leaf, allow_fresh=False):
    if not 2 <= len(states) <= 32:
        raise Refused('pure tree path budget')
    if any(state.effects or state.effect_snapshot
           or state.closure_setup or state.structure_setup
           or state.initialized_closures != set(state.fresh_closures)
           or not 0 <= state.heap_words <= (64 if allow_fresh else 0) for state in states):
        raise Refused('pure tree excludes heap and external effects')
    if any(len(state.code) > 256 for state in states):
        raise Refused('pure tree statement budget')
    branches = [(tuple(state.code), leaf(state)) for state in states]
    nodes = 0

    def render(paths):
        nonlocal nodes
        nodes += 1
        if nodes > 256:
            raise Refused('pure tree node budget')
        prefix = []
        while all(code for code, _ in paths) and len({code[0] for code, _ in paths}) == 1:
            prefix.append(paths[0][0][0])
            paths = [(code[1:], final) for code, final in paths]
        finished = [final for code, final in paths if not code]
        if finished:
            if len(finished) != len(paths) or len(set(finished)) != 1:
                raise Refused('ambiguous or partially overlapping pure tree leaves')
            return '\n'.join(prefix+[finished[0]])
        groups = {}
        for code, final in paths:
            condition = guard_condition(code[0])
            if condition is None:
                raise Refused('pure tree divergence is not guarded')
            groups.setdefault(condition, []).append((code[1:], final))
        expressions = {condition[0] for condition in groups}
        if len(expressions) == 1 and len(groups) == 2:
            expression = next(iter(expressions))
            branch = ('if ('+expression+') {\n'+render(groups[expression, True])+
                      '\n} else {\n'+render(groups[expression, False])+'\n}')
        else:
            clauses = []
            for (expression, truth), paths in groups.items():
                condition = expression if truth else '!('+expression+')'
                clauses.append('if ('+condition+') {\n'+render(paths)+'\n}')
            branch = ' else '.join(clauses)+' else { goto GB_TRACE_MISS; }'
        return '\n'.join(prefix+[branch])

    code = render(branches)
    return code, {'paths': len(states), 'nodes': nodes,
                  'inputStatements': sum(len(state.code) for state in states),
                  'emittedLines': len(code.splitlines())}
