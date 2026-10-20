"""Diagnostic generated-C injection; production needs emitter liveness marks."""
import json
import re


def inject(content, header):
    count = content.count("___GET_REST(")
    if not count:
        return content, 0
    definitions = dict(re.findall(r"^#define\s+(___[A-Z_]+)\s+(.+)$", content.replace("\\\n", " "), re.MULTILINE))
    prefix = f'#include {json.dumps(str(header))}\n'
    for name, required in (("___MD_ALL", ("___D_HEAP", "___D_R1", "___D_R2", "___D_R3")),
                           ("___MR_ALL", ("___R_HEAP", "___R_R1", "___R_R2", "___R_R3")),
                           ("___MW_ALL", ("___W_HEAP", "___W_R1", "___W_R2", "___W_R3"))):
        original = definitions[name]
        extra = " ".join(token for token in required if token not in original.split())
        prefix += f"#undef {name}\n#define {name} {original} {extra}\n"
    if content.count("___BEGIN_M_COD\n") != 1:
        raise RuntimeError("rest probe requires one original single-host module")
    return content.replace("___GET_REST(", "___GET_REST_DARWIN(").replace(
        "___BEGIN_M_COD\n", prefix + "___BEGIN_M_COD\n"), count
