# D1785: actual dynamic parameter entry feasibility

The original D1513 B / D1510 line remains selected and unchanged. This advances
a source/code-generation route, not a performance-admitted patch. No installed
toolchain, consumer Scheme, std/make, std/test, original RTS or original carrier
is modified. The first-log and <=55-second complete-build goals remain open.

## Mechanism and admission boundary

Gambit's header makes DYNAMIC modules use BIND_LATE. Removing the old static
parameter helper's !DYNAMIC guard alone is insufficient: its direct kernel
global structure references are not module-local late-bound references.

The prototype resolves all eight required kernel dependencies through the
generated module's actual glotbl indices. There are no new direct static
imports. Alias definitions and removal are restricted to DYNAMIC builds;
helper activation additionally retains Darwin/genuine GNU/non-Clang, single
host, label values, single VM, single-threaded VM, one processor, original
argument-register count and existing poll-mode restrictions.

Current bindings, primitive identities, parameter closure shape, live thread
cache entries, parameter descriptor getters and dynamic environments are still
read on execution. No parameter values or table lookup results are cached
across invocations. Misses retain the original global jump. The original stack
trip check remains. This tests existing parameter semantics, not a new cache.

The conversion refuses missing kernel dependencies, ambiguous global bindings,
incomplete module boundaries, duplicate injection and absent eligible call
sites. It does not silently add unresolved static symbols. Automatic dependency
registration in Gambit's emitter is not implemented; the isolated fixture
explicitly declares dependencies. This is not a general production compiler
or loader qualification.

## Native and actual execution evidence

D1775 generates C from a private Scheme fixture using the retained GSC.
D1776/D1777 fail because the generated linker name and ordinary load-derived
name disagree. D1778 loads without initializing; D1779 supplies an incorrect
load arity. All failed directories are retained. D1780 uses the source-verified
six-argument load API with explicit linker name module, including normal module
registration/initialization, and passes original/candidate native execution.

The reusable conversion in `tests/gambit_dynamic_parameter_entry.py` has five
passing focused unit tests. D1783 compiles and executes its actual output with
GNU GCC. Both original and candidate produce ten exact CASE-OK records, final
DYNAMIC-PARAMETER-OK 10 and exit zero. Candidate execution also emits one
diagnostic-only hit marker from inside the helper, proving actual participation
rather than merely compilation or a symbol's presence. The marker is absent
from the converter's default output and is not a synthetic progress heartbeat.

Cases cover default reads, a custom getter/filter, setter updates, parameterized
bindings, restoration, nested binding, ordinary/bound GC, continuation escape
and escape restoration. They do not prove special-port behavior, deep-environment
limits, arbitrary rebinding, forced poll paths or full native test-suite parity.

D1781 and D1784 separately execute original/candidate waves with twelve actual
concurrent processes per wave. Each run proves 240 cases, exact final records,
actual exit zero and the unchanged five-second genuine-output gate. All twelve
candidate processes in each run observe the helper hit. These are feasibility
and semantic/concurrency checks, not matched timing speedups or std framework
qualification. No real MCP build speed is inferred from them.

D1783 candidate C SHA256:
`a1fefbc189c97b01d2157cd44709257efb2b67dd84eca14dc4b3a9cf22036f24`.
Candidate dynamic artifact SHA256:
`35ab34922360eeacfcd2d49c6213d357b09497fb505c16d7d388af99a28f3fa6`.
Original artifact SHA256:
`55cee0fc6b44e8368eb5b1d7794697d27e427b0b7d636a304fe756682934298f`.

Next gate: register required dependencies through Gambit's emitter, qualify
actual dynamically loaded macro libraries and their executed coverage, then
measure a complete unchanged MCP cold build from the selected best line plus
only this candidate. Do not promote this small fixture to a major speedup.

Private evidence: `.data/d1775-dynamic-parameter/`,
`.data/d1776-dynamic-parameter-native/` through `.data/d1780-dynamic-parameter-native/`,
`.data/d1781-dynamic-parameter-concurrent/`, `.data/d1783-dynamic-parameter-native/`,
`.data/d1784-dynamic-parameter-concurrent/`. No live process remains.
