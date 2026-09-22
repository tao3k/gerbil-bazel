#!/usr/bin/env python3

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_real_consumer_ab as subject


class RealConsumerABTest(unittest.TestCase):
    def test_host_load_gate_uses_one_and_five_minute_windows(self) -> None:
        with mock.patch.object(subject.os, "getloadavg", return_value=(11.5, 12.0, 30.0)):
            observation = subject.host_load_observation(12, 1.0)

        self.assertTrue(observation["passed"])
        self.assertEqual(observation["gatedWindowsMinutes"], [1, 5])
        self.assertEqual(observation["maxAllowedLoad"], 12.0)

        with mock.patch.object(subject.os, "getloadavg", return_value=(12.1, 11.0, 1.0)):
            observation = subject.host_load_observation(12, 1.0)
        self.assertFalse(observation["passed"])

    def test_host_load_gate_is_opt_in(self) -> None:
        with mock.patch.object(subject.os, "getloadavg", return_value=(100.0, 100.0, 100.0)):
            observation = subject.host_load_observation(12, None)

        self.assertTrue(observation["passed"])
        self.assertIsNone(observation["maxAllowedLoad"])

    def test_candidate_timeout_only_bounds_measured_candidate(self) -> None:
        self.assertEqual(
            subject.measurement_timeout_seconds("baseline", 180.0, 65.35),
            180.0,
        )
        self.assertEqual(
            subject.measurement_timeout_seconds("candidate", 180.0, 65.35),
            65.35,
        )
        self.assertEqual(
            subject.measurement_timeout_seconds("candidate", 60.0, 65.35),
            60.0,
        )
        self.assertEqual(
            subject.measurement_timeout_seconds("candidate", 180.0, None),
            180.0,
        )

    def test_installed_library_identity_records_resolved_root_and_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "toolchain"
            library = home / "lib"
            for name in (
                "gerbil/compiler/base~0.o1",
                "gerbil/compiler/driver~0.o1",
                "std/make.o1",
                "static/gerbil__compiler__driver.scm",
            ):
                path = library / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode("utf-8"))
            expected_root = str(library.resolve())
            identity = subject.installed_library_identity(home)

        self.assertEqual(identity["resolvedRoot"], expected_root)
        self.assertFalse(identity["rootIsSymlink"])
        self.assertEqual(len(identity["requiredModuleSha256"]), 4)

    def test_installed_library_identity_exposes_split_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "toolchain"
            external = Path(directory) / "external-lib"
            for name in (
                "gerbil/compiler/base~0.o1",
                "gerbil/compiler/driver~0.o1",
                "std/make.o1",
                "static/gerbil__compiler__driver.scm",
            ):
                path = external / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"module")
            home.mkdir()
            (home / "lib").symlink_to(external, target_is_directory=True)
            expected_root = str(external.resolve())
            identity = subject.installed_library_identity(home)

        self.assertTrue(identity["rootIsSymlink"])
        self.assertEqual(identity["resolvedRoot"], expected_root)

    def test_cold_toolchain_preflight_imports_without_building_consumer(self) -> None:
        selected = {"gxi": "/candidate/bin/gxi", "home": "/candidate"}
        result = subject.framework.CommandResult(
            elapsed_ns=500_000_000,
            exit_code=0,
            timed_out=False,
            timeout_reason=None,
            events=({"elapsedNs": 500_000_000, "line": "toolchain-imports-qualified"},),
        )
        with mock.patch.object(subject, "build_environment", return_value={}), mock.patch.object(
            subject.framework, "run_timed", return_value=result
        ) as run_timed:
            receipt = subject.qualify_toolchain_imports(
                label="candidate",
                consumer="gerbil-mcp",
                repository=Path("/tmp/consumer"),
                selected=selected,
                build_cores=12,
                gcc="/opt/homebrew/bin/gcc-16",
            )

        command = run_timed.call_args.args[0]
        self.assertEqual(command[0], selected["gxi"])
        self.assertTrue(any(":std/net/ssl/libssl" in part for part in command))
        self.assertEqual(receipt["mode"], "toolchain-imports-only")
        self.assertTrue(receipt["passed"])

    def test_qualification_failure_retains_watchdog_and_last_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "failure.json"
            subject.write_qualification_failure(
                receipt_path,
                consumer="gerbil-mcp",
                phase="candidate-first-access",
                run={
                    "timedOut": True,
                    "timeoutReason": "silence",
                    "silence": {"beforeEvent": "graph-ready", "maxGapNs": 10_001_000_000},
                },
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["status"], "qualification-failed")
        self.assertEqual(receipt["failedPhase"], "candidate-first-access")
        self.assertEqual(receipt["run"]["timeoutReason"], "silence")
        self.assertEqual(receipt["run"]["silence"]["beforeEvent"], "graph-ready")

    def test_failed_baseline_does_not_start_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            receipt_path = root / "receipt.json"
            events = []

            def qualify(**kwargs):
                events.append(f"import-{kwargs['label']}")
                return {"passed": True}

            def failed_build(**kwargs):
                events.append(f"build-{kwargs['label']}")
                return {"passed": False, "timeoutReason": "silence"}

            selected = {
                "home": str(root / "toolchain"),
                "gxi": str(root / "toolchain/bin/gxi"),
                "gsc": str(root / "toolchain/bin/gsc"),
                "gxc": str(root / "toolchain/bin/gxc"),
                "gerbil": str(root / "toolchain/bin/gerbil"),
            }
            with mock.patch.object(subject, "git_output", return_value=""), mock.patch.object(
                subject, "clone_repository"
            ), mock.patch.object(subject, "toolchain", return_value=selected), mock.patch.object(
                subject, "require_binary_sha256", return_value="a" * 64
            ), mock.patch.object(subject, "sha256_file", return_value="a" * 64), mock.patch.object(
                subject, "qualify_toolchain_imports", side_effect=qualify
            ), mock.patch.object(subject, "prepare_measurement_state", return_value={"passed": True}), mock.patch.object(
                subject, "run_one", side_effect=failed_build
            ) as run_one:
                with self.assertRaisesRegex(RuntimeError, "candidate not comparable"):
                    subject.main(
                        [
                            "--consumer", "gerbil-mcp", "--repository", str(source),
                            "--baseline-home", str(root / "toolchain"),
                            "--candidate-home", str(root / "toolchain"),
                            "--expected-baseline-gerbil-sha256", "a" * 64,
                            "--gcc", "/opt/homebrew/bin/gcc-16",
                            "--receipt", str(receipt_path),
                        ]
                    )

            run_one.assert_called_once()
            self.assertEqual(events, ["import-baseline", "import-candidate", "build-baseline"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["failedPhase"], "baseline-measurement")
            self.assertEqual(receipt["run"]["timeoutReason"], "silence")

    def test_package_phase_metrics_attributes_major_package_costs(self) -> None:
        result = subject.framework.CommandResult(
            elapsed_ns=14_000_000_000,
            exit_code=0,
            timed_out=False,
            timeout_reason=None,
            events=(
                {"elapsedNs": 100_000_000, "line": "... build-observe phase=frontend event=start entries=2"},
                {"elapsedNs": 200_000_000, "line": "... build-observe phase=graph event=start"},
                {"elapsedNs": 2_200_000_000, "line": "... build-observe phase=graph event=ready elapsedMs=2000"},
                {"elapsedNs": 7_200_000_000, "line": "... build-observe phase=graph event=end elapsedMs=7000"},
                {"elapsedNs": 7_300_000_000, "line": "... build-observe phase=native-drain event=start"},
                {"elapsedNs": 12_300_000_000, "line": "... execute compile job (compile-file /tmp/large.scm) event=end status=passed elapsedMs=5100"},
                {"elapsedNs": 12_400_000_000, "line": "... build-observe phase=native-drain event=end"},
                {"elapsedNs": 12_500_000_000, "line": "... build-observe phase=frontend event=end elapsedMs=12400"},
            ),
        )

        metrics = subject.package_phase_metrics(result)

        self.assertEqual(metrics["graphReadyMs"], 2000.0)
        self.assertEqual(metrics["graphWorkMs"], 5000.0)
        self.assertEqual(metrics["nativeDrainMs"], 5100.0)
        self.assertEqual(metrics["frontendMs"], 12400.0)
        self.assertEqual(metrics["longestNativeJobs"][0]["subject"], "/tmp/large.scm")

    def test_package_phase_metrics_keep_executable_log_boundaries_separate(self) -> None:
        result = subject.framework.CommandResult(
            elapsed_ns=90_000_000_000,
            exit_code=0,
            timed_out=False,
            timeout_reason=None,
            events=(
                {"elapsedNs": 36_000_000_000, "line": "... compile main"},
                {"elapsedNs": 65_000_000_000, "line": "... execute compile job (compile-executable-object /tmp/module.c)"},
                {"elapsedNs": 84_000_000_000, "line": "... execute compile job (link-executable /tmp/program)"},
            ),
        )

        metrics = subject.package_phase_metrics(result)

        self.assertEqual(metrics["buildStartToMainMs"], 36_000.0)
        self.assertEqual(metrics["mainToFirstExecutableObjectMs"], 29_000.0)
        self.assertEqual(metrics["firstExecutableObjectToLinkMs"], 19_000.0)
        self.assertEqual(metrics["linkToBuildEndMs"], 6_000.0)

    def test_executable_boundaries_remain_unknown_without_log_markers(self) -> None:
        result = subject.framework.CommandResult(
            elapsed_ns=1_000_000_000,
            exit_code=0,
            timed_out=False,
            timeout_reason=None,
            events=({"elapsedNs": 100_000_000, "line": "... compile main"},),
        )

        metrics = subject.package_phase_metrics(result)

        self.assertEqual(metrics["buildStartToMainMs"], 100.0)
        self.assertIsNone(metrics["mainToFirstExecutableObjectMs"])
        self.assertIsNone(metrics["firstExecutableObjectToLinkMs"])
        self.assertIsNone(metrics["linkToBuildEndMs"])

    def test_bottleneck_comparison_keeps_phase_deltas_separate(self) -> None:
        comparison = subject.bottleneck_comparison(
            {
                "graphReadyMs": 2000.0,
                "graphWorkMs": 5000.0,
                "graphTotalMs": 7000.0,
                "nativeDrainMs": 5000.0,
                "frontendMs": 12000.0,
                "maxSilenceMs": 900.0,
                "longestNativeJobs": [{"subject": "baseline"}],
            },
            {
                "graphReadyMs": 1800.0,
                "graphWorkMs": 4000.0,
                "graphTotalMs": 5800.0,
                "nativeDrainMs": 4500.0,
                "frontendMs": 10300.0,
                "maxSilenceMs": 800.0,
                "longestNativeJobs": [{"subject": "candidate"}],
            },
        )

        self.assertEqual(comparison["metrics"]["graphWorkMs"]["deltaMs"], -1000.0)
        self.assertEqual(comparison["metrics"]["graphWorkMs"]["deltaPercent"], -20.0)
        self.assertEqual(comparison["candidateLongestNativeJobs"][0]["subject"], "candidate")

    def test_performance_admission_rejects_relative_regression(self) -> None:
        admission = subject.performance_admission(
            13_000_000_000,
            13_000_000_001,
            max_regression_percent=0.0,
            max_candidate_seconds=None,
        )

        self.assertFalse(admission["relativePassed"])
        self.assertFalse(admission["passed"])

    def test_performance_admission_rejects_absolute_baseline_drift(self) -> None:
        admission = subject.performance_admission(
            14_000_000_000,
            13_500_000_000,
            max_regression_percent=0.0,
            max_candidate_seconds=13.13,
        )

        self.assertTrue(admission["relativePassed"])
        self.assertFalse(admission["absolutePassed"])
        self.assertFalse(admission["passed"])

    def test_performance_admission_accepts_faster_candidate_under_absolute_gate(self) -> None:
        admission = subject.performance_admission(
            13_130_000_000,
            12_010_000_000,
            max_regression_percent=0.0,
            max_candidate_seconds=13.13,
        )

        self.assertTrue(admission["passed"])

    def test_binary_identity_gate_accepts_exact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "gerbil"
            executable.write_bytes(b"qualified-aot")
            expected = subject.sha256_file(executable)

            actual = subject.require_binary_sha256(
                {"gerbil": str(executable)}, expected, label="baseline"
            )

        self.assertEqual(actual, expected)

    def test_binary_identity_gate_rejects_drift_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "gerbil"
            executable.write_bytes(b"drifted-aot")

            with self.assertRaisesRegex(
                RuntimeError, "baseline gerbil identity mismatch"
            ):
                subject.require_binary_sha256(
                    {"gerbil": str(executable)}, "0" * 64, label="baseline"
                )

    def test_source_warmup_reads_only_tracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "tracked.ss").write_text("(displayln 1)\n", encoding="utf-8")
            (repository / "untracked.ss").write_text("ignored\n", encoding="utf-8")
            with mock.patch.object(
                subject.subprocess,
                "run",
                return_value=mock.Mock(stdout=b"tracked.ss\0"),
            ):
                result = subject.warm_tracked_sources(repository)

        self.assertEqual(result["trackedFileCount"], 1)
        self.assertEqual(result["trackedByteCount"], len("(displayln 1)\n"))
        self.assertEqual(len(result["contentSha256"]), 64)

    def test_environment_binds_one_toolchain_and_scrubs_loadpath(self) -> None:
        selected = {
            "home": "/candidate",
            "gxi": "/candidate/bin/gxi",
            "gsc": "/candidate/bin/gsc",
            "gxc": "/candidate/bin/gxc",
            "gerbil": "/candidate/bin/gerbil",
        }
        with mock.patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "GERBIL_LOADPATH": "/old/lib",
             "GERBIL_DARWIN_CANONICAL_RUNTIME_OBJECTS": "yes"},
            clear=True,
        ):
            environment = subject.build_environment(
                selected, Path("/consumer"), 12, "/opt/homebrew/bin/gcc-16"
            )

        self.assertEqual(environment["GERBIL_HOME"], "/candidate")
        self.assertEqual(environment["GERBIL_GSC"], "/candidate/bin/gsc")
        self.assertEqual(environment["GERBIL_GXC"], "/candidate/bin/gxc")
        self.assertEqual(environment["GERBIL_BUILD_CORES"], "12")
        self.assertEqual(environment["GERBIL_BUILD_VERBOSE"], "3")
        self.assertEqual(
            environment["GAMBOPT"],
            "~~=/candidate,~~bin=/candidate/bin,~~lib=/candidate/lib",
        )
        self.assertNotIn("GERBIL_LOADPATH", environment)
        self.assertNotIn("GERBIL_DARWIN_CANONICAL_RUNTIME_OBJECTS", environment)
        self.assertTrue(environment["PATH"].startswith("/candidate/bin"))

        selected["canonicalRuntimeObjects"] = "yes"
        candidate_environment = subject.build_environment(
            selected, Path("/consumer"), 12, "/opt/homebrew/bin/gcc-16"
        )
        self.assertEqual(
            candidate_environment["GERBIL_DARWIN_CANONICAL_RUNTIME_OBJECTS"], "yes"
        )

    def test_poo_command_uses_real_clone_justfile(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            subject.framework,
            "resolve_executable",
            return_value="/usr/bin/just",
        ):
            repository = Path(directory)
            command = subject.build_command(
                "gerbil-poo", repository, {"gerbil": "/candidate/bin/gerbil"}
            )

        self.assertEqual(command[0], "/usr/bin/just")
        self.assertEqual(command[-1], "build")
        self.assertIn(str(repository / "justfile"), command)

    def test_mcp_command_pins_selected_gerbil(self) -> None:
        with mock.patch.object(
            subject.framework,
            "resolve_executable",
            return_value="/usr/bin/make",
        ):
            command = subject.build_command(
                "gerbil-mcp", Path("/consumer"), {"gerbil": "/candidate/bin/gerbil"}
            )

        self.assertEqual(
            command,
            ("/usr/bin/make", "build", "GERBIL=/candidate/bin/gerbil"),
        )

    def test_poo_clean_command_uses_native_just_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            subject.framework,
            "resolve_executable",
            return_value="/usr/bin/just",
        ):
            repository = Path(directory)
            command = subject.clean_command(
                "gerbil-poo", repository, {"gerbil": "/candidate/bin/gerbil"}
            )

        self.assertEqual(command[-1], "clean")
        self.assertIn(str(repository / "justfile"), command)

    def test_cold_preparation_removes_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / ".gerbil").mkdir()
            result = subject.prepare_measurement_state(
                build_state="cold",
                consumer="gerbil-poo",
                repository=repository,
                selected={"gerbil": "/candidate/bin/gerbil"},
                build_cores=12,
                gcc=None,
                timeout_seconds=1,
            )

        self.assertEqual(result["mode"], "cold")
        self.assertTrue(result["passed"])

    @mock.patch.object(subject, "build_environment", return_value={})
    @mock.patch.object(subject, "clean_command", return_value=("just", "clean"))
    @mock.patch.object(subject.framework, "run_timed")
    def test_native_warm_preparation_uses_consumer_clean(
        self, run_timed: mock.Mock, _clean_command: mock.Mock, _environment: mock.Mock
    ) -> None:
        run_timed.return_value = mock.Mock(
            elapsed_ns=10, exit_code=0, timed_out=False
        )
        result = subject.prepare_measurement_state(
            build_state="native-warm",
            consumer="gerbil-poo",
            repository=Path("/consumer"),
            selected={"gerbil": "/candidate/bin/gerbil"},
            build_cores=12,
            gcc=None,
            timeout_seconds=1,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["command"], ["just", "clean"])
        run_timed.assert_called_once()

    def test_clear_outputs_removes_only_generated_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / ".gerbil").mkdir()
            (repository / ".gerbil" / "artifact").write_text("x", encoding="utf-8")
            (repository / "manifest.ss").write_text("generated", encoding="utf-8")
            (repository / "source.ss").write_text("source", encoding="utf-8")
            with mock.patch.object(subject, "git_output", return_value=""):
                subject.clear_consumer_outputs(repository)

            self.assertFalse((repository / ".gerbil").exists())
            self.assertFalse((repository / "manifest.ss").exists())
            self.assertTrue((repository / "source.ss").is_file())


if __name__ == "__main__":
    unittest.main()
