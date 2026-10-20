from pathlib import Path

from experiment_framework.tool_entry import KNOWN_WARNING, MARKER, commands, passed


def test_env_controls_use_same_absolute_interpreter():
    entries = commands(Path('/isolated/bin'))
    direct = entries['gxi-direct']
    assert entries['gerbil-env-absolute'][2:] == direct
    assert entries['gxpkg-env-absolute'][2:] == direct
    assert entries['gerbil-env-path'][2:] == ['gxi', *direct[1:]]


def test_marker_requires_success_and_no_extra_output():
    assert passed(0, MARKER + '\n')
    assert not passed(1, MARKER + '\n')
    assert not passed(0, 'warning\n' + MARKER + '\n')
    assert passed(0, MARKER + '\n' + KNOWN_WARNING + '\n')
