"""Read-only source coverage for supplementary, effect-free GVM branch trees."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

from gambit_guarded_trace import Program, Refused
from gambit_host_coalescing import section
from gambit_trace_tree import emit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--build-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fresh', action='store_true')
    parser.add_argument('--escape-prior', type=Path)
    parser.add_argument('--caller-label', action='append', default=[])
    parser.add_argument('--all-callers', action='store_true')
    parser.add_argument('--caller-module', action='append', default=[])
    parser.add_argument('--caller-boundaries', action='store_true')
    parser.add_argument('--scalarize-callers', action='store_true')
    parser.add_argument('--emit-scalar-callers', action='store_true')
    args = parser.parse_args()
    if args.escape_prior and not args.fresh:
        parser.error('escape audit requires fresh allocation models')
    if args.caller_label and (not args.fresh or args.escape_prior):
        parser.error('caller audit requires fresh mode and explicit labels only')
    if args.all_callers and (not args.fresh or args.escape_prior or args.caller_label or args.emit_scalar_callers):
        parser.error('all-caller audit requires fresh source-only mode, no prior or explicit labels')
    if args.caller_module and not args.all_callers:
        parser.error('caller module selection requires all-caller audit')
    if args.caller_boundaries and (not args.fresh or not (args.all_callers or args.caller_label)):
        parser.error('caller boundary audit requires source-only fresh caller mode')
    if args.scalarize_callers and not (args.caller_label or args.all_callers):
        parser.error('experimental scalarization requires explicit caller roots')
    if args.emit_scalar_callers and not args.scalarize_callers:
        parser.error('experimental caller emission requires scalarization')
    root = Path(__file__).resolve().parents[3]
    baseline, receipt, output = (p.resolve() for p in (args.baseline, args.build_receipt, args.output))
    if not all(p.is_relative_to(root / '.data') for p in (baseline, receipt, output)):
        parser.error('isolated original source and receipts under .data required')
    prior = json.loads(receipt.read_text())
    if prior.get('qualified') is not True or prior.get('diagnosticOnly') is not False:
        parser.error('successful uninstrumented source/object provenance required')
    modules = []
    for row in sorted(prior['objects'], key=lambda row: row['module']):
        if row.get('reusedOriginalObject') is not True:
            parser.error('only unchanged original input objects are supported')
        path = baseline / 'build/lib/static' / (row['module'].replace('/', '__')+'.c')
        data = path.read_bytes()
        if (hashlib.sha256(data).hexdigest() != row['generatedCSha256']
                or hashlib.sha256(path.with_suffix('.o').read_bytes()).hexdigest() != row['objectSha256']):
            parser.error('original source/object changed')
        original = data.decode()
        _, host, _ = section(original, '___BEGIN_M_COD', '___END_M_COD')
        _, body, _ = section(host, '___BEGIN_M_SW', '___END_M_SW')
        definitions = dict(re.findall(r'^#define[ \t]+([A-Za-z_]\w*)[ \t]+(.*)$',
                                     original.replace('\\\n', ' '), re.MULTILINE))
        modules.append(dict(prefix=f'gb_tree_m{len(modules)}', offset=0, path=path,
                            original=original, originalBody=body, body=body, controls=definitions))
    program = Program(modules, allow_polls=True, coalesce_polls=True,
                      pure_branches=not args.fresh, fresh_branches=args.fresh,
                      fresh_caller_regions=bool(args.caller_label or args.all_callers),
                      fresh_caller_boundaries=args.caller_boundaries)
    inputs = {str(module['path']): hashlib.sha256(module['path'].read_bytes()).hexdigest()
              for module in modules}
    positions = {}
    if args.caller_label:
        for label in args.caller_label:
            matches = [(mi, labels[label]) for mi, labels in program.labels.items() if label in labels]
            if len(matches) != 1:
                parser.error('caller label must identify one original source position')
            mi, position = matches[0]
            positions.setdefault(modules[mi]['path'].stem, set()).add(position)
    if args.escape_prior:
        prior_path = args.escape_prior.resolve()
        if not prior_path.is_relative_to(root / '.data'):
            parser.error('escape prior must be an isolated .data source receipt')
        source_receipt = json.loads(prior_path.read_text())
        if (source_receipt.get('analysisComplete') is not True
                or source_receipt.get('freshAllocationTrees') is not True
                or source_receipt.get('inputs') != inputs):
            parser.error('escape audit requires matching completed fresh source coverage')
        names = {module['path'].stem for module in modules}
        for row in source_receipt['candidates']:
            if row['module'] not in names or row['bodyLine'] < 1:
                parser.error('escape audit source position is invalid')
            positions.setdefault(row['module'], set()).add(row['bodyLine']-1)
    output.mkdir(parents=True, exist_ok=False)
    counts, refusals, candidates = collections.Counter(), collections.Counter(), []
    if not set(args.caller_module).issubset({module['path'].stem for module in modules}):
        parser.error('caller modules must identify retained original source units')
    for mi, module in enumerate(modules):
        if args.caller_module and module['path'].stem not in args.caller_module:
            continue
        roots = sorted(positions.get(module['path'].stem, ())) if args.escape_prior or args.caller_label else program.roots(mi)
        for position in roots:
            if position not in program.labels[mi].values():
                raise Refused('source root is not an original label boundary')
            counts['roots'] += 1
            states = program.traces(mi, position)
            counts['purePaths'] += len(states)
            if args.caller_label or args.all_callers:
                from gambit_fresh_escape import audit, scalarize
                completed = [state for state in states if
                             (state.frame <= 0 and (state.terminal is None or state.terminal[0] == 'GB_INPUT_STACK_RETURN'))
                             or (args.caller_boundaries and state.terminal and state.terminal[0] == 'GB_ORIGINAL_EFFECT')]
                counts['completedCallerPaths'] += len(completed)
                paths = []
                for state in completed:
                    is_boundary = bool(state.terminal and state.terminal[0] == 'GB_ORIGINAL_EFFECT')
                    target = state.terminal[2] if state.terminal else 'gb_in0'
                    if is_boundary:
                        final = program.materialize(state)
                        final += f'goto gb_scalar_boundary_{target[0]}_{target[1]};'
                        counts['originalEffectCallerPaths'] += 1
                    else:
                        final = program.materialize(state, live_only=True, result_only=True)
                        final += '___JUMPRET('+target+')'
                    paths.append(dict(**audit(state, final),
                                      calls=state.calls, steps=state.steps, polls=state.polls,
                                      frame=state.frame, returnOperand=target,
                                      originalEffectBoundary=is_boundary))
                    if args.scalarize_callers:
                        try:
                            changed, _ = scalarize(state, final)
                            after = audit(changed, final)
                            fragment = f'caller-{len(candidates)}-path-{len(paths)-1}.c-fragment'
                            (output / fragment).write_text('\n'.join(changed.code)+'\n'+final+'\n')
                            paths[-1]['experimentalRewrite'] = dict(fragment=fragment,
                                remainingHeapWords=changed.heap_words,
                                remainingPotentiallyElidableHeapWords=after['potentiallyElidableHeapWords'],
                                nativeQualified=False)
                        except Refused as error:
                            paths[-1]['scalarizationRefusal'] = str(error)
                maximum_elidable = max((path['potentiallyElidableHeapWords'] for path in paths), default=0)
                if args.all_callers and not maximum_elidable:
                    counts['callerRootsWithoutElision'] += 1
                    if counts['roots'] % 32 == 0:
                        print('CALLER-AUDIT-PROGRESS', module['path'].stem, dict(counts), flush=True)
                    continue
                candidates.append(dict(module=module['path'].stem, bodyLine=position+1,
                                       labels=sorted(label for label, point in program.labels[mi].items() if point == position),
                                       paths=len(paths), escapePaths=paths,
                                       maximumPotentiallyElidableHeapWords=maximum_elidable))
                if args.all_callers:
                    print('CALLER-ELISION-SOURCE', module['path'].stem, position+1, maximum_elidable, flush=True)
                continue
            if len(states) < 2:
                continue
            counts['multiPathRoots'] += 1
            if len(states) > 32:
                refusals['pure tree path budget'] += 1
                continue
            if args.fresh and not any(state.heap_words for state in states):
                continue
            def leaf(state):
                if state.heap_words and state.terminal:
                    raise Refused('fresh tree requires completed allocation and return')
                code = program.materialize(state, live_only=state.terminal is None)
                if state.terminal:
                    if state.terminal[0] != 'GB_ORIGINAL_EFFECT':
                        raise Refused('unexpected pure terminal')
                    owner, point = state.terminal[2]
                    code += f'goto gb_tree_resume_{owner}_{point};\n'
                else:
                    code += '___JUMPRET(gb_in0)\n'
                return code
            try:
                code, details = emit(states, leaf, allow_fresh=args.fresh)
            except Refused as error:
                refusals[str(error)] += 1
                continue
            name = f'tree-{len(candidates)}.c-fragment'
            (output / name).write_text(code+'\n')
            candidates.append(dict(module=module['path'].stem, bodyLine=position+1,
                                   fragment=name, **details,
                                   maximumFrame=max(state.peak_frame for state in states),
                                   maximumPolls=max(state.polls for state in states),
                                   maximumHeapWords=max(state.heap_words for state in states),
                                   allocatedReturnPaths=sum(state.heap_words > 0 and state.terminal is None
                                                            for state in states),
                                   computedReturnPaths=sum(state.terminal is None for state in states),
                                   originalEffectBoundaries=sum(state.terminal is not None for state in states)))
            if args.escape_prior:
                from gambit_fresh_escape import audit
                paths = [audit(state, program.materialize(state, live_only=state.terminal is None))
                         for state in states]
                candidates[-1]['escapePaths'] = paths
                candidates[-1]['maximumPotentiallyElidableHeapWords'] = max(
                    path['potentiallyElidableHeapWords'] for path in paths)
    report = dict(analysisComplete=True, runtimeQualified=False, performanceQualified=False,
                  scope='static-pure-branch-source-coverage-not-real-workload-hits',
                  freshAllocationTrees=args.fresh,
                  counts=dict(counts), treeRefusals=dict(refusals), candidates=candidates,
                  inputs=inputs,
                  escapeAuditOnly=bool(args.escape_prior),
                  callerAuditOnly=bool(args.caller_label or args.all_callers),
                  allCallersSourceAudit=args.all_callers, callerModules=args.caller_module,
                  callerBoundariesSourceAudit=args.caller_boundaries,
                  experimentalCallerScalarization=args.scalarize_callers,
                  analysisRefusals=[dict(instruction=line, reason=reason, paths=count)
                                    for (line, reason), count in program.refusals.most_common(30)],
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest())
    if args.escape_prior:
        report['scope'] = 'prior-roots-only-owned-field-escape-source-audit-not-optimization'
    if args.caller_label:
        report['scope'] = 'explicit-caller-bounded-single-result-source-audit-not-emitted-optimization'
    if args.all_callers:
        report['scope'] = 'selected-modules-bounded-caller-source-audit-not-native-or-performance-qualified'
    if args.scalarize_callers:
        report['scope'] = 'explicit-caller-scalarized-source-fragments-not-native-or-performance-qualified'
    if args.emit_scalar_callers:
        if args.caller_boundaries:
            from gambit_scalar_boundary import inject as inject_scalar
        else:
            from gambit_scalar_caller import inject as inject_scalar
        report['experimentalCallerEmission'] = inject_scalar(modules, labels=args.caller_label)
        for mi, module in enumerate(modules):
            if module['body'] != module['originalBody']:
                name = f'caller-module-{mi}.c-fragment'
                (output / name).write_text(module['body'])
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PURE-TREE-PLAN', dict(counts), 'fused', len(candidates), 'refusals', dict(refusals))


if __name__ == '__main__':
    main()
