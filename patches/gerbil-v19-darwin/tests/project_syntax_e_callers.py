"""Focused generated-Scheme prototype; do not change original source inputs."""
import argparse
import json
from pathlib import Path

from sexpdata import Quoted, Symbol, loads
from generate_syntax_e_projection import dump

S = Symbol
TARGETS = {S('gx#core-expand1'), S('gx#core-expand-head')}


def uses(node, name):
    if isinstance(node, Quoted):
        return 0
    if isinstance(node, list):
        return sum(uses(child, name) for child in node)
    return int(node == name)


def rewrite(text):
    if '#\\' in text:
        raise ValueError('Scheme character literals require the native reader')
    forms = loads('(' + text + ')', nil=None, true=None)
    changes = []
    def transform(node, owner=None):
        if not isinstance(node, list):
            return node
        if len(node) >= 3 and node[0] == S('define'):
            owner = node[1]
        if owner in TARGETS and len(node) == 3 and node[0] == S('let'):
            bindings, inner = node[1:]
            if (isinstance(bindings, list) and len(bindings) == 1
                    and len(bindings[0]) == 2
                    and isinstance(bindings[0][1], list)
                    and len(bindings[0][1]) == 2
                    and bindings[0][1][0] == S('gx#syntax-e')
                    and isinstance(inner, list) and len(inner) >= 3
                    and inner[0] == S('let') and len(inner[1]) == 2):
                pair, call = bindings[0]
                head, tail = inner[1]
                if (len(head) == 2 and len(tail) == 2
                        and head[1] == [S('##car'), pair]
                        and tail[1] == [S('##cdr'), pair]
                        and uses(inner[2:], pair) == 0
                        and uses(inner[2:], tail[0]) == 0):
                    changes.append(str(owner))
                    return [S('let'), [[head[0], [S('projection/car'), call[1]]]],
                            *[transform(body, owner) for body in inner[2:]]]
        return [transform(child, owner) for child in node]
    result = transform(forms)
    if sorted(changes) != sorted(map(str, TARGETS)):
        raise ValueError(f'exact two hotspot transformations required: {changes}')
    return '\n'.join(map(dump, result)) + '\n', changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output, changes = rewrite(args.input.read_text())
    with args.output.open('x') as out:
        out.write(output)
    print(json.dumps(dict(scope='private-generated-hotspot-prototype', changes=changes)))


if __name__ == '__main__':
    main()
