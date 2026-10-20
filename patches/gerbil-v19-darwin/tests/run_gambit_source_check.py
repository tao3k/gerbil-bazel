#!/usr/bin/env python3
"""Run the existing native MCP checker against an isolated Gambit source file."""
import argparse
import json
from pathlib import Path
import subprocess
from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--mcp", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--syntax", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    if not all(p.resolve().is_relative_to(repo / ".data") for p in (args.source, args.output, args.mcp)):
        parser.error("source and checker evidence must stay under project .data")
    env = build_environment()
    home = args.baseline.resolve() / "build"
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(args.output.parent.resolve() / "checker-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "source-check", "version": "1"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "gerbil_check_balance", "arguments": {"file_path": str(args.source.resolve())}}}]
    if args.syntax:
        requests.append({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "gerbil_check_syntax", "arguments": {"code": "(begin\n" + args.source.read_text() + "\n)"}}})
    result = subprocess.run([str(args.mcp.resolve())], input="".join(json.dumps(r) + "\n" for r in requests),
                            text=True, capture_output=True, env=env, timeout=40)
    args.output.write_text(result.stdout + "\nSTDERR\n" + result.stderr)
    responses = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    checks = [r for r in responses if r.get("id") in (2, 3)]
    print(json.dumps(checks))
    if result.returncode or len(checks) != len(requests) - 1 or any(
            r.get("error") or r.get("result", {}).get("isError") for r in checks):
        raise RuntimeError("source check failed; inspect retained checker response")


if __name__ == "__main__":
    main()
