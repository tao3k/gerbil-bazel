"""Prototype a descending stride-two clone of the original GC marker."""
import argparse
import hashlib
import json
from pathlib import Path


GUARD = r'''#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && \
    defined(___SINGLE_THREADED_VMS) && defined(___SINGLE_VM) && \
    (___MAX_PROCESSORS == 1) && (___WS == 8) && !defined(ENABLE_CONSISTENCY_CHECKS)
#define GAMBIT_DARWIN_STRIDED_MARK 1
#else
#define GAMBIT_DARWIN_STRIDED_MARK 0
#endif
'''


def transform(source):
    begin = "___HIDDEN void mark_array\n"
    end = "\n\n___HIDDEN void mark_captured_continuation\n"
    if source.count(begin) != 1 or source.count(end) != 1:
        raise ValueError("original marker function boundary differs")
    start = source.index(begin)
    finish = source.index(end, start)
    original = source[start:finish]
    split = "\n#endif\n{\n"
    if original.count(split) != 1 or original.count("___WORD *cell = start++;") != 1:
        raise ValueError("original marker declaration/iteration differs")
    header, body = original.split(split)
    clone = (header.replace("___HIDDEN void mark_array", "static void mark_array_stride2", 1)
             + "\n{\n" + body.replace("___WORD *cell = start++;",
                                         "___WORD *cell = start;\n      start -= 2;", 1))
    result = source[:finish] + "\n\n" + GUARD + "\n#if GAMBIT_DARWIN_STRIDED_MARK\n" + clone + "\n#endif\n" + source[finish:]
    key = """              for (i=words-2; i>=___GCHASHTABLE_KEY0; i-=2)
                mark_array (___PSP body+i, 1); /* mark objects in key fields */"""
    value = """              for (i=words-1; i>=___GCHASHTABLE_VAL0; i-=2)
                mark_array (___PSP body+i, 1); /* mark objects in value fields */"""
    for old, first, bound in ((key, 2, "KEY0"), (value, 1, "VAL0")):
        if result.count(old) != 1:
            raise ValueError("original strong GC-table scan differs")
        new = ("#if GAMBIT_DARWIN_STRIDED_MARK\n"
               f"              i = words-{first};\n"
               f"              if (i >= ___GCHASHTABLE_{bound})\n"
               "                mark_array_stride2 (___PSP body+i,\n"
               f"                                    (i-___GCHASHTABLE_{bound})/2+1);\n"
               "#else\n" + old + "\n#endif")
        result = result.replace(old, new, 1)
    return result, {"markerBodySha256": hashlib.sha256(body.encode()).hexdigest(),
                    "scope": "same-marker-same-descending-field-order-not-performance",
                    "originalMarkerPreserved": original in result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[3] / ".data"
    if not all(path.resolve().is_relative_to(data) for path in (args.source, args.output)):
        parser.error("prototype and receipt must remain under project .data")
    original = args.source.read_text()
    modified, report = transform(original)
    report["originalSha256"] = hashlib.sha256(original.encode()).hexdigest()
    report["modifiedSha256"] = hashlib.sha256(modified.encode()).hexdigest()
    report["generatorSha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    args.source.write_text(modified)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
