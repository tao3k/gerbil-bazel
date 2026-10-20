"""Experimental mutation-fenced prefix cache, never a Scheme result cache."""
import re


def thread_dependency(code):
    """Only proven low-field reads are independent of thread slots 25..27."""
    indexed = {"VECTORREF", "UNCHECKEDSTRUCTUREREF", "CLO"}
    low_or_pure = {"NOT", "NOTFALSEP", "EQP", "TYPE", "SUBTYPE", "STRUCTUREP",
                   "STRUCTURETYPE", "TYPEID", "TYPESUPER", "VECTORLENGTH", "FIX",
                   "FIXEQ", "FIXLT", "FIXLE", "FIXGT", "FIXGE", "BOOLEAN", "PAIRP",
                   "CAR", "CDR", "NULP", "VECTORP", "MEMALLOCATEDP", "FIXAND",
                   "LABEL_ENTRY_GET", "CAST_FAKEWORD_TO_WORD", "CAST", "TYPECAST",
                   "STRUCTUREDIOP", "BOXP", "UNBOX", "NULLP", "SYMBOLP", "PROCEDUREP"}
    type_values = set()
    for line in code:
        definition = re.fullmatch(r"___WORD (gb_t\d+)=\(___TYPE\(.*\)\);", line)
        if definition:
            type_values.add(definition[1])
    for line in code:
        for call in re.finditer(r"___([A-Z_]+)\(", line):
            if call[1] not in indexed:
                if call[1] not in low_or_pure:
                    return "1"
                continue
            start = call.end()
            depth, end, args = 0, start, []
            while end < len(line):
                char = line[end]
                if char == "(":
                    depth += 1
                elif char == ")":
                    if depth == 0:
                        args.append(line[start:end].strip())
                        break
                    depth -= 1
                elif char == "," and depth == 0:
                    args.append(line[start:end].strip())
                    start = end + 1
                end += 1
            if end == len(line) or len(args) < 2:
                return "1"
            index = args[1]
            literal = re.fullmatch(r"___FIX\((\d+)L?\)", index)
            # CLO uses an untagged field index and a one-word body offset.
            if call[1] == "CLO":
                literal = re.fullmatch(r"(\d+)L?", index)
            if literal and int(literal[1]) < 16:
                continue
            if call[1] != "CLO" and index in type_values:
                continue
            return "1"
    return "0"


def prefix(state, materialized, miss, site=0):
    definitions, checks, cheap = {}, [], []
    for line in state.code:
        definition = re.fullmatch(r"___WORD (gb_t\d+)=\((.*)\);", line)
        if definition:
            if "___STK(" in definition[2]:
                return None
            definitions[definition[1]] = definition[2]
        elif re.fullmatch(r"if \(!\(___MEMALLOCATEDP\(gb_in[0-4]\)\)\) goto GB_TRACE_MISS;", line):
            cheap.append(line.replace("GB_TRACE_MISS", miss))
        elif line.startswith("if (") and line.endswith("goto GB_TRACE_MISS;"):
            checks.append(line)
        else:
            return None
    inputs = sorted(set(re.findall(r"gb_in[0-4]", " ".join(definitions.values()) + " ".join(checks))))
    live = sorted(set(re.findall(r"gb_t\d+", materialized)), key=lambda name: int(name[4:]))
    if not live or len(live) > 16:
        return None
    declarations = "".join(f"___WORD {name};\n" for name in definitions)
    hash_expression = " ^ ".join(f"((unsigned long long){name} >> 3) ^ ((unsigned long long){name} >> 11)" for name in inputs) or "0"
    match = " && ".join(f"gb_slot->keys[{i}]=={name}" for i, name in enumerate(inputs)) or "1"
    result = "\n".join(cheap) + "\n" + declarations
    result += (f"static struct {{ unsigned long long epoch,thread_epoch; int thread_sensitive; ___WORD keys[{max(1, len(inputs))}], values[{len(live)}]; }} gb_cache[64];\n"
               f"__typeof__(gb_cache[0]) *gb_slot=&gb_cache[({hash_expression}) & 63];\n"
               f"if (gb_trace_epoch && gb_slot->epoch==gb_trace_epoch && {match} && "
               "(!gb_slot->thread_sensitive || (gb_trace_thread_epoch && gb_slot->thread_epoch==gb_trace_thread_epoch))) {\n")
    result += "".join(f"{name}=gb_slot->values[{i}];\n" for i, name in enumerate(live))
    result += f"GB_TRACE_CACHE_SITE({site});\n}} else {{\n"
    result += (f"if (gb_slot->epoch==gb_trace_epoch && gb_slot->thread_sensitive && "
               f"gb_slot->thread_epoch!=gb_trace_thread_epoch) {{ GB_TRACE_THREAD_CACHE_MISS({site}); }}\n"
               f"else {{ GB_TRACE_CACHE_MISS({site},gb_slot->epoch!=gb_trace_epoch); }}\n")
    for line in state.code:
        if line.replace("GB_TRACE_MISS", miss) in cheap:
            continue
        result += re.sub(r"^___WORD (gb_t\d+)=", r"\1=", line).replace("GB_TRACE_MISS", miss) + "\n"
    result += "".join(f"gb_slot->keys[{i}]={name};\n" for i, name in enumerate(inputs))
    result += "".join(f"gb_slot->values[{i}]={name};\n" for i, name in enumerate(live))
    result += f"gb_slot->thread_sensitive=({thread_dependency(state.code)});\n"
    result += "gb_slot->thread_epoch=gb_trace_thread_epoch;\n"
    result += "gb_slot->epoch=gb_trace_epoch;\n}\n"
    return result


