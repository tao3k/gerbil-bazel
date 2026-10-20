"""Isolated formatter-level prototype; retain each original module's code."""
import json
import re
from pathlib import Path
from gambit_local_returns import inject as inject_local_returns
from gambit_vector_calls import inject as inject_vector_calls
from gambit_leaf_clones import candidates as leaf_candidates, clone as clone_leaf
from gambit_known_returns import inject as inject_known_returns
from gambit_micro_clones import inject as inject_micro_clones
from gambit_guarded_trace import inject as inject_guarded_traces, PREAMBLE as TRACE_PREAMBLE
from gambit_trace_epoch_cache import PREAMBLE as EPOCH_PREAMBLE
from gambit_parameter_entry import inject as inject_parameter_entry, PREAMBLE as PARAMETER_PREAMBLE, identity_preamble
from gambit_bounded_primitives import inject as inject_bounded_primitives, PREAMBLE as BOUNDED_PRIMITIVE_PREAMBLE
from gambit_type_chain import PREAMBLE as TYPE_CHAIN_PREAMBLE


PRIVATE = {"___lp", "___lbltbl", "___symtbl", "___keytbl", "___cnstbl", "___subtbl", "___ofdtbl",
           "___glotbl", "___sym_names", "___key_names", "___glo_names", "___setup_mod", "___init_mod", "___module_descr"}
COMMON = "gb_coalesced_host"
REGS = "___D_HEAP ___D_FP ___D_R0 ___D_R1 ___D_R2 ___D_R3 ___D_R4"
READS = REGS.replace("___D_", "___R_")
WRITES = REGS.replace("___D_", "___W_")


def section(text, begin, end):
    before, marker, rest = text.partition(begin + "\n")
    middle, ending, after = rest.partition(end + "\n")
    if not marker or not ending or begin in before or end in after:
        raise RuntimeError(f"unique generated {begin} section required")
    return before, middle, after


def context(module, content, definitions=None, body=False):
    controls = module["controls"]
    aliases = {name: module["prefix"] + name for name in module["private"]}
    if body and module.get("cachedLabelBase"):
        aliases["___lp"] = module["cachedLabelBase"]
    aliases[module["host"]] = COMMON
    aliases[module["linker"]] = module["newLinker"]
    counts = module["counts"]
    offset = module["offset"]
    selectors = {
        "___GLOTBL": "0,0,0,0",
        "___SYMTBL": "___symtbl,___SYMCOUNT,0" if counts.get("___SYMCOUNT") else "0,0,0",
        "___KEYTBL": "___keytbl,___KEYCOUNT,0" if counts.get("___KEYCOUNT") else "0,0,0",
        "___CNSTBL": "___cnstbl,___CNSCOUNT" if counts.get("___CNSCOUNT") else "0,0",
        "___SUBTBL": "___subtbl,___SUBCOUNT" if counts.get("___SUBCOUNT") else "0,0",
        "___OFDTBL": "___ofdtbl,sizeof(___ofdtbl)/sizeof(___WORD)" if counts.get("___OFDCOUNT") else "0,0",
        "___LBLTBL": "&___lp,___lbltbl,___LBLCOUNT",
        "___MLBL(n)": f"(___lp+(((n)+{offset})*___LABEL_SIZE*___WS))",
        "___LBL(n)": "___MLBL(___PH_LBL0+(n))",
        "___PRC(i)": "___MLBL(i)",
        "___REF_PRC(i)": f"___REF_MEM(___SUBCOUNT+(i)+{offset},___tMEM1)",
    }
    if body:
        selectors.update(___MD_ALL=REGS, ___MR_ALL=READS, ___MW_ALL=WRITES)
    names = sorted(set(controls) | set(aliases) | {key.split("(")[0] for key in selectors})
    result = "\n".join(f'#pragma push_macro("{name}")\n#undef {name}' for name in names) + "\n"
    if definitions:
        result += "\n".join(f"#define {name} {value}" for name, value in definitions.items()) + "\n"
    result += "\n".join(f"#define {name} {value}" for name, value in aliases.items()) + "\n"
    result += "\n".join(f"#undef {name.split('(')[0]}\n#define {name} {value}" for name, value in selectors.items()) + "\n"
    result += content + "\n"
    result += "\n".join(f'#pragma pop_macro("{name}")' for name in reversed(names)) + "\n"
    return result


