"""Prototype guarded, read-only GVM call-chain traces with original fallbacks."""
from dataclasses import dataclass, field
from collections import Counter, deque
import re

from gambit_known_returns import PROC, LABEL
from gambit_trace_epoch_cache import prefix as cached_prefix, fences
from gambit_trace_outlining import outline
from gambit_type_chain import lower as lower_type_chain


GUARD = ("defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && "
         "defined(___SINGLE_HOST) && defined(___USE_LABEL_VALUES) && "
         "defined(___SINGLE_VM) && "
         "defined(___SINGLE_THREADED_VMS) && (___MAX_PROCESSORS == 1) && "
         "(___NB_ARG_REGS == 3)")
READS = {"NOT", "NOTFALSEP", "EQP", "TYPE", "SUBTYPE", "STRUCTUREP",
         "STRUCTURETYPE", "TYPEID", "TYPESUPER", "VECTORREF", "VECTORLENGTH",
         "UNCHECKEDSTRUCTUREREF", "FIX", "FIXEQ", "FIXLT", "FIXLE", "FIXGT",
         "FIXGE", "BOOLEAN", "PAIRP", "CAR", "CDR", "NULP", "VECTORP",
         "MEMALLOCATEDP", "FIXAND"}
ATOMS = {"___TRU", "___FAL", "___NUL", "___VOID", "___UNUSED", "___ABSENT"}
ALLOCATION_READS = {"STRUCTUREDIOP", "TYPECAST", "CLO", "BOXP", "UNBOX", "NULLP", "SYMBOLP", "PROCEDUREP"}


class Refused(Exception):
    pass


def macro(text):
    match = re.fullmatch(r"(___\w+)\((.*)\)", text.strip())
    if not match:
        raise Refused("not a structured macro expression")
    name, inside = match.groups()
    depth, start, args = 0, 0, []
    for index, char in enumerate(inside):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise Refused("unbalanced expression")
        elif char == "," and depth == 0:
            args.append(inside[start:index])
            start = index + 1
    if depth:
        raise Refused("unbalanced expression")
    args.append(inside[start:])
    return name.removeprefix("___"), args


@dataclass(frozen=True)
class Continuation:
    module: int
    position: int


@dataclass
class State:
    registers: dict = field(default_factory=lambda: {n: f"gb_in{n}" for n in range(5)})
    stack: dict = field(default_factory=dict)
    frame: int = 0
    nargs: int | None = None
    code: list = field(default_factory=list)
    visits: dict = field(default_factory=dict)
    calls: int = 0
    conditions: int = 0
    steps: int = 0
    polls: int = 0
    terminal: tuple | None = None
    actual_nargs: str = "gb_in_nargs"
    peak_frame: int = 0
    effects: int = 0
    effect_snapshot: tuple | None = None
    equal_words: dict = field(default_factory=dict)
    heap_words: int = 0
    fresh_pairs: set = field(default_factory=set)
    boolean_values: dict = field(default_factory=dict)
    fresh_closures: dict = field(default_factory=dict)
    initialized_closures: set = field(default_factory=set)
    closure_setup: tuple | None = None
    structure_setup: tuple | None = None
    last_structure: tuple | None = None
    fresh_structures: dict = field(default_factory=dict)
    guard_limit: int = 16
    type_chain_loops: int = 0
    fresh_pair_fields: dict = field(default_factory=dict)
    predicate_facts: dict | None = None
    infeasible: bool = False

    def fork(self):
        return State(dict(self.registers), dict(self.stack), self.frame, self.nargs,
                     list(self.code), dict(self.visits), self.calls,
                     self.conditions, self.steps, self.polls, self.terminal, self.actual_nargs,
                     self.peak_frame, self.effects, self.effect_snapshot, dict(self.equal_words), self.heap_words,
                     set(self.fresh_pairs), dict(self.boolean_values), dict(self.fresh_closures),
                     set(self.initialized_closures), self.closure_setup,
                     self.structure_setup, self.last_structure, dict(self.fresh_structures), self.guard_limit,
                     self.type_chain_loops, dict(self.fresh_pair_fields),
                     None if self.predicate_facts is None else dict(self.predicate_facts), self.infeasible)

    def symbolic(self, expression, active=frozenset()):
        expression = self.resolved_word(expression)
        if expression in active or len(active) >= 24:
            return expression
        declaration = next((line for line in self.code if line.startswith(f'___WORD {expression}=(')), None)
        if declaration and expression not in self.fresh_pairs and expression not in self.fresh_structures and expression not in self.fresh_closures:
            return self.symbolic(declaration.removeprefix(f'___WORD {expression}=(').removesuffix(');'), active | {expression})
        try:
            name, args = macro(expression)
        except Refused:
            return expression
        return '___'+name+'('+','.join(self.symbolic(arg, active) for arg in args)+')'

    def record_predicate(self, expression, truth):
        if self.predicate_facts is None:
            return
        expression = self.symbolic(expression)
        try:
            name, args = macro(expression)
            while name == 'NOT' and len(args) == 1:
                truth = not truth
                expression = args[0]
                name, args = macro(expression)
        except Refused:
            name, args = '', []
        facts = [(expression, truth)]
        if name == 'STRUCTUREDIOP' and len(args) == 2 and truth:
            facts += [('___STRUCTUREP('+args[0]+')', True),
                      ('___EQP(___TYPEID(___STRUCTURETYPE('+args[0]+')),'+args[1]+')', True),
                      ('___PAIRP('+args[0]+')', False)]
        elif name in {'STRUCTUREP', 'PAIRP'} and len(args) == 1 and truth:
            other = 'PAIRP' if name == 'STRUCTUREP' else 'STRUCTUREP'
            facts.append(('___'+other+'('+args[0]+')', False))
        for key, value in facts:
            if key in self.predicate_facts and self.predicate_facts[key] != value:
                self.infeasible = True
            self.predicate_facts[key] = value

    def resolved_word(self, value):
        if not isinstance(value, str):
            return value
        while value in self.equal_words:
            value = self.equal_words[value]
        return value

    def capture(self, expression):
        if isinstance(expression, Continuation):
            return expression
        if re.fullmatch(r"gb_(?:in[0-4]|t\d+)", expression):
            return expression
        name = f"gb_t{len(self.code)}"
        self.code.append(f"___WORD {name}=({expression});")
        if expression in {"___TRU", "___FAL"}:
            self.boolean_values[name] = expression
        return name

    def require(self, expression, truth=True):
        self.record_predicate(expression, truth)
        if self.infeasible:
            return
        self.conditions += 1
        if self.conditions > self.guard_limit:
            raise Refused("guard budget")
        miss = "GB_TRACE_EFFECT_MISS" if self.effects else "GB_TRACE_MISS"
        self.code.append(f"if ({'!' if truth else ''}({expression})) goto {miss};")
        if truth:
            equality = re.fullmatch(r"(gb_t\d+)==(.*)", expression)
            if equality:
                left, right = equality.groups()
            else:
                try:
                    name, args = macro(expression)
                except Refused:
                    return
                if name not in {"EQP", "FIXEQ"} or len(args) != 2:
                    return
                left, right = args
                if not re.fullmatch(r"gb_t\d+", left):
                    left, right = right, left
            if not re.fullmatch(r"gb_t\d+", left):
                return
            left, right = self.resolved_word(left), self.resolved_word(right)
            if left != right and re.fullmatch(r"gb_t\d+", left) and (
                    re.fullmatch(r"gb_(?:in[0-4]|t\d+)", right) or right in ATOMS or
                    re.fullmatch(r"___FIX\(-?\d+L?\)", right) or
                    re.fullmatch(r"\(\w+___lp\+\(\d+\*___LABEL_SIZE\*___WS\)\)", right)):
                self.equal_words[left] = right


