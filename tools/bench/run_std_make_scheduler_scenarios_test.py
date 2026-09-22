#!/usr/bin/env python3

import tempfile
import sys
import unittest
from unittest import mock
from pathlib import Path

import run_std_make_scheduler_scenarios as subject


class SchedulerObservationTest(unittest.TestCase):
    def result(self, *lines: tuple[int, str]) -> subject.CommandResult:
        return subject.CommandResult(
            exit_code=0,
            elapsed_ns=100,
            timed_out=False,
            events=tuple(
                {"elapsedNs": elapsed_ns, "line": line}
                for elapsed_ns, line in lines
            ),
        )

    def test_reports_staged_native_jobs(self) -> None:
        observation = subject.scheduler_observation(
            self.result(
                (10, "... compile upstream"),
                (20, "... enqueue compile job upstream"),
                (30, "... compile leaf"),
                (40, "... enqueue compile job leaf"),
                (50, "... execute compile job (compile-file upstream.scm)"),
            )
        )

        self.assertEqual(observation["observedOrder"], "staged")
        self.assertEqual(observation["gerbilCompileAnnouncementCount"], 2)
        self.assertEqual(observation["nativeJobEnqueueCount"], 2)
        self.assertEqual(observation["nativeJobStartCount"], 1)
        self.assertEqual(
            observation["nativeJobKindCounts"],
            {"compile-file": 1, "compile-batch": 0},
        )

    def test_reports_overlapped_native_jobs(self) -> None:
        observation = subject.scheduler_observation(
            self.result(
                (10, "... enqueue compile job upstream"),
                (20, "... execute compile job (compile-file upstream.scm)"),
                (30, "... enqueue compile job leaf"),
            )
        )

        self.assertEqual(observation["observedOrder"], "overlapped")

    def test_counts_batch_jobs_and_real_compiler_invocations(self) -> None:
        observation = subject.scheduler_observation(
            self.result(
                (10, "... execute compile job (compile-batch a.scm b.scm)"),
                (20, "invoke (gsc -c a.scm b.scm)"),
                (30, "... execute compile job (compile-batch c.scm)"),
                (40, "invoke (gsc -c c.scm)"),
            )
        )

        self.assertEqual(
            observation["nativeJobKindCounts"],
            {"compile-file": 0, "compile-batch": 2},
        )
        self.assertEqual(observation["nativeCompilerInvocationCount"], 2)

    def test_counts_concurrently_concatenated_log_records(self) -> None:
        observation = subject.scheduler_observation(
            self.result(
                (
                    10,
                    "#f... execute compile job (compile-batch a.scm)"
                    "... execute compile job (compile-batch b.scm)",
                ),
                (20, "invoke (gsc a.scm)invoke (gsc b.scm)"),
            )
        )

        self.assertEqual(observation["nativeJobStartCount"], 2)
        self.assertEqual(observation["nativeJobKindCounts"]["compile-batch"], 2)
        self.assertEqual(observation["nativeCompilerInvocationCount"], 2)

    def test_does_not_invent_an_order_without_native_events(self) -> None:
        observation = subject.scheduler_observation(
            self.result((10, "... enqueue compile job upstream"))
        )

        self.assertEqual(observation["observedOrder"], "unobserved")

    def test_parses_structured_build_observations_and_derives_bottleneck_metrics(self) -> None:
        observations = subject.build_observations(
            self.result(
                (
                    10,
                    "... build-observe phase=dependency event=end nodes=120 "
                    "edges=19 elapsedMs=23",
                ),
                (
                    20,
                    "... build-observe phase=native event=end jobs=240 workers=12 "
                    "completed=240 errors=0 peakActive=12 queueTotalMs=3408884 "
                    "queueMaxMs=28319 executionTotalMs=327721 executionMaxMs=2060 "
                    "workerConstructionTotalMs=0 workerConstructionMaxMs=0 "
                    "wallMs=28754 batches=1",
                ),
                (30, "... build-observe phase=build event=end elapsedMs=28841"),
            )
        )

        self.assertEqual(observations[0]["nodes"], 120)
        self.assertEqual(observations[1]["phase"], "native")
        self.assertEqual(observations[1]["elapsedNs"], 20)
        metrics = subject.derived_build_metrics(observations)
        self.assertEqual(metrics["nativeJobCount"], 240)
        self.assertAlmostEqual(metrics["nativeAverageQueueMs"], 14203.683333, places=5)
        self.assertAlmostEqual(metrics["nativeAverageExecutionMs"], 1365.504167, places=5)
        self.assertAlmostEqual(metrics["nativeWallShare"], 0.996983, places=5)
        self.assertAlmostEqual(metrics["nativeWorkerUtilization"], 0.949784, places=5)

    def test_terminal_summary_keeps_bulk_evidence_in_receipt(self) -> None:
        receipt = {
            "schema": subject.SCHEMA,
            "status": "failed",
            "cold": {
                "elapsedNs": 10_219_123_000,
                "derivedMetrics": {"nativeJobCount": 240},
                "events": [{"line": "large raw event"}],
            },
            "assertions": [
                {"name": "compile-complete", "passed": True},
                {"name": "runtime-object-unambiguous", "passed": False},
            ],
        }

        summary = subject.receipt_summary(receipt, Path("receipt.json"))

        self.assertEqual(summary["coldElapsedMs"], 10219.123)
        self.assertEqual(summary["derivedMetrics"], {"nativeJobCount": 240})
        self.assertEqual(
            summary["failedAssertions"], ["runtime-object-unambiguous"]
        )
        self.assertNotIn("events", summary)

    def test_terminal_stream_keeps_decisions_and_suppresses_per_file_noise(self) -> None:
        self.assertTrue(
            subject.should_stream_line(
                "... build-observe phase=native event=progress completed=12"
            )
        )
        self.assertTrue(subject.should_stream_line("*** ERROR IN worker -- failed"))
        self.assertFalse(subject.should_stream_line("... scan source ./module.ss"))
        self.assertFalse(subject.should_stream_line("... compile module"))

    def test_silence_observation_attributes_the_largest_gap(self) -> None:
        observation = subject.silence_observation(
            self.result((10, "first"), (80, "second"))
        )

        self.assertEqual(observation["maxGapNs"], 70)
        self.assertEqual(observation["beforeEvent"], "first")
        self.assertEqual(observation["afterEvent"], "second")

    def test_silence_observation_labels_watchdog_terminal(self) -> None:
        result = subject.CommandResult(
            exit_code=-1,
            elapsed_ns=100,
            timed_out=True,
            events=({"elapsedNs": 20, "line": "last output"},),
            timeout_reason="silence",
        )

        observation = subject.silence_observation(result)

        self.assertEqual(observation["maxGapNs"], 80)
        self.assertEqual(observation["afterEvent"], "<watchdog:silence>")
        self.assertEqual(observation["timeoutReason"], "silence")


