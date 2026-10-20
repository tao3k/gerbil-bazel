"""Sink fresh structures to existing deoptimization snapshots only."""
import re

from gambit_guarded_trace import Refused, macro


def sink(state, *, discard_result, reserved_heap_words):
    return _sink(state, discard_result=discard_result,
                 reserved_heap_words=reserved_heap_words, allow_pairs=False)


def sink_containers(state, *, discard_result, reserved_heap_words):
    """Keep original poll exits, materializing discarded pair/structure graphs."""
    return _sink(state, discard_result=discard_result,
                 reserved_heap_words=reserved_heap_words, allow_pairs=True)


def _sink(state, *, discard_result, reserved_heap_words, allow_pairs, discarded_nodes=None):
    if not discard_result or state.terminal is not None or state.effects or state.frame != 0:
        raise Refused('discarded transfer requires a completed effect-free return')
    if ((state.fresh_pairs and not allow_pairs) or state.fresh_closures or state.structure_setup is not None
            or state.closure_setup is not None):
        raise Refused('structure-only completed transfer required')
    if reserved_heap_words < state.heap_words:
        raise Refused('original full heap reservation required for deoptimization')
    nodes = dict(state.fresh_structures)
    if allow_pairs:
        if set(state.fresh_pair_fields) != set(state.fresh_pairs):
            raise Refused('complete fresh pair field inventory required')
        if set(nodes) & set(state.fresh_pairs):
            raise Refused('fresh constructor names must be disjoint')
        nodes.update(state.fresh_pair_fields)
    discarded = set(nodes) if discarded_nodes is None else set(discarded_nodes)
    if not discarded <= set(nodes):
        raise Refused('discarded nodes must be recorded fresh constructors')
    blocks, sequence, defined = {}, [], set()
    index = 0
    while index < len(state.code):
        line = state.code[index]
        pair = re.fullmatch(r'___WORD (gb_t\d+)=\(___CONS\((.*)\)\);', line)
        if pair and allow_pairs:
            name = pair[1]
            if name not in state.fresh_pairs or name in defined:
                raise Refused('unique recorded fresh pair constructor required')
            fields = state.fresh_pair_fields[name]
            if len(fields) != 2 or line != f'___WORD {name}=(___CONS({fields[0]},{fields[1]}));':
                raise Refused('pair fields disagree with original constructor')
            dependencies = {child for field in fields for child in nodes
                            if re.search(r'\b' + re.escape(child) + r'\b', field)}
            if not dependencies <= defined:
                raise Refused('fresh pair has cyclic or forward dependencies')
            blocks[name] = [line]
            defined.add(name)
            sequence.append(('definition', name, frozenset(defined)))
            index += 1
            continue
        if line.startswith('___BEGIN_ALLOC_STRUCTURE('):
            block = [line]
            index += 1
            while index < len(state.code) and state.code[index].startswith('___ADD_STRUCTURE_ELEM('):
                block.append(state.code[index])
                index += 1
            if index + 1 >= len(state.code) or not state.code[index].startswith('___END_ALLOC_STRUCTURE('):
                raise Refused('incomplete structure allocation block')
            block.append(state.code[index])
            result = re.fullmatch(r'___WORD (gb_t\d+)=\(___GET_STRUCTURE\((\d+)\)\);', state.code[index + 1])
            if not result or result[1] not in state.fresh_structures or result[1] in defined:
                raise Refused('unique recorded fresh structure result required')
            name, size = result[1], int(result[2])
            if len(nodes[name]) != size or len(block) != size + 2:
                raise Refused('structure fields and allocation extent disagree')
            begin, args = macro(block[0].rstrip(';'))
            end, end_args = macro(block[-1])
            expected = [f'___ADD_STRUCTURE_ELEM({offset},{value})' for offset, value in enumerate(nodes[name])]
            if (begin != 'BEGIN_ALLOC_STRUCTURE' or args != [f'{size}UL']
                    or end != 'END_ALLOC_STRUCTURE' or end_args != [str(size)]
                    or block[1:-1] != expected):
                raise Refused('allocation is not the recorded fresh constructor')
            dependencies = {child for field in nodes[name] for child in nodes
                            if re.search(r'\b' + re.escape(child) + r'\b', field)}
            if not dependencies <= defined:
                raise Refused('fresh constructor has cyclic or forward dependencies')
            block.append(state.code[index + 1])
            blocks[name] = block
            defined.add(name)
            sequence.append(('definition', name, frozenset(defined)))
            index += 2
            continue
        sequence.append(('code', line, frozenset(defined)))
        index += 1
    if set(blocks) != set(nodes) or sum(len(fields) + 1 for fields in nodes.values()) != state.heap_words:
        raise Refused('all reserved allocation must be represented by fresh structures')

    def references(text):
        return {name for name in discarded if re.search(r'\b' + re.escape(name) + r'\b', text)}

    output, snapshots = [], 0
    for kind, line, available in sequence:
        if kind == 'definition':
            if line not in discarded:
                if any(references(field) for field in nodes[line]):
                    raise Refused('retained constructor depends on a discarded address')
                output.extend(blocks[line])
            continue
        needed = references(line)
        if not needed:
            output.append(line)
            continue
        poll = line.splitlines()
        if (len(poll) < 4 or poll[0] != 'GB_TRACE_POLL_EVENT();'
                or not re.fullmatch(r'if \(___EXPECT_FALSE\(.*\)\) \{', poll[1])
                or poll[-1] != '}'
                or poll[-2] != '___JUMPEXTPRM(___NOTHING,___ps->handler_stack_limit)'):
            raise Refused('fresh address observed outside an existing poll exit')
        if references(poll[1]):
            raise Refused('poll eligibility must not read an unmaterialized constructor')
        emitted, active, materialized = set(), set(), []

        def emit(name):
            if name in active or name not in available:
                raise Refused('cyclic or unavailable fresh snapshot dependency')
            if name in emitted:
                return
            active.add(name)
            for field in nodes[name]:
                for child in sorted(references(field)):
                    emit(child)
            materialized.extend(blocks[name])
            active.remove(name)
            emitted.add(name)

        for name in sorted(needed):
            emit(name)
        output.append('\n'.join(poll[:2] + materialized + poll[2:]))
        snapshots += 1
    return output, dict(hotStructureAllocationsRemoved=len(discarded & set(state.fresh_structures)),
                        hotPairAllocationsRemoved=len(discarded & set(state.fresh_pairs)),
                        hotHeapWordsRemoved=sum(len(nodes[name]) + 1 for name in discarded),
                        materializingPollExits=snapshots,
                        requiredReservedHeapWords=state.heap_words)


