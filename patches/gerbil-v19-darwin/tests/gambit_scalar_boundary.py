"""Default-off scalar prefixes that resume before an original opaque operation."""
from gambit_fresh_escape import scalarize
from gambit_guarded_trace import GUARD, Program, Refused
from gambit_trace_tree import emit


def inject(modules, labels=None, apply=True, excluded=()):
    program = Program(modules, allow_polls=True, coalesce_polls=True,
                      fresh_branches=True, fresh_caller_regions=True,
                      fresh_caller_boundaries=True)
    edits, resumes, selections = {}, set(), []
    for mi, module in enumerate(modules):
        declarations = module.get('controls', {}).get('___MD_ALL')
        missing = {n for n in range(5) if declarations is not None and f'___D_R{n}' not in declarations}

        def materialize(state):
            code = program.materialize(state)
            for n in missing:
                if state.registers[n] != f'gb_in{n}':
                    raise Refused('boundary changes a register absent from its original host')
                code = code.replace(f'___SET_R{n}(gb_in{n})\n', '')
                if f'gb_in{n}' in code or any(f'gb_in{n}' in statement for statement in state.code):
                    raise Refused('boundary observes a register absent from its original host')
            return code

        roots = ([program.labels[mi][label] for label in labels if label in program.labels[mi]]
                 if labels is not None else program.roots(mi))
        for position in roots:
            if (mi, position) in excluded:
                continue
            states, removed = [], {}
            for state in program.traces(mi, position):
                if not state.terminal or state.terminal[0] != 'GB_ORIGINAL_EFFECT':
                    continue
                # Pending positive-offset stores can precede an original ADJFP.
                try:
                    final = materialize(state)
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
            miss, rollback = f'gb_prefix_miss_{site}', f'gb_prefix_rollback_{site}'
            peak, heap = max(state.peak_frame for state in states), max(state.heap_words for state in states)
            poll = (f'if (___EXPECT_FALSE((___fp-({peak})) < ___ps->stack_trip)) goto GB_TRACE_MISS;\n'
                    if any(state.polls for state in states) else '')
            points = set()

            def leaf(state):
                owner, point = state.terminal[2]
                points.add((owner, point))
                return (poll+materialize(state)
                        +f'GB_PURE_TREE_HIT({site});\nGB_SCALAR_ELIDED_WORDS({removed[id(state)]});\n'
                        +f'goto gb_scalar_boundary_{owner}_{point};\n')

            try:
                code, details = emit(states, leaf, allow_fresh=True)
            except Refused:
                continue
            guard = GUARD+' && (___WS == 8) && (___PAIR_SIZE == 2) && (___PAIR_BODY == 1)'
            guard += ' && !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT)'
            guard += ' && (___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0) && (___CLO_FREEVARS == 1) && (___SUBTYPED_BODY == 1)'
            if poll:
                guard += ' && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)'
            prelude = '___WORD *gb_heap_checkpoint=___hp;\n'
            prelude += f'if (___EXPECT_FALSE(___hp+{heap}>___ps->heap_limit)) goto {miss};\n'
            prelude += ''.join(f'___WORD gb_in{n}={"___PSR" if n in missing else "___R"}{n};\n' for n in range(5))
            prelude += 'int gb_in_nargs=___ps->na;\n'
            fallback = f'\n{rollback}:;\nGB_FRESH_TREE_ROLLBACK({site},___hp-gb_heap_checkpoint);\n___hp=gb_heap_checkpoint;\n'
            emitted = (f'\n#if {guard}\n{{\nGB_PURE_TREE_ENTRY({site});\n'
                       +poll.replace('GB_TRACE_MISS', miss)+prelude
                       +code.replace('GB_TRACE_MISS', rollback)+fallback
                       +f'}}\n{miss}:;\n#endif\n')
            edits.setdefault((mi, position), []).append(emitted)
            resumes.update(points)
            selections.append(dict(module=module['path'].stem, line=position+1,
                                   maximumHeapWords=heap,
                                   minimumElidedWords=min(removed[id(state)] for state in states),
                                   maximumElidedWords=max(removed[id(state)] for state in states),
                                   originalEffectBoundaries=len(points), **details))
    for owner, point in resumes:
        # Resume after any optimization entry at this point, before its original instruction.
        edits.setdefault((owner, point), []).append(f'\ngb_scalar_boundary_{owner}_{point}:;\n')
    for mi, module in enumerate(modules) if apply else ():
        lines = module['body'].splitlines(keepends=True)
        for (_, position), code in sorted(((key, value) for key, value in edits.items() if key[0] == mi), reverse=True):
            lines.insert(position, ''.join(code))
        module['body'] = ''.join(lines)
    result = dict(supplementaryPureTrees=selections, scalarBoundaryResumes=len(resumes),
                  scope='bounded-scalar-prefixes-original-effect-resume-not-performance-qualified')
    if not apply:
        result['nativeScalarEdits'] = {}
        for (mi, point), code in edits.items():
            result['nativeScalarEdits'].setdefault(mi, []).append((point, ''.join(code)))
    return result
