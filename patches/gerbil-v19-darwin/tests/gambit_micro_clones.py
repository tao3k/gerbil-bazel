"""Specialize bounded, nonallocating local GVM subroutines by continuation."""
import re
from gambit_known_returns import PROC, LABEL
from gambit_leaf_clones import OPS


GUARD = "defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)"


def inject(content, namespace, defer_frames=False):
    sites = returns = frames = 0
    def rewrite(match):
        nonlocal sites, returns, frames
        body = match[2]
        labels = {int(index): label for index, label in re.findall(r"___DEF_SLBL\((\d+),(___\w+)\)", body)}
        markers = list(LABEL.finditer(body))
        blocks = [(label[1], body[label.end():markers[i + 1].start() if i + 1 < len(markers) else len(body)])
                  for i, label in enumerate(markers)]
        by_label = {label: i for i, (label, _) in enumerate(blocks)}
        pattern = re.compile(r"___SET_R0\(___LBL\((\d+)\)\)\n(?:[ \t]*___ADJFP\(-?\d+\)\n)?[ \t]*___GOTO\((___\w+)\)")
        edits, copies, declarations = [], [], []
        for call in pattern.finditer(body):
            ret, entry = int(call[1]), call[2]
            if ret not in labels or entry not in by_label or sites >= 256:
                continue
            queue, visited, lines, valid = [by_label[entry]], set(), 0, True
            while queue and valid:
                i = queue.pop()
                if i in visited:
                    continue
                visited.add(i)
                _, block = blocks[i]
                lines += len(block.splitlines())
                # No safepoint, opaque effect, frame change or continuation mutation
                # may observe a specialized native-only continuation.
                allowed = OPS - {"POLL", "WRONG_NARGS", "IF_NARGS_EQ", "R0"}
                checked = block.replace("___JUMPRET(___R0)", "")
                tokens = set(re.findall(r"\b___([A-Za-z_]\w*)\b", checked))
                if lines > 64 or len(visited) > 8 or any(
                        token not in allowed and not re.fullmatch(r"L(?:\d+)?_\w+", token)
                        and not token.startswith(("SYM_", "KEY_", "GLO_", "G_", "S_", "K_")) for token in tokens):
                    valid = False
                    break
                for target in re.findall(r"___GOTO\((___\w+)\)", block):
                    if target not in by_label:
                        valid = False
                        break
                    queue.append(by_label[target])
                last = block.strip().splitlines()[-1].lstrip() if block.strip() else ""
                if not last.startswith(("___JUMPRET(", "___GOTO(")):
                    if i + 1 == len(blocks):
                        valid = False
                    else:
                        queue.append(i + 1)
            count = sum(blocks[i][1].count("___JUMPRET(___R0)") for i in visited)
            if not valid or not count:
                continue
            deferred = None
            if defer_frames:
                setup = re.search(
                    r"___SET_STK\(1,___R0\)\n[ \t]*___SET_STK\(2,___R1\)\n"
                    r"[ \t]*(?P<input>___SET_R1\(___STRUCTURETYPE\(___R1\)\))\n"
                    r"[ \t]*___SET_R0\(___LBL\((?P<ret>\d+)\)\)\n"
                    r"[ \t]*___ADJFP\((?P<frame>\d+)\)\n[ \t]*___GOTO\(___\w+\)$", body[:call.end()])
                continuation = blocks[by_label[labels[ret]]][1]
                hot = re.match(r"\s*___IF\(___NOTFALSEP\(___R1\)\)\n[ \t]*___GOTO\((___\w+)\)\n[ \t]*___END_IF", continuation)
                cold = re.match(r"\s*___IF\(___NOT\(___NOTFALSEP\(___R1\)\)\)\n[ \t]*___GOTO\((___\w+)\)\n[ \t]*___END_IF", continuation)
                if setup and int(setup["ret"]) == ret and ((hot and hot[1] in by_label) or cold):
                    frame = int(setup["frame"])
                    fast = blocks[by_label[hot[1]]][1] if hot else continuation[cold.end():]
                    expected = (rf"\s*___SET_R1\(___STK\({2-frame}\)\)\n"
                                rf"[ \t]*___SET_R0\(___STK\({1-frame}\)\)\n"
                                rf"[ \t]*___ADJFP\(-{frame}\)\n[ \t]*___JUMPRET\(___R0\)\s*")
                    if re.fullmatch(expected, fast):
                        deferred = (setup, frame, f"gb_saved_{namespace}_{sites}")
                if deferred is None:
                    continue
            mapping = {blocks[i][0]: f"gb_micro_{namespace}_{sites}_{i}" for i in visited}
            copy = ""
            for i in sorted(visited):
                label, block = blocks[i]
                copy += mapping[label] + ":\n"
                if label == entry:
                    copy += "GB_MICRO_EVENT();\n"
                for old, new in mapping.items():
                    block = re.sub(r"\b" + re.escape(old) + r"\b", new, block)
                if deferred:
                    setup, frame, saved = deferred
                    replacement = (f"___IF(___NOTFALSEP(___R1))\n___SET_R1({saved})\n___JUMPRET(___R0)\n___END_IF\n"
                                   f"___SET_STK(1,___R0)\n___SET_STK(2,{saved})\n"
                                   f"___SET_R0(___LBL({ret}))\n___ADJFP({frame})\n___GOTO({labels[ret]})")
                    block = block.replace("___JUMPRET(___R0)", replacement)
                else:
                    block = block.replace("___JUMPRET(___R0)", f"___GOTO({labels[ret]})")
                copy += block + "\n"
                last = blocks[i][1].strip().splitlines()[-1].lstrip() if blocks[i][1].strip() else ""
                if not last.startswith(("___JUMPRET(", "___GOTO(")):
                    copy += f"___GOTO({mapping[blocks[i + 1][0]]})\n"
            jump = re.search(r"___GOTO\(___\w+\)$", call[0])
            if deferred:
                setup, _, saved = deferred
                declarations.append(f"___WORD {saved};")
                replacement = (f"#if {GUARD} && (___MAX_PROCESSORS == 1)\n"
                               f"{saved}=___R1;\n{setup['input']}\n___GOTO({mapping[entry]})\n"
                               f"#else\n{setup[0]}\n#endif")
                edits.append((setup.start(), call.end(), replacement))
                frames += 1
            else:
                replacement = f"#if {GUARD}\n___GOTO({mapping[entry]})\n#else\n{jump[0]}\n#endif"
                edits.append((call.start() + jump.start(), call.end(), replacement))
            copies.append(copy)
            sites += 1
            returns += count
        for start, end, replacement in reversed(edits):
            body = body[:start] + replacement + body[end:]
        body = "\n".join(declarations) + "\n" + body if declarations else body
        if copies:
            # The original procedure ends in an explicit transfer; copies have
            # explicit exits and are never entered by linear fallthrough.
            last = match[2].strip().splitlines()[-1].lstrip()
            if not last.startswith(("___JUMPRET(", "___GOTO(", "___JUMP")):
                raise RuntimeError("local specialization requires a terminal original procedure")
            body += f"\n#if {GUARD}\n" + "\n".join(copies) + "\n#endif\n"
        return match[0][:match.start(2) - match.start()] + body + "___END_P_SW\n"
    result = PROC.sub(rewrite, content)
    return result, {"callsiteCopies": sites, "directReturns": returns, "deferredFrames": frames,
                    "selection": "bounded-static-local-read-only-no-poll-no-profile-data"}
