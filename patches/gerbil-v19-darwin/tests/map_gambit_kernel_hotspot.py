#!/usr/bin/env python3
"""Map a sampled native host offset only when debug and original text match."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shlex
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--offset", type=int, default=13604)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    source, output = args.source.resolve(), args.output.resolve()
    if platform.system() != "Darwin" or not output.is_relative_to(repo / ".data"):
        parser.error("Darwin-only probe under .data required")
    output.mkdir(parents=True, exist_ok=False)
    lib = source / "src/gambit/lib"
    env = build_environment()
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    dry = subprocess.check_output(["make", "-n", "-B", "_kernel.o"], cwd=lib, env=env, text=True)
    commands = [shlex.split(line) for line in dry.splitlines() if line.startswith(env["CC"] + " ")]
    if len(commands) != 1:
        raise RuntimeError("ambiguous official kernel command")
    command = commands[0]
    obj = output / "kernel-debug.o"
    command[command.index("-o") + 1] = str(obj)
    command += ["-g", "-fno-var-tracking", "-fno-var-tracking-assignments"]
    with (output / "compile.log").open("w") as log:
        subprocess.run(command, cwd=lib, env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=60)

    def text_bytes(path):
        dump = subprocess.check_output(["/usr/bin/otool", "-s", "__TEXT", "__text", str(path)], text=True)
        return b"".join(bytes.fromhex("".join(line.split()[1:])) for line in dump.splitlines()[2:])

    original_text, debug_text = text_bytes(lib / "_kernel.o"), text_bytes(obj)
    report = {"qualified": False, "textIdentical": original_text == debug_text,
              "originalTextSha256": hashlib.sha256(original_text).hexdigest(),
              "debugTextSha256": hashlib.sha256(debug_text).hexdigest(),
              "sampledOffset": args.offset}
    if report["textIdentical"]:
        symbols = subprocess.check_output(["/usr/bin/nm", "-n", str(obj)], text=True)
        rows = [line.split() for line in symbols.splitlines()]
        matches = [row for row in rows if len(row) == 3 and row[-1] == "____H___kernel"]
        if len(matches) != 1:
            raise RuntimeError("kernel host symbol not unique")
        address = int(matches[0][0], 16) + args.offset
        report["objectAddress"] = hex(address)
        result = subprocess.run(["xcrun", "dwarfdump", "--lookup", hex(address), str(obj)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        (output / "lookup.log").write_text(result.stdout)
        report["lookupExitCode"] = result.returncode
        report["qualified"] = result.returncode == 0 and "Line info" in result.stdout
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
