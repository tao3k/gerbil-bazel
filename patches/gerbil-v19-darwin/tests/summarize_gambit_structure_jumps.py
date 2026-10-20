#!/usr/bin/env python3
"""Explain bounded native structure completion versus primitive fallback."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    totals = Counter()
    modules = []
    for path in sorted(args.trace_dir.glob("*-jumps.tsv")):
        with path.open() as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != ["event", "calls"]:
                raise RuntimeError("unexpected native jump counter schema")
            counts = {int(row["event"]): int(row["calls"]) for row in reader}
        if (set(counts) != set(range(5)) or any(count < 0 for count in counts.values())
                or counts[0] != counts[2] + counts[3] + counts[4] or counts[1] > counts[3]):
            raise RuntimeError("incomplete native jump counts")
        totals.update(counts)
        modules.append({"module": path.name.split("-", 1)[1].removesuffix("-jumps.tsv"),
                        "total": counts[0], "nonStructure": counts[1], "true": counts[2],
                        "false": counts[3], "deepFallback": counts[4]})
    if not totals[0]:
        raise RuntimeError("no native structure jump observations")
    modules.sort(key=lambda row: row["total"], reverse=True)
    report = {"scope": "actual-native-structure-jumps-not-performance", "modules": modules,
              "total": totals[0], "nonStructure": totals[1], "true": totals[2],
              "false": totals[3], "deepFallback": totals[4],
              "deepFallbackFraction": totals[4] / totals[0]}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "modules"}))


if __name__ == "__main__":
    main()
