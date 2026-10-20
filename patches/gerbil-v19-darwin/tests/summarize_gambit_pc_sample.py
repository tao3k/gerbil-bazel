#!/usr/bin/env python3
"""Attribute a bounded macOS sample to native GVM landmarks, not call counts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def summarize(sample, generated, landmarks):
    owners = {row['index']: row['module'] for row in landmarks if row.get('module')}
    module = None
    for line in generated.splitlines():
        match = re.match(r'#define ___MODULE_NAME "([^"]+)"', line)
        if match:
            module = match[1]
        match = re.search(r'\.globl _gb_vm_pc_(\d+)_%=', line)
        if match:
            owners[int(match[1])] = module
    if set(owners) != set(range(len(landmarks))) or any(value is None for value in owners.values()):
        raise ValueError("landmark module ownership is incomplete")
    marker = "Sort by top of stack, same collapsed (when >= 5):"
    if marker not in sample:
        raise ValueError("sample has no self-sample summary")
    section = sample.split(marker, 1)[1].split("Binary Images:", 1)[0]
    totals = Counter()
    rows = []
    listed = attributed = 0
    for line in section.splitlines():
        match = re.match(r"\s*(.*?)\s+\(in ([^)]+)\)\s+(\d+)\s*$", line)
        if not match:
            if line.strip():
                raise ValueError("unexpected self-sample row")
            continue
        symbol, image, count = match.groups()
        count = int(count)
        listed += count
        landmark = re.fullmatch(r"_?gb_vm_pc_(\d+)_\d+", symbol)
        row = {"symbol": symbol, "image": image, "selfSamples": count}
        if landmark:
            index = int(landmark[1])
            if index >= len(landmarks):
                raise ValueError("native PC landmark outside generated metadata")
            row.update(landmarks[index], module=owners[index])
            totals[(owners[index], landmarks[index]["procedure"])] += count
            attributed += count
        rows.append(row)
    if not attributed:
        raise ValueError("sample did not resolve any native PC landmark")
    return {"scope": "bounded-native-self-samples-not-whole-startup-cpu",
            "performanceQualified": False, "listedSelfSamples": listed,
            "landmarkSelfSamples": attributed, "summaryExcludesGroupsBelowFive": True,
            "dyldSynchronousNotificationPresent": "blockOnSynchronousEvent" in sample,
            "topProcedures": [{"module": module, "procedure": procedure, "selfSamples": count}
                              for (module, procedure), count in totals.most_common()],
            "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[3] / ".data"
    if not all(path.resolve().is_relative_to(data) for path in (args.profile, args.sample, args.output)):
        parser.error("diagnostic inputs and output must stay under project .data")
    profile = json.loads((args.profile / "report.json").read_text())
    if not profile.get("diagnosticOnly") or not profile.get("nativePcLandmarks"):
        parser.error("a native-PC diagnostic profile is required")
    sample = args.sample.read_text()
    if profile.get("nativePcGeneratedFiles"):
        paths = [Path(name).resolve() for name in profile["nativePcGeneratedFiles"]]
        if not all(path.is_relative_to(data) for path in paths):
            parser.error("native runtime PC sources must stay under project .data")
        if any(profile.get("sourceHashes", {}).get(path.with_suffix(".o").name)
               != hashlib.sha256(path.read_bytes()).hexdigest() for path in paths):
            parser.error("native runtime PC source hash differs from compiled profile")
        generated = "\n".join(path.read_text() for path in paths)
    else:
        generated = ((args.profile / "gerbil-link.c").read_text() if not profile.get("nativePcModuleFiles")
                 else "\n".join((args.profile / "source/build/lib/static" / name).read_text()
                                for name in profile["nativePcModuleFiles"]))
    result = summarize(sample, generated,
                       json.loads((args.profile / "pc-landmarks.json").read_text()))
    result["sampleSha256"] = hashlib.sha256(sample.encode()).hexdigest()
    with args.output.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps({key: result[key] for key in ("listedSelfSamples", "landmarkSelfSamples", "topProcedures")}, indent=2))


if __name__ == "__main__":
    main()
