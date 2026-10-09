"""Fail-closed source CI wiring and compiler selection contracts."""
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tools/ci/build_source_toolchain.sh'
CI = (ROOT / '.github/workflows/ci.yml').read_text()
PUBLISH = (ROOT / '.github/workflows/publish-v19.yml').read_text()
SOURCE = SCRIPT.read_text()


class SourceToolchainTests(unittest.TestCase):
    def test_native_contract_has_no_ripgrep_dependency(self):
        script = (ROOT / 'patches/gerbil-v19-darwin/tests/check_static_object_reuse.sh').read_text()
        self.assertNotRegex(script, r'\brg\s')
        self.assertEqual(script.count("grep -Ec '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$'"), 2)
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'concurrent.log'
            for content, expected in (('GAMBIT-STATIC-OBJECT-HIT\n', 0),
                                      ('GAMBIT-STATIC-OBJECT-MISS\n', 0),
                                      ('GAMBIT-STATIC-OBJECT-HIT\nGAMBIT-STATIC-OBJECT-MISS\n', 1),
                                      ('unrelated\n', 1)):
                log.write_text(content)
                result = subprocess.run(['bash', '-c',
                                         'test "$(grep -Ec \'^GAMBIT-STATIC-OBJECT-(HIT|MISS)$\' "$1")" = 1',
                                         'contract', str(log)], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_static_contract_accepts_installed_current_symlink(self):
        script = ROOT / 'patches/gerbil-v19-darwin/tests/check_static_object_reuse.sh'
        data = ROOT / '.data'
        data.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data) as temp:
            directory = Path(temp)
            home = directory / 'installed'
            (home / 'bin').mkdir(parents=True)
            (home / 'include').mkdir()
            (home / 'include/gambit.h').write_text('/* selected header */\n')
            compiler = home / 'bin/gsc'
            compiler.write_text('#!/bin/sh\nexit 73\n')
            compiler.chmod(0o755)
            current = directory / 'current'
            current.symlink_to(home, target_is_directory=True)
            bin_alias = directory / 'selected-bin'
            bin_alias.symlink_to(home / 'bin', target_is_directory=True)
            source = directory / 'probe.c'
            source.write_text('int probe(void) { return 1; }\n')
            for index, bin_path in enumerate((current / 'bin', bin_alias)):
                output = directory / ('receipt-' + str(index))
                result = subprocess.run(['bash', str(script), str(bin_path), str(output),
                                         str(current), str(source)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 73, result.stderr)
                self.assertTrue((output / 'control.log').is_file())
                self.assertTrue((output / 'selected-toolchain.sha256').is_file())
            missing = subprocess.run(['bash', str(script), str(directory / 'missing'),
                                      str(directory / 'missing-output'), str(current), str(source)],
                                     capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((directory / 'missing-output').exists())

    def test_release_builds_and_hashes_frozen_darwin_bundle(self):
        identity = PUBLISH.split('patchset_sha="$({', 1)[1].split('} | git hash-object --stdin)', 1)[0]
        self.assertIn('if [[ "$TARGET_PLATFORM" == darwin-aarch64 ]]', identity)
        self.assertIn('done < patches/gerbil-v19-darwin/static-c-snapshot-candidate.series', identity)
        for name in ('static-reuse-helper-install.patch', 'static-snapshot-path-fallback.patch'):
            self.assertIn(name, identity)
            self.assertRegex(PUBLISH, r'git -C .* apply .*' + re.escape(name))
        self.assertIn('done < "$GITHUB_WORKSPACE/patches/gerbil-v19-darwin/static-c-snapshot-candidate.series"', PUBLISH)
        self.assertIn('--lock-sha256 a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2', PUBLISH)
        self.assertNotIn('apply "$GITHUB_WORKSPACE/patches/gerbil-v19-darwin/0015-', PUBLISH)

    def test_review_hardening_does_not_rewrite_frozen_lock(self):
        self.assertIn('static-reuse-helper-install.patch', SOURCE)
        self.assertIn('static-snapshot-path-fallback.patch', SOURCE)
        self.assertLess(SOURCE.index('done < "$root/patches/gerbil-v19-darwin/static-c-snapshot-candidate.series"'),
                        SOURCE.index('gambit_patches+=(patches/gerbil-v19-darwin/static-snapshot-path-fallback.patch)'))
        self.assertIn('check_static_snapshot_path_fallback.sh', CI)

    def test_darwin_installs_required_helpers_and_linux_is_unchanged(self):
        patch = (ROOT / 'patches/gerbil-v19-darwin/static-reuse-helper-install.patch').read_text()
        block = '\n'.join(line[1:] for line in patch.splitlines()
                          if line.startswith('+') and not line.startswith('+++'))
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / 'gambit/bin'
            source.mkdir(parents=True)
            destination = directory / 'installed/bin'
            destination.mkdir(parents=True)
            helpers = ('gambit-static-object-reuse', 'gambit-file-sha256')
            for name in helpers:
                path = source / name
                path.write_text('#!/bin/sh\nexit 0\n')
                path.chmod(0o755)
            env = dict(os.environ, GERBIL_BUILD_PREFIX=str(destination.parent))
            def install(platform):
                command = 'uname() { printf "%s\\n" ' + platform + '; }; die() { exit 77; };\n' + block
                return subprocess.run(['bash', '-ec', command], cwd=directory,
                                      env=env, capture_output=True, text=True)
            linux = install('Linux')
            self.assertEqual(linux.returncode, 0, linux.stderr)
            self.assertEqual(list(destination.iterdir()), [])
            darwin = install('Darwin')
            self.assertEqual(darwin.returncode, 0, darwin.stderr)
            for name in helpers:
                self.assertEqual((destination / name).read_bytes(), (source / name).read_bytes())
                self.assertTrue(os.access(destination / name, os.X_OK))
            for name in helpers:
                saved = source / (name + '.saved')
                (source / name).rename(saved)
                self.assertEqual(install('Darwin').returncode, 77)
                saved.rename(source / name)

    def test_static_snapshot_series_is_locked_and_darwin_only(self):
        before_darwin, darwin = SOURCE.split('if [[ "$platform" == Darwin ]]; then', 1)
        self.assertNotIn('static-c-snapshot-candidate.series', before_darwin)
        self.assertIn('static-c-snapshot-candidate.series', darwin)
        self.assertIn('--lock-sha256 a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2', darwin)
        self.assertIn('apply --reverse', SOURCE)
        self.assertIn('gambit-file-sha256', SOURCE)
        self.assertNotIn('export GAMBIT_DARWIN_STATIC_OBJECT_REUSE', SOURCE)
        self.assertIn('check_static_object_reuse.sh', CI)

    def test_revision_matches_audited_profile(self):
        profile = json.loads((ROOT / 'patches/gerbil-v19-darwin/runtime-object-reuse.json').read_text())
        self.assertIn('GERBIL_SOURCE_REVISION: ' + profile['gerbilRevision'], CI)
        self.assertIn('GAMBIT_SOURCE_REVISION: ' + profile['gambitRevision'], CI)
        self.assertIn('default: ' + profile['gerbilRevision'], PUBLISH)

    def test_main_ci_builds_source_not_release_or_bottle(self):
        bazel_job = CI.split('  lock-linux-seed:', 1)[0]
        self.assertNotIn('/releases/download/', bazel_job)
        self.assertNotIn('Install the tao3k Gerbil bottle', bazel_job)
        self.assertEqual(bazel_job.count('gerbil_provider: source-host'), 2)
        self.assertNotIn('${{ runner.temp }}', bazel_job)
        self.assertIn('GERBIL_PREFIX=$RUNNER_TEMP/gerbil-ci-install', bazel_job)
        for mode in ('prepare', 'build', 'verify'):
            self.assertIn('bash tools/ci/build_source_toolchain.sh ' + mode, bazel_job)

    def test_cache_cannot_restore_another_revision_or_patchset(self):
        self.assertIn('${{ github.sha }}-${{ steps.source.outputs.cache_identity }}', CI)
        self.assertNotIn('restore-keys:', CI)
        self.assertIn('$GERBIL_SOURCE_REVISION-$GAMBIT_SOURCE_REVISION-$compiler_hash-$patchset_hash', SOURCE)
        self.assertIn('.identity == $identity and .multipleVms == $multipleVms', SOURCE)

    def test_multiple_vm_flag_and_artifact_checks(self):
        self.assertIn('--enable-multiple-vms', SOURCE)
        self.assertIn('--enable-multiple-vms', PUBLISH)
        self.assertIn('multipleVms:$multipleVms', SOURCE)
        self.assertEqual(SOURCE.count("grep -Eq '^#define ___MULTIPLE_VMS"), 2)
        self.assertIn('"--enable-multiple-vms"] -', PUBLISH)
        self.assertIn('multiple_vms=true', SOURCE)
        self.assertNotIn('multiple_vms=false', SOURCE)
        self.assertIn('--enable-single-host=0 --enable-multiple-vms --enable-smp)', SOURCE)
        self.assertIn('portable-full-single-host-unlimited-multiple-vms', PUBLISH)
        self.assertIn('gxi tools/ci/multiple_vm_globals.ss', CI)
        self.assertIn('gxi "$GITHUB_WORKSPACE/tools/ci/multiple_vm_globals.ss"', PUBLISH)

    def test_multiple_vm_setup_fix_is_in_both_build_paths(self):
        name = 'gambit-v19-multiple-vms-global-setup-state.patch'
        self.assertIn(name, SOURCE)
        self.assertIn(name, PUBLISH)
        patch = (ROOT / 'patches' / name).read_text()
        self.assertIn('!defined(___SINGLE_VM)', patch)
        self.assertIn('+   ___P((___MAKE_GLOBAL_PSD', patch)
        self.assertIn('+          ___SCMOBJ e = make_global (___MAKE_GLOBAL_PSV', patch)
        self.assertNotIn('0016-gambit-multiple-vms-global-setup-state.patch', PUBLISH)
        common = SOURCE.split('if [[ "$platform" == Darwin ]]; then', 1)[0]
        self.assertIn(name, common)

    def test_global_capacity_growth_patch_is_shared_and_address_stable(self):
        name = 'gambit-v19-multiple-vms-global-capacity.patch'
        patch = (ROOT / 'patches' / name).read_text()
        self.assertIn(name, SOURCE)
        self.assertIn(name, PUBLISH)
        self.assertIn(name, SOURCE.split('if [[ "$platform" == Darwin ]]; then', 1)[0])
        self.assertIn('___GLO_SEGMENT_SIZE', patch)
        self.assertIn('ensure_glo_segment', patch)
        self.assertIn('free_glo_tables', patch)
        self.assertIn('segment+offset', patch)
        self.assertIn('__atomic_store_n (&vms->glos, table, __ATOMIC_RELEASE)', patch)
        added_lines = '\n'.join(line for line in patch.splitlines()
                                if line.startswith('+') and not line.startswith('+++'))
        self.assertNotIn('20000', added_lines)

    def test_darwin_patch_chain_includes_reuse_and_command_driver(self):
        for name in ('0007-gerbil-darwin-executable-runtime-object-reuse.patch',
                     '0008-gerbil-darwin-pure-module-original-path.patch',
                     '0015-gambit-darwin-literal-build-substitution.patch'):
            self.assertIn(name, SOURCE)
            self.assertIn(name, PUBLISH)
        self.assertLess(SOURCE.index('0007-gerbil'), SOURCE.index('0008-gerbil'))
        self.assertIn('if [[ "$platform" == Darwin ]]; then', SOURCE)

    def test_clang_is_rejected_before_checkout_or_build(self):
        with tempfile.TemporaryDirectory() as temp:
            compiler = Path(temp) / 'fake-clang'
            compiler.write_text('#!/bin/sh\nprintf "#define __GNUC__ 4\\n#define __clang__ 1\\n"\n')
            compiler.chmod(0o755)
            env = os.environ.copy()
            env.update(CC=str(compiler), GERBIL_SOURCE_REVISION='1' * 40,
                       GAMBIT_SOURCE_REVISION='2' * 40,
                       GERBIL_SOURCE_DIRECTORY=str(Path(temp) / 'source'),
                       GERBIL_PREFIX=str(Path(temp) / 'install'))
            result = subprocess.run(['bash', str(SCRIPT), 'build'], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('requires GNU GCC, not clang', result.stderr)
            self.assertFalse((Path(temp) / 'source').exists())

    def test_gambit_gate_uses_bootstrap_gsi_and_rejects_missing_artifacts(self):
        block = re.search(r'      if \[\[ "\$target" == gambit \]\]; then\n(.*?)\n      fi',
                          SOURCE, re.S).group(1)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in ('build/bin/gsc', 'bootstrap/bin/gsi'):
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('#!/bin/sh\nprintf "artifact-version\\n"\n')
                path.chmod(0o755)
            library = directory / 'build/lib/libgambit.a'
            library.parent.mkdir(parents=True)
            library.touch()
            def check():
                return subprocess.run(['bash', '-ec', block], cwd=directory,
                                      capture_output=True, text=True)
            valid = check()
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(valid.stdout.count('artifact-version'), 2)
            for name in ('build/bin/gsc', 'bootstrap/bin/gsi', 'build/lib/libgambit.a'):
                path = directory / name
                saved = path.with_suffix('.saved')
                path.rename(saved)
                failed = check()
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('Gambit build missing', failed.stderr)
                saved.rename(path)


if __name__ == '__main__':
    unittest.main()
