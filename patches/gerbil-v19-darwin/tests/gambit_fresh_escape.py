"""Conservative owned-object audit and explicit experimental scalarization."""
import re

from gambit_guarded_trace import Refused, macro


TEMP = re.compile(r'\bgb_t\d+\b')
DECL = re.compile(r'___WORD (gb_t\d+)=\((.*)\);')


def _facts(state):
    if (state.effects or state.effect_snapshot or state.structure_setup or state.closure_setup
            or state.initialized_closures != set(state.fresh_closures)):
        raise Refused('escape audit requires a complete isolated region')
    definitions = {}
    for statement in state.code:
        match = DECL.fullmatch(statement)
        if match:
            if match[1] in definitions:
                raise Refused('escape audit requires unique temporaries')
            definitions[match[1]] = match[2]
    fields = dict(state.fresh_structures)
    words = {name: len(values)+1 for name, values in fields.items()}
    pairs = {}
    for name in state.fresh_pairs:
        if name not in definitions:
            raise Refused('fresh pair lacks constructor temporary')
        kind, values = macro(definitions[name])
        if kind not in {'CONS', 'XCONS'} or len(values) != 2:
            raise Refused('fresh pair lacks exact constructor')
        pairs[name] = tuple(values if kind == 'CONS' else reversed(values))
        words[name] = 3
    for name, size in state.fresh_closures.items():
        words[name] = size+2
    if (len(words) != len(state.fresh_pairs)+len(state.fresh_structures)+len(state.fresh_closures)
            or sum(words.values()) != state.heap_words):
        raise Refused('fresh allocation inventory does not match modeled heap')

    def normalize(expression, active=frozenset()):
        if expression in definitions and expression not in words:
            if expression in active:
                raise Refused('cyclic temporary dependency')
            return normalize(definitions[expression], active | {expression})
        try:
            kind, args = macro(expression)
        except Refused:
            return expression
        if kind in {'CAR', 'CDR', 'CAAR'} and len(args) == 1:
            owner = normalize(args[0], active)
            if kind == 'CAAR':
                return normalize('___CAR('+normalize('___CAR('+owner+')', active)+')', active)
            if owner in pairs:
                return normalize(pairs[owner][kind == 'CDR'], active)
        if kind == 'UNCHECKEDSTRUCTUREREF' and len(args) == 4 and args[2:] == ['___FAL', '___FAL']:
            owner = normalize(args[0], active)
            index = re.fullmatch(r'___FIX\((\d+)L?\)', args[1])
            if owner in fields and index and int(index[1]) < len(fields[owner]):
                return normalize(fields[owner][int(index[1])], active)
        return expression

    return definitions, fields, pairs, words, normalize


def audit(state, final_code):
    definitions, fields, pairs, words, normalize = _facts(state)
    retained = set()
    reasons = {}

    def observe(expression, reason, visited=frozenset()):
        for name in TEMP.findall(expression):
            if name in visited:
                continue
            if name in words:
                retained.add(name)
                reasons.setdefault(name, set()).add(reason)
                for value in fields.get(name, pairs.get(name, ())):
                    observe(value, 'stored-in-observed-fresh-object', visited | {name})
            elif name in definitions:
                observe(normalize(definitions[name]), reason, visited | {name})

    observe(final_code, 'final-register-or-stack')
    for statement in state.code:
        match = DECL.fullmatch(statement)
        if match:
            if match[1] not in words:
                observe(normalize(match[2]), 'expression-observed')
        elif statement.startswith(('___BEGIN_ALLOC_STRUCTURE(', '___ADD_STRUCTURE_ELEM(',
                                   '___END_ALLOC_STRUCTURE(')):
            continue
        else:
            # Guards and closure stores remain observable; do not infer identity.
            observe(statement, 'guard-or-raw-statement')
    return dict(modeledHeapWords=state.heap_words,
                retainedHeapWords=sum(words[name] for name in retained),
                potentiallyElidableHeapWords=sum(value for name, value in words.items() if name not in retained),
                objects=[dict(name=name, words=value, retained=name in retained,
                              reasons=sorted(reasons.get(name, ()))) for name, value in sorted(words.items())],
                scope='conservative-owned-field-read-escape-audit-not-emitted-optimization')


def scalarize(state, final_code):
    """Opt-in rewrite; refuse anything not proved by the owned-object audit."""
    findings = audit(state, final_code)
    definitions, fields, pairs, words, normalize = _facts(state)
    dropped = {item['name'] for item in findings['objects'] if not item['retained']}
    # Raw closure initialization stores are deliberately not scalarized.
    if dropped & set(state.fresh_closures):
        raise Refused('closure scalarization is unsupported')
    rewritten = state.fork()
    code = []
    cursor = 0
    while cursor < len(state.code):
        statement = state.code[cursor]
        if statement.startswith('___BEGIN_ALLOC_STRUCTURE('):
            end = cursor + 1
            while end < len(state.code) and state.code[end].startswith('___ADD_STRUCTURE_ELEM('):
                end += 1
            if end + 1 >= len(state.code) or not state.code[end].startswith('___END_ALLOC_STRUCTURE('):
                raise Refused('structure scalarization requires a contiguous complete constructor')
            owner = DECL.fullmatch(state.code[end + 1])
            if not owner or owner[1] not in fields or not owner[2].startswith('___GET_STRUCTURE('):
                raise Refused('structure scalarization cannot identify result owner')
            if owner[1] in dropped:
                cursor = end + 2
                continue
        declaration = DECL.fullmatch(statement)
        if declaration:
            if declaration[1] not in dropped:
                expression = normalize(declaration[2]) if declaration[1] not in words else declaration[2]
                code.append(f'___WORD {declaration[1]}=({expression});')
        else:
            code.append(statement)
        cursor += 1
    if any(dropped & set(TEMP.findall(statement)) for statement in code + [final_code]):
        raise Refused('scalarization left an observable reference to a dropped object')
    rewritten.code = code
    rewritten.heap_words -= findings['potentiallyElidableHeapWords']
    rewritten.fresh_pairs -= dropped
    rewritten.fresh_pair_fields = {name: value for name, value in rewritten.fresh_pair_fields.items() if name not in dropped}
    rewritten.fresh_structures = {name: value for name, value in rewritten.fresh_structures.items() if name not in dropped}
    if rewritten.last_structure and rewritten.last_structure[1] in dropped:
        rewritten.last_structure = None
    return rewritten, findings
