# D936-D965 Gambit Execution Cost And Link Integration

## Identity And Admission

The authoritative `git.cons.io` v0.19-staging head was checked again on
2026-10-03 and remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
Gambit remains `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
The GitHub mirror returns an older July commit, not a newer staging head.
No checkout or installation was switched to that mirror commit.

All experiments use real GNU GCC 16 and isolated project `.data` output.
std/make, GXPkg and MCP source semantics and consumer flags are unchanged.
Full D935 functional qualification and its approximately 19.3% complete
preparation CPU reduction are retained separately. Startup admission still
fails; nothing here is delivered as a successful startup fix.

## Bounded Follow-Ups

Each ABBA sample imports the same 187 MCP modules and exits successfully.
External host load is not controlled, so wall time is not admitted.

| Candidate relative to complete D935 | Original CPU seconds | Candidate CPU seconds | Decision |
| --- | --- | --- | --- |
| D936 one shallow descriptor prefix | 6.264, 6.628 | 6.121, 6.160 | About 4.7% mean reduction; not promoted as startup fix |
| D937 four shallow prefixes | 6.447, 6.023 | 6.166, 5.946 | Overlapping ranges; no additional stable gain |
| D938 module-local binding table | 6.469, 6.607 | 6.574, 6.314 | Overlapping ranges; rejected |
| D939 external-call branch layout | 6.468, 6.192 | 6.216, 6.209 | Overlapping ranges; rejected |

D936 and D937 each pass source balance/syntax and the original-reference
6609-assertion contract in twelve concurrent candidate VMs. These remain
partial runtime experiments, not new complete compiler source integrations.
Evidence: the corresponding `.data/d936-*` through `.data/d939-*` reports.

Official D935 MCP clean again leaves zero native project images. A bounded
sample of the unchanged first-compile window completes; actual first compile
is 38.113 seconds and the strict output gate fails. Valid native leaf locations
include the expander core host entry and its common external-exit stores.
Object and final executable disassembly agree at the sampled exit offset.
Some reconstructed stack paths contain unknown addresses; they are not used
for complete CPU attribution. Evidence: `.data/d935-residual-first-window/`.

Dropping apparently dead register stores is not admitted: `mem.c` scans the
entire processor register array and the kernel interrupt handler pushes all
GVM registers. Stale unrefreshed heap pointers cannot be assumed safe.

## Gambit Linker Integration

The source `targ-link` separately computes resource unions and module preload
entries before calling `targ-link-aux`. Existing bundle experiments alter the
native object list; ordinary consumers would not automatically link their new
objects. A Gambit-only implementation needs a carrier in its existing link C.

D940 proves a tiny native carrier with the original a.o, b.o and main.o object
list. The generated link C embeds a separately namespaced module body, retains
old symbol/global resource definitions and replaces only actual preload
entries. Original initialization order and module aliases survive. An original
link reference and twelve concurrent candidates pass cross-module rebinding,
non-procedure exceptions and 200 explicit GCs per process.
Evidence: `.data/d940-embedded-link-contract-concurrent/report.json`.

D941 additionally merges the original generated C host bodies, without
recompiling their Scheme as a bundle. Per-module private data, constants,
procedure bases, bindings and original branches remain distinct. Unreachable
prefix label descriptors let the existing setup routine initialize a common
host-label table, with no runtime flag, representation or ABI change.

The first prototype exposes a zero-map descriptor bug during setup; native
debugging locates its null out-of-line descriptor read. A nonzero inline map
fixes it. The next contract catches a procedure-base error in the second
module; preserving its own PRC base fixes that. Original reference and all
twelve candidates then pass the same rebinding/exception/GC/alias contract.
Evidence: `.data/d941-original-host-coalescing-contract-procedure-base-fixed/`.
These failed prototypes are retained; neither failure is a performance sample.

## D942 Real Runtime Gate

The next isolated profile retains the original eleven measured hot objects and
their hashes, and constructs one merged host in the existing link unit. It has
11818 host labels, 62716 unreachable prefix descriptors and about 19.6 MiB of
generated link input, below the explicit 24-MiB diagnostic ceiling.

The first GNU compile catches the table host's missing unboxed floating locals.
The generator now parses continued preprocessor definitions and carries the
two original F64 declarations into the shared host. No floating algorithm is
changed. That compile succeeds, but its import smoke stalls. Investigation
finds a return-label conversion error: the original host's implicit first
label must be included in each module's LBL base. The failed process group is
stopped and its report/sample retained, not admitted as a performance sample.

The corrected contract now explicitly triggers GC inside a coalesced module,
in addition to the original 200 external GCs, rebinding and alias checks.
The original native reference and twelve concurrent candidate processes pass.
Evidence: `.data/d941-original-host-coalescing-contract-return-label-fixed/`.

A fresh GNU build with that return-label correction passes real
std/make/std/test/std/build-script imports. All eleven original module objects
are reused and GSC is unchanged. This is a qualified partial-runtime profile,
not a complete toolchain or a startup performance result.
Evidence: `.data/d942-original-host-coalescing-profile-return-label-fixed/`.

The same 187 preparation imports pass sequential ABBA. Total child CPU is
5.359 and 5.321 seconds for D935 versus 4.996 and 5.160 for the merged host:
about 4.9% mean reduction, insufficient for the startup objective.
Evidence: `.data/d942-original-host-coalescing-cpu/report.json`.

The partial runtime passes 49 runtime/import/make/test runs at hardware-derived
12-process concurrency. The make contract covers cold, no-op and incremental
builds and three std/test cases. Peak GNU frontends observed is eleven, not
twelve; full hardware frontend concurrency is not claimed.
Evidence: `.data/d942-concurrent-make-test/report.json`.

With the same verified D935 runtime HOME, official MCP clean passes with zero
native project images, and the candidate's real first compile is 10.402 seconds.
The strict ten-second output gate still fails. This stops after first compile,
does not complete the build and is explicitly a partial-runtime measurement.
Evidence: `.data/d942-mcp-first-compile-shared-home/report.json`.

The copied candidate HOME separately times out during official clean. Its
native sample is dominated by dyld's dynamic-image mapping/fcntl path, rather
than an admitted Scheme execution attribution. The same binary with verified
D935 HOME exits clean successfully. This copy/loader effect is kept separate
from CPU evidence, and does not qualify a complete candidate toolchain.
Evidence: `.data/d942-own-home-clean-sample/`,
`.data/d942-clean-stall-sample/`, `.data/d942-mcp-first-compile/`.

Automatic
Darwin-only Gambit source integration, full rebuilt toolchain and whole MCP
build/test qualification remain required. This prototype is not production
compiler code and is not startup delivery.
The earlier failed profile is retained separately at
`.data/d942-original-host-coalescing-profile-typed-locals-fixed/`.

## D943 Kernel Admission

The earlier destination counts identify frequent kernel host exits not covered
by D942's eleven-module group. An isolated carrier now retains the original
kernel linker name and the runtime archive's original preload entry, embedding
its original generated body in the common host without an ABI change.
Native compilation uses the kernel's existing HAVE_CONFIG_H and internal
header directories; consumer optimization flags are unchanged.

The original reference and twelve concurrent candidates pass the small native
GC/rebinding/exception/alias contract. Missing-header and configuration failures
are retained as build failures, not performance samples.
Evidence: `.data/d943-kernel-host-coalescing-contract-native-config/`.

The stronger continuation/wind/multiple-value/Scheme-thread contract passes:
each of twelve concurrent processes also runs twelve Scheme threads.
The real kernel/eleven-module host profile compiles and passes standard imports.
Sequential 187-module ABBA total CPU is 5.746 and 5.343 seconds for D935 versus
5.182 and 5.156 for the kernel group, about 6.8% mean reduction. This is not
admitted as a large or qualified startup improvement.
Evidence: `.data/d943-kernel-control-flow-contract/`,
`.data/d943-kernel-original-host-coalescing-profile/`,
`.data/d943-kernel-host-coalescing-cpu/`.

## D944 Residual Kernel Labels

A post-D935 kernel-entry counter resolves original GVM label IDs, distinguishing
procedure entries from returns. The same 187-module preparation records
12611506 host entries, including 6266273 returns in kernel handlers, 4157993
procedure entries in apply, and 573754 dynamic-env-bind entries. These are
execution counts, not CPU attribution or a performance benchmark.

The largest handler is label 35, the rest-parameter constructor: 6256162 entries.
A shape histogram shows 5644756 (90.2%) fit the three argument-register geometry.
That is a geometric upper bound, before optional/key guards and heap-space
fallback, not a claim that an implementation already accelerates 90.2%.
Evidence: `.data/d944-post-loop-kernel-label-observation/kernel-label-summary.json`,
`.data/d944-rest-shape-counts/`.

## D945 Short Rest Probe

A Darwin/GNU-only C prototype constructs pure short rest lists directly in
registers, with no stack arguments and only when enough heap space is available.
All other shapes retain the original handler. It passes the original reference
and twelve concurrent native processes for arities 0-12, wrong arity, fresh list
identity/order, GC and control flow. A real eleven-module profile covers 262
generated GET_REST sites and passes standard imports.

ABBA total CPU is 5.327 and 5.471 seconds for D935 versus 5.039 and 5.429 for
the probe: overlapping ranges, about 3.0% mean reduction, not admitted as a
reliable startup fix. Production emitter liveness integration is not performed.
Evidence: `.data/d945-rest-register-contract/`, `.data/d945-rest-register-profile/`,
`.data/d945-rest-register-cpu/`.

## D946 Native Structure Jump

Inspection of D935 generated C shows type-chain predicate IR creates GVM
continuation frames even on short chains. A C jump-inliner probe disables that
IR expansion and performs a bounded four-descriptor nonallocating walk instead.
The caller's original block checks remain; deeper/cyclic chains jump to the
original interruptible kernel primitive. No mutable type cache is introduced.

MCP balance/syntax checks pass before compilation. The original reference and
twelve concurrent VMs pass the 6609-assertion native contract; seven native
primitive jump sites are exercised. The initial missing macro compile failure
is retained separately. The real hot-module build passes imports with 174
native jump sites. ABBA CPU is 5.359 and 5.308 seconds for D935 versus 5.367
and 5.527 for the candidate, about 2.1% slower. This is rejected as an
optimization, not source-toolchain delivery.
Evidence: `.data/d946-native-structure-jump/`,
`.data/d946-native-structure-jump-contract-header-fixed/`,
`.data/d946-native-structure-jump-profile/`, `.data/d946-native-structure-jump-cpu/`.

## D947-D948 Current Residual Evidence

D947 retains exact D935 generated C and adds matching native debug symbols.
Official clean leaves zero native project images; the sampled first-compile
window still takes 10.684 seconds and fails the output gate. Resolved leaves
include context resolution, hash/interface dispatch and host entries. The
sample has incomplete reconstructed paths and is not complete CPU attribution.
It stops after first compile, not a completed MCP build.
Evidence: `.data/d947-residual-native-leaves/official-first-window/`.

D948 reruns the existing host-exit diagnostic against the post-D935 runtime,
not the older primitive implementation. The same 187-module preparation passes.
All 415858485 recorded exits resolve, compared with the earlier 527837000-scale
record. Kernel destinations shrink to 6688096; the major remaining routes are
hash/table (33002588), interface/mop in both directions (31866928 each),
hash/interface in both directions (31866835 each), and core/hash (31864703).
Counts are not CPU percentages. They justify investigating native dispatch
across the current SDK host group, not another kernel flag experiment.
Evidence: `.data/d948-post-loop-host-exit-observation/host-summary.json`.

## D949 Guarded Known-Target Dispatch

A diagnostic link formatter recognizes original module-global procedure labels
and literal SET_GLO/PRC initializers. At a known global call it compares the
current binding with that exact procedure before taking a direct native goto.
Rebound procedures use the original indirect path; safe non-procedure errors
retain their original global-variable handler. Original argument checks, heap
and register state, procedure metadata and GC maps are retained. The fast path
is restricted to Darwin GNU single-host label-value builds.

The small reference and twelve concurrent candidates pass rebinding, exceptions,
GC, continuation/wind/multiple-value and Scheme-thread checks, covering four
guarded callsites. A real eleven-module profile identifies 2775 callsites and
passes imports. Sequential ABBA total CPU is 5.393 and 5.276 seconds for D935
versus 4.659 and 4.745 for the guarded group: about 11.9% mean reduction with
nonoverlapping ranges in this bounded run. This is a partial runtime comparison,
not a full-toolchain qualification or an isolated comparison against D942.

Official clean again leaves zero native project images. The candidate's real
first compile is 8.382 seconds, still within the unresolved 7-8 second startup
range. Passing the ten-second diagnostic output gate does not meet the requested
startup objective, nor does this run complete the MCP build. The 49 concurrent
runtime/import/make/test checks pass; observed GNU frontend peak is twelve.
No production Gambit source integration or consumer change is made.
Evidence: `.data/d949-guarded-global-jump-contract/`,
`.data/d949-guarded-global-jump-profile/`, `.data/d949-guarded-global-jump-cpu/`,
`.data/d949-mcp-first-compile/`, `.data/d949-concurrent-make-test/`.

## D950 Return Targets In Progress

The next diagnostic counts actual R0 return targets by procedure, resolving them
against each module's original label metadata. A shared C host still has separate
heap label tables: subtracting the first module's table base is invalid. The
initial import check catches this counter-mapping bug and rejects the profile.
The corrected diagnostic checks each module's actual label-table interval;
a separate missing standard-library declaration is caught at compilation and
fixed. Both failures are retained and are not performance observations.
The checked-bases build passes standard imports and the actual 187-module
preparation. Its R0-only scope records 238412489 returns, 233421132 inside the
group. The context-resolve procedure makes 25949541 R0 returns to one local
label. This is not every return: stack-slot returns are not instrumented.
These counts motivate a bounded static local-continuation rule, not a
MCP-specific profile embedded in the compiler.
Evidence: `.data/d950-return-label-profile/`,
`.data/d950-return-label-profile-private-bases/`,
`.data/d950-return-label-profile-checked-bases/`,
`.data/d950-return-label-observation/return-summary.json`.

## D951 Static Local Continuations In Progress

The next generated-C prototype collects the procedure's literal SET_R0/LBL
targets. With at most four distinct local continuations, an R0 return checks
those exact labels and takes a direct native goto; all other R0 values retain
the original return. There is no recorded-profile input, consumer-specific
symbol choice, mutable cache, new ABI, or change outside Darwin/GNU single-host
label-value builds.

The first small fixture has zero rewritten sites and is not coverage of the
new rule. A stronger fixture includes real type-chain IR, hit/miss and
non-structure results with GC between checks. It has three rewritten return
sites and passes the native reference and twelve concurrent candidates, with
the existing rebinding, exception and control-flow assertions retained.
The real runtime compiles and passes imports with 316 rewritten return sites.
ABBA now uses D949 as the baseline binary and the same D935 HOME, isolating the
new rule: total CPU is 4.826 and 4.585 seconds for D949 versus 4.531 and 4.571
for D951, about 3.3% additional mean reduction in this bounded run. The small
gap between ranges is not a claim of a large or universally stable gain.

Official clean leaves zero native project images and real first compile is
7.965 seconds. The startup objective remains unmet. All 49 concurrent
runtime/import/make/test checks pass at twelve-process capacity; the actual
GNU frontend peak is eleven, so full hardware frontend concurrency is not
claimed for this run. No whole MCP build/test or production source qualification
is claimed by these partial-runtime checks.
Evidence: `.data/d951-local-return-contract/`,
`.data/d951-local-return-contract-type-loop/`, `.data/d951-local-return-profile/`,
`.data/d951-local-return-cpu/`, `.data/d951-mcp-first-compile/`,
`.data/d951-concurrent-make-test/`.

## D952 Native Jump Regression Diagnosis In Progress

D946's four-descriptor native walk did not beat D935. Instead of increasing
the bound speculatively, a diagnostic counts total native entries, non-structure
inputs, true/false completions, and deep-chain fallback to the original
primitive. It uses the same checked compiler hook and original module selection;
there is no timing admission for the instrumented executable. Compilation and
actual MCP preparation pass. Across 115153945 native checks, all complete within
the four-descriptor bound: 87550789 true, 27603156 false, zero deep fallback.
Non-structure inputs account for 25168524 checks. Increasing the bound is thus
rejected as an explanation or remedy for D946 on this exact workload.
Generated stx C still saves R0/object, installs a return label, adjusts an
eight-word frame and invokes the jump probe before testing its boolean result.
The precise contribution of those operations is not individually timed.
Evidence: `.data/d952-native-structure-fallback-profile/`,
`.data/d952-native-structure-fallback-observation/jump-summary.json`.

## D953 Expression Probe In Progress

A checked private compiler hook introduces an IR-only primitive object with an
expression inliner. Its bounded nonallocating probe returns true, false or
ABSENT; ABSENT uses the original D935 interruptible IR, while runtime rebinding
uses the original call. The normal expression path does not require the
primitive jump's argument-register shuffle or result continuation. No runtime
Scheme binding, mutable cache, consumer change or new native ABI is added.

Native MCP source balance/syntax checks pass before compilation. Original
reference and twelve concurrent VMs each pass the 6609-assertion structure
contract, including deep chains, mutable descriptors and cyclic interrupt/GC
behavior. Generated C contains the actual expression helper at seven sites.
The real eleven-module build and 187-module ABBA imports pass. CPU is 5.415
and 5.347 seconds for D935 versus 5.175 and 5.460 for D953: overlapping ranges,
about 1.2% mean reduction, not admitted as a useful optimization. Removing the
visible jump scaffolding alone does not establish a meaningful execution gain.
Evidence: `.data/d953-native-expression/`, `.data/d953-native-expression-contract/`,
`.data/d953-native-expression-profile/`, `.data/d953-native-expression-cpu/`.

## D954 Native Host Shape In Progress

The original core host at object address 0x1990 reads state with LDP and enters
the native label without changing SP. Its external exit at 0x11034 already uses
three paired state stores, followed by PC and a native tail branch. An aggregate
store rewrite is therefore not pursued, and no GC-root store is removed.

Bounded disassembly of all eleven original host entries finds stack adjustment
only in runtime/table (80 bytes). D951's common host at object address 0xff84
instead establishes a 64-byte frame and uses callee-saved registers. This is
actual machine C-stack behavior, distinct from GVM continuation frame budgets;
it is not yet an attribution of CPU time or proof of a Darwin/Linux difference.

A fresh profile keeps table's original object/preload/host and merges the other
ten originals, retaining D949 binding guards and D951 local continuation guards.
The fresh host at object address 0xdba0 has no entry SP adjustment: the intended
machine shape is restored. ABBA CPU is 6.311 and 5.503 seconds for D951 versus
5.988 and 5.728 for D954, overlapping ranges and about 0.8% mean difference.
Host load is 64-74; no wall-time admission is made. This isolates an actual ABI
change but does not support it as the principal execution bottleneck. D954 is
not promoted. No consumer source or flags are changed.
Evidence: `.data/d954-leaf-host-profile/`; inspected objects are the immutable
D935 core/table objects and D951 `gerbil-link.o`;
`.data/d954-leaf-host-cpu/`.

## D955 Entry Label Bases In Progress

The original single host computes its label-table base in the local `___start`
at entry. The coalescing prototype's per-module selectors instead read each
private global `___lp` at label construction and guarded target comparisons.
This does not preserve the original invocation-local base optimization.

An isolated formatter change snapshots all original permanent label bases on
host entry and uses those values in code and guarded target comparisons.
Metadata initialization still uses the original globals. There is no type
result cache, no omitted VM-state store and no changed module binding behavior.
The existing native GC/type/control-flow/rebinding reference and twelve
concurrent candidates pass. Real eleven-module GNU compilation and all four
187-module preparation runs pass. ABBA CPU is 5.439 and 5.009 seconds for D951
versus 5.715 and 5.304 for D955, about 5.5% higher candidate mean. Host load
is 78-124; no wall-time admission is made. The snapshot candidate is rejected,
not integrated into staging, and does not qualify the startup optimization.
Evidence: `.data/d955-entry-label-base-contract/`,
`.data/d955-entry-label-base-profile/`, `.data/d955-entry-label-base-cpu/`.

## D956 Generic Entry Diagnostic In Progress

Previous guards cover global calls and selected local returns, not generic
procedure-vector dispatch. A separate diagnostic counts generic calls with
pure register/stack operands against the original native label map. Procedure
values, SELF, argument counts, VM roots and original jump/error handlers are
unchanged. Native-address hashing is initialized once inside the common host;
duplicate native addresses are reported rather than silently treated as unique
Scheme procedures. Non-procedure and external entries have separate sentinels.
Instrumented timings are not performance evidence. The diagnostic has no
consumer changes and no staging source integration.

The strengthened contract passes original reference and twelve native VMs,
with twelve internal calls, forty-eight external calls and twelve non-procedure
calls observed. The eleven-module GNU build passes. Real MCP preparation counts
68246874 generic calls, 67097081 internal. The class-of source group has
33368624 calls, 33367442 reaching the native address represented by the module
initializer's L45 (99.996%). The hash-get group has 31390677 calls, 31379120
reaching the address represented by gc-table-ref (99.963%). These are native
address observations, not a proof of unique Scheme procedure identity: GCC
coalesces thirty-two label addresses. A second checked run reproduces the counts
and explicitly validates all 187 preparations and final IMPORT-OK with exit 0.

Initial diagnostic failures are preserved: INTRO table rows were not executable
labels, PROCEDUREP requires the generated C temporary, and LABEL_ENTRY_GET
returns a descriptor rather than the machine address. Coverage initially had
only external calls because original resource objects retain some bindings;
module-init-created closures now exercise internal entries. The first real run
finished preparation but the harness rejected the destructor's count trailer;
normalization is allowed only in single-candidate diagnostic mode, not paired
performance runs. Evidence: `.data/d956-generic-entry-contract-all-paths/`,
`.data/d956-generic-entry-profile/`,
`.data/d956-generic-entry-observation-checked/`.

## D957 Static Vector Entry Guards In Progress

A bounded rule uses only generated module-init code and PROC descriptors to
find procedure values and their exact argument counts. At adjacent global-vector
load/generic-call sites it emits at most eight exact descriptor guards. Hits
preserve the actual closure SELF and original argument checks; misses execute
the original generic call and non-procedure handler. Table mutation is allowed,
no dispatch result is cached, and no observed profile target or MCP-specific
symbol is embedded. The class-of site has four statically derived candidates.
Emission is Darwin/GNU single-host-only; other targets retain original code.

The first small fixture had no rewritten site because safe vector-ref was
outlined; its zero-site admission failed correctly. A localized unsafe read of
the known test vector, with safe function-call semantics, now exercises the
actual generated shape. Native contracts include captured closure state,
vector mutation to another procedure and mutation to a non-procedure. A
test-only event macro requires actual guard hits and both fallbacks; it is
absent from the performance candidate. Original reference and twelve native
candidate VMs pass; each candidate records one actual guard hit and two actual
fallbacks, including the safe non-procedure exception. The noninstrumented
eleven-module GNU build and import gate pass. ABBA CPU is 5.012 and 4.996
seconds for D951 versus 5.130 and 4.772 for D957: overlapping ranges, about
1.1% mean reduction, not admitted as a useful optimization. No staging source
integration or startup admission is claimed.
Evidence: `.data/d957-vector-entry-contract-inline/`,
`.data/d957-vector-entry-contract-counted/`, `.data/d957-vector-entry-profile/`,
`.data/d957-vector-entry-cpu/`.

## D958 Preserve Generic Safety Mode In Progress

D957 adds PROCEDUREP even to original NOTSAFE calls, and its miss path rereads
the descriptor through the original generic macro. The next isolated candidate
uses the original SAFE/NOTSAFE mode (including the existing override macros).
A known-procedure miss reuses its descriptor with the original nargs/SELF/JUMP
sequence; an unknown/non-procedure value still uses the original generic macro
and handler. There is no assumption that a safe site always has a procedure.
The reference and twelve native candidates pass, each with an actual guard hit
and two actual mutation/exception fallbacks. The uninstrumented GNU build and
all four 187-module preparation runs pass. ABBA CPU is 5.243 and 4.818 seconds
for D951 versus 4.852 and 4.931 for D958, overlapping ranges and about 2.8%
mean difference. This does not establish a useful gain and is not promoted.
Evidence: `.data/d958-vector-entry-contract/`, `.data/d958-vector-entry-profile/`,
`.data/d958-vector-entry-cpu/`.

## D959 Guarded Read-Only Leaf Clones In Progress

Original GVM native entry and continuation labels remain in an address-taken
host table. A bounded code-generation prototype adds call-site copies of short
read-only process bodies, guarded by the existing exact global procedure
binding check. New native copy labels are never added to that table. The
intended optimization is a smaller direct-control-flow region for GNU GCC,
not an assumption that a mutable type or binding is constant. This is still a
performance hypothesis, not a proven Darwin/Linux attribution.

Selection uses an explicit primitive read/control-flow whitelist, at most
64 body lines/eight entry labels/three required arguments, and a 256-copy
budget. Allocations, writes, SET_R0, FP changes and opaque procedure calls are
excluded. All original instructions and checks are retained. Private callee
constant tables, PH_LBL0 and label descriptors are kept: a poll can resume
the original callee with its original GC map. A return to a known caller label
has an exact R0 guard with the original return fallback. Other platforms keep
original calls. The performance candidate has no counter or new runtime ABI.

The original reference and twelve concurrent native candidates pass, with four
actual copied entries in each candidate. Coverage includes hit/miss predicates,
mutable descriptor IDs, a cyclic type chain yielding at an internal poll to a
worker which performs GC and breaks the cycle, global procedure rebinding,
non-procedure exceptions and existing continuation/wind/values tests. Initial
fixture failures (wrong setter arity, anonymous lambda not a named global
provider) remain recorded. The final provider uses the same Gambit block form
as Gerbil-generated SCM. Real GNU/MCP compilation and CPU admission remain
not admitted. The global-only real build selects thirty copies of raw-table
accessors and symbolic? but exceeds its 300-second GNU compile budget. It does
not cover the dominant class-of or gc-table-e returns, and is not qualified.
No staging source change or startup delivery is claimed.
Evidence: `.data/d959-leaf-clone-contract-poll/`,
`.data/d959-leaf-clone-profile/`.

## D960-D961 Internal Copies And Shared Fallback

Known JUMPINT calls preserve their original direct entry, skipping the argument
prologue and not changing nargs or SELF. A two-argument caller to a one-argument
predicate validates this difference. Reference and twelve candidate VMs pass,
each with six actual copy entries. The real build selects thirty global and
twenty-two internal copies and passes GNU compilation and imports. ABBA CPU is
5.450 and 5.164 seconds for D951 versus 5.287 and 5.173 for D960, overlapping
ranges and about 1.4% mean difference. It is not promoted.

D961 routes copied return fallbacks through one original JUMPRET dispatcher to
avoid duplicating indirect return sites. Its twelve-process contract passes,
but no real profile or performance admission is attempted: inspection shows
the dominant class-of predicate is already a local expanded subroutine, not a
JUMPINT to class-type?. gc-table-e has a cold rehash path and is outside the
read-only full-body rule. The earlier expected hot-target coverage was wrong;
no claim that these copies address those two dominant returns is retained.
Evidence: `.data/d960-internal-leaf-contract/`,
`.data/d960-internal-leaf-profile/`, `.data/d960-internal-leaf-cpu/`,
`.data/d961-shared-leaf-return-contract/`.

## D962 Static Known Return Destinations Rejected

The next rule copies no body and duplicates no original indirect return. It
collects visible caller continuations for known JUMPINT targets, plus bounded
read-only local subroutine regions reached after SET_R0(LBL(n)). At original
R0 returns it emits up to four exact descriptor checks and direct gotos, then
the original return fallback. It changes no nargs, SELF, frames, GC descriptors
or binding semantics and uses no observed profile targets. Darwin/GNU-only
guards retain original behavior elsewhere.

Source-only inspection now confirms guards at the actual module initializer's
type loop (return to L46), instead of the unrelated standalone class-type?
procedure. The first native reference and twelve candidates pass with two
actual guarded internal returns per candidate, including cyclic poll/GC and
mutable descriptors. The strengthened local fixture also passes reference and
twelve VMs, with four actual guard hits per VM: two internal returns and true/
false returns from a local type subroutine. Its non-structure sample preserves
the original early return. The real candidate emits 386 guarded return sites;
GNU compilation and all four 187-module import runs pass. User CPU is
A=5.557539/5.134293 and B=5.390742/5.066627 seconds: about 2.2% lower mean,
with overlapping samples under host load above 117. This is not admitted as
a startup improvement; no official-first or full-toolchain promotion follows.
Evidence: `.data/d962-known-return-contract/`,
`.data/d962-known-return-contract-covered/`, `.data/d962-known-return-profile/`.
CPU evidence: `.data/d962-known-return-cpu/`.

## D963 Local Continuation Specialization In Progress

The next isolated rule specializes only statically visible local GVM subroutine
calls. Bounded regions (64 lines, eight blocks) must contain no allocation,
poll, opaque call, frame change or R0 use except the terminal return. Copies
use direct gotos to the original continuation; caller SET_R0 and all original
frame operations remain intact. Original labels and descriptors remain, and
non-Darwin/GNU configurations keep the original path. This is an execution
cost hypothesis, not a delivered startup optimization. Native semantic and
actual-hit checks precede a real GCC profile and uninstrumented CPU comparison.

Reference and twelve concurrent native candidates pass. The tiny candidate
contains one local copy and two direct returns; true and false paths produce
actual clone entries. Three focused unit tests cover original frame/descriptor
retention, native-only fallback, explicit fallthrough/backedges, and rejection
of polls, R0/frame mutation, stack writes and heap checks. The real eleven-module
render selects exactly the MOP initializer's L125/L126/L127 type loop returning
to L46 (one copy, two direct returns), not standalone class-type?. Its caller
still saves STK(1)/STK(2), sets LBL(46), and adjusts FP by eight. GNU compilation
and import qualification pass. The uninstrumented ABBA run is incomplete:
the second candidate reaches the 60-second CPU-diagnostic wall budget under
load above 130. Only A=5.575663 and B=5.228899 user CPU seconds complete;
this is not a complete ABBA result or an admitted speedup.
Evidence: `.data/d963-local-subroutine-contract/`,
`.data/d963-local-subroutine-profile/`.
Incomplete timing: `.data/d963-local-subroutine-cpu/`.

## D964 Deferred Local Frames Rejected

Source inspection identifies transient frame traffic surrounding the hot local
type predicate even on its immediate-success return. A stricter candidate
matches exactly two root saves, structure-type input setup, a local readonly
no-poll subroutine, and a success continuation that restores the saved object
and R0 before returning. The success path keeps the original R0, holds the
object in a private C temporary during this no-safepoint window and returns
without constructing the transient frame. The false path first materializes
the original stack slots, return descriptor and FP, then enters the original
continuation before any original poll/call. No runtime ABI or binding cache is
added. This path additionally requires MAX_PROCESSORS=1; all other configurations
retain the original setup. Existing host-entry/exit root synchronization is
unchanged. RTS setup.c uses synchronized OP_GARBAGE_COLLECT; mem.c scans saved
processor FP and roots at its collection phase. The candidate admits no poll,
heap check or opaque call while its C temporary is live outside VM roots.

The first fixture correctly fails the actual-copy gate because its boolean
branch direction is inverted relative to MOP. After covering both equivalent
branch layouts, original reference and twelve concurrent native candidates
pass, each repeatedly testing true return and false return through real GC.
The strengthened fixture makes the cold return observably different: GC is
followed by allocation of a new structure, whose type must be the saved cold
object. Reference and twelve candidates pass 100 true/cold pairs per VM plus
interleaved GC. Thus an incorrectly bypassed cold branch cannot pass by merely
returning the original object. The actual eleven-module rendering specializes
exactly the MOP initializer type-check frame (one deferred frame, two returns).
Four unit tests cover frame reconstruction, platform fallback, rejection gates,
backedges and original frames. This is semantic evidence, not speedup evidence.
Evidence: `.data/d964-deferred-frame-contract/` (rejected zero-coverage fixture),
`.data/d964-deferred-frame-contract-branch-covered/`,
`.data/d964-deferred-frame-contract-gc-observable/`,
`.data/d964-deferred-frame-profile/`: the first compile-link attempt exceeds
its 300-second build-only limit. The narrow resume verifies all retained object
and generated-C hashes, then compiles the identical C (SHA256
eaab2bccd50bf31aea882cf52f8c7639c2932f3fd02e4b5aecbbcfacb884d41d),
links and passes imports; GSC is unchanged. Resume compilation takes 321.506
wall seconds on this loaded host. Its distinct `resume-link-report.json` records
qualification without overwriting the original failed report. This is partial
runtime qualification, not a complete toolchain or startup result. All four
uninstrumented 187-module preparations pass. User CPU A=5.538332/5.828905,
B=5.571879/5.626673 seconds: about 1.5% lower candidate mean, with overlapping
samples. Load ranges from 117 to 152. This does not justify startup promotion,
so no official-first or full-toolchain rebuild follows this candidate.
CPU evidence: `.data/d964-deferred-frame-cpu/`.

The CPU-only harness now accepts a bounded, recorded wall budget (default 60,
maximum 180 seconds) to finish CPU samples on a heavily loaded host. This does
not change the official first-compile/no-output gate or qualify loaded-host wall
times as startup results. Existing incomplete observations remain retained.

## D965 RTS Hash Probe Diagnostic In Progress

The known GC-table dispatch count does not distinguish a cheap C call from a
long collision chain. The next diagnostic changes only RTS gc_hash_table_ref
to count field probes, hit/miss returns and lazy rehashes. Hash mixing, probing,
key/value reads, insertions and rehash policy remain unchanged. The first slot
and every collision slot are counted; the terminal histogram includes 1..31
steps and a >=32 bucket. Counts have a separate file receipt and no timer claim.
The CPU harness rejects this flag in paired performance mode. Actual GNU RTS
compilation and the same 187-module workload precede any optimization decision.
Evidence: `.data/d965-gc-hash-probe-source/` (counter-only source preparation).
