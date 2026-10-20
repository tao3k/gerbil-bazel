#!/usr/bin/env python3
"""Resolve counted returns against the exact coalesced label map."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--label-map", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kind", choices=("returns", "gen"), default="returns")
    args = parser.parse_args()
    labels = json.loads(args.label_map.read_text())
    groups = defaultdict(Counter)
    files = sorted(args.trace_dir.glob(f"*-{args.kind}.tsv"))
    if not files:
        raise RuntimeError("no return-label observations")
    for path in files:
        with path.open() as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != ["source", "target", "calls"]:
                raise RuntimeError("unexpected counter schema")
            for row in reader:
                source, target, calls = (int(row[key]) for key in reader.fieldnames)
                sentinels = (65534, 65535) if args.kind == "gen" else (65535,)
                if str(source) not in labels or (target not in sentinels and str(target) not in labels) or calls <= 0:
                    raise RuntimeError("unmapped or invalid counted label")
                groups[source][target] += calls
    rows = []
    for source, targets in groups.items():
        target, count = targets.most_common(1)[0]
        total = sum(targets.values())
        rows.append({"source": source, "sourceLabel": labels[str(source)],
                     "target": target, "targetLabel": labels.get(str(target)),
                     "calls": total, "dominantCalls": count,
                     "dominantFraction": count / total, "distinctTargets": len(targets)})
    rows.sort(key=lambda row: row["calls"], reverse=True)
    total = sum(row["calls"] for row in rows)
    internal = sum(count for targets in groups.values() for target, count in targets.items() if str(target) in labels)
    candidates = [row for row in rows if str(row["target"]) in labels and row["dominantCalls"] >= 100000
                  and row["dominantFraction"] >= 0.9]
    report = {"scope": f"actual-{args.kind}-label-counts-not-performance", "files": len(files),
              "labelMapSha256": hashlib.sha256(args.label_map.read_bytes()).hexdigest(),
              "totalCalls": total, "internalCalls": internal,
              "topProcedures": rows[:30], "dominantCandidates": candidates,
              "dominantCandidateCalls": sum(row["dominantCalls"] for row in candidates)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("topProcedures", "dominantCandidates")}))


if __name__ == "__main__":
    main()