def sink_unobserved(program, state, *, reserved_heap_words):
    """Preserve normal return objects; materialize only snapshot-only constructors."""
    from gambit_fresh_escape import audit
    if state.effects or state.frame > 0 or (state.terminal is not None and
            state.terminal[0] != 'GB_INPUT_STACK_RETURN'):
        raise Refused('completed normal-return ownership proof required')
    target = state.terminal[2] if state.terminal else 'gb_in0'
    final = program.materialize(state, live_only=True, result_only=True) + '___JUMPRET(' + target + ')'
    normal = state.fork()
    normal.code = [line for line in normal.code
                   if not line.startswith('GB_TRACE_POLL_EVENT();\n')]
    findings = audit(normal, final)
    discarded = {item['name'] for item in findings['objects'] if not item['retained']}
    work = state.fork()
    # Original frame/return exports stay in final, outside allocation sinking.
    work.frame, work.terminal = 0, None
    code, report = _sink(work, discard_result=True, reserved_heap_words=reserved_heap_words,
                         allow_pairs=True, discarded_nodes=discarded)
    report.update(normalRetainedHeapWords=findings['retainedHeapWords'],
                  discardedNodes=sorted(discarded), originalFrameDelta=state.frame)
    return code, final, report


def sink_projected_boundary(program, state, *, reserved_heap_words, pair_snapshots=False):
    if (state.effects or state.frame > 0 or state.terminal is None
            or state.terminal[:2] != ('GB_ORIGINAL_EFFECT', 0)):
        raise Refused('completed original projected caller boundary required')
    module, position = state.terminal[2]
    reset_return = False
    for line in program.lines[module][position:position + 8]:
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r'___SET_STK\(-?\d+,___R1\)', line):
            continue
        if re.fullmatch(r'___SET_R0\(___LBL\(\d+\)\)', line):
            reset_return = True
            continue
        if re.fullmatch(r'___ADJFP\(-?\d+\)', line):
            continue
        if re.fullmatch(r'___JUMPGLO(?:SAFE|NOTSAFE)\(___SET_NARGS\(1\),\d+,___G_\w+\)', line) and reset_return:
            break
        raise Refused('caller observes unknown state before one-argument global call')
    else:
        raise Refused('bounded caller ABI clobber proof unavailable')
    if reserved_heap_words < state.heap_words:
        raise Refused('original full heap reservation required for projected boundary')
    fresh = set(state.fresh_structures) | set(state.fresh_pairs)

    def references(value):
        return {name for name in fresh if re.search(r'\b' + re.escape(name) + r'\b', str(value))}

    live_stack = {slot:value for slot,value in state.stack.items() if slot <= state.frame}
    if references(state.registers[1]) or any(references(value) for value in live_stack.values()):
        raise Refused('fresh projected value or live caller stack still escapes')
    work = state.fork()
    if not pair_snapshots:
        for name in sorted(state.fresh_pairs):
            fields = state.fresh_pair_fields.get(name)
            if fields is None or len(fields) != 2:
                raise Refused('recorded fresh pair fields required')
            declaration = f'___WORD {name}=(___CONS({fields[0]},{fields[1]}));'
            if work.code.count(declaration) != 1 or any(
                    references(line) & {name} for line in work.code if line != declaration):
                raise Refused('fresh result pair has an observable address use')
            work.code.remove(declaration)
            work.heap_words -= 3
        work.fresh_pairs.clear()
        work.fresh_pair_fields.clear()
    # The actual negative frame delta is retained in the exported native state.
    work.frame, work.terminal = 0, None
    emitter = sink_containers if pair_snapshots else sink
    code, report = emitter(work, discard_result=True, reserved_heap_words=reserved_heap_words)
    exported = state.fork()
    exported.stack = live_stack
    for register in (0, 2, 3, 4):
        exported.registers[register] = '___VOID'
    report.update(hotPairAllocationsRemoved=len(state.fresh_pairs),
                  hotHeapWordsRemoved=report['hotHeapWordsRemoved'] +
                      (0 if pair_snapshots else 3 * len(state.fresh_pairs)),
                  requiredReservedHeapWords=state.heap_words, exportedFrameDelta=state.frame,
                  clobberedRegisters=[0, 2, 3, 4])
    return code, exported, report
