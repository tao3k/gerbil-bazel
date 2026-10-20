"""Bounded native helpers keep guarded traces outside the large GVM CFG."""
import re


def outline(program, state, site, guard):
    def temps(snapshot):
        values = [*snapshot.registers.values(), *(value for key, value in snapshot.stack.items()
                                                   if key <= snapshot.frame)]
        values = [snapshot.resolved_word(value) for value in values]
        return {value for value in values if isinstance(value, str) and re.fullmatch(r"gb_t\d+", value)}
    snapshot = state.effect_snapshot[2]
    final, cold = temps(state), temps(snapshot)
    if state.terminal and state.terminal[0] not in {'GB_ORIGINAL_EFFECT', 'GB_ORIGINAL_REENTRY'}:
        final.update(re.findall(r'\bgb_t\d+\b', str(state.resolved_word(state.terminal[2]))))
    words = sorted(final | cold, key=lambda name: int(name[4:]))
    if len(words) > 24:
        raise ValueError("outlined native result budget")
    inputs = sorted(set(re.findall(r"gb_in[0-4]", "\n".join(state.code))))
    parameters = [f"___WORD {word}" for word in inputs]
    arguments = list(inputs)
    if "___ps" in "\n".join(state.code):
        parameters.append("___processor_state ___ps")
        arguments.append("___ps")
    if any(token in "\n".join(state.code) for token in ("___STK(", "___fp")):
        parameters.append("___WORD *___fp")
        arguments.append("___fp")
    name = f"gb_trace_native_{site}"
    code = f"\n#if {guard}\nstruct {name}_result {{ ___WORD words[{max(1, len(words))}]; }};\n"
    code += (f"static int __attribute__((noinline,optimize(\"O3\"))) {name}("
             + ",".join([*parameters, f"struct {name}_result *out"])
             + ") {\n___WORD ___temp;\n")
    code += "\n".join(state.code).replace("GB_TRACE_MISS", "gb_native_miss").replace("GB_TRACE_EFFECT_MISS", "gb_native_effect_miss") + "\n"
    code += "".join(f"out->words[{index}]={word};\n" for index, word in enumerate(words))
    code += "return 1;\ngb_native_effect_miss:;\n"
    code += "".join(f"out->words[{index}]={word};\n" for index, word in enumerate(words) if word in cold)
    code += "return -1;\ngb_native_miss:;\nreturn 0;\n}\n#endif\n"
    caller = f"struct {name}_result gb_native_result;\n"
    caller += f"int gb_native_status={name}(" + ",".join([*arguments, "&gb_native_result"]) + ");\n"
    caller += "if (!gb_native_status) goto GB_TRACE_MISS;\n"
    caller += "".join(f"___WORD {word};\n" for word in words)
    caller += "".join(f"{word}=gb_native_result.words[{index}];\n" for index, word in enumerate(words) if word in cold)
    caller += "if (gb_native_status < 0) goto GB_TRACE_EFFECT_MISS;\n"
    caller += "".join(f"{word}=gb_native_result.words[{index}];\n" for index, word in enumerate(words) if word not in cold)
    return code, caller
