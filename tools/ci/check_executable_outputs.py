#!/usr/bin/env python3
"""Exercise two executable targets sharing one compiler-owned static closure."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    real_gsc = subprocess.check_output(
        ["gxi", "-e", '(displayln (path-expand "bin/gsc" (gerbil-home)))'],
        text=True, timeout=10).strip()
    if not Path(real_gsc).is_file():
        raise RuntimeError("installed Gerbil-owned Gambit compiler required")
    with tempfile.TemporaryDirectory(prefix="gerbil-executable-outputs-") as folder:
        root = Path(folder)
        (root / "gerbil.pkg").write_text("(package: executable-output-control)\n")
        (root / "shared.ss").write_text(
            '(export answer answer-code)\n(def answer 42)\n(defrules answer-code () ((_) 0))\n')
        for name in ("first", "second"):
            (root / (name + ".ss")).write_text(
                '(import "shared")\n(export main)\n'
                '(def (main . _) (displayln (+ answer (answer-code))))\n')
        (root / "build.ss").write_text(
            '(import :std/build-script)\n'
            "(defbuild-script '(\"shared\" (exe: \"first\") (exe: \"second\")) optimize: #f)\n")
        tools = root / "compiler-tools"
        tools.mkdir()
        # The driver resolves Gambit helpers beside its selected gsc. Keep that
        # standard SDK layout while interposing only the compiler command.
        for tool in Path(real_gsc).parent.iterdir():
            if tool.name != "gsc":
                (tools / tool.name).symlink_to(tool)
        wrapper = tools / "gsc"
        wrapper.write_text("#!/usr/bin/env python3\n" +
            'import os, pathlib, subprocess, sys, time\n'
            'args = sys.argv[1:]\n'
            'guard = pathlib.Path(os.environ["OUTPUT_PROBE_GUARD"])\n'
            'link = "-link" in args and sys.platform.startswith("linux")\n'
            'held = False\n'
            'try:\n'
            ' if link:\n'
            '  try: guard.touch(exist_ok=False); held = True\n'
            '  except FileExistsError: raise SystemExit("overlapping shared executable C writers")\n'
            '  time.sleep(1)\n'
            ' if "-link" in args:\n'
            '  try: pathlib.Path(os.environ["OUTPUT_PROBE_FAIL_ONCE"]).unlink()\n'
            '  except FileNotFoundError: pass\n'
            '  else: raise SystemExit(73)\n'
            ' result = subprocess.run([os.environ["OUTPUT_PROBE_GSC"], *args])\n'
            ' raise SystemExit(result.returncode)\n'
            'finally:\n'
            ' if held: guard.unlink()\n')
        wrapper.chmod(0o755)
        env = dict(os.environ, GERBIL_BUILD_CORES="4",
                   GERBIL_PATH=str(root / ".gerbil"), GERBIL_GSC=str(wrapper),
                   OUTPUT_PROBE_GSC=real_gsc,
                   OUTPUT_PROBE_GUARD=str(root / "shared-writer.guard"),
                   OUTPUT_PROBE_FAIL_ONCE=str(root / "fail-once"))
        subprocess.run(["gxi", "build.ss", "compile"], cwd=root, env=env,
                       check=True, timeout=120)
        for name in ("first", "second"):
            result = subprocess.run([str(root / ".gerbil/bin" / name)],
                                    capture_output=True, text=True, check=True, timeout=10)
            if result.stdout.strip() != "42":
                raise AssertionError((name, result.stdout))
        # A failing producer must release the shared-output transaction and
        # propagate failure after draining its peer; the next build recovers.
        for name in ("first", "second"):
            (root / ".gerbil/bin" / name).unlink()
        (root / "fail-once").touch()
        failed = subprocess.run(["gxi", "build.ss", "compile"], cwd=root, env=env,
                                timeout=120)
        if failed.returncode == 0:
            raise AssertionError("failed executable producer was admitted")
        subprocess.run(["gxi", "build.ss", "compile"], cwd=root, env=env,
                       check=True, timeout=120)
        for name in ("first", "second"):
            result = subprocess.run([str(root / ".gerbil/bin" / name)],
                                    capture_output=True, text=True, check=True, timeout=10)
            if result.stdout.strip() != "42":
                raise AssertionError((name, result.stdout))
        if (root / "shared-writer.guard").exists():
            raise AssertionError("compiler output transaction did not release")
    print("EXECUTABLE-OUTPUTS-OK shared closure, 2 products, 4 compiler workers, failure/recovery")


if __name__ == "__main__":
    main()
