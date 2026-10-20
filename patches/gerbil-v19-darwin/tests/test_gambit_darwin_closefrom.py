import pytest

from gambit_darwin_closefrom import BRANCH, GUARD, transform
from experiment_framework.spawn import CLOSEFROM_CASES, semantic_admission


def original():
    return '\nint ___closefrom\n(int start_fd) {\n#if defined(USE_closefrom)\nclosefrom(start_fd);\n' + BRANCH + '''
  max_fds = sysconf (_SC_OPEN_MAX);
  for (fd=start_fd; fd<max_fds; fd++) ___close_no_EINTR (fd);
  return 0;
#endif
}

int ___dup_no_EINTR (int fd) { return dup(fd); }
'''


def test_only_darwin_gnu_changes_and_original_scan_remains():
    text = transform(original())
    assert text.count('#if ' + GUARD) == 2
    assert 'for (fd=start_fd; fd<max_fds; fd++) ___close_no_EINTR (fd);' in text
    assert 'malloc' not in text and 'opendir' not in text
    assert text.index('int max_fds;') < text.index('if (___gb_darwin_close_open_fds (start_fd))')


def test_inventory_must_be_complete_before_any_close():
    text = transform(original())
    assert 'bytes >= sizeof (fds)' in text
    assert 'bytes % sizeof (fds[0]) != 0' in text
    assert text.index('if (fds[i].proc_fd < 0)') < text.index('if (fds[i].proc_fd >= start_fd)')
    assert 'struct proc_fdinfo fds[4096];' in text
    assert '__attribute__((noinline))' in text


def test_drift_and_double_application_are_rejected():
    with pytest.raises(ValueError):
        transform(original().replace('int max_fds;', 'int different;'))
    with pytest.raises(ValueError):
        transform(transform(original()))


def test_fd_contract_requires_every_case_and_terminal_ok():
    text = ''.join('CASE-OK ' + name + '\n' for name in CLOSEFROM_CASES)
    assert semantic_admission(text + 'OK closefrom-semantics\n', True, True, 'closefrom')
    assert not semantic_admission(text, True, True, 'closefrom')
    assert not semantic_admission(text + 'OK closefrom-semantics\n', False, True, 'closefrom')
    assert not semantic_admission(text + 'OK closefrom-semantics\n', True, False, 'closefrom')