class Program:
    def __init__(self, modules, allow_polls=False, restart_polls=False, coalesce_polls=False,
                 primitive_boundary=False, inline_lookup=False, transactional_allocations=False,
                 lookup_return_branches=False, pure_branches=False, fresh_branches=False,
                 fresh_caller_regions=False, fresh_caller_boundaries=False):
        if fresh_caller_boundaries and not fresh_caller_regions:
            raise Refused('fresh boundary audit requires isolated caller mode')
        if fresh_caller_regions and not fresh_branches:
            raise Refused('fresh caller analysis requires isolated fresh mode')
        if fresh_branches:
            if (pure_branches or transactional_allocations or inline_lookup
                    or lookup_return_branches or primitive_boundary or restart_polls):
                raise Refused('fresh branch mode requires an isolated bounded region')
            pure_branches = transactional_allocations = True
        if pure_branches and not fresh_branches and (transactional_allocations or inline_lookup or lookup_return_branches):
            raise Refused('pure branch candidates exclude allocation and effectful lookup modes')
        self.modules = modules
        self.allow_polls = allow_polls
        self.restart_polls = restart_polls
        self.coalesce_polls = coalesce_polls
        self.primitive_boundary = primitive_boundary
        self.inline_lookup = inline_lookup
        self.transactional_allocations = transactional_allocations
        self.lookup_return_branches = lookup_return_branches
        self.pure_branches = pure_branches
        self.fresh_branches = fresh_branches
        self.fresh_caller_regions = fresh_caller_regions
        self.fresh_caller_boundaries = fresh_caller_boundaries
        self.preserved_points = set()
        self.refusals = Counter()
        self.lines, self.labels, self.scopes = {}, {}, {}
        self.entries, self.providers, self.dynamic = {}, {}, {}
        self.procedures = {}
        self.known_procedures = set()
        for mi, module in enumerate(modules):
            body = module["originalBody"]
            lines = self.lines[mi] = body.splitlines()
            labels = self.labels[mi] = {}
            for index, line in enumerate(lines):
                match = LABEL.fullmatch(line.strip())
                if match:
                    labels[match[1]] = index + 1
            if self.fresh_caller_regions:
                metadata = module['original'].split('___BEGIN_LBL\n', 1)[1].split('___END_LBL', 1)[0]
                rows = [row.strip().lstrip(',') for row in metadata.splitlines() if row.strip()]
                self.known_procedures.update(self.descriptor(mi, absolute)
                    for absolute, row in enumerate(rows)
                    if re.fullmatch(r'___DEF_LBL_PROC\(___\w+,\d+,-?\d+\)', row))
            for match in PROC.finditer(body):
                base, fragment = int(match[1]), match[2]
                first = body[:match.start(2)].count("\n")
                end = first + len(fragment.splitlines())
                by_index = {int(n): labels[label] for n, label in re.findall(
                    r"___DEF_SLBL\((\d+),(___\w+)\)", fragment)}
                for index in range(first, end):
                    self.scopes[mi, index] = (base, by_index)
                for relative, position in by_index.items():
                    self.entries[mi, base + relative] = position
                if 0 in by_index:
                    self.procedures[mi, base] = fragment
            init = re.search(r"#define ___PH_LBL0 (\d+).*?___BEGIN_P_SW\n(.*?)___END_P_SW", body, re.S)
            if init:
                base, code = int(init[1]), init[2]
                indices = {int(n) for n in re.findall(r"___SET_R[1-4]\(___LBL\((\d+)\)\)", code)}
                indices.update(int(n) for n in re.findall(r"___LBL\((\d+)\)", code))
                indices.update(int(n) for n in re.findall(
                    r"___BEGIN_SETUP_CLO\(\d+,(?:___R[0-4]|___STK\(-?\d+\)),(\d+)\)", code))
                indices.update(int(n) - base for n in re.findall(r"___PRC\((\d+)\)", code))
                metadata = module["original"].split("___BEGIN_LBL\n", 1)[1].split("___END_LBL", 1)[0]
                rows = [row.strip().lstrip(",") for row in metadata.splitlines() if row.strip()]
                for relative in sorted(indices):
                    absolute = base + relative
                    if absolute >= len(rows) or (mi, absolute) not in self.entries:
                        continue
                    descriptor = re.fullmatch(r"___DEF_LBL_PROC\(___\w+,(\d+),-?\d+\)", rows[absolute])
                    if descriptor:
                        self.dynamic.setdefault((mi, int(descriptor[1])), []).append(absolute)
            for global_name, absolute in re.findall(r"___DEF_MOD_GLO\(\d+,(___G_\w+),(\d+)\)", module["original"]):
                self.providers.setdefault(global_name, set()).add((mi, int(absolute)))
            for global_name, absolute in re.findall(r"___SET_GLO\(\d+,(___G_\w+),___PRC\((\d+)\)\)", body):
                self.providers.setdefault(global_name, set()).add((mi, int(absolute)))
        self.external = {}
        if primitive_boundary:
            for (mi, absolute), fragment in self.procedures.items():
                if "___GCHASHTABLEREF(" not in fragment:
                    continue
                metadata = self.modules[mi]["original"].split("___BEGIN_LBL\n", 1)[1].split("___END_LBL", 1)[0]
                rows = [row.strip().lstrip(",") for row in metadata.splitlines() if row.strip()]
                descriptor = re.fullmatch(r"___DEF_LBL_PROC\(___\w+,(\d+),-?\d+\)", rows[absolute])
                if descriptor and int(descriptor[1]) <= 3:
                    self.external.setdefault(int(descriptor[1]), []).append((mi, absolute))

    def descriptor(self, mi, absolute):
        module = self.modules[mi]
        return f"({module['prefix']}___lp+({absolute + module['offset']}*___LABEL_SIZE*___WS))"

    def expression(self, text, mi, position, state):
        text = text.strip()
        register = re.fullmatch(r"___R([0-4])", text)
        if register:
            return state.registers[int(register[1])]
        if text in ATOMS or re.fullmatch(r"-?\d+L?", text):
            return text
        module = self.modules[mi]
        if text in module["controls"]:
            if not text.startswith(("___SYM_", "___KEY_", "___GLO_")):
                raise Refused("unknown generated constant")
            return self.expression(module["controls"][text], mi, position, state)
        name, args = macro(text)
        if name == "STK":
            key = state.frame + int(args[0])
            if key not in state.stack:
                state.stack[key] = state.capture(f"___STK({key})")
            return state.stack[key]
        if name == "LBL":
            _, by_index = self.scopes[mi, position]
            return Continuation(mi, by_index[int(args[0])])
        if name == "PRC":
            return self.descriptor(mi, int(args[0]))
        if name in {"SYM", "KEY", "SUB"}:
            table = {"SYM": "symtbl", "KEY": "keytbl", "SUB": "subtbl"}[name]
            return f"___CAST_FAKEWORD_TO_WORD({module['prefix']}___{table}[{int(args[0])}])"
        if name == "CNS" and (self.transactional_allocations or self.pure_branches):
            if len(args) != 1 or not re.fullmatch(r"\d+", args[0].strip()):
                raise Refused("nonconstant static pair reference")
            return (f"___PAIR_FROM_START(___ALIGNUP({module['prefix']}___cnstbl,___WS)"
                    f"+{int(args[0])}*(___PAIR_BODY+___PAIR_SIZE))")
        if name == "GLO":
            if len(args) != 2 or not re.fullmatch(r"___G_\w+", args[1]):
                raise Refused("global shape")
            return f"GB_TRACE_GLO({module['prefix']}___glotbl,{int(args[0])},{args[1]})"
        if name in {"CONS", "XCONS"} and self.transactional_allocations:
            if (len(args) != 2 or state.effects or state.structure_setup is not None or state.heap_words + 3 > 64
                    or any(re.search(r"___(?:X?CONS)\(", arg) for arg in args)):
                raise Refused("unbounded, nested or externally effectful allocation")
            values = [self.expression(arg, mi, position, state) for arg in args]
            if any(isinstance(value, Continuation) for value in values):
                raise Refused("continuation observed as allocation data")
            state.heap_words += 3
            result = state.capture("___" + name + "(" + ",".join(values) + ")")
            state.fresh_pairs.add(result)
            if self.fresh_caller_regions:
                state.fresh_pair_fields[result] = tuple(values if name == "CONS" else reversed(values))
            state.last_structure = None
            return result
        if name == "ALLOC_CLO" and self.transactional_allocations:
            if len(args) != 1 or not re.fullmatch(r"\d+(?:UL)?", args[0]):
                raise Refused("nonconstant fresh closure size")
            size = int(args[0].removesuffix("UL"))
            if state.effects or state.structure_setup is not None or size > 16 or state.heap_words + size + 2 > 64:
                raise Refused("unbounded or externally effectful closure allocation")
            result = state.capture(f"___ALLOC_CLO({size}UL)")
            state.heap_words += size + 2
            state.fresh_closures[result] = size
            state.last_structure = None
            return result
        if name == "GET_STRUCTURE" and self.transactional_allocations:
            if (len(args) != 1 or state.structure_setup is not None or state.last_structure is None
                    or not args[0].isdigit() or int(args[0]) != state.last_structure[0]):
                raise Refused("structure result does not name the completed current allocation")
            return state.last_structure[1]
        if name not in READS and not (self.fresh_branches and name == 'CAAR') and not ((self.transactional_allocations or self.pure_branches)
                                     and name in ALLOCATION_READS):
            raise Refused("effectful or unsupported expression")
        values = [self.expression(arg, mi, position, state) for arg in args]
        if self.fresh_caller_regions:
            normalized = []
            for value in values:
                if isinstance(value, str):
                    declaration = next((line for line in state.code if line.startswith(f"___WORD {value}=(")), None)
                    if declaration:
                        atom = declaration.removeprefix(f"___WORD {value}=(").removesuffix(");")
                        if atom in {"___NUL", "___TRU", "___FAL", "0", "1"}:
                            value = atom
                normalized.append(value)
            values = normalized
            if name == 'UNCHECKEDSTRUCTUREREF' and len(values) == 4 and values[2:] == ['___FAL', '___FAL']:
                fields = state.fresh_structures.get(values[0]) if isinstance(values[0], str) else None
                index = re.fullmatch(r'___FIX\((\d+)L?\)', values[1]) if isinstance(values[1], str) else None
                if fields and index and int(index[1]) < len(fields):
                    return fields[int(index[1])]
            if name == 'STRUCTUREDIOP' and len(values) == 2 and all(isinstance(value, str) for value in values) and values[0] in state.fresh_structures:
                return '___EQP(___TYPEID('+state.fresh_structures[values[0]][0]+'),'+values[1]+')'
            if len(values) == 1:
                fields = state.fresh_pair_fields.get(values[0]) if isinstance(values[0], str) else None
                if fields and name in {"CAR", "CDR"}:
                    return fields[name == "CDR"]
                if name == "NULLP" and values[0] == "___NUL":
                    return "1"
                if name == "PAIRP" and values[0] in {"___NUL", "___TRU", "___FAL"}:
                    return "0"
                if name == "NOT" and values[0] in {"0", "1"}:
                    return str(1 - int(values[0]))
        if any(isinstance(value, Continuation) for value in values):
            if self.transactional_allocations and name == "PROCEDUREP" and len(values) == 1:
                values = [self.value(values[0])]
            else:
                raise Refused("continuation observed as data")
        if self.fresh_caller_regions and name == 'PROCEDUREP' and len(values) == 1:
            if values[0] in self.known_procedures:
                return '1'
        if self.transactional_allocations:
            if len(values) == 1 and values[0] in state.fresh_pairs:
                if name == "PAIRP":
                    return "1"
                if name in {"NULLP", "STRUCTUREP", "SYMBOLP", "BOXP", "PROCEDUREP"}:
                    return "0"
            if len(values) == 1 and values[0] in state.fresh_closures:
                if name == "PROCEDUREP":
                    return "1"
                if name in {"NULLP", "STRUCTUREP", "SYMBOLP", "BOXP", "PAIRP"}:
                    return "0"
            if len(values) == 1 and values[0] in state.fresh_structures:
                if name == "STRUCTUREP":
                    return "1"
                if name in {"NULLP", "SYMBOLP", "BOXP", "PAIRP", "PROCEDUREP"}:
                    return "0"
                if name == "STRUCTURETYPE":
                    return state.fresh_structures[values[0]][0]
            if name == "CLO" and values[0] in state.fresh_closures and values[0] not in state.initialized_closures:
                raise Refused("read of incomplete fresh closure")
            if name == "STRUCTUREDIOP" and len(values) == 2 and values[0] in state.fresh_pairs:
                return "0"
            if name == "NOT" and values in (["0"], ["1"]):
                return "1" if values == ["0"] else "0"
            if name == "BOOLEAN" and values in (["0"], ["1"]):
                return "___TRU" if values == ["1"] else "___FAL"
            if name == "NOTFALSEP" and len(values) == 1:
                known = state.boolean_values.get(values[0], values[0])
                if known in {"___TRU", "___FAL"}:
                    return "1" if known == "___TRU" else "0"
        return "___" + name + "(" + ",".join(values) + ")"

    def dispatcher(self, mi, absolute):
        position = self.entries.get((mi, absolute))
        if position is None:
            return False
        tail = self.lines[mi][position:position + 10]
        return any("___JUMPGEN" in line for line in tail) and not any(
            "___POLL(" in line or "___ADJFP(" in line for line in tail)

    def reaches_dispatcher(self, mi, absolute, depth=2):
        if self.dispatcher(mi, absolute):
            return True
        if not self.allow_polls or depth == 0:
            return False
        fragment = self.procedures.get((mi, absolute), "")
        for global_name in re.findall(r"___JUMPGLO(?:SAFE|NOTSAFE)\(___SET_NARGS\(\d+\),\d+,(___G_\w+)\)", fragment):
            targets = self.providers.get(global_name, set())
            if len(targets) == 1 and self.reaches_dispatcher(*next(iter(targets)), depth - 1):
                return True
        return False

    def value(self, value):
        if isinstance(value, Continuation):
            indices = [absolute for (owner, absolute), position in self.entries.items()
                       if owner == value.module and position == value.position]
            if len(indices) != 1:
                raise Refused("ambiguous continuation descriptor")
            return self.descriptor(value.module, indices[0])
        return value

    def materialize(self, state, live_only=False, result_only=False):
        if result_only and (not self.fresh_branches or state.effects or state.effect_snapshot
                or state.frame > 0 or state.structure_setup or state.closure_setup
                or state.initialized_closures != set(state.fresh_closures)
                or state.terminal and state.terminal[0] != 'GB_INPUT_STACK_RETURN'):
            raise Refused('single-result materialization requires a complete fresh return')
        code = ""
        for key, value in sorted(state.stack.items()):
            if not live_only or key <= state.frame:
                code += f"___SET_STK({key},{self.value(state.resolved_word(value))})\n"
        for register in range(2 if result_only else 5):
            code += f"___SET_R{register}({self.value(state.resolved_word(state.registers[register]))})\n"
        code += f"___SET_NARGS({state.actual_nargs})\n"
        return code + f"___ADJFP({state.frame})\n"

    def roots(self, mi):
        for position in sorted(set(self.labels[mi].values())):
            tail = self.lines[mi][position:position + 20]
            if any("___IF_NARGS_EQ" in line for line in tail[:2]):
                continue
            for line in tail:
                if LABEL.fullmatch(line.strip()) or "___POLL(" in line:
                    break
                match = re.fullmatch(r"\s*___JUMPGLO(?:SAFE|NOTSAFE)\(___SET_NARGS\(\d+\),\d+,(___G_\w+)\)", line)
                if match:
                    targets = self.providers.get(match[1], set())
                    if len(targets) == 1 and (self.transactional_allocations or self.pure_branches
                                             or self.reaches_dispatcher(*next(iter(targets)))):
                        yield position
                    break
                if self.pure_branches and re.fullmatch(
                        r'\s*___JUMPINT\(___SET_NARGS\(\d+\),___PRC\(\d+\),___\w+\)', line):
                    yield position
                    break

    def traces(self, mi, position, initial_state=None, max_paths=64):
        if type(max_paths) is not int or not 1 <= max_paths <= 1024:
            raise ValueError('trace path limit must be an integer from 1 to 1024')
        results = []
        root_module = mi
        root_point = mi, position
        step_budget = 512 if self.fresh_caller_regions else 256 if self.lookup_return_branches else 192 if self.inline_lookup else 128
        work = 0
        pending = deque()
        def boundary(mi, position, state):
            complete = (state.structure_setup is None and state.closure_setup is None
                        and state.initialized_closures == set(state.fresh_closures))
            if (self.pure_branches and state.calls and state.code and not state.effects
                    and (not self.fresh_caller_boundaries or complete)
                    and (not state.heap_words or self.fresh_caller_boundaries and complete)):
                state.terminal = ('GB_ORIGINAL_EFFECT', 0, (mi, position))
                results.append(state)
        def walk(mi, position, state):
            if self.fresh_caller_regions:
                pending.append((mi, position, state))
            else:
                step(mi, position, state)

        def step(mi, position, state):
            nonlocal work
            if state.infeasible:
                self.refusals[('caller-region', 'infeasible predicate conjunction')] += 1
                return
            # Re-entry exports the exact next-iteration GVM state, not a lookup result.
            if self.lookup_return_branches and state.effects and (mi, position) == root_point:
                state.terminal = ('GB_ORIGINAL_REENTRY', 0, root_point)
                results.append(state)
                return
            if len(results) >= max_paths or state.steps >= step_budget or abs(state.frame) > 128:
                if self.fresh_caller_regions:
                    self.refusals[('caller-region', 'path, statement or frame budget')] += 1
                return
            key = mi, position
            if self.fresh_caller_regions:
                key = (mi, position, state.registers[0],
                       tuple((slot, value) for slot, value in sorted(state.stack.items())
                             if isinstance(value, Continuation)))
            state.visits[key] = state.visits.get(key, 0) + 1
            if state.visits[key] > 2:
                if self.fresh_caller_regions:
                    self.refusals[(self.lines[mi][position].strip(), 'caller continuation-scoped visit budget')] += 1
                return
            while position < len(self.lines[mi]):
                if self.pure_branches and state.calls and (mi, position) in self.preserved_points:
                    boundary(mi, position, state)
                    return
                state.steps += 1
                work += 1
                if self.fresh_caller_regions and work > 20000:
                    self.refusals[('caller-region', 'total analysis work budget')] += 1
                    return
                if state.steps > step_budget:
                    return
                line = self.lines[mi][position].strip()
                if not line:
                    position += 1
                    continue
                if LABEL.fullmatch(line):
                    walk(mi, position + 1, state)
                    return
                if self.lookup_return_branches and state.effects:
                    lowered = lower_type_chain(self, mi, position, state)
                    if lowered is not None:
                        position = lowered
                        continue
                before = state.fork() if self.pure_branches else None
                try:
                    name, args = macro(line)
                    if name == "IF_NARGS_EQ":
                        if state.nargs != int(args[0]):
                            return
                    elif name == "WRONG_NARGS":
                        pass
                    elif name.startswith("SET_R") and name[-1:] in "01234":
                        if self.primitive_boundary and args[0].startswith("___GCHASHTABLEREF(") and state.calls >= 2:
                            if not self.inline_lookup:
                                state.terminal = ("GB_ORIGINAL_EFFECT", 0, (mi, position))
                                results.append(state)
                                return
                            if state.effects:
                                return
                            _, lookup_args = macro(args[0])
                            values = [self.expression(arg, mi, position, state) for arg in lookup_args]
                            if len(values) != 2 or any(isinstance(value, Continuation) for value in values):
                                return
                            value = state.capture("___GCHASHTABLEREF(" + ",".join(values) + ")")
                            state.registers[int(name[-1])] = value
                            state.effect_snapshot = (mi, position + 1, state.fork())
                            state.effects = 1
                            position += 1
                            continue
                        value = self.expression(args[0], mi, position, state)
                        state.registers[int(name[-1])] = value if value in state.registers.values() else state.capture(value)
                    elif name == "SET_STK":
                        state.stack[state.frame + int(args[0])] = self.expression(args[1], mi, position, state)
                    elif name == "ADJFP":
                        state.frame += int(args[0])
                    elif name == "BEGIN_ALLOC_STRUCTURE" and self.transactional_allocations:
                        if (len(args) != 1 or not re.fullmatch(r"\d+(?:UL)?", args[0])
                                or state.structure_setup is not None or state.closure_setup is not None):
                            raise Refused("nested or malformed structure allocation")
                        size = int(args[0].removesuffix("UL"))
                        if not 1 <= size <= 16 or state.heap_words + size + 1 > 64:
                            raise Refused("unbounded structure allocation")
                        state.heap_words += size + 1
                        state.last_structure = None
                        state.structure_setup = (size, ())
                        state.code.append(f"___BEGIN_ALLOC_STRUCTURE({size}UL);")
                    elif name == "ADD_STRUCTURE_ELEM" and self.transactional_allocations:
                        if len(args) != 2 or state.structure_setup is None:
                            raise Refused("field write outside fresh structure allocation")
                        size, fields = state.structure_setup
                        index = int(args[0])
                        if index < 0 or index >= size or index in dict(fields):
                            raise Refused("invalid or duplicate fresh structure field")
                        value = self.value(self.expression(args[1], mi, position, state))
                        state.code.append(f"___ADD_STRUCTURE_ELEM({index},{value})")
                        state.structure_setup = (size, fields + ((index, value),))
                    elif name == "END_ALLOC_STRUCTURE" and self.transactional_allocations:
                        if len(args) != 1 or state.structure_setup is None:
                            raise Refused("structure completion without owner")
                        size, fields = state.structure_setup
                        if int(args[0]) != size or set(dict(fields)) != set(range(size)):
                            raise Refused("incomplete fresh structure fields")
                        state.code.append(f"___END_ALLOC_STRUCTURE({size})")
                        result = state.capture(f"___GET_STRUCTURE({size})")
                        state.fresh_structures[result] = tuple(dict(fields)[i] for i in range(size))
                        state.last_structure = (size, result)
                        state.structure_setup = None
                    elif name == "BEGIN_SETUP_CLO" and self.transactional_allocations:
                        if len(args) != 3 or state.closure_setup is not None:
                            raise Refused("nested or malformed closure setup")
                        size = int(args[0])
                        owner = self.expression(args[1], mi, position, state)
                        if (state.fresh_closures.get(owner) != size
                                or owner in state.initialized_closures):
                            raise Refused("setup does not own a fresh closure")
                        _, by_index = self.scopes[mi, position]
                        label = self.value(Continuation(mi, by_index[int(args[2])]))
                        state.code.append(f"___BODY0_AS({owner},___tSUBTYPED)[___LABEL_ENTRY_OR_DESCR]={label};")
                        state.closure_setup = (owner, size, frozenset())
                    elif name == "ADD_CLO_ELEM" and self.transactional_allocations:
                        if len(args) != 2 or state.closure_setup is None:
                            raise Refused("field write outside fresh closure setup")
                        owner, size, fields = state.closure_setup
                        index = int(args[0])
                        if index < 0 or index >= size or index in fields:
                            raise Refused("invalid or duplicate fresh closure field")
                        value = self.value(self.expression(args[1], mi, position, state))
                        state.code.append(f"___BODY0_AS({owner},___tSUBTYPED)[{index}+___CLO_FREEVARS]={value};")
                        state.closure_setup = (owner, size, fields | {index})
                    elif name == "END_SETUP_CLO" and self.transactional_allocations:
                        if len(args) != 1 or state.closure_setup is None:
                            raise Refused("closure setup completion without owner")
                        owner, size, fields = state.closure_setup
                        if int(args[0]) != size or fields != frozenset(range(size)):
                            raise Refused("incomplete fresh closure fields")
                        state.initialized_closures.add(owner)
                        state.closure_setup = None
                    elif name == "CHECK_HEAP" and self.transactional_allocations:
                        # Entry reserves the complete bounded region; no GC is allowed.
                        if len(args) != 2 or any(not re.fullmatch(r"\d+", arg.strip()) for arg in args):
                            return
                    elif name == "POLL" and self.allow_polls:
                        if state.structure_setup is not None:
                            raise Refused("poll during incomplete structure allocation")
                        state.polls += 1
                        state.peak_frame = max(state.peak_frame, state.frame)
                        if state.polls > (16 if self.fresh_caller_regions else 7 if self.lookup_return_branches else 4):
                            return
                        base, by_index = self.scopes[mi, position]
                        relative = int(args[0])
                        if relative not in by_index:
                            return
                        if self.coalesce_polls:
                            position += 1
                            continue
                        if self.restart_polls:
                            state.code.append("GB_TRACE_POLL_EVENT();\n"
                                f"if (___EXPECT_FALSE((___fp-({state.frame})) < ___ps->stack_trip)) goto GB_TRACE_MISS;")
                            position += 1
                            continue
                        checkpoint = self.materialize(state)
                        resume = self.descriptor(mi, base + relative)
                        state.code.append(
                            "GB_TRACE_POLL_EVENT();\n"
                            f"if (___EXPECT_FALSE((___fp-({state.frame})) < ___ps->stack_trip)) {{\n"
                            + checkpoint + f"___ps->temp1={resume};\n"
                            "___JUMPEXTPRM(___NOTHING,___ps->handler_stack_limit)\n}")
                    elif name == "IF":
                        condition = self.expression(args[0], mi, position, state)
                        jump_name, jump_args = macro(self.lines[mi][position + 1].strip())
                        if jump_name != "GOTO" or self.lines[mi][position + 2].strip() != "___END_IF":
                            return
                        if self.labels[mi][jump_args[0]] == position + 4:
                            position += 3
                            continue
                        if self.transactional_allocations and condition in {"0", "1"}:
                            walk(mi, self.labels[mi][jump_args[0]] if condition == "1" else position + 3, state)
                            return
                        yes, no = state.fork(), state.fork()
                        yes.require(condition)
                        no.require(condition, False)
                        walk(mi, position + 3, no)
                        walk(mi, self.labels[mi][jump_args[0]], yes)
                        return
                    elif name == "IF_GOTO" and self.fresh_caller_regions:
                        condition = self.expression(args[0], mi, position, state)
                        if condition in {"0", "1"}:
                            walk(mi, self.labels[mi][args[1]] if condition == "1" else position + 1, state)
                        else:
                            yes, no = state.fork(), state.fork()
                            yes.require(condition)
                            no.require(condition, False)
                            walk(mi, position + 1, no)
                            walk(mi, self.labels[mi][args[1]], yes)
                        return
                    elif name == "GOTO":
                        walk(mi, self.labels[mi][args[0]], state)
                        return
                    elif name == "JUMPRET":
                        target = self.expression(args[0], mi, position, state)
                        if isinstance(target, Continuation):
                            if state.effects and target.module == root_module:
                                if self.lookup_return_branches:
                                    walk(target.module, target.position, state)
                                    return
                                point = target.position
                                # Fold only restoration reads and negative frame adjustment.
                                for _ in range(8):
                                    try:
                                        restore, values = macro(self.lines[target.module][point].strip())
                                        if restore.startswith("SET_R") and restore[-1:] in "01234":
                                            state.registers[int(restore[-1])] = state.capture(self.expression(values[0], target.module, point, state))
                                        elif restore == "ADJFP" and int(values[0]) < 0:
                                            state.frame += int(values[0])
                                        else:
                                            break
                                    except (Refused, KeyError, ValueError, IndexError):
                                        break
                                    point += 1
                                state.terminal = ("GB_ORIGINAL_RETURN", 0, (target.module, point))
                                results.append(state)
                            else:
                                walk(target.module, target.position, state)
                        elif self.lookup_return_branches and state.effects and not isinstance(target, Continuation):
                            state.terminal = ('GB_ORIGINAL_RET_TO', 0, target)
                            results.append(state)
                        elif target == 'gb_in0' and self.pure_branches and state.calls and (
                                state.frame == 0 or self.fresh_branches and state.frame < 0):
                            if (state.structure_setup is None and state.closure_setup is None
                                    and state.initialized_closures == set(state.fresh_closures)):
                                results.append(state)
                        elif (self.fresh_caller_regions and state.calls and state.frame <= 0
                              and isinstance(target, str)
                              and any(re.fullmatch(r'___WORD '+re.escape(target)+r'=\(___STK\(-?\d+\)\);',
                                                   line) for line in state.code)
                              and state.structure_setup is None and state.closure_setup is None
                              and state.initialized_closures == set(state.fresh_closures)):
                            state.terminal = ('GB_INPUT_STACK_RETURN', 0, target)
                            results.append(state)
                        elif target == "gb_in0" and state.calls >= 2 and (
                                state.registers[1] in {"gb_in1", "gb_in2", "gb_in3"}
                                or (self.transactional_allocations and state.heap_words and state.frame == 0)):
                            # Only identity-result paths are selected in this first prototype.
                            results.append(state)
                        elif self.fresh_caller_regions:
                            self.refusals[(line, 'unsupported caller return operand or frame')] += 1
                        return
                    elif name in {"JUMPGLOSAFE", "JUMPGLONOTSAFE", "JUMPGENSAFE", "JUMPGENNOTSAFE", "JUMPINT"}:
                        nargs_name, nargs = macro(args[0])
                        if (nargs_name != "SET_NARGS" or not 0 <= int(nargs[0]) <= (16 if self.transactional_allocations else 3)
                                or state.structure_setup is not None
                                or state.calls >= (16 if self.fresh_caller_regions else 8 if self.primitive_boundary else 6)):
                            if self.fresh_caller_regions:
                                self.refusals[(line, 'caller call, arity or partial allocation budget')] += 1
                            return
                        terminal = None
                        if self.allow_polls and name.startswith("JUMPGEN") and state.calls >= 3:
                            terminal = state.fork()
                            value = terminal.capture(self.expression(args[1], mi, position, terminal))
                            terminal.terminal = (name, int(nargs[0]), value)
                            terminal.nargs = int(nargs[0])
                            terminal.actual_nargs = nargs[0]
                        state.nargs = int(nargs[0])
                        if name != "JUMPINT":
                            state.actual_nargs = nargs[0]
                        state.calls += 1
                        if name.startswith("JUMPGLO"):
                            targets = self.providers.get(args[2], set())
                            if len(targets) != 1:
                                if self.fresh_caller_regions:
                                    self.refusals[(line, 'unresolved global provider')] += 1
                                if self.fresh_caller_boundaries and before is not None:
                                    boundary(mi, position, before)
                                return
                            target_mi, absolute = next(iter(targets))
                            value = state.capture(self.expression(f"___GLO({args[1]},{args[2]})", mi, position, state))
                            state.require(f"{value}=={self.descriptor(target_mi, absolute)}")
                            state.registers[4] = value
                            walk(target_mi, self.entries[target_mi, absolute], state)
                        elif name == "JUMPINT":
                            walk(mi, self.labels[mi][args[2]], state)
                        else:
                            known = self.expression(args[1], mi, position, state) if self.fresh_caller_regions else None
                            if isinstance(known, Continuation):
                                state.registers[4] = self.value(known)
                                walk(known.module, known.position, state)
                                return
                            external = self.external.get(state.nargs, [])
                            candidates = external + [(mi, absolute) for absolute in self.dynamic.get((mi, state.nargs), [])]
                            candidates = list(dict.fromkeys(candidates))
                            if len(candidates) > 8 and external:
                                candidates = external[:8]
                            if not candidates or len(candidates) > 8:
                                if self.fresh_caller_regions:
                                    self.refusals[(line, 'unresolved generic provider set')] += 1
                                if self.fresh_caller_boundaries and before is not None:
                                    boundary(mi, position, before)
                                if terminal:
                                    results.append(terminal)
                                return
                            value = state.capture(self.expression(args[1], mi, position, state))
                            state.require(f"___PROCEDUREP({value})")
                            entry = state.capture(f"___LABEL_ENTRY_GET({value})")
                            for target_mi, absolute in candidates:
                                branch = state.fork()
                                branch.require(f"{entry}=={self.descriptor(target_mi, absolute)}")
                                branch.registers[4] = value
                                walk(target_mi, self.entries[target_mi, absolute], branch)
                            if terminal and len(results) < max_paths:
                                results.append(terminal)
                        return
                    else:
                        if self.fresh_caller_regions:
                            self.refusals[(line, 'unsupported caller instruction')] += 1
                        if before is not None:
                            boundary(mi, position, before)
                        return
                except (Refused, KeyError, ValueError, IndexError) as error:
                    if self.transactional_allocations or self.pure_branches:
                        self.refusals[(line, str(error))] += 1
                    if before is not None:
                        boundary(mi, position, before)
                    return
                position += 1
        if initial_state is not None and not isinstance(initial_state, State):
            raise TypeError('trace initial state must be a State')
        initial = initial_state.fork() if initial_state is not None else State(
            guard_limit=32 if self.fresh_caller_regions else 24 if self.lookup_return_branches else 16,
            predicate_facts={} if self.fresh_caller_regions else None)
        walk(mi, position, initial)
        while pending and len(results) < max_paths and work <= 20000:
            step(*pending.popleft())
        return results


