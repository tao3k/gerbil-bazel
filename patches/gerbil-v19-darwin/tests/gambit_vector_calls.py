"""Guard vector dispatch with statically constructed module-init procedures."""
import re


def inject(original, body):
    init = re.search(r"#define ___PH_LBL0 (\d+).*?___BEGIN_P_SW\n(.*?)___END_P_SW", body, re.DOTALL)
    metadata = original.split("___BEGIN_LBL\n", 1)[1].split("___END_LBL", 1)[0]
    rows = [row.strip().lstrip(",") for row in metadata.splitlines() if row.strip()]
    candidates = {}
    if init:
        base, init_body = int(init.group(1)), init.group(2)
        indices = {int(value) for value in re.findall(r"___SET_R[1-4]\(___LBL\((\d+)\)\)", init_body)}
        indices.update(int(value) for value in re.findall(r"___BEGIN_SETUP_CLO\(\d+,(?:___R[0-4]|___STK\(-?\d+\)),(\d+)\)", init_body))
        labels = {int(index): label for index, label in re.findall(r"___DEF_SLBL\((\d+),(___L\w+)\)", init_body)}
        for index in sorted(indices):
            absolute = base + index
            if absolute >= len(rows) or index not in labels:
                continue
            descriptor = re.fullmatch(r"___DEF_LBL_PROC\(___\w+,(\d+),-?\d+\)", rows[absolute])
            if descriptor:
                candidates.setdefault(int(descriptor.group(1)), []).append((absolute, labels[index]))
    sites = guards = 0
    pattern = re.compile(
        r"(?P<load>^[ \t]*___SET_(?P<register>R[1-4])\(___VECTORREF\(___GLO_\w+,(?:___R[0-4]|___FIX\(-?\d+L\))\)\)\n)"
        r"[ \t]*(?P<jump>___JUMPGEN(?P<kind>SAFE|NOTSAFE)\((?P<nargs>___SET_NARGS\((?P<arity>\d+)\)),___(?P=register)\))", re.MULTILINE)

    def replace(match):
        nonlocal sites, guards
        targets = candidates.get(int(match["arity"]), [])
        if not targets or len(targets) > 8:
            return match.group(0)
        sites += 1
        guards += len(targets)
        code = match["load"] + "#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
        code += "{ ___WORD gb_value=___" + match["register"] + f";\nif (GB_VECTOR_VALID_{match['kind']}(gb_value)) {{\n___WORD gb_entry=___LABEL_ENTRY_GET(gb_value);\n"
        for index, label in targets:
            code += f"if(gb_entry==___MLBL({index})) {{GB_VECTOR_EVENT(1); {match['nargs']} ___SELF=gb_value; ___GOTO({label})}}\n"
        code += f"GB_VECTOR_EVENT(0); {match['nargs']} ___SELF=gb_value; ___JUMP(gb_entry)\n}}\nGB_VECTOR_EVENT(0);\n" + match["jump"] + "\n}\n#else\n" + match["jump"] + "\n#endif"
        return code

    result = pattern.sub(replace, body)
    return result, {"sites": sites, "entryGuards": guards,
                    "staticInitCandidates": {str(arity): values for arity, values in candidates.items()},
                    "selection": "at-most-eight-static-module-init-procedure-values-no-profile-data"}
