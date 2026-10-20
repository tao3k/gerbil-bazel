"""Bounded call-site clones of read-only GVM leaf code; retain GC labels."""
import re


OPS = {
    "DEF_SLBL", "DEF_GLBL", "IF_NARGS_EQ", "NOTHING", "WRONG_NARGS",
    "IF", "NOT", "GOTO", "END_IF", "SET_R1", "SET_R2", "SET_R3", "SET_R4",
    "STRUCTUREP", "STRUCTURETYPE", "TYPESUPER", "TYPEID", "POLL", "NOTFALSEP",
    "EQP", "BOOLEAN", "TRU", "FAL", "JUMPRET", "FIX", "PAIRP", "CAR", "CDR",
    "NULP", "VECTORP", "VECTORLENGTH", "VECTORREF", "UNCHECKEDSTRUCTUREREF",
    "FIXEQ", "FIXLT", "FIXLE", "FIXGT", "FIXGE", "SYMBOLP", "KEYWORDP",
    "STRINGP", "CHARP", "GLO", "SYM", "KEY", "CNS", "SUB", "STK",
    "R0", "R1", "R2", "R3", "R4",
}


def candidates(module):
    result = {}
    pattern = re.compile(r"#undef ___PH_PROC\n#define ___PH_PROC (___\w+)\n"
                         r"#undef ___PH_LBL0\n#define ___PH_LBL0 (\d+)\n"
                         r".*?___BEGIN_P_SW\n(.*?)___END_P_SW\n", re.DOTALL)
    for match in pattern.finditer(module.get("originalBody", module["body"])):
        host, base, body = match.groups()
        if len(body.splitlines()) > 64 or body.count("___DEF_SLBL(") > 8:
            continue
        tokens = set(re.findall(r"\b___([A-Za-z_]\w*)\b", body))
        if any(token not in OPS and not re.fullmatch(r"L(?:\d+)?_\w+", token)
               and not token.startswith(("SYM_", "KEY_", "GLO_", "G_", "S_", "K_")) for token in tokens):
            continue
        defined = set(re.findall(r"___DEF_SLBL\(\d+,(___\w+)\)", body))
        defined.update(re.findall(r"___DEF_GLBL\((___\w+)\)", body))
        if not set(re.findall(r"___GOTO\((___\w+)\)", body)).issubset(defined):
            continue
        if "___JUMPRET(___R0)" not in body or re.search(r"___JUMPRET\((?!___R0\))", body):
            continue
        arity = re.search(r"___IF_NARGS_EQ\((\d+),___NOTHING\)", body)
        entry = re.search(r"___DEF_SLBL\(0,(___\w+)\)", body)
        if not arity or not entry or int(arity[1]) > 3:
            continue
        result[int(base)] = {"host": host, "base": int(base), "body": body,
                             "arity": int(arity[1]), "entry": entry[1]}
    return result


def clone(module, candidate, prefix, expected_return=None, return_label=None, entry_override=None):
    body = candidate["body"]
    labels = set(re.findall(r"___DEF_SLBL\(\d+,(___\w+)\)", body))
    labels.update(re.findall(r"___DEF_GLBL\((___\w+)\)", body))
    if not labels:
        raise RuntimeError("clone requires explicit native labels")
    if expected_return is not None:
        body = body.replace("___JUMPRET(___R0)",
            f"if (___R0==({expected_return})) {{___GOTO({return_label})}}\n   GB_LEAF_RETURN()")
    else:
        body = body.replace("___JUMPRET(___R0)", "GB_LEAF_RETURN()")
    body = body.replace(f"___DEF_SLBL(0,{candidate['entry']})",
                        f"___DEF_SLBL(0,{candidate['entry']})\nGB_LEAF_EVENT();", 1)
    if entry_override and entry_override != candidate["entry"]:
        if entry_override not in labels:
            raise RuntimeError("internal clone must use its original checked entry")
        body = body.replace(f"___DEF_GLBL({entry_override})",
                            f"___DEF_GLBL({entry_override})\nGB_LEAF_EVENT();", 1)
    for label in sorted(labels, key=len, reverse=True):
        body = re.sub(r"\b" + re.escape(label) + r"\b", prefix + label, body)
    # Private tables and PH_LBL0 remain the callee's: a poll resumes its original
    # descriptor, never an unregistered clone address.
    definitions = {name: value for name, value in module["controls"].items()
                   if name in set(re.findall(r"\b___\w+\b", candidate["body"]))}
    definitions.update(___PH_PROC=candidate["host"], ___PH_LBL0=str(candidate["base"]))
    for name in ("___symtbl", "___keytbl", "___cnstbl", "___subtbl", "___ofdtbl", "___glotbl"):
        definitions[name] = module["prefix"] + name
    definitions["___MLBL(n)"] = f"({module['prefix']}___lp+(((n)+{module['offset']})*___LABEL_SIZE*___WS))"
    definitions["___LBL(n)"] = "___MLBL(___PH_LBL0+(n))"
    names = sorted({name.split("(")[0] for name in definitions})
    result = "\n".join(f'#pragma push_macro("{name}")\n#undef {name}' for name in names) + "\n"
    result += "\n".join(f"#define {name} {value}" for name, value in definitions.items()) + "\n"
    result += "#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
    result += body + "\n#endif\n"
    result += "\n".join(f'#pragma pop_macro("{name}")' for name in reversed(names)) + "\n"
    return result, prefix + (entry_override or candidate["entry"])
