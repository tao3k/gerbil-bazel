#!/usr/bin/env python3
"""Invalidate only premature stdlib checkpoints after interrupted native jobs."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
build = args.source.resolve() / "build"
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
missing = {}
for source in sorted((build / "lib/std").rglob("*.scm")):
    artifact = source.with_suffix(".o1")
    valid = (artifact.exists() and artifact.stat().st_size > 0
             and artifact.stat().st_mtime_ns >= source.stat().st_mtime_ns)
    if valid:
        valid = subprocess.run(["otool", "-L", str(artifact)],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL).returncode == 0
    if not valid:
        relative = source.relative_to(build / "lib").with_suffix("")
        owner = str(relative).split("~", 1)[0]
        missing.setdefault(owner, []).append(str(source.relative_to(build)))
report = {"missingNative": missing, "invalidated": []}
for owner in missing:
    checkpoint = build / "lib/static" / (owner.replace("/", "__") + ".scm")
    if checkpoint.exists():
        checkpoint.rename(output / checkpoint.name)
        report["invalidated"].append(str(checkpoint.relative_to(build)))
(output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"D882-STD-REPAIR modules={len(missing)} checkpoints={len(report['invalidated'])}")