class FixtureTest(unittest.TestCase):
    def test_timed_runner_reads_pseudo_terminal_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subject.run_timed(
                (sys.executable, "-c", "print('pty-output', flush=True)"),
                phase="pty-unit",
                cwd=Path(directory),
                environment={},
                timeout_seconds=5.0,
                silence_timeout_seconds=2.0,
                pseudo_terminal=True,
            )

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.output, "pty-output")

    def test_resolve_executable_reports_the_requested_tool(self) -> None:
        with mock.patch.object(subject.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "gsc is unavailable"):
                subject.resolve_executable(None, ("gsc",), name="gsc")

    def test_resolve_gerbil_gsc_uses_the_gxi_toolchain(self) -> None:
        with mock.patch.object(
            subject.subprocess,
            "run",
            return_value=mock.Mock(
                returncode=0, stdout="/toolchain/bin/gsc\n", stderr=""
            ),
        ), mock.patch.object(
            subject, "resolve_executable", return_value="/toolchain/bin/gsc"
        ) as resolve:
            self.assertEqual(
                subject.resolve_gerbil_gsc("/toolchain/bin/gxi", None),
                "/toolchain/bin/gsc",
            )
            resolve.assert_called_once_with(
                "/toolchain/bin/gsc", (), name="Gerbil Gambit gsc"
            )

    def test_darwin_environment_removes_nix_linker_pollution(self) -> None:
        environment = {
            "SDKROOT": "/nix/sdk",
            "CPATH": "/nix/include",
            "LIBRARY_PATH": "/nix/lib",
            "CC": "/opt/homebrew/bin/gcc-16",
        }
        with mock.patch.object(subject.platform, "system", return_value="Darwin"):
            sanitized = subject.sanitize_build_environment(environment)

        self.assertNotIn("SDKROOT", sanitized)
        self.assertNotIn("CPATH", sanitized)
        self.assertNotIn("LIBRARY_PATH", sanitized)
        self.assertEqual(sanitized["CC"], "/opt/homebrew/bin/gcc-16")
        self.assertEqual(sanitized["COMPILER_PATH"], "/usr/bin")

    def test_fixture_is_neutral_and_dependency_order_is_reversed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject.write_fixture(root)

            build_script = (root / "build.ss").read_text(encoding="utf-8")
            self.assertIn("\"leaf\" \"middle\" \"upstream\"", build_script)
            self.assertIn("parallelize: #t", build_script)
            self.assertNotIn("poo", build_script.lower())
            self.assertNotIn("asp", build_script.lower())
            consumer = (root / "consumer.ss").read_text(encoding="utf-8")
            self.assertIn('(load-module "std-make-scheduler-fixture/leaf")', consumer)
            self.assertIn("consumer value mismatch", consumer)
            self.assertIn("consumer-observe event=end status=passed modules=9", consumer)
            self.assertTrue((root / "failure.ss").is_file())

    def test_runtime_object_candidates_expose_stale_generations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base.ssi").write_text("interface", encoding="utf-8")
            (root / "base.o1").write_bytes(b"old")
            (root / "base.o2").write_bytes(b"new")
            (root / "base.o1.dSYM").mkdir()

            candidates = subject.runtime_object_candidates(str(root / "base.ssi"))

            self.assertEqual(
                [Path(candidate["path"]).name for candidate in candidates],
                ["base.o1", "base.o2"],
            )
            self.assertNotEqual(candidates[0]["sha256"], candidates[1]["sha256"])

    def test_artifact_manifest_excludes_matching_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root / "lib"
            library.mkdir()
            (library / "module.o1").write_bytes(b"native")
            (library / "module.o1.dSYM").mkdir()

            artifacts = subject.artifact_manifest(root, "*.o*")

            self.assertEqual([Path(item["path"]).name for item in artifacts], ["module.o1"])


if __name__ == "__main__":
    unittest.main()
