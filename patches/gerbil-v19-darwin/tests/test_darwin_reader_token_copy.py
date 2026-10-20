import pytest
from prepare_darwin_reader_token_copy import NEW, prepare


def test_port_commit_follows_complete_validation():
    assert NEW.count('for (j=0; j<___arg5; ++j)') == 1
    commit = NEW.index('___PORT_CHAR_RCURLINE_FIELD')
    assert commit > NEW.index('if (j == ___arg5)')
    assert commit > NEW.index('code < 128 &&')
    assert NEW.index('___STRINGSET') < commit
    assert '___FIX(newline_count)' in NEW and 'start+last_newline+1' in NEW


def test_unrecognized_source_is_rejected():
    with pytest.raises(ValueError):
        prepare('not the selected reader')