def inject(modules, allow_polls=False, restart_polls=False, coalesce_polls=False,
           primitive_boundary=False, epoch_cache=False, inline_lookup=False, outline_lookup=False,
           transactional_allocations=False, lookup_return_branches=False,
           supplementary_pure_branches=False, supplementary_fresh_branches=False,
           scalar_caller_labels=(), scalar_boundary_labels=(), outline_return_traces=False):
    if outline_return_traces and (not outline_lookup or not lookup_return_branches):
        raise Refused('return outlining requires outlined lookup and precise return branches')
    if scalar_boundary_labels and scalar_caller_labels:
        raise Refused('return and boundary scalarization are separate experiments')
    if scalar_boundary_labels and (supplementary_pure_branches or supplementary_fresh_branches or transactional_allocations or epoch_cache):
        raise Refused('boundary scalarization requires the unchanged uncached readonly carrier')
    if scalar_caller_labels and (supplementary_pure_branches or supplementary_fresh_branches or transactional_allocations or epoch_cache):
        raise Refused('caller scalarization is a separate uncached readonly experiment')
    if supplementary_fresh_branches and supplementary_pure_branches:
        raise Refused('supplementary fresh and pure modes are separate experiments')
    if (supplementary_pure_branches or supplementary_fresh_branches) and (transactional_allocations or epoch_cache):
        raise Refused('supplementary pure trees exclude allocation and result-cache experiments')
    if lookup_return_branches and not inline_lookup:
        raise Refused('lookup return branches require precise lookup fallback')
    if transactional_allocations and (not restart_polls or epoch_cache or inline_lookup
                                      or primitive_boundary or outline_lookup or coalesce_polls):
        raise Refused("transactional allocations require individual restart polls and no external effects")
    if epoch_cache and not coalesce_polls:
        raise Refused("epoch cache requires coalesced boundary polls")
    if inline_lookup and (epoch_cache or not coalesce_polls or not primitive_boundary):
        raise Refused("inline lookup requires uncached coalesced primitive traces")
    if outline_lookup and not inline_lookup:
        raise Refused("outlining requires precise inline lookup fallback")
    program = Program(modules, allow_polls, restart_polls, coalesce_polls, primitive_boundary, inline_lookup,
                      transactional_allocations, lookup_return_branches)
    selections = []
    edits_by_module = {mi: [] for mi in range(len(modules))}
    resumes = set()
    helpers = []
    for mi, module in enumerate(modules):
        edits = edits_by_module[mi]
        for position in program.roots(mi):
            traces = program.traces(mi, position)
            if not traces or len(selections) >= 256:
                continue
            if transactional_allocations:
                traces = [state for state in traces if state.heap_words and not state.effects
                          and state.closure_setup is None
                          and state.structure_setup is None
                          and state.initialized_closures == set(state.fresh_closures)]
                if not traces:
                    continue
            # Keep one bounded success path; all other values use original code.
            checkpoints = [trace for trace in traces if trace.terminal and trace.polls >= 2
                           and not isinstance(trace.registers[0], Continuation)]
            boundaries = [trace for trace in traces if trace.terminal and trace.terminal[0] == "GB_ORIGINAL_EFFECT"]
            state = (boundaries[0] if boundaries else min(checkpoints, key=lambda trace: trace.calls) if checkpoints else
                     next((trace for trace in traces if not trace.terminal), traces[0]))
            if inline_lookup:
                completed = [trace for trace in traces if trace.effects and trace.terminal
                             and trace.terminal[0] in {"GB_ORIGINAL_RETURN", "GB_ORIGINAL_REENTRY", "GB_ORIGINAL_RET_TO"}]
                if not completed:
                    continue
                reentries = [trace for trace in completed if trace.terminal[0] == 'GB_ORIGINAL_REENTRY']
                state = max(reentries, key=lambda trace: trace.type_chain_loops) if reentries else completed[0]
            site = len(selections)
            miss = f"gb_trace_miss_{site}"
            effect_miss = f"gb_trace_effect_miss_{site}"
            guard = GUARD
            if transactional_allocations:
                guard += " && (___WS == 8) && (___PAIR_SIZE == 2) && (___PAIR_BODY == 1) && !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT)"
                guard += " && (___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0) && (___CLO_FREEVARS == 1) && (___SUBTYPED_BODY == 1)"
            if epoch_cache or inline_lookup:
                guard += " && !defined(___DYNAMIC)"
            if state.polls:
                guard += " && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)"
            emitted = "\n#if " + guard + "\n{\n"
            emitted += f"GB_TRACE_ENTRY({site});\n"
            allocation_miss = f"gb_trace_allocation_miss_{site}"
            if transactional_allocations:
                emitted += "___WORD *gb_heap_checkpoint=___hp;\n"
                emitted += f"if (___EXPECT_FALSE(___hp+{state.heap_words}>___ps->heap_limit)) goto {miss};\n"
            boundary_check = ("GB_TRACE_POLL_EVENT();\n"
                              f"if (___EXPECT_FALSE((___fp-({state.peak_frame})) < ___ps->stack_trip)) goto {miss};\n")
            if coalesce_polls and state.polls:
                emitted += boundary_check
            emitted += "".join(f"___WORD gb_in{n}=___R{n};\n" for n in range(5))
            emitted += "int gb_in_nargs=___ps->na;\n"
            materialized = program.materialize(state, live_only=True)
            terminal_value = state.terminal[2] if state.terminal else ""
            cache = cached_prefix(state, materialized + str(terminal_value), miss, site) if epoch_cache else None
            outlined = outline_lookup and (outline_return_traces or not lookup_return_branches or
                                           state.terminal[0] == 'GB_ORIGINAL_REENTRY')
            if outlined:
                helper, caller = outline(program, state, site, guard)
                helpers.append(helper)
                emitted += caller.replace("GB_TRACE_MISS", miss).replace("GB_TRACE_EFFECT_MISS", effect_miss)
            else:
                trace_code = "\n".join(state.code)
                guard_misses = []
                if transactional_allocations:
                    def count_guard(match):
                        index = len(guard_misses)
                        if index >= 64:
                            raise Refused("allocation guard diagnostic budget")
                        guard_misses.append(match[1])
                        return f"if ({match[1]}) {{ GB_TRACE_GUARD_MISS({site},{index}); goto GB_TRACE_MISS; }}"
                    trace_code = re.sub(r"^if \((.*)\) goto GB_TRACE_MISS;$", count_guard, trace_code, flags=re.MULTILINE)
                emitted += cache if cache else trace_code.replace(
                    "GB_TRACE_MISS", allocation_miss if transactional_allocations else miss).replace(
                    "GB_TRACE_EFFECT_MISS", effect_miss) + "\n"
            if coalesce_polls and state.polls:
                emitted += boundary_check.replace(miss, effect_miss) if state.effects else boundary_check
            emitted += materialized
            emitted += f"GB_TRACE_HIT({site});\n"
            if state.terminal:
                name, nargs, value = state.terminal
                if name in {"GB_ORIGINAL_EFFECT", "GB_ORIGINAL_RETURN", "GB_ORIGINAL_REENTRY"}:
                    owner, point = value
                    resumes.add((owner, point))
                    if name == 'GB_ORIGINAL_REENTRY':
                        emitted += f'GB_TRACE_REENTRY_EVENT({site});\n'
                    emitted += f"goto gb_trace_resume_{owner}_{point};\n"
                elif name == 'GB_ORIGINAL_RET_TO':
                    emitted += f'___JUMPRET({program.value(value)})\n'
                else:
                    emitted += f"___{name}(___SET_NARGS({nargs}),{program.value(value)})\n"
            else:
                emitted += "___JUMPRET(gb_in0)\n"
            if state.effect_snapshot:
                owner, point, snapshot = state.effect_snapshot
                resumes.add((owner, point))
                emitted += f"{effect_miss}:;\n" + program.materialize(snapshot, live_only=True)
                emitted += f"goto gb_trace_resume_{owner}_{point};\n"
            if transactional_allocations:
                emitted += f"{allocation_miss}:;\n___hp=gb_heap_checkpoint;\n"
            emitted += f"}}\n{miss}:;\n#endif\n"
            edits.append((position, emitted))
            selections.append({"module": module["path"].stem, "line": position + 1,
                               "callsRemoved": state.calls, "conditions": state.conditions,
                               "frameDelta": state.frame, "steps": state.steps,
                               "result": state.registers[1], "polls": state.polls,
                               "peakFrame": state.peak_frame, "coalescedPolls": coalesce_polls,
                               "epochCachedPrefix": cache is not None,
                               "inlinedLookups": state.effects,
                               "outlinedLookup": outlined,
                               "lookupReturnBranches": lookup_return_branches,
                               "loweredTypeChainLoops": state.type_chain_loops,
                               "transactionalHeapWords": state.heap_words,
                               "transactionalFreshClosures": len(state.fresh_closures),
                               "transactionalFreshStructures": len(state.fresh_structures),
                               "transactionalFreshPairs": len(state.fresh_pairs),
                               "allocationGuardMisses": guard_misses if transactional_allocations else [],
                               "terminal": state.terminal[0] if state.terminal else "return"})
    pure_selections = []
    if supplementary_pure_branches or supplementary_fresh_branches:
        from gambit_trace_tree import emit as emit_tree
        pure = Program(modules, allow_polls=True, coalesce_polls=True,
                       pure_branches=not supplementary_fresh_branches,
                       fresh_branches=supplementary_fresh_branches)
        pure.preserved_points = {(mi, position) for mi, edits in edits_by_module.items()
                                 for position, _ in edits}
        for mi, module in enumerate(modules):
            for position in pure.roots(mi):
                if (mi, position) in pure.preserved_points or (mi, position) in resumes:
                    continue
                states = pure.traces(mi, position)
                if not 2 <= len(states) <= 32 or len(pure_selections) >= 256:
                    continue
                heap_words = max(state.heap_words for state in states)
                if supplementary_fresh_branches and not heap_words:
                    continue
                site = len(pure_selections)
                miss = f'gb_pure_tree_miss_{site}'
                pending_resumes = set()
                peak = max(state.peak_frame for state in states)
                poll_check = (f'if (___EXPECT_FALSE((___fp-({peak})) < ___ps->stack_trip)) '
                              'goto GB_TRACE_MISS;\n') if any(state.polls for state in states) else ''
                def leaf(state):
                    if state.heap_words and state.terminal:
                        raise Refused('fresh tree requires completed allocation and return')
                    # A boundary can precede ADJFP: pending stack stores remain live.
                    code = poll_check+pure.materialize(state, live_only=state.terminal is None)
                    code += f'GB_PURE_TREE_HIT({site});\n'
                    if supplementary_fresh_branches and state.heap_words:
                        code += f'GB_FRESH_TREE_COMMIT({site},{state.heap_words});\n'
                    if state.terminal:
                        if state.terminal[0] != 'GB_ORIGINAL_EFFECT':
                            raise Refused('unsupported pure tree terminal')
                        owner, point = state.terminal[2]
                        pending_resumes.add((owner, point))
                        code += f'goto gb_trace_resume_{owner}_{point};\n'
                    else:
                        code += '___JUMPRET(gb_in0)\n'
                    return code
                try:
                    code, details = emit_tree(states, leaf, allow_fresh=supplementary_fresh_branches)
                except Refused:
                    continue
                guard = GUARD
                if supplementary_fresh_branches:
                    guard += ' && (___WS == 8) && (___PAIR_SIZE == 2) && (___PAIR_BODY == 1) && !defined(___USE_HANDLES) && !defined(___DEBUG_HEAP_LIMIT)'
                    guard += ' && (___CLO_LOWLEVEL_TRAMPOLINE_SIZE == 0) && (___CLO_FREEVARS == 1) && (___SUBTYPED_BODY == 1)'
                if any(state.polls for state in states):
                    guard += ' && !defined(___HEARTBEAT_USING_POLL_COUNTDOWN) && !defined(___DEBUG_STACK_LIMIT)'
                prelude = ''.join(f'___WORD gb_in{n}=___R{n};\n' for n in range(5))
                prelude += 'int gb_in_nargs=___ps->na;\n'
                rollback = ''
                tree_miss = miss
                if supplementary_fresh_branches:
                    prelude = ('___WORD *gb_heap_checkpoint=___hp;\n'
                               +f'if (___EXPECT_FALSE(___hp+{heap_words}>___ps->heap_limit)) goto {miss};\n'
                               +prelude)
                    tree_miss = f'gb_fresh_tree_rollback_{site}'
                    rollback = (f'\n{tree_miss}:;\n'
                                +f'GB_FRESH_TREE_ROLLBACK({site},___hp-gb_heap_checkpoint);\n'
                                +'___hp=gb_heap_checkpoint;\n')
                emitted = (f'\n#if {guard}\n{{\nGB_PURE_TREE_ENTRY({site});\n'
                           +poll_check.replace('GB_TRACE_MISS', miss)+prelude
                           +code.replace('GB_TRACE_MISS', tree_miss)+rollback
                           +f'\n}}\n{miss}:;\n#endif\n')
                edits_by_module[mi].append((position, emitted))
                resumes.update(pending_resumes)
                pure_selections.append(dict(module=module['path'].stem, line=position+1,
                                            maximumFrame=peak, **details,
                                            freshAllocationTree=supplementary_fresh_branches,
                                            maximumHeapWords=heap_words,
                                            allocatedReturnPaths=sum(state.heap_words > 0 and state.terminal is None
                                                                     for state in states)))
    for mi, position in resumes:
        edits_by_module[mi].append((position, f"\n#if {GUARD}\ngb_trace_resume_{mi}_{position}:;\n#endif\n"))
    barriers = fences(program, READS) if epoch_cache else []
    if len(barriers) > 65534:
        raise Refused("mutation diagnostic site budget")
    for site, (mi, position) in enumerate(barriers, 2):
        fence = "GB_TRACE_FRESH_ALLOCATION_AT" if (mi, position) in program.fresh_epoch_fences else "GB_TRACE_INVALIDATE_AT"
        edits_by_module[mi].append((position, f"{fence}({site});\n"))
    scalar_details = {}
    if scalar_caller_labels:
        from gambit_scalar_caller import inject as inject_scalar
        scalar_details = inject_scalar(modules, labels=scalar_caller_labels, apply=False,
            excluded={(mi, position) for mi, edits in edits_by_module.items() for position, _ in edits} | resumes)
        for mi, edits in scalar_details.pop('nativeScalarEdits').items():
            edits_by_module[mi].extend(edits)
    boundary_details = {}
    if scalar_boundary_labels:
        from gambit_scalar_boundary import inject as inject_boundary
        boundary_details = inject_boundary(modules, labels=scalar_boundary_labels, apply=False,
            excluded={(mi, position) for mi, edits in edits_by_module.items() for position, _ in edits} | resumes)
        for mi, edits in boundary_details.pop('nativeScalarEdits').items():
            edits_by_module[mi].extend(edits)
    for mi, module in enumerate(modules):
        lines = module["body"].splitlines(keepends=True)
        if module["body"] != module["originalBody"]:
            raise Refused("trace prototype requires unmodified original body")
        for position, emitted in sorted(edits_by_module[mi], reverse=True):
            lines.insert(position, emitted)
        module["body"] = "".join(lines)
    return {"guardedReadOnlyTraces": selections,
            "scalarCallerTrees": scalar_details.get('supplementaryPureTrees', []),
            "scalarCallerRefusals": scalar_details.get('scalarizationRefusals', []),
            "scalarBoundaryTrees": boundary_details.get('supplementaryPureTrees', []),
            "scalarBoundaryResumes": boundary_details.get('scalarBoundaryResumes', 0),
            "supplementaryPureTrees": pure_selections,
            "transactionalTraceRefusals": [{"instruction": line, "reason": reason, "staticPaths": count}
                                            for (line, reason), count in program.refusals.most_common(30)],
            "nativeTraceHelpers": "".join(helpers),
            "epochMutationFences": len(barriers),
            "epochFreshAllocationFences": len(program.fresh_epoch_fences) if epoch_cache else 0,
            "epochFenceSites": [{"site": site, "module": modules[mi]["path"].stem,
                                 "line": position + 1, "instruction": program.lines[mi][position].strip(),
                                 "freshAllocation": (mi, position) in program.fresh_epoch_fences}
                                for site, (mi, position) in enumerate(barriers, 2)],
            "selection": ("static-transactional-fresh-allocation-call-chains-no-profile-data-no-result-cache"
                          if transactional_allocations else
                          "static-readonly-identity-call-chains-no-profile-data-no-result-cache")}


