"""Fail-closed source CI wiring and compiler selection contracts."""
import json
import os
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
        self.assertIn('.identity == $identity and .multipleVms == true', SOURCE)

    def test_multiple_vm_flag_and_artifact_checks(self):
        self.assertIn('--enable-multiple-vms', SOURCE)
        self.assertIn('--enable-multiple-vms', PUBLISH)
        self.assertIn('multipleVms:true', SOURCE)
        self.assertEqual(SOURCE.count("grep -Eq '^#define ___MULTIPLE_VMS"), 2)
        self.assertIn('any(. == "--enable-multiple-vms")', PUBLISH)

    def test_multiple_vm_setup_fix_is_in_both_build_paths(self):
        name = '0016-gambit-multiple-vms-global-setup-state.patch'
        self.assertIn('gambit_patches=(' + name + ')', SOURCE)
        self.assertIn(name, PUBLISH)
        patch = (ROOT / 'patches/gerbil-v19-darwin' / name).read_text()
        self.assertIn('+   ___P((___processor_state ___ps,', patch)
        self.assertIn('+          ___SCMOBJ e = make_global (___ps,', patch)

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


if __name__ == '__main__':
    unittest.main()
