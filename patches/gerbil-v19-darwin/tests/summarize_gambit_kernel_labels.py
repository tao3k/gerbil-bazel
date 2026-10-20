#!/usr/bin/env python3
"""Resolve diagnostic kernel label IDs against original generated metadata."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

from gambit_host_coalescing import section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-unit", choices=("kernel", "std"), default="kernel")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    if not all(path.resolve().is_relative_to(repo / ".data") for path in (args.source, args.counts, args.output)):
        parser.error("source and receipts must stay under project .data")
    text = args.source.read_text()
    symbols = {int(index): json.loads(name) for index, name in re.findall(
        r'^___DEF_SYM\((\d+),[^,]+,("(?:[^"\\]|\\.)*")\)$', text, re.MULTILINE)}
    _, labels, _ = section(text, "___BEGIN_LBL", "___END_LBL")
    descriptors = []
    current = None
    for line in labels.splitlines():
        row = re.match(r"\s*,?___DEF_LBL_(INTRO|PROC|RET)\((.*)", line)
        if not row:
            if line.strip():
                raise RuntimeError("unexpected label descriptor layout")
            continue
        kind, value = row.groups()
        if kind == "INTRO":
            name = re.search(r"___REF_SYM\((\d+),", value)
            current = symbols[int(name.group(1))] if name else value.split(",", 1)[0]
        if current is None:
            raise RuntimeError("label before first introduction")
        descriptors.append({"kind": kind, "procedure": current})
    expected = int(re.search(r"^#define ___LBLCOUNT (\d+)$", text, re.MULTILINE).group(1))
    if len(descriptors) != expected:
        raise RuntimeError("descriptor count differs from compiled kernel")
    totals, procedure_entries, returns = Counter(), Counter(), Counter()
    files = sorted(args.counts.glob("*.tsv"))
    if not files:
        raise RuntimeError("no kernel label counters")
    for path in files:
        with path.open() as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != ["label", "calls"]:
                raise RuntimeError("unexpected counter fields")
            seen = set()
            for row in reader:
                index, calls = int(row["label"]), int(row["calls"])
                if index in seen or not 0 <= index < expected or calls <= 0:
                    raise RuntimeError("invalid or duplicate kernel counter")
                seen.add(index)
                descriptor = descriptors[index]
                key = descriptor["procedure"]
                totals[key] += calls
                (returns if descriptor["kind"] == "RET" else procedure_entries)[key] += calls
    if args.source.stem != "_" + args.runtime_unit:
        parser.error("runtime unit does not match the original source filename")
    report = {"scope": f"{args.runtime_unit}-host-label-counts-not-cpu-attribution", "performanceQualified": False,
              "runtimeUnit": args.runtime_unit,
              "kernelGeneratedCSha256": hashlib.sha256(text.encode()).hexdigest(),
              "labelCount": expected, "processCount": len(files), "hostEntries": sum(totals.values()),
              "procedureEntries": sum(procedure_entries.values()), "returnEntries": sum(returns.values()),
              "topProcedures": [{"procedure": name, "hostEntries": count,
                                  "procedureEntries": procedure_entries[name], "returnEntries": returns[name]}
                                 for name, count in totals.most_common(30)]}
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("processCount", "hostEntries", "procedureEntries", "returnEntries")}, indent=2))
    print(json.dumps(report["topProcedures"][:12], indent=2))


if __name__ == "__main__":
    main()