PREAMBLE = """
#ifndef GB_PURE_TREE_ENTRY
#define GB_PURE_TREE_ENTRY(site) ((void)0)
#endif
#ifndef GB_PURE_TREE_HIT
#define GB_PURE_TREE_HIT(site) ((void)0)
#endif
#ifndef GB_SCALAR_ELIDED_WORDS
#define GB_SCALAR_ELIDED_WORDS(words) ((void)0)
#endif
#ifndef GB_FRESH_TREE_ROLLBACK
#define GB_FRESH_TREE_ROLLBACK(site,words) ((void)0)
#endif
#ifndef GB_FRESH_TREE_COMMIT
#define GB_FRESH_TREE_COMMIT(site,words) ((void)0)
#endif
#ifdef ___BIND_LATE
#define GB_TRACE_GLO(table,index,glo) ___GLOCELL((*___CAST(___glo_struct*,table[index])).val)
#else
#define GB_TRACE_GLO(table,index,glo) ___GLOCELL(glo.val)
#endif
#ifndef GB_TRACE_HIT
#define GB_TRACE_HIT(site) ((void)0)
#endif
#ifndef GB_TRACE_ENTRY
#define GB_TRACE_ENTRY(site) ((void)0)
#endif
#ifndef GB_TRACE_GUARD_MISS
#define GB_TRACE_GUARD_MISS(site,guard) ((void)0)
#endif
#ifndef GB_TRACE_EFFECT_EVENT
#define GB_TRACE_EFFECT_EVENT(site) ((void)0)
#endif
#ifndef GB_TRACE_REENTRY_EVENT
#define GB_TRACE_REENTRY_EVENT(site) ((void)0)
#endif
#ifndef GB_TRACE_POLL_EVENT
#define GB_TRACE_POLL_EVENT() ((void)0)
#endif
"""
