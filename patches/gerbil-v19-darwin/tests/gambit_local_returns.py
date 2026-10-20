"""Prototype bounded local-continuation guards in original generated C."""
import re


def inject(content):
    procedures = sites = guards = 0
    def rewrite(match):
        nonlocal procedures, sites, guards
        body = match.group(1)
        targets = sorted({int(index) for index in re.findall(r"___SET_R0\(___LBL\((\d+)\)\)", body)})
        if not targets or len(targets) > 4:
            return match.group(0)
        labels = {}
        for index, label in re.findall(r"___DEF_SLBL\((\d+),(___L\w+)\)", body):
            labels.setdefault(int(index), set()).add(label)
        if any(len(labels.get(index, set())) != 1 for index in targets):
            return match.group(0)
        count = len(re.findall(r"^\s*___JUMPRET\(___R0\)$", body, re.MULTILINE))
        if not count:
            return match.group(0)
        prefix = "#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
        prefix += "\n".join(f"if (___R0==___LBL({index})) {{___GOTO({next(iter(labels[index]))})}}" for index in targets)
        prefix += "\n#endif\n   ___JUMPRET(___R0)"
        body = re.sub(r"^[ \t]*___JUMPRET\(___R0\)$", lambda _: prefix, body, flags=re.MULTILINE)
        procedures += 1
        sites += count
        guards += count * len(targets)
        return "___BEGIN_P_SW\n" + body + "___END_P_SW\n"
    result = re.sub(r"___BEGIN_P_SW\n(.*?)___END_P_SW\n", rewrite, content, flags=re.DOTALL)
    return result, {"procedures": procedures, "returnSites": sites, "labelGuards": guards,
                    "selection": "at-most-four-static-local-R0-continuations-no-profile-data"}
