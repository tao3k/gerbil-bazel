from pathlib import Path
import pytest

from prepare_darwin_fork_fd import prepare


ROOT = Path(__file__).resolve().parents[3]


def original():
    return (ROOT / '.data/d1391-runtime-object-source/src/gambit/lib/os_io.c').read_text()


def test_spawn_eligibility_and_exec_semantics_unchanged():
    before = original()
    after = prepare(before)
    start = before.index('              if (spawn_errno == 0)')
    stop = before.index('          if ((pid = fork ()) < 0)', start)
    assert before[start:stop] in after
    assert '              execvp (argv[0], argv);' in after
    assert 'gb_closefrom_fork_child(fd+1) < 0) goto return_errno' in after
    assert '            ___closefrom (fd+1);\n#endif' in after


def test_boundary_drift_rejected():
    with pytest.raises(ValueError):
        prepare(original().replace('___closefrom (fd+1);', '___closefrom (fd);'))


def test_helper_is_bounded_and_fail_closed_without_parent_snapshot():
    text = Path(__file__).with_name('darwin_fork_fd_probe.h').read_text()
    assert 'bytes < (int) sizeof(fds)' in text
    assert 'bytes % sizeof(fds[0]) == 0' in text
    assert 'result = ___closefrom(start_fd)' in text
    assert 'sigprocmask(SIG_SETMASK, &previous, NULL)' in text
    assert 'getpid(), PROC_PIDLISTFDS, 0, fds, sizeof(fds)' in text
    assert 'malloc' not in text and 'rlimit' not in text
