"""Explicit experimental caller scalarization, never enabled by normal builds."""
from gambit_fresh_escape import scalarize
from gambit_guarded_trace import GUARD, Program, Refused
from gambit_trace_tree import emit


def inject(modules, labels=None, apply=True, excluded=()):
    program = Program(modules, allow_polls=True, coalesce_polls=True,
                      fresh_branches=True, fresh_caller_regions=True)
    edits, selections, refusals = {}, [], []
    for mi, module in enumerate(modules):
        roots = ([program.labels[mi][label] for label in labels if label in program.labels[mi]]
                 if labels is not None else program.roots(mi))
        for position in roots:
            if (mi, position) in excluded:
                continue
            states, removed = [], {}
            for state in program.traces(mi, position):
                if state.frame > 0 or state.terminal and state.terminal[0] != 'GB_INPUT_STACK_RETURN':
                    continue
                target = state.terminal[2] if state.terminal else 'gb_in0'
                final = program.materialize(state, live_only=True, result_only=True)+'___JUMPRET('+target+')'
                try:
                    changed, receipt = scalarize(state, final)
                except Refused:
                    continue
                if not receipt['potentiallyElidableHeapWords']:
                    continue
                removed[id(changed)] = receipt['potentiallyElidableHeapWords']
                states.append(changed)
                if len(states) == 32:
                    break
            if len(states) < 2 or len(selections) >= 16:
                continue
            site = len(selections)
            miss, rollback = f'gb_scalar_miss_{site}', f'gb_scalar_rollback_{site}'
            peak = max(state.peak_frame for state in states)
            heap = max(state.heap_words for state in states)
            poll = (f'if (___EXPECT_FALSE((___fp-({peak})) < ___ps->stack_trip)) goto GB_TRACE_MISS;\n'
                    if any(state.polls for state in states) else '')

            def leaf(state):
                target = state.terminal[2] if state.terminal else 'gb_in0'
                return (poll+program.materialize(state, live_only=True, result_only=True)
                        +f'GB_PURE_TREE_HIT({site});\n'
                        +f'GB_SCALAR_ELIDED_WORDS({removed[id(state)]});\n'
                        +'___JUMPRET('+target+')\n')

            try:
                code, details = emit(states, leaf, allow_fresh=True)
            except Refused as error:
                refusals.append(dict(module=module['path'].stem, line=position+1, reason=str(error)))
                continue
            guard = GUARD+' && (___WS == 8) && (___PAIR_SIZE == 2) && (___PAIR_BODY == 1)'
            guard += ' && !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT)'
            guard += ' && (___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0) && (___CLO_FREEVARS == 1) && (___SUBTYPED_BODY == 1)'
            if poll:
                guard += ' && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)'
            prelude = '___WORD *gb_heap_checkpoint=___hp;\n'
            prelude += f'if (___EXPECT_FALSE(___hp+{heap}>___ps->heap_limit)) goto {miss};\n'
            prelude += ''.join(f'___WORD gb_in{n}=___R{n};\n' for n in range(5))
            prelude += 'int gb_in_nargs=___ps->na;\n'
            fallback = f'\n{rollback}:;\nGB_FRESH_TREE_ROLLBACK({site},___hp-gb_heap_checkpoint);\n___hp=gb_heap_checkpoint;\n'
            emitted = (f'\n#if {guard}\n{{\nGB_PURE_TREE_ENTRY({site});\n'
                       +poll.replace('GB_TRACE_MISS', miss)+prelude
                       +code.replace('GB_TRACE_MISS', rollback)+fallback
                       +f'}}\n{miss}:;\n#endif\n')
            edits.setdefault(mi, []).append((position, emitted))
            selections.append(dict(module=module['path'].stem, line=position+1,
                                   maximumHeapWords=heap,
                                   minimumElidedWords=min(removed[id(state)] for state in states),
                                   maximumElidedWords=max(removed[id(state)] for state in states), **details))
    for mi, changes in edits.items() if apply else ():
        lines = modules[mi]['body'].splitlines(keepends=True)
        for position, code in sorted(changes, reverse=True):
            lines.insert(position, code)
        modules[mi]['body'] = ''.join(lines)
    result = dict(supplementaryPureTrees=selections, scalarizationRefusals=refusals)
    if not apply:
        result['nativeScalarEdits'] = edits
    return result
