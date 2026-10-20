"""Semantic prototype: retain both field computations, omit only result pair."""
import argparse
import json
from pathlib import Path

from sexpdata import Brackets, Quoted, Symbol, loads

S = Symbol


def dump(value):
    if isinstance(value, Symbol):
        text = str(value)
        if any(c.isspace() or c in '()[]";\\' for c in text):
            raise ValueError('unsupported symbol spelling')
        return text
    if isinstance(value, Quoted):
        return "'" + dump(value.x)
    if isinstance(value, Brackets):
        return '[' + ' '.join(map(dump, value.I)) + ']'
    if isinstance(value, list):
        return '(' + ' '.join(map(dump, value)) + ')'
    if type(value) is str:
        return json.dumps(value)
    if type(value) in (int, float):
        return str(value)
    raise ValueError('unsupported generated datum')


def find_definition(forms):
    found = []
    def visit(node):
        if isinstance(node, list):
            if len(node) >= 3 and node[:2] == [S('define'), S('gx#syntax-e')]:
                found.append(node)
            else:
                for child in node:
                    visit(child)
    visit(forms)
    if len(found) != 1:
        raise ValueError('unique syntax-e definition required')
    return found[0]


def projected_lambda(original, field, discard_unused_field=False):
    if field not in ('car', 'cdr'):
        raise ValueError('unsupported projection')
    replacements = 0
    def tail(node, loops=frozenset()):
        nonlocal replacements
        if isinstance(node, list) and node:
            if node[0] == S('if') and len(node) == 4:
                return [node[0], node[1], tail(node[2], loops), tail(node[3], loops)]
            if node[0] == S('let'):
                if isinstance(node[1], Symbol):
                    return [*node[:-1], tail(node[-1], loops | {node[1]})]
                return [*node[:-1], tail(node[-1], loops)]
            if node[0] in loops:
                return node
            if node[0] == S('cons') and len(node) == 3:
                if not all(isinstance(x, list) and x and x[0] == S('gx#stx-wrap')
                           for x in node[1:]):
                    raise ValueError('unknown tail constructor')
                replacements += 1
                if discard_unused_field:
                    return node[1 if field == 'car' else 2]
                return [S('let*'), [[S('projection-head'), node[1]],
                                   [S('projection-tail'), node[2]]],
                        S('projection-head' if field == 'car' else 'projection-tail')]
        return [S(field), node]
    if original[0] != S('lambda') or len(original) != 3:
        raise ValueError('single lambda body required')
    result = [*original[:-1], tail(original[-1])]
    if replacements != 1:
        raise ValueError('exactly one result-pair constructor required')
    return result


def generate(text, native_guard=False, discard_unused_field=False):
    original = find_definition(loads('(' + text + ')', nil=None, true=None))[2]
    globals = ('gx#syntax-e', 'gx#apply-mark', 'gx#stx-wrap', 'gx#stx-source',
               'foldl__0', 'gx#syntax-wrap::t')
    if discard_unused_field:
        globals += ('gx#stx-apply-mark', '__foldl1')
    references = [[S('##global-var-ref'), S('projection-global-' + str(index))]
                  for index in range(len(globals))]
    forms = [[S('define'), S('projection-global-' + str(index)),
              [S('##make-global-var'), Quoted(S(name))]]
             for index, name in enumerate(globals)]
    captures = [(S('projection-original-' + str(index)), reference)
                for index, reference in enumerate(references)]
    forms += [[S('define'), snapshot, reference] for snapshot, reference in captures]
    guard = [S('and'), *[[S('eq?'), reference, snapshot]
                        for snapshot, reference in captures]]
    if native_guard:
        guard.insert(1, [S('projection-native-platform?')])
    for field in ('car', 'cdr'):
        name = S('projection-syntax-e/' + field)
        forms.append([S('define'), name,
                      projected_lambda(original, field, discard_unused_field)])
        forms.append([S('define'), [S('projection/' + field), S('stx')],
                      [S('if'), guard,
                       [name, S('stx')], [S(field), [references[0], S('stx')]]]])
    prefix = ''
    if native_guard:
        prefix = '''(define projection-native-platform?
  (c-lambda () bool
#<<projection-c-end
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
___result = 1;
#else
___result = 0;
#endif
projection-c-end
))
'''
    return prefix + '\n'.join(map(dump, forms)) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-guard', action='store_true')
    parser.add_argument('--discard-unused-field', action='store_true')
    args = parser.parse_args()
    with args.output.open('x') as out:
        out.write(generate(args.input.read_text(), args.native_guard,
                           args.discard_unused_field))
    print(json.dumps(dict(generated=True, scope='semantic-prototype-not-native-optimization',
                          omittedResultConstructors=1,
                          skippedFieldComputations=int(args.discard_unused_field))))


if __name__ == '__main__':
    main()