def owned_closure_initializers(program):
    owned = set()
    for mi, position in program.scopes:
        lines = program.lines[mi]
        allocation = re.fullmatch(r"\s*___SET_(R[0-4]|STK)\((.*)___ALLOC_CLO\((\d+)UL\)\)\s*", lines[position])
        if not allocation:
            continue
        size = int(allocation[3])
        if size > 16:
            continue
        if allocation[1] == "STK":
            slot = re.fullmatch(r"(-?\d+),", allocation[2])
            if not slot:
                continue
            target = f"___STK({slot[1]})"
        elif allocation[2]:
            continue
        else:
            target = f"___{allocation[1]}"
        setup = position + 1
        if any((mi, point) not in program.scopes for point in range(position, setup + size + 2)):
            continue
        if not re.fullmatch(r"\s*___BEGIN_SETUP_CLO\(" + str(size) + "," + re.escape(target) + r",\d+\)\s*", lines[setup]):
            continue
        fields = []
        for offset in range(size):
            field = re.fullmatch(r"\s*___ADD_CLO_ELEM\((\d+),.*\)\s*", lines[setup + offset + 1])
            if not field:
                break
            fields.append(int(field[1]))
        if sorted(fields) != list(range(size)):
            continue
        if not re.fullmatch(r"\s*___END_SETUP_CLO\(" + str(size) + r"\)\s*", lines[setup + size + 1]):
            continue
        owned.update((mi, point) for point in range(position, setup + size + 2))
    return owned


def fences(program, reads):
    # Unknown instructions, including foreign C, invalidate conservatively.
    allowed = set(reads) | {"GLO", "SYM", "KEY", "SUB", "STK", "LBL", "PRC", "CLO",
        "SYMBOLP", "KEYWORDP", "STRINGP", "CHARP", "PROCEDUREP", "FIXPOSITIVEP",
        "STRUCTUREDIOP", "GET_STRUCTURE", "GET_SUBTYPED", "END_SETUP_CLO",
        "BEGIN_ALLOC_STRUCTURE", "ADD_STRUCTURE_ELEM", "END_ALLOC_STRUCTURE",
        "BEGIN_IF", "END_IF", "BEGIN_ELSE", "END_ELSE", "IF", "GOTO", "DEF_SLBL", "DEF_GLBL",
        "IF_NARGS_EQ", "WRONG_NARGS", "NOTHING",
        "GET_REST", "GET_KEY", "GET_REST_KEY", "GET_KEY_REST",
        "SET_STK", "ADJFP", "SET_NARGS", "JUMPRET", "JUMPINT", "JUMPGLOSAFE", "JUMPGLONOTSAFE",
        "JUMPGENSAFE", "JUMPGENNOTSAFE", "JUMPEXTPRM", "POLL", "CHECK_HEAP",
        "FIXADD", "FIXSUB", "FIXMUL", "FIXZEROP", "FIXNUMP", "FIXASHL", "NULLP", "INT", "CAST", "CAST_FAKEWORD_TO_WORD",
        "BEGIN_ALLOC_PAIR", "END_ALLOC_PAIR", "ADD_PAIR_ELEM", "BEGIN_ALLOC_SUBTYPED", "END_ALLOC_SUBTYPED",
        "BEGIN_ALLOC_VECTOR", "END_ALLOC_VECTOR", "ADD_VECTOR_ELEM", "BEGIN_ALLOC_VECTOR_EXPR",
        "END_ALLOC_VECTOR_EXPR", "ADD_VECTOR_ELEM_EXPR", "GCHASHTABLEREF"}
    allowed.update(f"SET_R{n}" for n in range(5))
    edits, consumed = [], set()
    owned = owned_closure_initializers(program)
    fresh_pairs = {"CONS", "XCONS"}
    fresh_closures = {"ALLOC_CLO", "BEGIN_SETUP_CLO", "ADD_CLO_ELEM", "END_SETUP_CLO"}
    program.fresh_epoch_fences = set()
    # Generated macro invocations may span lines; never split their arguments.
    tokens = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*|[()]', re.S)
    if any("___CFUN" in module["originalBody"] for module in program.modules):
        raise ValueError("epoch cache excludes foreign C callbacks")
    for mi, position in program.scopes:
        if (mi, position) in consumed:
            continue
        line = program.lines[mi][position].strip()
        if not line or line.startswith(("#", "/*", "//")):
            continue
        if line == "{ ___SCMOBJ ___RESULT;":
            end = position + 1
            while (mi, end) in program.scopes and program.lines[mi][end].strip() != "}":
                part = program.lines[mi][end].strip()
                if not (re.fullmatch(r"___RESULT\s*=\s*___FIX\((?:___\w+|\d+)\)\s*;", part)
                        or re.fullmatch(r"___SET_R[0-4]\(___RESULT\)", part)
                        or re.fullmatch(r"#(?:ifdef ___\w+|else|endif)", part)):
                    raise ValueError("epoch cache excludes effectful embedded C")
                consumed.add((mi, end))
                end += 1
            if (mi, end) not in program.scopes:
                raise ValueError("unterminated constant-result block")
            consumed.add((mi, end))
            continue
        end = position
        while True:
            depth = sum(1 if token == "(" else -1 if token == ")" else 0 for token in tokens.findall(line))
            if depth <= 0:
                break
            end += 1
            if (mi, end) not in program.scopes:
                raise ValueError("unterminated GVM macro invocation")
            consumed.add((mi, end))
            line += "\n" + program.lines[mi][end].strip()
        if line in {"___END_IF", "___END_ELSE", "___NOTHING"}:
            continue
        if not line.startswith("___"):
            raise ValueError(f"epoch cache requires macro-only GVM bodies: module {mi}, line {position + 1}: {line[:160]}")
        operations = set(re.findall(r"___(\w+)\s*\(", line))
        if not operations or not operations <= allowed:
            edits.append((mi, position))
            calls = re.findall(r"\b([A-Za-z_]\w*)\s*\(", line)
            macro_only = all(call.startswith("___") for call in calls)
            if macro_only and (operations and operations <= allowed | fresh_pairs or
                (mi, position) in owned and operations <= allowed | fresh_pairs | fresh_closures):
                program.fresh_epoch_fences.add((mi, position))
    return edits


