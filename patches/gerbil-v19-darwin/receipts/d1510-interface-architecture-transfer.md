# D1510 Interface Architecture Transfer

Research only: no runtime edit, candidate admission, new timing baseline or
toolchain completion. Retain the historical 47.771713 / 47.824226 / 47.927094
cold builds and the active 5 / 50 / 112-second whole-task gates. The second
strict complete-test wave is DENY; see `d1510-112-test-guard.md`.

## Primary Sources And Their Limits

[Rebuilding Racket on Chez Scheme](https://www-old.cs.utah.edu/plt/publications/icfp19-rddkmstz.pdf)
is an ICFP 2019 experience report. Its
[supplementary build analysis](https://www2.cs.utah.edu/plt/rkt-on-chez/appendix.pdf)
separates expansion from final compilation and identifies loading and
instantiating compile-time modules as significant end-to-end costs.
The supplement explicitly uses x86-64 Linux: this is architecture evidence,
not evidence of a Darwin cause or a predicted Gambit speedup.

[Racket's linklet contract](https://docs.racket-lang.org/reference/linklets.html)
separates serializable code from live imported instances, with separate
module phases and metadata. Loading code does not eliminate instantiation:
definitions and expressions still run against current imported instances.
Its representation below macros cannot be equated with serializing Gerbil
syntax objects carrying lexical contexts and mutable bindings.

[Julia's native-cache results](https://www.julialang.org/blog/2023/04/julia-1.9-highlights/)
distinguish time-to-first-execution from time-to-load. Large gains in the
former do not imply the latter disappears. Precompilation can increase by
10-50 percent and cache files grow. AOT reuse must account for construction
cost as well as subsequent launches; no Julia ratio is a Gambit forecast.

[Julia's package-image design](https://docs.julialang.org/en/v1/devdocs/pkgimg/)
uses shared libraries containing code and data, selected against compilation
configuration. Its explicit macOS linker workaround is `-undefined
dynamic_lookup` for the `-lSystem` boundary. That is a platform-linking contract,
not a mechanism for faster Scheme macro execution or permission to change
the retained GNU GCC driver/linker flags.

[XNU's Clutch/Edge scheduler design](https://github.com/apple-oss-distributions/xnu/blob/main/doc/scheduler/sched_clutch_edge.md)
does account for thread groups, QoS and heterogeneous clusters. D1017 already
records requested USER_INTERACTIVE in the original VM controls. Requested
QoS is not effective residency, but the available evidence does not justify
another priority-raising candidate. Do not relabel scheduling as the proven
cause of the recorded expansion cost.

## Exact Gerbil Boundary

The retained source separates two different artifacts:

- `compiler/driver.ss:844` emits textual `.ssi` metadata, prelude, package,
  namespace and generated interface forms. Its separate `compile-phi` path
  generates phase runtime Scheme/native artifacts.
- `expander/module.ss:139` reads an interface, constructs a fresh module
  context, calls `core-expand-module-begin`, quotes its body and registers
  the context. Evaluation is delayed through the original atomic promise.
- `expander/top.ss:273` expands runtime binding declarations, installs live
  bindings/properties and returns context-bearing syntax.
- `expander/top.ss:327` expands/evaluates syntax binding expressions at the
  next phase and installs their values in the current context.

Actual `std/io/api.ssi` reexports ten interfaces. Actual
`std/io/interface/base.ssi` interleaves runtime declarations, syntax bindings,
macro properties and a begin-syntax native-phase load. Native provider reuse
therefore does not, by itself, eliminate interface reconstruction. Conversely,
the previously observed nested import durations cannot be summed or assigned
exclusively to reconstruction.

The real-phase controls in `d1510-real-phase-import-boundary.md` already show
that serializing the existing native phase is not the next win. The remaining
research question is whether a compiled interface-construction program could
avoid repeated generic expansion while constructing the same fresh contexts,
bindings and syntax. This is not raw-AST restoration or reuse of another
process's initialized state. It is an unimplemented hypothesis, not a claim
that `.ssi` alone owns the measured import budget.

Existing `d1510-stdlib-joint-import-eval.md` already supplies joint, nested
callback accounting on the retained host. Its make/json residual import
intervals are 1.209263 / 1.165717 seconds after subtracting observed nested
callbacks. These residuals include internal work and observer overhead, not
pure binding reconstruction. Its begin-form own intervals are 0.404402 /
0.823771 seconds respectively. Keep those observations separate from admission
timings and do not rerun the same import census. The missing distinction is
which operations inside the residual are preparation versus required live
construction, and which begin execution remains after existing native reuse.

Before any candidate, establish the reached cost of that distinction from
these existing boundaries. A useful implementation must preserve original
import order, phases, dependency identity, delayed evaluation, reload/cycle/error
behavior, lexical marks, mutable properties and GC roots. It must support
independent standard-library modules; no package-name special case is permitted.
Any deployment remains Darwin-only with unchanged fallback elsewhere. The
code-versus-instance idea is general, not intrinsically Mach-O-specific, and
must not be sold as a demonstrated platform cause or admitted improvement.

## Reached Transformer Observation

The subsequent diagnostic uses the retained `expander` object's mutable `e`
field. `apply-macro-expander` reads that field in the native dispatch path,
unlike global function rebinding that may be bypassed. Wrappers delegate every
invocation to the original handler, use the existing joint nesting depth,
subtract reached children once and restore all original handler fields before
emitting results. No compiled code, interface file or installed runtime changes.

Fresh make/test/json/list processes use only the standard library and an empty
package home. All four finish with original cached-context identity, final OK,
exit zero, unchanged frozen binary and export/native-module inventories exactly
matching the earlier original control. These checks cover observed import
behavior, not all library assertions or full build/test correctness.

| Library | Runtime declarations / observed own seconds | Syntax declarations / observed own seconds | Import forms / observed own seconds |
| --- | ---: | ---: | ---: |
| make | 5,369 / 0.008585 | 581 / 0.030153 | 56 / 0.208792 |
| test | 3,604 / 0.002566 | 469 / 0.016497 | 37 / 0.027691 |
| encoding/json | 8,979 / 0.038180 | 1,852 / 0.043841 | 138 / 0.454581 |
| list/list | 3,151 / 0.046725 | 329 / 0.008362 | 31 / 0.123424 |

Begin-syntax own observations are 0.001619 / 0.000383 / 0.002748 / 0.011178
seconds respectively after subtracting nested evaluation. No export wrapper
entry is reached: the module-body source invokes its export function directly.
Do not infer zero export work. Joint Scheme-eval own intervals in this same
run are 0.192930 / 0.038973 / 0.743361 / 0.094409 seconds. Neither internal
direct calls nor scheduler/GC effects within an observed interval are removed.
Instrumentation overhead and wall variability remain; these are not speedups.

This narrows the next decision: do not construct a declaration-only compiled
interface candidate on the assumption that thousands of runtime declarations
own the import interval. The measured make/runtime-declaration interval does
not support a major gain. Import-form handling and execution remain reached
costs worth separating. `core-expand-import%` creates import records, binds
them through current contexts and evaluates positive-phase dependencies;
module/export resolution and mutable binding semantics must remain intact.
No new caching, eager import or consumer change follows from these observations.

Evidence: `.data/d1510-stdlib-interface-transformers-v2/report.json`; original
comparison `.data/d1510-stdlib-gambit-eval-split-control-v1/report.json`.
The v1 launch fails during sandboxed host discovery before any Scheme process
starts; it is not a runtime failure or a timing observation. Selected Python
trace/import regression tests: 20 passed. All four Scheme processes are terminal.

## Original Import Binding Census

A further read-only diagnostic inspects original import results, not a cached
resolver or changed binding algorithm. At phase-zero module-context import
entries with rebinding disabled, it snapshots the original table's key/value
pairs. After the unmodified handler finishes, it counts returned import records
and checks whether any prior binding object remains at the same key. It never
resolves an export again or omits an original bind. A local per-form key set
separately counts repeated phase-zero symbol keys in the returned records.

| Library | Observed import forms | Phase-zero symbol-key binding attempts | Prior object retained | Repeated keys within one form |
| --- | ---: | ---: | ---: | ---: |
| make | 56 | 61,428 | 0 | 5,376 |
| test | 37 | 31,956 | 0 | 754 |
| encoding/json | 138 | 110,753 | 0 | 9,419 |
| list/list | 31 | 30,767 | 0 | 753 |

The narrow strong-prior-retention count is also zero for every library.
Intra-form repeated keys are about 8.75 / 2.36 / 8.50 / 2.45 percent of
observed attempts respectively. These are count fractions, not cost fractions,
safe omission counts or a performance ceiling. Phase-shifted imports and
non-symbol keys are outside this census. It cannot infer that repeated keys
have identical sources, weak flags, callback effects or error behavior.

The proposed prior-binding allocation shortcut therefore has no demonstrated
coverage in this observation. Do not implement it or reopen the rejected
whole-context memo from these counts. A repeated-key shortcut also lacks a
major cost budget and semantic eligibility; no such candidate is constructed.
Most counted imports install bindings in newly constructed contexts. Reusing
mutable binding objects across those contexts would change mutation isolation,
so allocation counts alone do not justify a shared binding cache.

All four independent original libraries finish with cached-context identity,
final OK, exit zero, unchanged frozen host and inventories matching the original
control. The v1 census covers only prior retention; v2 adds intra-form repeats
without changing original execution. Snapshot/key-set work makes their wall
times unsuitable as performance comparisons.

Evidence: `.data/d1510-stdlib-import-binding-census-v1/report.json` and
`.data/d1510-stdlib-import-binding-census-v2/report.json`. Selected diagnostic
regression tests: 34 passed. All eight Scheme processes are terminal; no full
build/test rerun, runtime patch admission, gate change or publication follows.

## Source Audit: Import Records Are Retained Mutable State

The 2026-10-08 read-only review checks the next proposed immutable-preparation
boundary against the retained source and its generated interface. It does not
rerun the import observer or construct a candidate. The frozen binary hash was
rechecked unchanged; historical timing and 5/50/112 gates remain separate.

`expander/module.ss:15-22` declares module-import/module-export and
import-set/export-set structures. `final: #t` prevents subtype extension; it
does not make their fields immutable. The retained generated
`build/lib/static/gerbil__expander__module.scm:48-54,147` defines field setters.
The actual `build/lib/gerbil/expander/module.ssi:21-34,88-96` exposes setters for
module-import-source and import-set-imports, including unchecked variants.
No repository-local setter call is needed to establish the public capability.

`core-expand-import%` at `expander/module.ss:783-789` maps current exports into
fresh module-import records. Its `import!` at lines 840-872 both binds those
records and retains them in `module-context-import`; the resulting syntax body
also contains them. Compiler driver/compile/optimize later read their phase
and source fields. They are not proven dead expansion-only intermediates.
Deleting or sharing these records requires an observability/identity proof;
sharing an initialized binding is a separate, already rejected shortcut.

Compiler `generate-meta-code` at `compiler/driver.ss:904` produces interface
forms from the already expanded module code. `compiler/compile.ss:1258`
separately emits native phase loads; lines 1438-1496 emit runtime declarations,
syntax bindings and aliases. Thus `.ssi` generic expansion is interface
instantiation, not evidence that the original user macro source is compiled
again. Precompiling the interface must not be confused with the already native
phase implementation or with skipping live import instantiation.

Four-question decision:

| Question | Answer |
| --- | --- |
| Is shared immutable import preparation correct? | Not when the shared material contains these live records. Retention and exported mutation disprove that immutability premise. |
| Has it been explored? | Compiled-interface transfer is already reviewed above. This audit adds the specific retained-record/setter boundary; it is not a new compiler implementation. |
| Is it worth implementing now? | NO to record sharing/deletion. Declaration-only compilation already lacks a major reached budget. A fresh-instance construction program would need a distinct cost and equivalence argument. |
| Expected benefit? | No supported seconds/factor estimate. The observed make declaration time of 0.008585s is not a forecast or a current MCP cost fraction; broader import time includes required live work. |

The Racket paper and linklet contract were rechecked, not newly discovered.
They separate compiled code from instantiation and mutable imported variables;
they do not make Gerbil's records immutable. The experience report's figure 4
also reports greater startup/load and source-compilation time for its Racket CS
comparison than the original Racket. The architecture alone is not a speedup
promise or a Darwin-specific remedy. No ratio is transplanted to Gambit.

Result: no runtime edit or build admission. Continue only with a source
mechanism that preserves fresh records, binding callbacks, phase execution,
reload/cycle/error behavior and current compiler consumers, and has a defensible
removable-cost budget. Do not repeat the interface census or raw-AST/native-phase
serialization experiments to bypass this prerequisite.

## Construction Program: Staging And Observer Boundary

The user explicitly requested continued deep source research after the blocked
turn. Missing cost attribution limits implementation admission; it does not
forbid analysis of mechanisms. No new recording, runtime edit or candidate
construction follows from this review.

The retained module entry at `expander/module.ss:633-645` accepts a fully
expanded sealed module body without calling `core-expand-module-body`.
`sealed-syntax?` at `expander/stx.ss:35-40` recognizes syntax-quote objects;
it is not a validator that imports or binding installation already happened.
Wrapping an ordinary SSI body in a quote would therefore skip required work
and is NO, not a loader optimization.

The normal path has two stages. `core-expand-block` runs head expansion,
resolves the form and invokes its special handler. Module-body `expand-body`
then handles value expressions and deferred exports. Many core handlers already
return sealed syntax. The second traversal must not be described as rerunning
every macro twice. Export resolution uses the resulting live context, including
bindings installed during the first stage, so moving exports into an eager
per-form program is not automatically equivalent.

A genuinely different compiler-produced interface construction program would
need to instantiate fresh contexts, import records and bindings, preserve
the first-stage effects in their original order, and finish deferred exports
before delivering context-correct expanded syntax. Properties may evaluate
expressions; syntax declarations evaluate at the next phase. It must retain
dependency loading, initializer callbacks, errors, lexical marks, atomic delayed
module evaluation and original compiler-facing import/code fields. Existing
sealed output is a possible integration boundary only after these obligations
are satisfied, not proof that a construction program is correct.

There is also an important limit to the earlier 0.008585s declaration result:
`tests/stdlib_import_trace.scm:212-227` wraps the core expander's `e` procedure
and starts the transformer timer when that wrapper is invoked. Calls before
it, including head expansion, identifier resolution and expander-method
selection (`core.ss:281,430-438`), are not measured by that handler interval.
Consequently the small number neither proves all per-declaration preparation
is small nor establishes that the unmeasured portion is large. The earlier
decision remains NO to implementation from declaration counts alone, not a
blanket rejection of every compiler-produced fresh-interface program.

Four-question review for the full construction-program mechanism:

| Question | Answer |
| --- | --- |
| Correct path? | Plausible integration boundary exists, but the two stages and all live effects must be replayed. A quoted SSI or reused initialized context is incorrect. |
| Already explored? | The broad hypothesis is recorded above. This review makes the sealed-entry, deferred-export and handler-timer boundaries explicit; it does not reopen raw AST restoration or declaration-only deletion. |
| Worth optimizing? | ANALYZE ONLY. It addresses generic interface execution rather than an MCP branch, but no significant removable outer-dispatch budget is proved. |
| Expected benefit? | Unknown. Saving is limited to avoided preparation/dispatch, not required instantiation or phase execution. Any extra native factory compilation, image loading and validation must be charged against cold build and startup. No seconds or factor forecast is admitted. |

Research should stay on this complete caller-to-handler path, not return to
symbol-hash filtering, shared import objects, runtime-only CLI dispatch, native
phase serialization or a wider provider allowlist. A future implementation
must be generic, Darwin/GNU activated with ordinary fallback elsewhere, and
qualify independent stdlib controls plus real MCP under 5/50/112 gates. The
historical 47-second cold builds and 105.750982-second test are unchanged;
current stable complete-test admission remains unresolved.

## Single-Step Head Resolution Transfer

Read-only source review identifies a concrete outer-handler operation:
`core-expand-head` (`expander/core.ss:281`) tests the head using
`core-bound-identifier?` (`:771`), which resolves its binding. If that test
succeeds, `core-expand*` returns without invoking another expander. The block
caller then resolves the same returned head again at `:330`. Expression
expansion has related lookups at `:201` and `:226`; these are related sites,
not evidence that all their resolutions can safely be removed.

A possible mechanism is returning the terminal resolved binding alongside
the expanded head to an internal caller. This is a single-step result transfer,
not a persistent cache. No result may cross a macro invocation, a binding
mutation or a later form without a separate correctness argument. Resolution
is not wholly pure: `core-context-shift` (`:652`) can create phase contexts.
The first resolution and its effects must remain. Import/alias unwrapping,
dynamic context/phase/marks, live handler replacement and exception order also
remain part of the contract. No implementation or new measurement was made.

| Review question | Decision |
| --- | --- |
| Correct path? | Concrete duplicate work exists on the successful core-head stop path. Passing its terminal result is plausible; a general binding cache is not justified. |
| Already explored? | No exact matching mechanism was found in the checked exclusion, architecture, accountability, D970 and D936 records. This bounded search is not a claim about every historical experiment. |
| Worth optimizing? | ANALYZE ONLY. It is a generic caller-path mechanism, subordinate to the full interface-construction architecture, not yet a major-cost candidate. |
| Expected benefit? | Unknown. One avoided resolution per eligible handoff is a source-level bound, not a time estimate. Neither handler-own timings nor declaration counts establish its critical-path share. |

## Reached Hardware Cycle Follow-Up

The later [original-native live-boundary controls](d1510-head-resolution-live-boundary.md)
reject unguarded terminal binding transfer: the reached core-expander predicate
can replace the context binding before the caller re-resolves it. This supersedes
the earlier purely source-level plausibility judgment, not the immutable
code/live-instance distinction. The original public-resolver wrapper did not
observe these internal native calls and is not qualified attribution.

The existing recorder now accepts CPU Profiler and a shared diagnostic deadline;
default CPU Counters remains available. Framework/metric regression checks pass
33 tests. This is diagnostic infrastructure, not a runtime performance patch.

One frozen-runtime process imports std/make, std/test and std/build-script,
exits zero with final OK, and leaves the runtime/GSC hashes unchanged. Recording
and TOC export succeed, but CPU-table export exhausts the 30-second shared
budget. Its original report remains unqualified. A separate bounded offline
export of the saved trace succeeds without launching another Scheme process.
The existing native CPU summarizer validates 871 running samples, 540,361,734
active cycles and 510,119,186 native-function cycles against image UUIDs and
function starts. These two diagnostic stages must not be described as one
within-budget recording success or a product timing.

Self-sample contributions are coalesced host 25.85%, ordinary/constant-propagated
mark_array 11.09%/8.63%, GC-hash set/ref 8.02%/7.81%, and movable-object scan
3.26%. The process includes bootstrap as well as target imports. Native host
samples do not identify individual Scheme procedures; hash samples do not prove
ownership by expander context tables. No exclusive duplicate-resolution cost,
Darwin/Linux cause or removable wall-time fraction follows.

Bounded disassembly of the same frozen binary places hot hash PCs in the scalar
probe loads and related return paths. The selected HASH_STEP macro uses
multiplication, not modulo division. This does not establish cache-miss latency
or justify changing hash policy. Prior SIMD-probe, cold-rehash-tail and bounded
context-burst failures remain closed. The research target remains reducing
redundant caller-level work while preserving live interface construction, not
retuning those primitive candidates because they appear in a profile.

Evidence: `.data/d1510-stdlib-exclusive-cpu-v1/` (`report.json`, `toc.xml`,
`cpu-profile.xml`, `cpu-summary.json`). No new cold build, complete-test wave,
candidate binary, performance admission or publication occurred.

## Actual Context-Table Layout Boundary

The existing stdlib runner now supports a single original std/make physical
context-table snapshot, separate from its original multi-library modes.
No hash-policy change or optimization candidate is implemented.

V1 fails with SIGBUS: the diagnostic incorrectly passes the HashTable interface
shell to an unchecked raw-table accessor. Source `runtime/hash.ss:426` wraps
the underlying GC table in a HashTable instance. V2 unwraps the interface but
its type check incorrectly requires the low-level `__gc-table::t` to satisfy
the Gerbil class contract; it exits 70. V3 uses the original interface accessor
and Gambit structure-supertype chain before touching physical fields. These
are fixture failures, not frozen-runtime performance regressions. Failed
directories remain unchanged.

V3 finishes import, evaluation, cached identity and final OK with unchanged
frozen binary. Each table's snapshot rejects any GC across its field copy;
pending moved-key rehash is normalized through the original hash-ref operation.
It captures 71 distinct loaded module-context tables and 83,498 occupied keys.
This covers phase-zero module tables after import/evaluation, not all phase
contexts or the workload's weighted lookup stream. Snapshots and raw encodings
remain private under `.data/d1510-stdlib-hash-layout-v3/`.

Offline checks require exact capacity/slot count, recorded occupied count and
the current multiply-based address hash. For these subtype-one keys the raw
tagged word is `2 * encoding - 1`, masked to 64 bits. Every occupied key is
reachable from its computed starting slot without crossing an UNUSED slot.
Mean successful physical probe length is 2.637931 slots and maximum is 145.
This is an unweighted static lookup model, not measured lookup counts, elapsed
CPU, latency or a demonstrated Darwin/Linux difference. The observations do
not yet admit a mixer replacement or a speedup forecast.

[Linear Probing with 5-Independent Hashing](https://arxiv.org/abs/1509.04549)
supports checking distribution and clustering rather than treating fewer
instructions as sufficient. It is a general hashing analysis, not a Darwin
optimization result, and does not establish that Gambit's mixer is the cause
of the recorded platform gap. Prior SIMD bursts, symbol-key filtering,
cold-tail helpers and context bursts remain closed.

## Address-Mixer Model: No Main-Line Candidate

The unified framework's `hash-layout` command validates the existing V3
snapshot without executing Scheme. It requires the completed frozen-runtime
receipt, ordered physical slots, exact capacity/count, unique subtype-one keys,
a terminating empty slot, and reachability using the original hash. The
source report and transcript digests are recorded. Six analyzer checks plus
fifteen framework checks pass; no original workload is rerun.

Both replay models insert the same keys in original physical-slot order at
the same capacities, with the same descending scalar probe sequence. This is
not original historical insertion order or an executed runtime candidate.
The alternative uses a two-multiply 32-bit avalanche finalizer after the
original address fold, not a demonstrated five-independent hash family.

| Fixed-order model | Successful mean slots | Uniform-start missing mean slots | Maximum insertion slots |
| --- | ---: | ---: | ---: |
| Original | 2.637931 | 9.176022 | 166 |
| Avalanche32 | 2.395818 | 7.831208 | 171 |

The original physical lookup maximum remains 145; it is not the replay's
maximum insertion length. Successful probe reduction is about 9.18%; the
uniform-start missing reduction is about 14.66%. Actual missing-key start
distribution and lookup-frequency weighting are unknown. Added mixer
instructions, GC/rehash behavior and native execution are not measured.
Neither table-slot ratio predicts a product-time improvement.

Four-question decision: the reached hash-probe budget made distribution worth
checking; bounded history search found no identical avalanche replacement;
the observed model is not sufficiently strong for the requested major-cost
candidate, and its maximum insertion tail is worse; expected end-to-end benefit
remains unproved. NO to compiling this specific avalanche32 model as the next
main-line candidate, enlarging it by trying arbitrary constants, or publishing
the offline ratio as startup/build/test acceleration. This is an admission
rejection from insufficient benefit evidence, not a measured runtime regression.

Evidence: `.data/d1510-stdlib-hash-layout-model-v1/report.json`. Recompute with
`python3 patches/gerbil-v19-darwin/tests/experiment.py hash-layout --snapshot
.data/d1510-stdlib-hash-layout-v3 --output <fresh-project-data-directory>` at
the repository root. No cold build or full-test timing has changed.

## Exact Native Line Follow-Up Without Recompilation

The existing line aggregator now accepts the frozen flat runtime and explicit
carrier source/object, exposed through the shared `native-lines` command.
This is offline attribution, not a runtime transformation. The old baseline
mode remains available. Twenty-six native-line, relocation and framework
checks pass, including rejection of changed targets, text extents and CPU
identity while allowing raw symbol-index renumbering.

D1608 initially appears usable because text bytes and objdump's symbolic
relocation rows match. Stronger canonicalization finds 16,630 changed defined
data-target offsets, split between displacements of 768 and 944 bytes. Thus
the attempted V1 refuses that mapping; matching symbol names alone was not
enough. No partial line result is admitted from D1608 for this runtime.

The existing original GNU debug sidecar V1 was previously incomplete because
its raw relocation bytes differed. Reprocessing that same object against the
current frozen carrier establishes identical text and canonical relocation
targets (including symbol section, relative value, descriptor, instruction
offset/type/width), with matching CPU type/subtype and counts. Original
source, reference object, compiler-driver and sidecar hashes are verified.
The old incomplete receipt is not rewritten; V2 records its digest and the
new text identity proof. No compiler or Scheme workload is launched.

All 160 coalesced-host PCs from the existing stdlib CPU profile map through
exact DWARF line intervals, with zero unmapped cycles. Source text is quoted
only for the hash-checked carrier; included source files without a compile-time
identity proof are not treated as validated current code.

| First macro at compiler-assigned line | Share of host self cycles |
| --- | ---: |
| IF | 19.40% |
| END_M_HLBL | 18.11% |
| IF_NARGS_EQ | 12.89% |
| JUMPGLONOTSAFE | 7.66% |
| JUMPRET | 7.64% |
| END_M_COD | 5.83% |

These groupings are compiler-assigned C-line weights. Shared entry/exit lines
cannot be assigned exclusively to a Scheme procedure; argument checks and
conditionals remain spread across many operations. They do not establish a
single resolver's exclusive cycles or a removable first-log fraction. The
direction remains reducing generic interface calls/preparation while preserving
live construction, not reopening the rejected host-frame, return-outline,
parameter-result or GC variants from a macro category's apparent weight.

Evidence: `.data/d1510-stdlib-native-lines-v2/report.json`. No candidate,
new cold build, complete-test wave or product acceleration is admitted.

## Avoid Another Low-Coverage GC Experiment

The existing D1008 marker counts include 43,237,938 copied objects. Its exact
bucket definition places only 1,260,154 copies above eight words (about 2.91
percent), with maximum 238 words. Counts are not elapsed-time attribution.
The original GCC O3 `mark_array` disassembly already contains a 128-bit copy
loop with a scalar remainder. A proposed bulk `memcpy` replacement therefore
needs a distinct reached instruction budget; scalar-only or large-object
assumptions are not supported. D968's barrier/chunk rejection stays closed.

Private evidence: `.data/d1008-gc-mark-counts/counts.json`,
`.data/d1102-original-mcp-cpu-profiler/cpu-summary.json`, original runtime
objects in `.data/d1391-runtime-object-source/src/gambit/lib/` and selected
standard-library interfaces in `.data/d1510-mcp-test-source-home-v2/build/lib/`.

## Stable-Symbol Table And Nonmoving-Key Rehash Review

No runtime candidate is built. Two distinct mechanisms were checked rather
than relabeling the denied symbol-name comparison filter or cold-tail stack
outline. The original source hashes and frozen runtime remain selected.

`runtime/table.ss:289` already provides `symbolic-hash` through
`##symbol-hash`, and `hash.ss:497` supplies a symbolic table constructor.
Its raw table uses quadratic probing, a seed and fixnum modulo; it is not a
drop-in specialization of Gambit's scalar address-probe loop. Normal marked
identifier binding substitutes a gensym in `core.ss:604`, and identifier
resolution consults that substitution before table lookup. This explains
why normal binding keys can be symbols without proving a symbol-only API.

Actual original-native contracts establish that public `core-context-put!`,
`core-context-get` and `core-context-bind!` also accept a pair key by identity.
A distinct equal-looking pair does not resolve, and rebinding calls the live
callback with the prior value exactly once. Direct replacement by a
symbol-only constructor would narrow this existing key contract; the default
symbolic table does not even request checked keys. A generic fallback or
different representation needs a separate correctness and cost argument.

The original fixture was extended from nineteen to twenty-five ordered cases
and run in twelve hardware-derived concurrent processes. All **300** cases,
final markers and exits pass, including mark-to-gensym resolution and unchanged
gensym symbolic hash across an explicit GC. The latter does not prove that the
particular symbol moved. No consumer package is loaded and no production table
is replaced. The entire diagnostic wave is 1.371907 seconds, not a startup,
clean-build, full-test measurement or acceleration. Evidence:
`.data/d1510-context-key-contract-v1/report.json` and twelve original logs.

Source inspection also reveals a more limited algorithmic opportunity:
`mem.c:5715` conservatively sets KEY_MOVED for strong tables with allocated
keys after GC, while `mem.c:211` requires interned symbols to be permanent.
Avoiding unnecessary rearrangement for an all-nonmoving-key table would be
different from removing a stack frame. But any mechanism must preserve mixed
movable keys, unchecked/raw mutation, deleted entries/free counters, weak
tables and union-find parent-link conversion. Setter-only classification is
not justified by the existing mutation contract.

[Chez 7.4's release notes](https://www.scheme.com/csv7.4/7.4.html) describe
generation-friendly eq hashing that avoids rehash overhead for objects that
did not move. This is an architectural precedent, not a measured Darwin/GNU
Gambit gain or a reason to copy Chez's different collector protocol.

The existing validated stdlib CPU trace records 6,467,550 self cycles in
`gc_hash_table_rehash_in_situ`, or **1.196893%** of 540,361,734 sampled active
cycles. Even deleting this entire sampled category would yield only about
1.0121x in a zero-overhead CPU sensitivity calculation. It is not a wall-time
upper bound, covers bootstrap as well as imports, and does not establish the
MCP first-log fraction. Added classification scans would have their own cost.
This is insufficient evidence for the requested major-gain mainline candidate.
The existing trace is reused; no profiler, compiler or unchanged MCP campaign
is launched to repeat it.

Four-question decision: direct symbol-only replacement fails the observed
generic-key contract; no identical table-representation/nonmoving-key mechanism
was found in the bounded exclusion and receipt search, which is not proof of
complete historical novelty; a nonmoving-key rehash shortcut is not a major
target on the available cycle evidence; no credible seconds estimate exists.
**NO** to direct table replacement and to a standalone nonmoving-key rehash
performance build from these data. Preserve these findings and continue on
reached caller-level Scheme work rather than trying hash-policy constants.

Historical first logs 4.850866/4.573628/4.592897 seconds, complete cold builds
47.771713/47.824226/47.927094 seconds and full-test 105.750982 seconds remain
historical. Current whole-task gates remain 5/50/112; current complete-test
qualification is still open. No performance patch is admitted here.
