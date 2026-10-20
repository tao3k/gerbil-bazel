import pytest

from gambit_child_path_spawn import transform
from experiment_framework.spawn import EXPECTED_CASES, semantic_admission


@pytest.fixture
def original():
    return '''#if defined(__APPLE__) && defined(__MACH__)
#define USE_DARWIN_POSIX_SPAWN
#endif
___SCMOBJ ___device_stream_setup_from_process
{
#ifdef USE_DARWIN_POSIX_SPAWN
      if (argv[0][n] == 0)
        use_posix_spawn = 0;
              if (spawn_errno == 0)
                spawn_errno =
                  posix_spawnp (&pid,
                                argv[0],
                                &actions,
                                &attributes,
                                argv,
                                env != NULL ? env : environ);
              if (attributes_initialized)
                posix_spawnattr_destroy (&attributes);
              if (actions_initialized)
                posix_spawn_file_actions_destroy (&actions);
              if (spawn_errno != 0)
                {
                  errno = spawn_errno;
                }
          else
#endif
          if ((pid = fork ()) < 0) {}
}
'''


def test_private_candidate_uses_child_env_not_mutable_caller_path(original):
    generated = transform(original)
    assert 'getenv(' not in generated
    assert 'env[i] + 5' in generated
    assert 'posix_spawn(pid, candidate, actions, attributes, argv, env)' in generated
    assert 'else if (result != ENOENT && result != ENOTDIR)' in generated
    assert 'return denied ? EACCES : result;' in generated
    assert '___ALLOC_MEM' in generated and '___FREE_MEM(candidate)' in generated


def test_darwin_gnu_only_and_original_shell_fallback_survive(original):
    generated = transform(original)
    assert '#if defined(USE_DARWIN_POSIX_SPAWN) && defined(__GNUC__) && !defined(__clang__)' in generated
    assert '#if !defined(__GNUC__) || defined(__clang__)\n          use_posix_spawn = 0;' in generated
    assert generated.index('posix_spawn_file_actions_destroy') < generated.index('goto gb_child_path_fork;')
    assert '(spawn_errno == ENOEXEC || spawn_errno == ENAMETOOLONG)' in generated
    assert generated.count('if ((pid = fork ()) < 0)') == 1
    assert 'if (!name_length) return ENOENT;' in generated


def test_drift_and_reapplication_are_rejected(original):
    with pytest.raises(ValueError):
        transform(original.replace('use_posix_spawn = 0;', 'different = 0;'))
    with pytest.raises(ValueError):
        transform(transform(original))


def test_semantic_receipt_requires_every_named_case_and_final_ok():
    text = ''.join('CASE-OK ' + name + '\n' for name in EXPECTED_CASES)
    completed = text + 'OK child-path-spawn-semantics\n'
    assert semantic_admission(completed, True, True)
    assert not semantic_admission(completed, False, True)
    assert not semantic_admission(completed, True, False)
    assert not semantic_admission(text, True, True)
    assert not semantic_admission(completed.replace('CASE-OK child-path\n',
                                                   'CASE-OK empty-command\n'), True, True)
    assert not semantic_admission('*** ERROR\n' + completed, True, True)


def test_actual_assertions_are_flushed_not_synthetic_progress():
    from pathlib import Path
    source = Path(__file__).with_name('child_path_spawn_semantics.ss').read_text()
    assert '(display "CASE-OK ") (displayln label) (force-output)' in source
    assert source.index('(unless (equal? expected actual)') < source.index('(force-output)')
