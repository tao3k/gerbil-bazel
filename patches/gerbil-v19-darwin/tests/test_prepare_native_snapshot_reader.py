import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[2]


def prepare_fixture(directory, *options):
    source = directory / 'source'
    (source / 'gsc').mkdir(parents=True)
    (source / 'gsi').mkdir()
    (source / 'gsc/_gsc.scm').write_text('(##include "../gsi/main.scm")\n')
    (source / 'gsi/main.scm').write_text('''                      (define (do-compile-file-to-target x)
                               (compile-file-to-target
                                   file
                                   options: (add-seq-num opts)
                                   output: output))
                      (define (do-build-executable x) x)
    (combine-option! 'pkg-config-path)
                           (module-ref symbol) (linker-name string)
                      (let loop2 ((lst arguments)) #f)
''')
    output = directory / 'output'
    subprocess.run([sys.executable, str(TESTS / 'prepare_native_generated_c_gsc.py'),
                    '--source', str(source), '--output', str(output), *options], check=True)
    return output


def test_default_reader_bytes_are_unchanged():
    with tempfile.TemporaryDirectory(prefix='snapshot-prepare-test-', dir=ROOT / '.data') as tmp:
        output = prepare_fixture(Path(tmp))
        assert (output / 'gsc/gambit-generated-c-reads.scm').read_bytes() == (
            TESTS / 'gambit-generated-c-reads.scm').read_bytes()
        assert not (output / '.git').exists()


def test_snapshot_option_really_applies_patch_in_own_git_root():
    with tempfile.TemporaryDirectory(prefix='snapshot-prepare-test-', dir=ROOT / '.data') as tmp:
        output = prepare_fixture(Path(tmp), '--native-digests', '--planned-producers', '--snapshot-reader')
        reader = (output / 'gsc/gambit-generated-c-reads.scm').read_text()
        assert '(apply original (cons snapshot (cdr args)))' in reader
        assert 'unsupported snapshot compiler reader' in reader
        assert '(path-extension path)' in reader
        patch = TESTS.parent / '0025-gambit-darwin-generated-c-snapshot-reader.patch'
        subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)], cwd=output, check=True)
        subprocess.run(['git', 'apply', '--reverse', str(patch)], cwd=output, check=True)
        assert (output / 'gsc/gambit-generated-c-reads.scm').read_bytes() == (
            TESTS / 'gambit-generated-c-reads.scm').read_bytes()


def test_closed_link_is_late_and_does_not_install_singleton_hooks():
    with tempfile.TemporaryDirectory(prefix='closed-link-prepare-test-', dir=ROOT / '.data') as tmp:
        output = prepare_fixture(Path(tmp), '--native-digests', '--snapshot-reader', '--closed-link-only')
        main = (output / 'gsi/main.scm').read_text()
        assert 'generated-c-native-compile-file-to-target' not in main
        assert 'generated-c-native-link-arguments' not in main
        assert 'generated-c-native-select-producer-options' not in main
        assert main.index('(c#target-name target)') < main.index('(let loop2')
        assert '(closed-c-binding string)' in main
        assert '(closed-c-entry string)' in main
        assert "'(closed-c-binding closed-c-entry)" in main
        source = (output / 'gsc/_gsc.scm').read_text()
        assert 'gambit-generated-c-closed-link.scm' in source
        assert 'gambit-generated-c-native.scm' not in source
        assert 'gambit-generated-c-planned-producer.scm' not in source
        assert 'gambit-generated-c-members.scm' not in source
        assert (output / 'gsc/gambit-generated-c-closed-link.scm').read_bytes() == (
            TESTS / 'gambit-generated-c-closed-link.scm').read_bytes()


def test_member_tools_require_closed_link_before_creating_output():
    with tempfile.TemporaryDirectory(prefix='member-prepare-test-', dir=ROOT / '.data') as tmp:
        directory = Path(tmp)
        with pytest.raises(subprocess.CalledProcessError):
            prepare_fixture(directory, '--native-digests', '--snapshot-reader', '--member-tools')
        assert not (directory / 'output').exists()


def test_member_patch_full_reverse_forward_parity():
    with tempfile.TemporaryDirectory(prefix='member-prepare-test-', dir=ROOT / '.data') as tmp:
        output = prepare_fixture(Path(tmp), '--native-digests', '--snapshot-reader',
                                 '--closed-link-only', '--member-tools')
        files = ['gsc/_gsc.scm', 'gsc/gambit-generated-c-members.scm',
                 'gsc/gambit-generated-c-closed-link.scm']
        before = {name: (output / name).read_bytes() for name in files}
        assert before[files[1]] == (TESTS / 'gambit-generated-c-members.scm').read_bytes()
        patches = [TESTS.parent / name for name in (
            '0041-gambit-darwin-closed-link-member-proofs.patch',
            '0042-gambit-darwin-member-link-request-guard.patch',
        )]
        for patch in reversed(patches):
            for args in [('--reverse', '--check'), ('--reverse',)]:
                subprocess.run(['git', 'apply', *args, str(patch)], cwd=output, check=True)
        assert not (output / files[1]).exists()
        assert (output / files[2]).read_bytes() == (
            TESTS / 'gambit-generated-c-closed-link.scm').read_bytes()
        for patch in patches:
            for args in [('--check',), ()]:
                subprocess.run(['git', 'apply', *args, str(patch)], cwd=output, check=True)
        assert {name: (output / name).read_bytes() for name in files} == before
