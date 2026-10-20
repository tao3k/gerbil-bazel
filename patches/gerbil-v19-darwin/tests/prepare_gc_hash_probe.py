"""Prepare an isolated, counter-only RTS source without changing hash policy."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess


def instrument(source):
    begin = source.index("___SCMOBJ ___gc_hash_table_ref\n")
    end = source.index("___SCMOBJ ___gc_hash_table_set\n", begin)
    body = source[begin:end]
    if body.count("  int size2;") != 1:
        raise RuntimeError("hash reference locals changed")
    body = body.replace("  int size2;", "  unsigned gb_probe_steps = 0;\n  int gb_probe_count = ___INT(___FIELD(WEAK,ht,___GCHASHTABLE_COUNT));\n  int size2;")
    reads = r"obj = ___FIELD\(WEAK,\s*ht, probe2\+___GCHASHTABLE_KEY0\);"
    body, count = re.subn(reads, lambda m: "++gb_probe_steps;\n  " + m[0], body)
    if count != 2:
        raise RuntimeError("hash initial and collision reads changed")
    body, count = re.subn(r"return (___FIELD\(WEAK, ht, probe2\+___GCHASHTABLE_VAL0\));",
                         r"GB_GC_PROBE_RETURN(\1,1);", body)
    if count != 2 or body.count("return ___UNUSED;") != 1:
        raise RuntimeError("hash terminal returns changed")
    body = body.replace("return ___UNUSED;", "GB_GC_PROBE_RETURN(___UNUSED,0);")
    if body.count("    gc_hash_table_rehash_in_situ (ht);") != 1:
        raise RuntimeError("lazy rehash branch changed")
    body = body.replace("    gc_hash_table_rehash_in_situ (ht);",
                        "    { ++gb_gc_probe_rehashes; gc_hash_table_rehash_in_situ (ht); }")
    return source[:begin] + '#include "gambit-gc-hash-probe-count.h"\n' + body + source[end:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3] / ".data"
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if platform.system() != "Darwin" or not all(p.is_relative_to(root) for p in (baseline, output)) or output.exists():
        parser.error("fresh project-data Darwin source required")
    subprocess.run(["/bin/cp", "-cR", str(baseline), str(output)], check=True)
    path = output / "src/gambit/lib/mem.c"
    original = path.read_text()
    changed = instrument(original)
    path.write_text(changed)
    header = Path(__file__).with_name("gambit-gc-hash-probe-count.h")
    (path.parent / header.name).write_bytes(header.read_bytes())
    report = {"scope": "counter-only-rts-hash-probe-no-performance",
              "originalMemSha256": hashlib.sha256(original.encode()).hexdigest(),
              "instrumentedMemSha256": hashlib.sha256(changed.encode()).hexdigest(),
              "headerSha256": hashlib.sha256(header.read_bytes()).hexdigest(),
              "hashPolicyChanged": False, "consumerFlagsChanged": False}
    (output / "gc-hash-probe-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("HASH-PROBE-PREPARED counter-only; hash/read/write policy unchanged", flush=True)


if __name__ == "__main__":
    main()
