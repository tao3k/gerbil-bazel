import pytest

from gambit_two_word_copy import GUARD, transform


SOURCE = '''___HIDDEN void mark_array
{
                while (words > 0)
                  {
                    *alloc++ = *body++;
                    words--;
                  }
}
___HIDDEN void mark_captured_continuation
'''


def test_exact_fallback_and_sequential_copy():
    changed = transform(SOURCE)
    assert '#if ' + GUARD in changed
    assert changed.index('alloc[0] = body[0]') < changed.index('alloc[1] = body[1]')
    assert 'words = 0;' in changed
    assert SOURCE.split('{', 1)[1].split('\n}', 1)[0] in changed


def test_repeated_transform_rejected():
    with pytest.raises(ValueError):
        transform(transform(SOURCE))


def test_unexpected_original_rejected():
    with pytest.raises(ValueError):
        transform(SOURCE.replace('words > 0', 'words >= 0'))