def render(paths, link_content, output, runtime_linkers=(), guarded_global_jumps=False, return_label_count=False,
           local_return_guards=False, cache_label_bases=False, gen_entry_count=False, vector_entry_guards=False,
           guarded_leaf_clones=False, internal_leaf_clones=False, known_return_guards=False,
           local_subroutine_clones=False, defer_local_frames=False, guarded_readonly_traces=False,
           guarded_trace_polls=False, guarded_trace_restart_polls=False,
           guarded_trace_coalesce_polls=False, guarded_trace_primitive_boundary=False,
           guarded_trace_epoch_cache=False, guarded_trace_inline_lookup=False,
           guarded_trace_outline_lookup=False, parameter_entry_fastpath=False,
           guarded_trace_allocations=False, parameter_identity_return=False, parameter_env_lookup=False,
           bounded_primitive_entries=False, guarded_trace_lookup_return_branches=False,
           supplementary_pure_branches=False, supplementary_fresh_branches=False,
           scalar_caller_labels=(), scalar_boundary_labels=(), guarded_trace_outline_returns=False):
    if guarded_trace_outline_returns and not (guarded_readonly_traces and
            guarded_trace_outline_lookup and guarded_trace_lookup_return_branches):
        raise ValueError('return outlining requires readonly outlined lookup and return branches')
    if scalar_boundary_labels and not guarded_readonly_traces:
        raise RuntimeError('boundary scalarization requires readonly trace carrier')
    if scalar_caller_labels and not guarded_readonly_traces:
        raise RuntimeError('caller scalarization requires readonly trace carrier')
    if (supplementary_pure_branches or supplementary_fresh_branches) and not guarded_readonly_traces:
        raise ValueError('supplementary pure trees require readonly traces')
    if parameter_identity_return and not parameter_entry_fastpath:
        raise ValueError('identity return requires the original parameter-entry guards')
    if parameter_entry_fastpath and guarded_trace_epoch_cache and not parameter_identity_return:
        raise ValueError('parameter/epoch composition requires explicit identity/coherence mode')
    if parameter_env_lookup and not parameter_identity_return:
        raise ValueError('environment lookup requires explicit identity/coherence mode')
    modules = []
    dummy_prefix = []
    offset = 0
    for index, path in enumerate(paths):
        original = path.read_text()
        logical_lines = original.replace("\\\n", " ")
        definitions = {name: value or "" for name, value in re.findall(
            r"^#define[ \t]+([A-Za-z_]\w*)(?:[ \t]+(.*))?$", logical_lines, re.MULTILINE)}
        counts = {name: int(value) for name, value in definitions.items() if name.endswith("COUNT") and value.isdigit()}
        before, host, after = section(original, "___BEGIN_M_COD", "___END_M_COD")
        _, hlbl, _ = section(host, "___BEGIN_M_HLBL", "___END_M_HLBL")
        _, body, _ = section(host, "___BEGIN_M_SW", "___END_M_SW")
        hlbl_rows = [line.strip() for line in hlbl.splitlines() if line.strip()]
        count = counts.get("___LBLCOUNT")
        if not count or len(hlbl_rows) != count:
            raise RuntimeError("host label count and module descriptor differ")
        private = PRIVATE | set(re.findall(r"\b___X\d+\b", original)) | set(re.findall(r"\b___L[0-9]*_\w+\b", original))
        module = {"prefix": f"gb_m{index}", "controls": definitions, "counts": counts,
                  "private": private, "host": definitions["___MH_PROC"],
                  "linker": definitions["___LINKER_ID"],
                  "newLinker": definitions["___LINKER_ID"] if definitions["___LINKER_ID"] in runtime_linkers else f"gb_link_m{index}",
                  "offset": offset, "body": body, "originalBody": body, "hlbl": hlbl, "path": path,
                  "original": original,
                  "typedLocals": re.findall(r"___D_[A-Z0-9]+\(\s*___\w+\s*\)", definitions["___MD_ALL"])}
        metadata = before + after
        metadata = metadata.replace(f"#define ___LBLCOUNT {count}\n", f"#define ___LBLCOUNT {count + offset}\n")
        lb_before, labels, lb_after = section(metadata, "___BEGIN_LBL", "___END_LBL")
        rows = [line.strip().lstrip(",") for line in labels.splitlines() if line.strip()]
        if len(rows) != count or any(not re.match(r"___DEF_LBL_(INTRO|PROC|RET)\(", row) for row in rows):
            raise RuntimeError("structured original label descriptors required")
        padded = dummy_prefix + rows
        metadata = lb_before + "___BEGIN_LBL\n " + "\n,".join(padded) + "\n___END_LBL\n" + lb_after
        destination = output / f"coalesced-module-{index}.c"
        destination.write_text(metadata)
        module["metadata"] = destination
        modules.append(module)
        # Prefix unreachable descriptors so the existing setup routine can walk
        # the common host-label table without a runtime flag or ABI change.
        for row in rows:
            kind = re.match(r"___DEF_LBL_(INTRO|PROC|RET)\(", row).group(1)
            if kind == "INTRO":
                dummy_prefix.append(f"___DEF_LBL_INTRO({COMMON},___REF_FAL,___REF_FAL,1,0)")
            elif kind == "PROC":
                dummy_prefix.append(f"___DEF_LBL_PROC({COMMON},0,-1)")
            else:
                dummy_prefix.append(f"___DEF_LBL_RET({COMMON},___IFD(___RETI,0,0,0x3fL))")
        offset += count
    if offset > 65536:
        raise RuntimeError("coalesced label budget exceeded")
    trace_details = inject_guarded_traces(modules, guarded_trace_polls, guarded_trace_restart_polls,
                                         guarded_trace_coalesce_polls,
                                         guarded_trace_primitive_boundary,
                                         guarded_trace_epoch_cache,
                                         guarded_trace_inline_lookup,
                                         guarded_trace_outline_lookup,
                                         guarded_trace_allocations,
                                         guarded_trace_lookup_return_branches,
                                         supplementary_pure_branches,
                                         supplementary_fresh_branches,
                                         scalar_caller_labels, scalar_boundary_labels,
                                         outline_return_traces=guarded_trace_outline_returns) if guarded_readonly_traces else {}
    trace_helpers = trace_details.pop("nativeTraceHelpers", "")
    parameter_details = inject_parameter_entry(modules) if parameter_entry_fastpath else {}
    bounded_details = inject_bounded_primitives(modules) if bounded_primitive_entries else {}
    if cache_label_bases:
        for module in modules:
            module["cachedLabelBase"] = module["prefix"] + "_entry_lp"
    local_returns = {}
    known_returns = {}
    micro_clones = {}
    if local_subroutine_clones:
        for index, module in enumerate(modules):
            module["body"], details = inject_micro_clones(module["body"], index, defer_local_frames)
            micro_clones[module["path"].stem] = details
    if known_return_guards:
        for module in modules:
            module["body"], details = inject_known_returns(module["body"])
            known_returns[module["path"].stem] = details
    vector_calls = {}
    if vector_entry_guards:
        for module in modules:
            module["body"], details = inject_vector_calls(module["original"], module["body"])
            vector_calls[module["path"].stem] = details
    if local_return_guards:
        for module in modules:
            module["body"], details = inject_local_returns(module["body"])
            local_returns[module["path"].stem] = details
    gen_calls = 0
    if return_label_count or gen_entry_count:
        label_map = {}
        for module in modules:
            procedure = None
            rows = [row.strip() for row in module["hlbl"].splitlines() if row.strip()]
            for index, row in enumerate(rows):
                label = re.fullmatch(r"___DEF_M_HLBL\((___\w+)\)", row)
                if label and label.group(1).startswith("___L0_"):
                    procedure = label.group(1)[6:]
                label_map[index + module["offset"]] = {
                    "module": module["path"].stem, "procedure": procedure,
                    "label": label.group(1) if label else None}
            if return_label_count:
                module["body"] = module["body"].replace("___JUMPRET(___R0)",
                    f"gb_count_return(___R0,___PH_LBL0+{module['offset']},{COMMON});\n   ___JUMPRET(___R0)")
            if gen_entry_count:
                pattern = re.compile(r"___JUMPGEN(?:SAFE|NOTSAFE)\((?:___SET_NARGS\(\d+\)|___NOTHING),(___R[0-4]|___STK\(\d+\))\)")
                def count_gen(match):
                    nonlocal gen_calls
                    gen_calls += 1
                    return f"gb_count_gen({match.group(1)},___PH_LBL0+{module['offset']},{COMMON});\n   " + match.group(0)
                module["body"] = pattern.sub(count_gen, module["body"])
        (output / "return-label-map.json").write_text(json.dumps(label_map, indent=2) + "\n")

    guarded_calls = 0
    leaf_copies = []
    leaf_details = []
    leaves = {module["prefix"]: leaf_candidates(module) for module in modules} if guarded_leaf_clones else {}
    def return_site(module, start):
        preceding = module["body"][:start]
        proc_base = re.findall(r"#define ___PH_LBL0 (\d+)", preceding)
        current_body = preceding.rsplit("___BEGIN_P_SW\n", 1)[-1]
        return_indices = re.findall(r"___SET_R0\(___LBL\((\d+)\)\)", current_body)
        if proc_base and return_indices:
            ret = int(return_indices[-1])
            native = re.search(r"___DEF_SLBL\(" + str(ret) + r",(___\w+)\)",
                               module["body"][preceding.rfind("___BEGIN_P_SW\n"):].split("___END_P_SW", 1)[0])
            if native:
                absolute = int(proc_base[-1]) + ret + module["offset"]
                return f"({module['prefix']}___lp+({absolute}*___LABEL_SIZE*___WS))", module["prefix"] + native[1]
        return None, None
    if guarded_global_jumps:
        providers = {}
        for module in modules:
            for glo, label_index in re.findall(
                    r"___DEF_MOD_GLO\(\d+,(___G_\w+),(\d+)\)", module["original"]):
                providers.setdefault(glo, set()).add((module["prefix"], int(label_index)))
            for glo, label_index in re.findall(
                    r"___SET_GLO\(\d+,(___G_\w+),___PRC\((\d+)\)\)", module["body"]):
                providers.setdefault(glo, set()).add((module["prefix"], int(label_index)))
        by_prefix = {module["prefix"]: module for module in modules}
        pattern = re.compile(r"___JUMPGLO(SAFE|NOTSAFE)\((___SET_NARGS\(\d+\)|___NOTHING),(\d+),(___G_\w+)\)")
        active_module = None
        def replace(match):
            nonlocal guarded_calls
            kind, nargs, index, glo = match.groups()
            candidates = providers.get(glo, set())
            if len(candidates) != 1:
                return match.group(0)
            prefix, label_index = next(iter(candidates))
            target = by_prefix[prefix]
            rows = [row.strip() for row in target["hlbl"].splitlines() if row.strip()]
            label = re.fullmatch(r"___DEF_M_HLBL\((___\w+)\)", rows[label_index])
            if not label:
                raise RuntimeError("global procedure has no native entry label")
            base = target.get("cachedLabelBase", prefix + "___lp")
            expected = f"({base}+(({label_index + target['offset']})*___LABEL_SIZE*___WS))"
            guarded_calls += 1
            destination = prefix + label.group(1)
            candidate = leaves.get(prefix, {}).get(label_index)
            if candidate and nargs == f"___SET_NARGS({candidate['arity']})" and len(leaf_copies) < 256:
                # A return guard is safe even when control flow invalidates the
                # nearest lexical R0 setter; the original return remains.
                expected_return, return_label = return_site(active_module, match.start())
                copied, destination = clone_leaf(target, candidate, f"gb_clone{len(leaf_copies)}", expected_return, return_label)
                leaf_copies.append(copied)
                leaf_details.append({"callerModule": active_module["path"].stem,
                                     "calleeModule": target["path"].stem, "calleeBase": label_index,
                                     "calleeHost": candidate["host"], "returnGuard": expected_return is not None,
                                     "dispatchKind": "global"})
            return f"GB_DIRECT_{kind}({nargs},{index},{glo},{expected},{destination})"
        for module in modules:
            active_module = module
            module["body"] = pattern.sub(replace, module["body"])
    if internal_leaf_clones:
        pattern = re.compile(r"___JUMPINT\((___SET_NARGS\(\d+\)|___NOTHING),___PRC\((\d+)\),(___\w+)\)")
        for module in modules:
            def replace_internal(match):
                nargs, index, label = match.groups()
                candidate = leaves.get(module["prefix"], {}).get(int(index))
                if not candidate or len(leaf_copies) >= 256 or nargs != f"___SET_NARGS({candidate['arity']})":
                    return match.group(0)
                if label not in set(re.findall(r"___DEF_GLBL\((___\w+)\)", candidate["body"])):
                    return match.group(0)
                expected_return, return_label = return_site(module, match.start())
                copied, destination = clone_leaf(module, candidate, f"gb_clone{len(leaf_copies)}",
                                                 expected_return, return_label, label)
                leaf_copies.append(copied)
                leaf_details.append({"callerModule": module["path"].stem, "calleeModule": module["path"].stem,
                                     "calleeBase": int(index), "calleeHost": candidate["host"],
                                     "returnGuard": expected_return is not None, "dispatchKind": "internal"})
                return ("#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
                        f"___GOTO({destination})\n#else\n{match.group(0)}\n#endif")
            module["body"] = pattern.sub(replace_internal, module["body"])

    declarations = "\n".join(f"___DEF_NEW_LNK({module['newLinker']})" for module in modules)
    if link_content.count("___BEGIN_NEW_LNK\n") != 1:
        raise RuntimeError("unique new linker declarations required")
    link_content = link_content.replace("___BEGIN_NEW_LNK\n", "___BEGIN_NEW_LNK\n" + declarations + "\n")
    for module in modules:
        old = f"___DEF_LNK({module['linker']})"
        if module["linker"] in runtime_linkers:
            if old in link_content:
                raise RuntimeError("runtime module must retain its archive preload entry")
            continue
        if link_content.count(old) != 1:
            raise RuntimeError("unique original module preload required")
        link_content = link_content.replace(old, f"___DEF_LNK({module['newLinker']})")

    result = link_content + f"\n___HIDDEN void {COMMON}(___processor_state ___ps);\n"
    if guarded_readonly_traces:
        result += TRACE_PREAMBLE
        if guarded_trace_lookup_return_branches:
            result += TYPE_CHAIN_PREAMBLE
    if guarded_trace_epoch_cache:
        result += EPOCH_PREAMBLE
    if parameter_entry_fastpath:
        result += identity_preamble(coherent_epoch=guarded_trace_epoch_cache, env_lookup=parameter_env_lookup) if parameter_identity_return else PARAMETER_PREAMBLE
    if bounded_primitive_entries:
        result += BOUNDED_PRIMITIVE_PREAMBLE
    if known_return_guards:
        result += "\n#ifndef GB_KNOWN_RETURN_EVENT\n#define GB_KNOWN_RETURN_EVENT() ((void)0)\n#endif\n"
    if guarded_leaf_clones:
        result += "\n#ifndef GB_LEAF_EVENT\n#define GB_LEAF_EVENT() ((void)0)\n#endif\n"
        result += "#define GB_LEAF_RETURN() {___pc=___R0; ___GOTO(gb_leaf_return_dispatch)}\n"
    if vector_entry_guards:
        result += "\n#ifndef GB_VECTOR_EVENT\n#define GB_VECTOR_EVENT(kind) ((void)0)\n#endif\n"
        result += '''
#define GB_VECTOR_VALID_SAFE(value) ___PROCEDUREP(value)
#define GB_VECTOR_VALID_NOTSAFE(value) 1
#ifdef ___NOT_SAFE_CALLS
#undef GB_VECTOR_VALID_SAFE
#define GB_VECTOR_VALID_SAFE(value) 1
#endif
#ifdef ___SAFE_CALLS
#undef GB_VECTOR_VALID_NOTSAFE
#define GB_VECTOR_VALID_NOTSAFE(value) ___PROCEDUREP(value)
#endif
'''
    if guarded_global_jumps:
        result += '''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)
#define GB_DIRECT_NOTSAFE(nargs,i,glo,expected,label) {nargs ___SELF=___GLO(i,glo); if (___SELF==(expected)) {___GOTO(label)} ___JUMP(___LABEL_ENTRY_GET(___SELF))}
#define GB_DIRECT_SAFE(nargs,i,glo,expected,label) {nargs ___SELF=___GLO(i,glo); if (___SELF==(expected)) {___GOTO(label)} if (___EXPECT_TRUE(___PROCEDUREP(___SELF))) {___JUMP(___LABEL_ENTRY_GET(___SELF))} ___ps->temp4=(___WORD)&___GLOSTRUCT(i,glo); ___JUMPEXTPRM(___NOTHING,___ps->handler_not_proc_glo)}
#ifdef ___NOT_SAFE_CALLS
#undef GB_DIRECT_SAFE
#define GB_DIRECT_SAFE(nargs,i,glo,expected,label) GB_DIRECT_NOTSAFE(nargs,i,glo,expected,label)
#endif
#ifdef ___SAFE_CALLS
#undef GB_DIRECT_NOTSAFE
#define GB_DIRECT_NOTSAFE(nargs,i,glo,expected,label) GB_DIRECT_SAFE(nargs,i,glo,expected,label)
#endif
#else
#define GB_DIRECT_NOTSAFE(nargs,i,glo,expected,label) ___JUMPGLONOTSAFE(nargs,i,glo)
#define GB_DIRECT_SAFE(nargs,i,glo,expected,label) ___JUMPGLOSAFE(nargs,i,glo)
#endif
'''
    result += "#ifndef GB_MICRO_EVENT\n#define GB_MICRO_EVENT() ((void)0)\n#endif\n"
    for module in modules:
        result += f"___LOCAL ___WORD {module['prefix']}___lp;\n"
        result += context(module, f'#include {json.dumps(str(module["metadata"]))}')
    result += trace_helpers
    if gen_entry_count:
        header = output / "gambit-gen-entry-count.h"
        header.write_bytes(Path(__file__).with_name(header.name).read_bytes())
        result += f'#include {json.dumps(str(header))}\n'
    if return_label_count:
        header = output / "gambit-return-label-count.h"
        header.write_bytes(Path(__file__).with_name(header.name).read_bytes())
        result += "#include <stdlib.h>\nstatic unsigned gb_return_target(___WORD value) {\n"
        for module in modules:
            base = module["prefix"] + "___lp"
            first, last = module["offset"], module["offset"] + module["counts"]["___LBLCOUNT"]
            result += (f"if ({base} && value >= {base}+({first}*___LABEL_SIZE*___WS) && "
                       f"value < {base}+({last}*___LABEL_SIZE*___WS)) {{\n"
                       f"___WORD delta=value-{base}; if(delta % (___LABEL_SIZE*___WS)) abort(); "
                       "return delta/(___LABEL_SIZE*___WS); }\n")
        result += "return 65535; }\n"
        result += f'#include {json.dumps(str(header))}\n'
    first = modules[0]
    typed_locals = sorted({declaration for module in modules for declaration in module["typedLocals"]})
    declarations = REGS + " " + " ".join(typed_locals)
    root = f'''#undef ___MH_PROC
#define ___MH_PROC {COMMON}
#undef ___MD_ALL
#define ___MD_ALL {declarations}
#undef ___MR_ALL
#define ___MR_ALL {READS}
#undef ___MW_ALL
#define ___MW_ALL {WRITES}
#undef ___MLBL
#define ___MLBL(n) ({first['prefix']}___lp+((n)*___LABEL_SIZE*___WS))
___BEGIN_M_COD
'''
    result += root
    if gen_entry_count:
        result += "if (!gb_gen_labels_ready) {\nstatic const ___WORD gb_gen_entries[]={\n"
        for module in modules:
            for index, row in enumerate(row for row in module["hlbl"].splitlines() if row.strip()):
                label = re.fullmatch(r"\s*___DEF_M_HLBL\((___\w+)\)\s*", row)
                if row.strip() == "___DEF_M_HLBL_INTRO":
                    result += "0,\n"
                    continue
                if not label:
                    raise RuntimeError("structured native labels required for entry diagnostic")
                result += f"(___WORD)&&{module['prefix']}{label.group(1)},\n"
        result += "}; unsigned gb_i; for(gb_i=0;gb_i<sizeof(gb_gen_entries)/sizeof(gb_gen_entries[0]);++gb_i) if(gb_gen_entries[gb_i]) gb_register_gen_label(gb_gen_entries[gb_i],gb_i);\ngb_gen_labels_ready=1; }\n"
    if cache_label_bases:
        result += "\n".join(f"___WORD {module['cachedLabelBase']}={module['prefix']}___lp;" for module in modules) + "\n"
    result += "___BEGIN_M_HLBL\n"
    for module in modules:
        # Only local goto-label names need their module scope in this table.
        for line in module["hlbl"].splitlines():
            match = re.search(r"___DEF_M_HLBL\((___\w+)\)", line)
            result += (line.replace(match.group(1), module["prefix"] + match.group(1)) if match else line) + "\n"
    result += "___END_M_HLBL\n"
    if guarded_trace_epoch_cache:
        result += "GB_TRACE_INVALIDATE_AT(0);\n"
    result += "___BEGIN_M_SW\n"
    for module in modules:
        result += context(module, module["body"], definitions=module["controls"], body=True)
    result += "\n".join(leaf_copies)
    if leaf_copies:
        result += ("\n#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES)\n"
                   "gb_leaf_return_dispatch:\n___JUMPRET(___pc)\n#endif\n")
    result += "___END_M_SW\n___END_M_COD\n"
    return result, {"moduleCount": len(modules), "hostCount": 1, "totalHostLabels": offset,
                    "dummyLabelDescriptors": sum(module["offset"] for module in modules),
                    "typedLocals": typed_locals,
                    "runtimeAbiChanged": False, "originalSchemeRecompiledAsBundle": False,
                    "retainedRuntimeLinkers": sorted(runtime_linkers),
                    "guardedGlobalJumpCallsites": guarded_calls,
                    "returnLabelDiagnostic": return_label_count,
                    "genericEntryDiagnostic": gen_entry_count,
                    "genericEntryCountCallsites": gen_calls,
                    "vectorEntryGuards": vector_calls,
                    "guardedLeafClones": leaf_details,
                    "knownReturnGuards": known_returns,
                    "localSubroutineClones": micro_clones,
                    "localReturnGuards": local_returns,
                    "entryLabelBaseSnapshots": cache_label_bases,
                    **trace_details, **parameter_details, **bounded_details}
