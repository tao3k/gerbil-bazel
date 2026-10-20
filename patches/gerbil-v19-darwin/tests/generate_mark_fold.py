"""Private canonical mark-fold specialization; retain every wrapper result."""
from sexpdata import Quoted, Symbol, loads
from generate_syntax_e_projection import dump

S = Symbol


def definition(forms, name):
    found = []
    def visit(node):
        if isinstance(node, list):
            if len(node) == 3 and node[:2] == [S('define'), S(name)]:
                found.append(node)
            else:
                for child in node:
                    visit(child)
    visit(forms)
    if len(found) != 1 or found[0][2][0] != S('lambda'):
        raise ValueError('unique generated lambda required: ' + name)
    return found[0][2]


def substitute(node, bindings):
    if isinstance(node, Quoted):
        return node
    if isinstance(node, list):
        return [substitute(child, bindings) for child in node]
    return bindings.get(node, node) if isinstance(node, Symbol) else node


def generate(text):
    forms = loads('(' + text + ')', nil=None, true=None)
    wrap = definition(forms, 'gx#stx-wrap')
    apply = definition(forms, 'gx#stx-apply-mark')
    source = definition(forms, 'gx#stx-source')
    if len(wrap) != 3 or len(wrap[1]) != 2 or len(apply) != 3 or len(apply[1]) != 2:
        raise ValueError('bounded source shape required')
    stx, marks = wrap[1]
    callback = wrap[2][1]
    if (len(wrap[2]) != 4 or wrap[2][0] != S('foldl__0') or
            wrap[2][2:] != [stx, marks] or callback[0] != S('lambda') or
            callback[2] != [S('gx#stx-apply-mark'), callback[1][1], callback[1][0]]):
        raise ValueError('canonical one-list mark callback required')
    source_calls = 0
    def inline_source(node):
        nonlocal source_calls
        if isinstance(node, list):
            if node and node[0] == S('gx#stx-source'):
                if node != [S('gx#stx-source'), apply[1][0]]:
                    raise ValueError('source argument must be the existing value')
                source_calls += 1
                return substitute(source[2], {source[1][0]: apply[1][0]})
            return [inline_source(child) for child in node]
        return node
    body = inline_source(apply[2])
    if source_calls != 1:
        raise ValueError('exact source-read site required')
    inline = substitute(body, {apply[1][0]: S('mark-fold-value'),
                               apply[1][1]: S('mark-fold-mark')})
    names = ('foldl__0', '__foldl1', 'gx#stx-apply-mark', 'gx#stx-source',
             'gx#syntax-wrap::t')
    prefix = '''(define mark-fold-native-platform?
  (c-lambda () bool
#<<mark-fold-c-end
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
___result = 1;
#else
___result = 0;
#endif
mark-fold-c-end
))
(define mark-fold-native-enabled? (mark-fold-native-platform?))
'''
    captures = []
    guards = [S('mark-fold-native-enabled?')]
    for index, name in enumerate(names):
        handle, saved = S('mark-fold-global-' + str(index)), S('mark-fold-original-' + str(index))
        reference = [S('##global-var-ref'), handle]
        captures += [[S('define'), handle, [S('##make-global-var'), Quoted(S(name))]],
                     [S('define'), saved, reference]]
        guards += [[S('eq?'), reference, saved]]
    loop = [S('let'), S('mark-fold-loop'),
            [[S('mark-fold-rest'), marks], [S('mark-fold-value'), stx]],
            [S('if'), [S('pair?'), S('mark-fold-rest')],
             [S('let*'), [[S('mark-fold-mark'), [S('##car'), S('mark-fold-rest')]],
                         [S('mark-fold-next'), [S('##cdr'), S('mark-fold-rest')]],
                         [S('mark-fold-result'), inline]],
              [S('mark-fold-loop'), S('mark-fold-next'), S('mark-fold-result')]],
             S('mark-fold-value')]]
    rewritten = [S('lambda'), wrap[1], [S('if'), [S('and'), *guards], loop, wrap[2]]]
    return dump(rewritten), prefix + '\n'.join(map(dump, captures)) + '\n'
