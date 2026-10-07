"""Count declared test cases structurally, excluding comments and fixture strings."""
from pathlib import Path
import sexpdata


def case_names(path):
    found = []

    def walk(form):
        if not isinstance(form, list) or not form:
            return
        head = form[0]
        if head in (sexpdata.Symbol('quote'), sexpdata.Symbol('quasiquote'),
                    sexpdata.Symbol('quote-syntax')):
            return
        if head == sexpdata.Symbol('test-case'):
            if len(form) < 2 or type(form[1]) is not str:
                raise ValueError(f'nonliteral test case in {Path(path).name}')
            found.append(form[1])
        for child in form:
            walk(child)

    for form in sexpdata.parse(Path(path).read_text()):
        walk(form)
    return found
