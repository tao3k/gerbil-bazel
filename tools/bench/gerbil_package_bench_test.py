import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from gerbil_bench import cleanup, dumps
from gerbil_bench.execution import Budget, execute
from gerbil_bench.runner import load_profile, run, validate_inventory
from gerbil_bench.storage import atomic_json, digest, lease, relative


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / 'tools/bench').mkdir(parents=True)
        atomic_json(self.root / 'tools/bench/retention.json', dict(schema=1,
                    protectedPaths=[], protectedReceipts=[]))
        self.run = self.root / '.data/bench/runs/check'
        self.project = self.run / '0/project'
        self.project.mkdir(parents=True)
        (self.project / 'artifact.o').write_bytes(b'object')
        (self.run / 'build.log').write_text('OK\n')
        atomic_json(self.run / 'receipt.json', dict(state='terminal', protectedPaths=[]))

    def tearDown(self):
        self.temporary.cleanup()

    def test_paths_reject_absolute_and_escape(self):
        for value in ('/opt/gerbil', '../other', '.data/../../other'):
            with self.assertRaises(ValueError):
                relative(self.root, value)

    def test_reviewed_cleanup_preserves_receipts_logs(self):
        path = self.root / '.data/plan.json'
        atomic_json(path, cleanup.plan(self.root, ['check']))
        result = cleanup.apply(self.root, path, digest(path))
        self.assertTrue(result['complete'])
        self.assertFalse(self.project.exists())
        self.assertTrue((self.run / 'build.log').exists())
        self.assertTrue((self.run / 'receipt.json').exists())

    def test_changed_tree_denies_cleanup(self):
        path = self.root / '.data/plan.json'
        atomic_json(path, cleanup.plan(self.root, ['check']))
        (self.project / 'new.o').write_bytes(b'new')
        with self.assertRaises(ValueError):
            cleanup.apply(self.root, path, digest(path))
        self.assertTrue(self.project.exists())

    def test_protected_inputs_and_running_runs(self):
        for record in (dict(state='running', protectedPaths=[]),
                       dict(state='terminal', protectedPaths=['.data/bench/runs/check/0/project/artifact.o'])):
            atomic_json(self.run / 'receipt.json', record)
            with self.assertRaises(ValueError):
                cleanup.plan(self.root, ['check'])

    def test_symlink_denied(self):
        (self.project / 'outside').symlink_to(self.root)
        with self.assertRaises(ValueError):
            cleanup.plan(self.root, ['check'])

    def test_cleanup_rejects_escape_and_unmanaged_names(self):
        for name in ('../check', '/outside', 'missing'):
            with self.assertRaises((ValueError, FileNotFoundError)):
                cleanup.plan(self.root, [name])

    def test_cleanup_rejects_unapproved_digest(self):
        path = self.root / '.data/plan.json'
        atomic_json(path, cleanup.plan(self.root, ['check']))
        with self.assertRaises(ValueError):
            cleanup.apply(self.root, path, '0' * 64)
        self.assertTrue(self.project.exists())

    def test_active_lease_blocks_cleanup(self):
        with lease(self.root):
            with self.assertRaises(BlockingIOError):
                with lease(self.root, exclusive=True):
                    self.fail('exclusive cleanup acquired while run active')

    def test_retention_preserves_logs_and_drops_copies(self):
        result = cleanup.retain(self.root, 'check', 'receipts')
        self.assertEqual(result['state'], 'cleaned')
        self.assertEqual(result['removedProjects'], 1)
        self.assertFalse(self.project.exists())
        self.assertTrue((self.run / 'build.log').exists())

    def test_failed_retention_keeps_failed_round(self):
        atomic_json(self.run / 'receipt.json', dict(state='terminal', protectedPaths=[],
                    runs=[dict(index=0, passed=False)]))
        result = cleanup.retain(self.root, 'check', 'failed')
        self.assertEqual(result['state'], 'cleaned')
        self.assertTrue(self.project.exists())

    def test_auto_cleanup_defers_for_live_lease(self):
        with lease(self.root):
            result = cleanup.retain(self.root, 'check', 'receipts')
        self.assertEqual(result['state'], 'deferred')
        self.assertTrue(self.project.exists())

    def test_dump_cleanup_only_generated_dumps(self):
        (self.project / 'unit.c.123r.expand').write_bytes(b'dump')
        (self.project / 'unit.c').write_bytes(b'source')
        (self.project / 'report.json').write_text('{}')
        value = dumps.plan(self.root, ['.data/bench/runs/check'])
        self.assertEqual(len(value['targets']), 1)
        path = self.root / '.data/dump-plan.json'
        atomic_json(path, value)
        with patch('gerbil_bench.dumps.ensure_not_open'):
            result = dumps.apply(self.root, path, digest(path))
        self.assertTrue(result['complete'])
        self.assertTrue((self.project / 'unit.c').exists())
        self.assertTrue((self.project / 'artifact.o').exists())
        self.assertTrue((self.project / 'report.json').exists())

    def test_dump_cleanup_protects_baseline_graph(self):
        (self.project / 'unit.c.123r.expand').write_bytes(b'dump')
        pin = self.root / 'tools/bench/pin.json'
        atomic_json(pin, dict(artifact='.data/bench/runs/check/0/project/artifact.o'))
        atomic_json(self.root / 'tools/bench/retention.json', dict(schema=1,
                    protectedPaths=[], protectedReceipts=['tools/bench/pin.json']))
        value = dumps.plan(self.root, ['.data/bench/runs/check'])
        self.assertEqual(value['targets'], [])
        self.assertEqual(len(value['protectedFiles']), 1)

    def test_dump_revalidation_rejects_changed_file(self):
        dump = self.project / 'unit.c.123r.expand'
        dump.write_bytes(b'dump')
        path = self.root / '.data/dump-plan.json'
        atomic_json(path, dumps.plan(self.root, ['.data/bench/runs/check']))
        dump.write_bytes(b'changed dump')
        with self.assertRaises(ValueError):
            dumps.apply(self.root, path, digest(path))
        self.assertTrue(dump.exists())

    def test_legacy_package_cache_keeps_sources_and_receipts(self):
        (self.project / 'gerbil.pkg').write_text('(package: example)')
        (self.project / 'main.ss').write_text('source')
        cache = self.project / '.gerbil/lib'
        cache.mkdir(parents=True)
        (cache / 'compiled.o').write_bytes(b'compiled')
        value = dumps.plan(self.root, ['.data/bench/runs/check'], kind='package-caches')
        self.assertEqual(len(value['targets']), 1)
        plan_path = self.root / '.data/cache-plan.json'
        atomic_json(plan_path, value)
        with patch('gerbil_bench.dumps.ensure_not_open'):
            result = dumps.apply(self.root, plan_path, digest(plan_path))
        self.assertTrue(result['complete'])
        self.assertFalse(cache.exists())
        self.assertTrue((self.project / 'main.ss').exists())
        self.assertTrue((self.run / 'receipt.json').exists())

    def test_legacy_cache_live_process_blocks_apply(self):
        (self.project / 'gerbil.pkg').write_text('package')
        cache = self.project / '.gerbil/bin'
        cache.mkdir(parents=True)
        (cache / 'program').write_bytes(b'program')
        path = self.root / '.data/cache-plan.json'
        atomic_json(path, dumps.plan(self.root, ['.data/bench/runs/check'], kind='package-caches'))
        with patch('gerbil_bench.dumps.ensure_not_open', side_effect=ValueError('live process')):
            with self.assertRaises(ValueError):
                dumps.apply(self.root, path, digest(path))
        self.assertTrue(cache.exists())

    def execution(self, code, budget=None, **kwargs):
        return execute([sys.executable, '-c', code], self.root, os.environ.copy(),
                       self.root / 'test.log', budget or Budget(2, 1), **kwargs)

    def test_legacy_plan_rejects_directory_symlink(self):
        (self.root / '.data/alias').symlink_to(self.run, target_is_directory=True)
        with self.assertRaises(ValueError):
            dumps.plan(self.root, ['.data/alias'])

    def test_legacy_plan_requires_matching_action_and_kind(self):
        (self.project / 'unit.c.123r.expand').write_bytes(b'dump')
        value = dumps.plan(self.root, ['.data/bench/runs/check'])
        value['action'] = 'remove-legacy-package-build-caches'
        path = self.root / '.data/wrong-plan.json'
        atomic_json(path, value)
        with self.assertRaises(ValueError):
            dumps.apply(self.root, path, digest(path))

    def test_open_file_snapshot_denies_warning_and_live_descendant(self):
        for result in (dict(returncode=1, stdout=b'', stderr=b''),
                       dict(returncode=0, stdout=b'', stderr=b'permission denied'),
                       dict(returncode=0, stdout=('p123\nn' + str(self.project / 'artifact.o') + '\n').encode(), stderr=b'')):
            from subprocess import CompletedProcess
            with patch('gerbil_bench.dumps.subprocess.run', return_value=CompletedProcess([], **result)):
                with self.assertRaises(ValueError):
                    dumps.ensure_not_open([self.project])

    def test_pinned_receipt_blocks_managed_cleanup(self):
        pin = self.root / 'tools/bench/pin.json'
        atomic_json(pin, dict(artifact='.data/bench/runs/check/0/project/artifact.o'))
        atomic_json(self.root / 'tools/bench/retention.json', dict(schema=1,
                    protectedPaths=[], protectedReceipts=['tools/bench/pin.json']))
        with self.assertRaises(ValueError):
            cleanup.plan(self.root, ['check'])

    def test_optional_local_anchor_can_be_absent(self):
        atomic_json(self.root / 'tools/bench/retention.json', dict(schema=1,
                    protectedPaths=[], protectedReceipts=[], optionalReceipts=['patches/missing.json']))
        self.assertEqual(len(cleanup.plan(self.root, ['check'])['targets']), 1)

    def test_exception_retention_cleans_only_owned_terminal_run(self):
        def fail(*args, created, **kwargs):
            record = json.loads((self.run / 'receipt.json').read_text())
            created(record)
            raise RuntimeError('owned run failed')
        with patch('gerbil_bench.runner._run', side_effect=fail):
            with self.assertRaises(RuntimeError):
                run(self.root, None, None, 'check')
        self.assertFalse(self.project.exists())
        self.assertEqual(json.loads((self.run / 'receipt.json').read_text())['retention']['state'], 'cleaned')

    def test_validation_failure_does_not_adopt_existing_run(self):
        with patch('gerbil_bench.runner._run', side_effect=FileExistsError('existing ID')):
            with self.assertRaises(FileExistsError):
                run(self.root, None, None, 'check')
        self.assertTrue(self.project.exists())
        self.assertNotIn('retention', json.loads((self.run / 'receipt.json').read_text()))

    def test_success_requires_final_ok(self):
        self.assertTrue(self.execution("print('OK')", final_ok=True)['passed'])
        for code in ("print('not complete')", "print('CASE-FAIL bad'); print('OK')",
                     "print('OK'); raise SystemExit(1)"):
            self.assertFalse(self.execution(code, final_ok=True)['passed'])

    def test_first_log_deadline_kills_child(self):
        row = self.execution('import time; time.sleep(2)', Budget(1, .05))
        self.assertFalse(row['passed'])
        self.assertEqual(row['stop'], 'first-log-deadline')
        self.assertLess(row['wallSeconds'], 1)

    def test_complete_deadline_is_separate(self):
        row = self.execution("import time; print('OK', flush=True); time.sleep(2)", Budget(.1, 1))
        self.assertEqual(row['stop'], 'complete-time-deadline')

    def test_descendant_pipe_cannot_hide_root_exit(self):
        # Allow interpreter startup; the deadline must still kill the pipe holder.
        row = self.execution("import subprocess, sys; print('OK', flush=True); "
                             "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'])",
                             Budget(1, 1))
        self.assertEqual(row['exitCode'], 0)
        self.assertFalse(row['passed'])
        self.assertEqual(row['stop'], 'complete-time-deadline')

    def test_checked_in_mcp_inventory_matches_source(self):
        root = Path(__file__).resolve().parents[2]
        source = root / '.data/gerbil-mcp'
        if not source.exists():
            self.skipTest('optional local MCP checkout absent')
        profile = load_profile(root / 'tools/bench/profiles/mcp.json')
        self.assertEqual(len(validate_inventory(profile, source)), 39)

    def test_compile_marker_not_banner(self):
        budget = Budget(1, .05)
        row = self.execution("import time; print('banner', flush=True); time.sleep(1)", budget, compile_only=True)
        self.assertFalse(row['passed'])
        self.assertIsNone(budget.first_elapsed)

    def test_package_profiles_are_not_mcp_specific(self):
        for name in ('mcp', 'another_package'):
            path = self.root / f'{name}.json'
            atomic_json(path, dict(schema=1, name=name, source='.data/source',
                                  clean=['{gerbil}', 'clean'], build=['{gerbil}', 'build'],
                                  tests=[['{gerbil}', 'test', 'test/a-test.ss']]))
            self.assertEqual(load_profile(path)['name'], name)

    def test_inventory_rejects_missing_extra_duplicate(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'a-test.ss').write_text('test')
        (source / 'b-test.ss').write_text('test')
        profile = dict(tests=[['{gerbil}', 'test', 'a-test.ss']], testGlobs=['*-test.ss'])
        with self.assertRaises(ValueError):
            validate_inventory(profile, source)
        profile['tests'].append(['{gerbil}', 'test', 'b-test.ss'])
        self.assertEqual(len(validate_inventory(profile, source)), 2)
        profile['tests'].append(profile['tests'][0])
        with self.assertRaises(ValueError):
            validate_inventory(profile, source)

    def test_two_packages_end_to_end_with_fake_toolchain(self):
        # This validates orchestration only, never Scheme correctness or speed.
        tool = self.root / '.data/tool'
        (tool / 'bin').mkdir(parents=True)
        binary = tool / 'gerbil'
        binary.write_text('#!' + sys.executable + '\nimport pathlib, sys\n'
                          "if sys.argv[1] == 'build':\n"
                          " pathlib.Path('artifact.o').write_text('built')\n"
                          " print('... compile module')\n"
                          "else: print('OK')\n")
        binary.chmod(0o755)
        for name in ('gsc', 'gsi', 'gambuild-C'):
            (tool / 'bin' / name).write_text('fake compiler')
        gcc = tool / 'gcc'
        gcc.write_text('#!/bin/sh\nprintf "gcc (Free Software Foundation) test\\n"\n')
        gcc.chmod(0o755)
        selected = self.root / '.data/toolchain.json'
        atomic_json(selected, dict(binary='.data/tool/gerbil', home='.data/tool',
                                  driver='.data/tool/bin', binarySha256=digest(binary),
                                  gccEnvironment='BENCH_TEST_GCC'))
        with patch.dict(os.environ, BENCH_TEST_GCC=str(gcc)), patch('gerbil_bench.runner.workers', return_value=2):
            for name in ('first', 'second'):
                source = self.root / '.data' / name
                source.mkdir()
                (source / 'a-test.ss').write_text('a')
                (source / 'b-test.ss').write_text('b')
                profile = self.root / f'{name}.json'
                atomic_json(profile, dict(schema=1, name=name, source=f'.data/{name}',
                    clean=['{gerbil}', 'clean'], build=['{gerbil}', 'build'],
                    tests=[['{gerbil}', 'test', 'a-test.ss'], ['{gerbil}', 'test', 'b-test.ss']],
                    testGlobs=['*-test.ss'], artifactGlobs=['artifact.o']))
                receipt = run(self.root, profile, selected, name, rounds=2)
                self.assertEqual(receipt['decision'], 'ALLOW')
                self.assertEqual(len(receipt['runs']), 2)
                self.assertEqual(receipt['retention']['state'], 'cleaned')
                self.assertFalse((self.root / '.data/bench/runs' / name / '0/project').exists())
                self.assertNotIn(str(self.root), json.dumps(receipt))
                self.assertTrue((source / 'a-test.ss').exists())


if __name__ == '__main__':
    unittest.main()
