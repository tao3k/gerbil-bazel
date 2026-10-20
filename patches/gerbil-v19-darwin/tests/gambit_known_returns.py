"""Guard statically visible internal and local-subroutine return destinations."""
import re
from collections import defaultdict
from gambit_leaf_clones import OPS


PROC = re.compile(r"#define ___PH_LBL0 (\d+)\n.*?___BEGIN_P_SW\n(.*?)___END_P_SW\n", re.DOTALL)
LABEL = re.compile(r"___DEF_(?:SLBL\(\d+,|GLBL\()(___\w+)\)")


def inject(content):
    procedures = [(int(match[1]), match[2], match) for match in PROC.finditer(content)]
    targets = defaultdict(set)
    micro = defaultdict(set)
    for base, body, match in procedures:
        labels = {int(index): label for index, label in re.findall(r"___DEF_SLBL\((\d+),(___\w+)\)", body)}
        for call in re.finditer(r"___JUMPINT\(___SET_NARGS\(\d+\),___PRC\((\d+)\),___\w+\)", body):
            setters = re.findall(r"___SET_R0\(___LBL\((\d+)\)\)", body[:call.start()])
            if setters and int(setters[-1]) in labels:
                index = int(setters[-1])
                targets[int(call[1])].add((base + index, labels[index]))
        blocks = []
        matches = list(LABEL.finditer(body))
        for index, label in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            blocks.append((label[1], label.end(), body[label.end():end]))
        by_label = {label: index for index, (label, _, _) in enumerate(blocks)}
        pattern = re.compile(r"___SET_R0\(___LBL\((\d+)\)\)\n(?:[ \t]*___ADJFP\(-?\d+\)\n)?[ \t]*___GOTO\((___\w+)\)")
        for call in pattern.finditer(body):
            ret, entry = int(call[1]), call[2]
            if ret not in labels or entry not in by_label:
                continue
            queue, visited, returns, lines = [by_label[entry]], set(), [], 0
            valid = True
            while queue:
                index = queue.pop()
                if index in visited:
                    continue
                visited.add(index)
                _, start, block = blocks[index]
                lines += len(block.splitlines())
                tokens = set(re.findall(r"\b___([A-Za-z_]\w*)\b", block))
                if lines > 64 or len(visited) > 8 or any(
                        token not in OPS and not re.fullmatch(r"L(?:\d+)?_\w+", token)
                        and not token.startswith(("SYM_", "KEY_", "GLO_", "G_", "S_", "K_")) for token in tokens):
                    valid = False
                    break
                returns.extend(start + item.start()
                               for item in re.finditer(r"___JUMPRET\(___R0\)", block))
                for target in re.findall(r"___GOTO\((___\w+)\)", block):
                    if target not in by_label:
                        valid = False
                        break
                    queue.append(by_label[target])
                last = block.strip().splitlines()[-1].lstrip() if block.strip() else ""
                if not last.startswith(("___JUMPRET(", "___GOTO(")) and index + 1 < len(blocks):
                    queue.append(index + 1)
            if valid:
                for offset in returns:
                    micro[(base, offset)].add((base + ret, labels[ret]))
    sites = guards = 0
    def rewrite(match):
        nonlocal sites, guards
        base, body = int(match[1]), match[2]
        choices = sorted(targets.get(base, set()))[:4]
        def replace(ret):
            nonlocal sites, guards
            selected = sorted(set(choices) | micro.get((base, ret.start()), set()))[:4]
            if not selected:
                return ret[0]
            sites += 1
            guards += len(selected)
            result = "#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
            result += "\n".join(f"if(___R0==___MLBL({index})) {{GB_KNOWN_RETURN_EVENT(); ___GOTO({label})}}" for index, label in selected)
            return result + "\n#endif\n" + ret[0]
        rewritten = re.sub(r"___JUMPRET\(___R0\)", replace, body)
        return match[0][:match.start(2) - match.start()] + rewritten + "___END_P_SW\n"
    result = PROC.sub(rewrite, content)
    return result, {"returnSites": sites, "labelGuards": guards,
                    "microReturnSites": len(micro), "internalCalleeGroups": len(targets),
                    "selection": "bounded-static-internal-callers-and-read-only-local-subroutines-no-profile-data"}