PREAMBLE = r"""
#ifndef GB_TRACE_CACHE_HIT
#define GB_TRACE_CACHE_HIT() ((void)0)
#endif
#ifndef GB_TRACE_CACHE_SITE
#define GB_TRACE_CACHE_SITE(site) GB_TRACE_CACHE_HIT()
#endif
#ifndef GB_TRACE_CACHE_MISS
#define GB_TRACE_CACHE_MISS(site,stale) ((void)0)
#endif
#ifndef GB_TRACE_FENCE_SITE
#define GB_TRACE_FENCE_SITE(site) ((void)0)
#endif
#ifndef GB_TRACE_THREAD_CACHE_MISS
#define GB_TRACE_THREAD_CACHE_MISS(site) ((void)0)
#endif
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && defined(___SINGLE_VM) && defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && (___NB_ARG_REGS == 3) && !defined(___DYNAMIC)
static unsigned long long gb_trace_epoch=1,gb_trace_thread_epoch=1;
/* Zero permanently disables caches after wraparound. */
#define GB_TRACE_INVALIDATE() do { if (gb_trace_epoch) ++gb_trace_epoch; } while (0)
#define GB_TRACE_INVALIDATE_AT(site) do { GB_TRACE_FENCE_SITE(site); GB_TRACE_INVALIDATE(); } while (0)
#if !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT) && (___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0)
#define GB_TRACE_FRESH_ALLOCATION_AT(site) ((void)0)
#else
#define GB_TRACE_FRESH_ALLOCATION_AT(site) GB_TRACE_INVALIDATE_AT(site)
#endif
#if (___WS == 8) && (___TB <= 3) && !defined(___USE_HANDLES) && (___PAIR_BODY == 1) && (___SUBTYPED_BODY == 1) && (___CLO_FREEVARS == 1) && (___THREAD_DENV_CACHE1 == 25) && (___THREAD_DENV_CACHE2 == 26) && (___THREAD_DENV_CACHE3 == 27) && (___TYPE_ID == 1) && (___TYPE_SUPER == 4) && (___STRUCTURE_TYPE == 0)
#define GB_TRACE_THREAD_INVALIDATE_AT(site) do { if (gb_trace_thread_epoch) ++gb_trace_thread_epoch; } while (0)
#else
#define GB_TRACE_THREAD_INVALIDATE_AT(site) GB_TRACE_INVALIDATE_AT(site)
#endif
#undef ___GCHASHTABLEREF
#define ___GCHASHTABLEREF(x,y) ({ ___WORD gb_ht=(x),gb_key=(y); if (!___FIXZEROP(___FIXAND(___GCHASHTABLE_FLAGS_FIELD(gb_ht),___FIX(___GCHASHTABLE_FLAG_KEY_MOVED)))) GB_TRACE_INVALIDATE_AT(1); ___EXT(___gc_hash_table_ref)(gb_ht,gb_key); })
#else
#define GB_TRACE_INVALIDATE() ((void)0)
#define GB_TRACE_INVALIDATE_AT(site) ((void)0)
#define GB_TRACE_FRESH_ALLOCATION_AT(site) ((void)0)
#define GB_TRACE_THREAD_INVALIDATE_AT(site) ((void)0)
#endif
"""
