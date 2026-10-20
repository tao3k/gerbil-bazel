#!/usr/bin/env python3
"""Resolve diagnostic host counters against exact retained Mach-O images."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess


def symbols(image):
    commands = subprocess.check_output(["/usr/bin/otool", "-l", str(image)], text=True)
    base = None
    in_text = False
    for line in commands.splitlines():
        words = line.split()
        if words[:1] == ["segname"]:
            in_text = words[1] == "__TEXT"
        if in_text and words[:1] == ["vmaddr"]:
            base = int(words[1], 16)
            break
    if base is None:
        raise RuntimeError("Mach-O text segment missing")
    table = {}
    text = subprocess.check_output(["/usr/bin/nm", "-n", str(image)], text=True)
    for line in text.splitlines():
        words = line.split()
        if len(words) == 3 and words[1] in ("t", "T"):
            table[int(words[0], 16) - base] = words[2]
    return table


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    if not all(path.resolve().is_relative_to(repo / ".data") for path in (args.trace_dir, args.output)):
        parser.error("counter evidence must stay under project .data")
    tables = {}
    edges = Counter()
    destinations = Counter()
    unresolved = 0
    files = sorted(args.trace_dir.glob("*.tsv"))
    if not files:
        raise RuntimeError("no host counter files")
    for path in files:
        with path.open(newline="") as source:
            for row in csv.DictReader(source, delimiter="\t"):
                count = int(row["calls"])
                image = Path(row["image"])
                if row["image"] == "<unmapped>":
                    target = "<unmapped>"
                else:
                    if image not in tables:
                        tables[image] = symbols(image)
                    target = tables[image].get(int(row["offset"], 16), "<unresolved>")
                if target.startswith("<"):
                    unresolved += count
                edges[row["module"], target] += count
                destinations[target] += count
    report = {"scope": "actual-host-exits-not-performance", "files": len(files),
              "totalCalls": sum(destinations.values()), "unresolvedCalls": unresolved,
              "destinations": dict(destinations.most_common()),
              "edges": [{"from": caller, "to": target, "calls": count}
                        for (caller, target), count in edges.most_common()]}
    with args.output.open("x") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key != "edges"}))


if __name__ == "__main__":
    main()
