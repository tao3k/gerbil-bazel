"""Local packaging, immutable publication and workflow admission contracts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = json.loads((ROOT / 'tools/toolchain/profile.json').read_text())
SHELL = os.environ.get('TOOLCHAIN_TEST_SHELL', 'bash')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.artifacts = self.directory / 'artifacts'
        self.artifacts.mkdir()
        self.existing = self.directory / 'existing'
        self.existing.mkdir()
        self.bin = self.directory / 'bin'
        self.bin.mkdir()
        gh = self.bin / 'gh'
        gh.write_text('''#!/bin/bash
set -eu
if [[ "$1" == api ]]; then printf '%s\\n' "$API_RUN"; exit 0; fi
if [[ "$1 $2" == "release view" ]]; then exit "$EXISTS_STATUS"; fi
if [[ "$1 $2" == "release download" ]]; then
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == --dir ]]; then cp "$EXISTING"/* "$2"; exit 0; fi
    shift
  done
  exit 1
fi
if [[ "$1 $2" == "release create" ]]; then printf '%s\\n' "$@" > "$CREATED"; exit 0; fi
exit 99
''')
        gh.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + ':' + os.environ['PATH'],
                        EXISTS_STATUS='1', EXISTING=str(self.existing),
                        CREATED=str(self.directory / 'created'), GITHUB_SHA='a' * 40)
        self.tag = 'gerbil-v0.19-local-contract'
        archive = self.artifacts / (self.tag + '.tar.gz')
        archive.write_bytes(b'contract archive')
        sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.receipt = dict(identity='exact-source-compiler-patchset', releaseTag=self.tag,
                            archiveSha256=sha)
        self.write_receipt(self.artifacts)
        (self.artifacts / (self.tag + '.tar.gz.sha256')).write_text(sha + '  ' + archive.name + '\n')

    def write_receipt(self, directory):
        (directory / (self.tag + '.json')).write_text(json.dumps(self.receipt))

    def publish(self):
        return subprocess.run([SHELL, str(ROOT / 'tools/release/publish_toolchain.sh'),
                               str(self.artifacts)], env=self.env, text=True, capture_output=True)

    def test_new_release(self):
        self.env['RELEASE_COMMIT'] = 'b' * 40
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = (self.directory / 'created').read_text().splitlines()
        self.assertEqual(arguments[arguments.index('--target') + 1], 'b' * 40)

    def prepare_existing(self):
        self.env['EXISTS_STATUS'] = '0'
        self.write_receipt(self.existing)
        checksum = self.tag + '.tar.gz.sha256'
        (self.existing / checksum).write_bytes((self.artifacts / checksum).read_bytes())

    def test_existing_release_is_verified_not_overwritten(self):
        self.prepare_existing()
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('IMMUTABLE-RELEASE-REUSED', result.stdout)
        self.assertFalse((self.directory / 'created').exists())

    def test_wrong_existing_identity_is_denied(self):
        self.prepare_existing()
        self.receipt['identity'] = 'wrong'
        self.write_receipt(self.existing)
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertFalse((self.directory / 'created').exists())

    def test_wrong_existing_checksum_is_denied(self):
        self.prepare_existing()
        (self.existing / (self.tag + '.tar.gz.sha256')).write_text('0' * 64 + '  ' + self.tag + '.tar.gz\n')
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertFalse((self.directory / 'created').exists())

    def test_tampered_archive_is_denied_before_network(self):
        (self.artifacts / (self.tag + '.tar.gz')).write_bytes(b'tampered')
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertFalse((self.directory / 'created').exists())

    def test_receipt_checksum_mismatch_is_denied(self):
        self.receipt['archiveSha256'] = '0' * 64
        self.write_receipt(self.artifacts)
        self.assertNotEqual(self.publish().returncode, 0)

    def test_multiple_archives_are_denied(self):
        (self.artifacts / 'extra.tar.gz').write_bytes(b'extra')
        self.assertNotEqual(self.publish().returncode, 0)

    def test_workflow_is_exact_head_dual_platform_distribution(self):
        workflow = (ROOT / '.github/workflows/publish-v19.yml').read_text()
        ci = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertIn('workflow_run:', workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)
        self.assertIn("github.event.workflow_run.event == 'push'", workflow)
        self.assertIn('github.event.workflow_run.head_repository.full_name == github.repository', workflow)
        self.assertIn('.head_sha == $sha and .head_branch == "main"', (ROOT / 'tools/release/plan_publish.sh').read_text())
        for platform in ('linux-x86_64', 'darwin-aarch64'):
            self.assertIn(platform, workflow)
        self.assertIn('run-id: ${{ needs.plan.outputs.source_run }}', workflow)
        self.assertIn('name: v19-source-${{ runner.os }}', ci)
        self.assertIn('name: v19-source-${{ matrix.os }}', workflow)
        self.assertIn('RELEASE_COMMIT: ${{ needs.plan.outputs.commit }}', workflow)
        self.assertNotIn('./configure', workflow)

    def plan(self, **overrides):
        env = dict(self.env, GITHUB_OUTPUT=str(self.directory / 'outputs'),
                   GITHUB_REPOSITORY='tao3k/gerbil-bazel', SOURCE_RUN='', UPSTREAM_REF='')
        env.update(overrides)
        return subprocess.run([SHELL, str(ROOT / 'tools/release/plan_publish.sh')],
                              cwd=ROOT, env=env, text=True, capture_output=True)

    def test_manual_plan_defaults_to_both_platforms(self):
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        values = dict(line.split('=', 1) for line in (self.directory / 'outputs').read_text().splitlines())
        self.assertEqual([row['platform'] for row in json.loads(values['matrix'])['include']],
                         ['linux-x86_64', 'darwin-aarch64'])

    def test_manual_wrong_platform_or_revision_is_denied(self):
        self.assertNotEqual(self.plan(PLATFORM='unknown').returncode, 0)
        self.assertNotEqual(self.plan(UPSTREAM_REF='wrong').returncode, 0)

    def test_distribution_requires_exact_successful_main_push(self):
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        admitted = dict(head_sha=commit, head_branch='main', conclusion='success', name='CI', event='push')
        env = dict(self.env, GITHUB_OUTPUT=str(self.directory / 'outputs'),
                   GITHUB_REPOSITORY='tao3k/gerbil-bazel', SOURCE_RUN='123', UPSTREAM_REF='')
        for changes in ({}, {'head_sha':'0' * 40}, {'head_branch':'feature'},
                        {'conclusion':'failure'}, {'name':'Other'}, {'event':'pull_request'}):
            env['API_RUN'] = json.dumps(dict(admitted, **changes))
            result = subprocess.run([SHELL, str(ROOT / 'tools/release/plan_publish.sh')],
                                    cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode == 0, not changes, result.stderr)
            if not changes:
                values = dict(line.split('=', 1) for line in (self.directory / 'outputs').read_text().splitlines())
                self.assertEqual([row['runner'] for row in json.loads(values['matrix'])['include']],
                                 ['ubuntu-latest', 'ubuntu-latest'])

    def test_package_both_platforms_and_preserve_manifest(self):
        for system, platform in PROFILE['platforms'].items():
            with self.subTest(system=system):
                prefix = self.directory / system
                (prefix / 'bin').mkdir(parents=True)
                (prefix / 'current/lib').mkdir(parents=True)
                compiler = prefix / 'bin/gxi'
                compiler.write_text('#!/bin/sh\necho "Gerbil ' + PROFILE['gerbilRevision'][:7] + ' on Gambit local"\n')
                compiler.chmod(0o755)
                (prefix / 'activate').write_text((ROOT / 'tools/release/activate-gerbil.sh').read_text())
                receipt = dict(identity='qualified-' + system, sourceRevision=PROFILE['gerbilRevision'],
                               gambitRevision=PROFILE['gambitRevision'], patchsetHash='1' * 64,
                               platform=platform['capability'], buildProfile=platform['buildProfile'],
                               multipleVms=True, configureArguments=PROFILE['configure'] + platform['configure'])
                (prefix / 'ci-source-toolchain.json').write_text(json.dumps(receipt))
                output = self.directory / ('release-' + system)
                env = dict(self.env, GERBIL_PREFIX=str(prefix), GERBIL_RELEASE_DIRECTORY=str(output))
                result = subprocess.run([SHELL, str(ROOT / 'tools/release/package_toolchain.sh')],
                                        env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                archive, = output.glob('*.tar.gz')
                with tarfile.open(archive) as stream:
                    manifest = json.load(stream.extractfile('gerbil-v0.19-' + platform['capability'] + '/gerbil-toolchain-release.json'))
                self.assertEqual(manifest['upstreamRevision'], PROFILE['gerbilRevision'])
                self.assertEqual(manifest['platform']['os'], platform['capability'].split('-')[0])
                packaged = json.loads(next(output.glob('*.json')).read_text())
                self.assertEqual(packaged['identity'], receipt['identity'])
                self.assertEqual(packaged['archiveSha256'], hashlib.sha256(archive.read_bytes()).hexdigest())
                self.assertFalse(list(output.glob('.capability.*')))


if __name__ == '__main__':
    unittest.main()
