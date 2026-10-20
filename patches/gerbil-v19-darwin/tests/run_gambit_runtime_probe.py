#!/usr/bin/env python3
"""Use one native probe with two independently built library roots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
from threading import Thread
import time

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toolchain-source", type=Path, required=True)
    parser.add_argument("--probe-lib", type=Path, required=True)
    parser.add_argument("--baseline-path", type=Path, required=True)
    parser.add_argument("--candidate-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(repo / ".data"):
        parser.error("output must be inside project .data")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    for name in ("GERBIL_BUILD_PREFIX", "GERBIL_BUILD_VERBOSE", "GAMBIT_HOST_GROUP_BUDGET"):
        env.pop(name, None)
    home = args.toolchain_source.resolve() / "build"
    probe = args.probe_lib.resolve()
    env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    hashes = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
              for file in probe.glob("*.o1")}
    if len(hashes) != 2:
        raise RuntimeError("exactly two compiled probe artifacts required")
    report = {"qualified": False, "performanceQualified": False,
              "hostLoadStart": os.getloadavg(), "probeNativeHashes": hashes, "runs": []}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        save()
        roots = {"baseline": args.baseline_path.resolve(), "candidate": args.candidate_path.resolve()}
        for index, mode in enumerate(("baseline", "candidate", "candidate", "baseline", "baseline", "candidate")):
            name = f"{index}-{mode}"
            e = dict(env)
            e.update(GERBIL_PATH=str(roots[mode]),
                     GERBIL_LOADPATH=f"{probe}:{roots[mode] / 'lib'}:{home / 'lib'}")
            started = time.monotonic()
            events = {}
            print(f"START {name}", flush=True)
            with (output / f"{name}.log").open("w") as log:
                child = subprocess.Popen([str(home / "bin/gxi"), "-e", "(import :d889-runtime-probe)"],
                                         env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, start_new_session=True)

                def collect():
                    for line in child.stdout:
                        log.write(line)
                        log.flush()
                        if line.startswith("READY "):
                            events["readySeconds"] = time.monotonic() - started
                        if line.startswith("RUNTIME-RESULT "):
                            events["result"] = json.loads(line.removeprefix("RUNTIME-RESULT "))

                reader = Thread(target=collect)
                reader.start()
                previous, progress = None, started
                try:
                    while child.poll() is None:
                        time.sleep(2)
                        snapshot = subprocess.run(["ps", "-p", str(child.pid), "-o", "time="],
                                                  capture_output=True, text=True)
                        if snapshot.returncode and child.poll() is not None:
                            break
                        if snapshot.returncode:
                            raise RuntimeError("process activity query failed")
                        activity = snapshot.stdout.strip()
                        state = (activity, log.tell())
                        now = time.monotonic()
                        if state != previous:
                            progress = now
                        previous = state
                        print(f"PROGRESS {name}: cpu={activity} bytes={state[1]}", flush=True)
                        if child.poll() is None and (now - progress > 10 or now - started > 180):
                            raise TimeoutError(f"{name}: progress/180-second gate")
                    status = child.wait()
                    reader.join(timeout=5)
                except BaseException:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGTERM)
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
                    reader.join(timeout=5)
                    raise
            content = (output / f"{name}.log").read_text()
            result = events.get("result")
            if status != 0 or "*** ERROR" in content or not result or result[0] != 3300000 or not content.rstrip().endswith("OK"):
                raise RuntimeError(f"{name}: native result gate failed")
            report["runs"].append({"mode": mode, "log": f"{name}.log", **events,
                                    "checksum": result[0], "cpuSeconds": result[1], "wallSeconds": result[2]})
            save()
            print(f"OK {name}: {result}", flush=True)
        for mode in roots:
            report[mode + "MedianCpuSeconds"] = statistics.median(row["cpuSeconds"] for row in report["runs"] if row["mode"] == mode)
        report["runtimeNonRegressionObserved"] = report["candidateMedianCpuSeconds"] <= report["baselineMedianCpuSeconds"]
        current = {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in probe.glob("*.o1")}
        if current != hashes:
            raise RuntimeError("probe artifacts changed during runtime comparison")
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        save()


if __name__ == "__main__":
    main()
