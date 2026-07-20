#!/usr/bin/env python3

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import run_build_scenarios as subject


class BazelTargetVersionTest(unittest.TestCase):
    def test_uses_bazel_tool_stdout_without_ui_stderr(self) -> None:
        workspace = Path("/workspace")
        output_user_root = Path("/tmp/bazel-output-user-root")
        command = (
            "/usr/bin/bazelisk",
            "--output_user_root=/tmp/bazel-output-user-root",
            "run",
            "--color=no",
            "--curses=no",
            "--noshow_progress",
            "--disk_cache=",
            "--remote_cache=",
            "@local_gerbil//:gxi",
            "--",
            "--version",
        )

        with patch.object(subject.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess(
                command,
                0,
                stdout="Gerbil 07c8481 on Gambit v4.9.7\n",
                stderr="INFO: Build completed successfully\n",
            )

            version = subject.bazel_target_version(
                "/usr/bin/bazelisk",
                "@local_gerbil//:gxi",
                workspace=workspace,
                output_user_root=output_user_root,
            )

        self.assertEqual(version, "Gerbil 07c8481 on Gambit v4.9.7")
        run.assert_called_once_with(
            command,
            check=False,
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_fails_with_bazel_diagnostic(self) -> None:
        with patch.object(subject.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess(
                ("bazelisk", "run"),
                1,
                stdout="",
                stderr="ERROR: toolchain resolution failed\n",
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "toolchain resolution failed",
            ):
                subject.bazel_target_version(
                    "bazelisk",
                    "@local_gerbil//:gxi",
                    workspace=Path("/workspace"),
                    output_user_root=Path("/tmp/bazel-output-user-root"),
                )

    def test_rejects_empty_tool_output(self) -> None:
        with patch.object(subject.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess(
                ("bazelisk", "run"),
                0,
                stdout="\n",
                stderr="",
            )

            with self.assertRaisesRegex(RuntimeError, "empty version output"):
                subject.bazel_target_version(
                    "bazelisk",
                    "@local_gerbil//:gxi",
                    workspace=Path("/workspace"),
                    output_user_root=Path("/tmp/bazel-output-user-root"),
                )


class ScenarioContractTest(unittest.TestCase):
    def test_configuration_delta_changes_one_provider_neutral_input(self) -> None:
        scenario = next(
            item
            for item in subject.SCENARIOS
            if item.identifier == "configuration-delta"
        )

        self.assertEqual(
            scenario.build_flags,
            (subject.DEPENDENCY_FLAG, subject.CONFIGURATION_FLAG),
        )
        self.assertFalse(
            any("GERBIL_NATIVE_ABI" in flag for flag in scenario.build_flags)
        )
        self.assertEqual(
            scenario.expected_labels,
            frozenset(
                {
                    "//tests/smoke:compile",
                    "//tests/smoke:dependency_compile",
                    "//tests/smoke:independent_compile",
                }
            ),
        )

    def test_configuration_failure_names_project_action_boundary(self) -> None:
        decision = subject.optimization_decision(
            [{"id": "configuration-delta", "status": "failed"}]
        )

        self.assertEqual(
            decision["optimizationCandidate"],
            "project-action-configuration-identity",
        )


if __name__ == "__main__":
    unittest.main()
