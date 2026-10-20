"""Experimental trace ranking; ranking never removes runtime guards."""


def self_typed_constructor_guard(state, lowering):
    """Prefer paths recognizing a fresh record by its constructor descriptor."""
    if len(state['freshStructures']) < 2:
        return False
    descriptors = {fields[0] for fields in state['freshStructures'].values()}
    return any(
        line.startswith(f'if ((___NOT(___EQP(___TYPEID({descriptor}),')
        and line.endswith('))) goto GB_TRACE_MISS;')
        for descriptor in descriptors
        for line in lowering['code']
    )


def select_candidate(candidates):
    if not candidates:
        raise ValueError('no accepted trace candidates')
    return min(candidates, key=lambda item: (
        not self_typed_constructor_guard(item[1], item[2]),
        len('\n'.join(item[2]['code'])),
        item[0],
    ))
