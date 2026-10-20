# D1510 Native Procedure Budget Boundary

The initial sections are a read-only follow-up; later sections record separate
diagnostic workloads and constructions. None is optimization admission. Retain
47.771713 / 47.824226 / 47.927094 seconds cold and the 5 / 50 / 112-second
whole-task gates. Stable full-test qualification remains open.

## Input Identity

The existing standard-library CPU sample contains 540,361,734 active cycles.
The exact native-line receipt has zero unmapped coalesced-host cycles and the
frozen runtime SHA256
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Current input hashes were checked before the following offline aggregation:

| Input | SHA256 |
| --- | --- |
| `.data/d1510-stdlib-exclusive-cpu-v1/cpu-summary.json` | `f68c61f6170e975ef36bc8150e221fa57e59c904b2b00f34c4abed59a12245bd` |
| `.data/d1510-stdlib-native-lines-v2/report.json` | `8c9ff7df90913ecf2c2a2b8d43500d0c1e96100d117a8a7e8929682fcf38ef2e` |
| `.data/d1510-source-loader-linked/gerbil-link.c` | `59385f75b21bf17f517f6752b5641b955e14cbafcad330d8f70a80cf17a3ecc4` |

## Aggregate Budget, Not Wall-Time Attribution

Disjoint self-cycle groups from that sample are:

| Group | Active cycles | Share of sampled active cycles |
| --- | ---: | ---: |
| Coalesced host | 139,677,318 | 25.85% |
| Mark arrays, movable scanning, collection and hash rehash | 132,959,093 | 24.61% |
| GC-hash ref/set | 85,562,435 | 15.83% |
| Gerbil runtime init native host | 28,796,909 | 5.33% |
| Names containing `dyld`, `mach_o::` or `MachO` | 4,645,494 | 0.86% |

The last group is a literal symbol-name classification, not all platform cost.
It excludes unsampled waits, kernel work and any unidentified loader routines.
This active-cycle sample cannot establish a Darwin/Linux ratio or a wall-time
upper bound. It does not support making dynamic-loader fixups alone the next
major-gain implementation. Required Scheme execution and allocation remain
the larger reached research boundary.

## Lexical Procedure Follow-Up

For each hash-verified carrier line in the existing line receipt, track the
current `#define ___PH_PROC` only inside `___BEGIN_P_SW` / `___END_P_SW`.
Leave module-level/shared lines unassigned. This is a generated-source lexical
classification, not stack attribution or exclusive Scheme-procedure timing.
GCC can merge instructions and assign their DWARF line to one source location.

| Lexical region | Active-cycle weight | Share of all sampled active cycles |
| --- | ---: | ---: |
| Shared/outside procedure | 33,756,130 | 6.2470% |
| `gx#syntax-e` | 8,091,705 | 1.4975% |
| `gx#core-expand-export%` | 5,941,500 | 1.0995% |
| `make-final-slot-accessor` | 5,000,584 | 0.9254% |
| `__make-class-predicate` | 4,249,119 | 0.7863% |
| `gx#stx-e` | 4,163,865 | 0.7706% |
| `gx#core-resolve-module-export` | 4,000,271 | 0.7403% |

Do not interpret the accessor region as repeated factory construction. Carrier
line 227120 is the one-argument check after `___DEF_SLBL(2,...)`, inside the
returned accessor closure; the factory's entry takes three arguments and
allocates the closure earlier in the same procedure region. Retained
`runtime/mop.ss:702` explicitly defines a curried factory returning this
accessor. The sampled 3,000,366 cycles at line 227120 therefore do not establish
removable closure construction. Neither the entire 5,000,584-cycle region nor
the class-predicate region is a justified factory-allocation budget.

Likewise, the three identifier-resolution lexical regions have weights
1,402,921 / 1,306,345 / 1,000,099 cycles. They exclude called hash/accessor work
and shared native lines; absence of a sampled `core-expand-head` region does
not mean its execution is free. These data do not supply a large exclusive
budget for guarded head-binding transfer. The live-predicate contract and its
408 original cases remain authoritative; the unguarded variant stays NO.

## Four-Question Decision

| Question | Decision |
| --- | --- |
| Correct path? | Reducing generic interface execution is aligned, but factory sharing is not justified by a lexical region containing factory and closure code. Live records and effects must remain fresh. |
| Already explored? | The underlying CPU recording and exact line mapping already exist. This follow-up only separates lexical source regions and catches the factory/closure attribution error; no denied experiment is rerun. |
| Worth implementing? | NO to a factory-cache, single-probe hash or guarded-head candidate from these weights alone. Import preparation versus required live construction still needs a reached removable-work argument. |
| Expected benefit? | No supported seconds or factor forecast. Saving all GC-hash ref self cycles would remove only 7.8144% of sampled active cycles, and a context-only single-probe operation cannot be assumed to cover all those calls. |

The next source work should identify avoidable operations in the actual import
construction graph, including caller-side syntax/accessor work, rather than
retune primitive loops or infer creation costs from procedure names. Independent
stdlib correctness and real MCP clean/build/full-test remain required for any
future Darwin-only GNU GCC candidate.

## Existing Capacity Policy: No Blind Preallocation Candidate

The retained `expander/module.ss:60` already initializes prelude-context tables
with `make-hash-table-eq size: (length in)` before binding their imports. Module
contexts and ordinary phi/local contexts use the default constructor instead.
Consequently "all interface contexts start at the default size" is a false
premise. The prelude size hint is physical capacity, not a guarantee that later
insertion will never resize.

`runtime/table.ss:500` selects loads `.45 / .6363961030678927 / .9`.
The default GC table receives size 16 (`:515-518`). Its resize path allocates
and rehashes a new table (`:554-559`); set retries only when the original
primitive requests it (`:578-585`). In Gambit `_system.scm:1595`, the desired
capacity is calculated from the live count and middle load, not unconditional
doubling. The loose-prime allocator can round that capacity. Do not invent a
geometric allocation bound or count every reference as a growing resize.

Reusing the existing `hash_layout.parse_tables` validator on the original V3
transcript gives 71 tables, 83,498 occupied keys and 116,463 physical key/value
slots, with maximum capacity 4,621 and aggregate occupancy 0.7169487305.
At eight-byte words, their array payload plus five metadata words per table
is **1,866,248 bytes**; object headers, wrapper objects and allocator rounding
are excluded. This is current live payload after normalization, not cumulative
allocation, peak heap, all phase tables, historical resize counts or measured
resize time. It cannot be subtracted from a different import-allocation batch
or used as an end-to-end speedup estimate.

| Question | Decision |
| --- | --- |
| Correct path? | A fresh-table capacity hint could preserve bindings, but mutating live table policy needs public wrapper, callback, key and GC contracts. Global enlargement has no demonstrated benefit here. |
| Already explored? | Prelude pre-sizing already exists upstream. This source review is distinct from the rejected bounded context lookup burst, which changed native miss traversal rather than table allocation. No burst is reconstructed. |
| Worth implementing? | ANALYZE ONLY for a specific measured growth boundary; NO to global size/load sweeps or blanket context preallocation from this snapshot. |
| Expected benefit? | Unknown: neither cumulative resize allocation nor exclusive CPU is recorded. Live payload and occupied-key counts do not justify a seconds-scale claim. |

Input identities for this follow-up:

| Input | SHA256 |
| --- | --- |
| `.data/d1510-stdlib-hash-layout-v3/0.log` | `ab92a3f7846d5df81bd9a907d40ea4f02eb54eea655103b435265177518c99ae` |
| `.data/d1510-stdlib-hash-layout-v3/report.json` | `6af0682bdb1e3ecf3d9eaca9a73d27f6967b7d881fe418d3aea7e4612ea25fc6` |
| Retained `expander/module.ss` | `f665ac12169cc60043eb467b203abc27cfc005ace09898cecd56d6aa492b9396` |
| Retained `runtime/table.ss` | `9c16a1878b6c820ce0ababde46dc181a61b4713d06857957177c60e828e267b1` |

Only offline validation and source reads were performed. No runtime/table
policy, performance gate, frozen object or consumer source was changed.
The existing `test_hash_layout.py` pytest checks pass **6/6**. An initial
unittest-discovery invocation found zero tests and exited 5; it is not counted
as validation. These parser checks are not Scheme or complete-test acceptance.

## Selective Import Index: Check Syntax Before Claiming Coverage

Retained `expander/module.ss:801-813` builds an equal-key export index for
`(spec: path . specs)` imports. This allocates composite `(phi . name)` keys
for every source export before selecting requested names. It is distinct from
the ordinary `import1` path at `:783-789`, which maps all exports into fresh
retained import records. Optimizing the selective index cannot eliminate that
ordinary mapping.

An original native Scheme reader parsed all top-level datums of the four
existing root interface files, recursively classifying `spec:` under
`%#import` versus `%#export`. No source was expanded, imported or rewritten.

| Root interface | Import forms | Export forms | Import spec forms | Export spec forms |
| --- | ---: | ---: | ---: | ---: |
| std/make | 1 | 1 | 0 | 13 |
| std/test | 1 | 1 | 0 | 0 |
| std/encoding/json | 1 | 1 | 0 | 0 |
| std/list/list | 1 | 1 | 0 | 0 |

The make interface's thirteen `spec:` forms are **exports**, not evidence
that it rebuilds the selective import index thirteen times. This audit is
limited to root files: dependencies, dynamic transformers and other phases
can still reach selective imports. It does not establish a zero whole-import
cost. NO to selecting this index rewrite as a major-gain implementation from
root syntax alone; there is no measured removable budget or seconds forecast.
The next execution investigation remains the ordinary fresh import-record
and binding construction path, not a package-specific selective-import fix.

Root file SHA256 values, under the retained build's `lib/` directory:

| File | SHA256 |
| --- | --- |
| std/make.ssi | `86bce94f12ca4ee46c7937c42fc86f6daad0f5cb4477830b26c9ceef863233f9` |
| std/test.ssi | `e745b33acbdf21c1009784e8c1815550b1b7b6cd7888f4deeff6e7f27d9412b7` |
| std/encoding/json.ssi | `c59acd623c99bc04589bb9604b2017df239101e1d179ee708b46f24be12589ab` |
| std/list/list.ssi | `d7b8207af2bb9a21d006639600de508977889bad1626ae8d7d73b455b62de7f4` |

All four reader invocations exited zero. No performance qualification,
production edit or new build/test campaign follows this source-only check.

## Import Construction And Callback Closure Budget

The next source review checks the ordinary path, not the selective index.
`core-bind-import!` resolves the current export, allocates a fresh import
binding and calls its live initializer before `core-bind!`. Existing original
contracts already prove those ordering and mutation boundaries; bypassing the
generic binding constructor is also already performed in generated code.
No repetition of that contract or a shared binding cache is justified.

One distinct operation exists in generated `core-bind!__%`: its first native
instruction allocates the four-capture `update-binding` closure, before key
substitution, phase shifting and the target-table lookup. `core-context-bind!`
uses this closure only if a binding is already present. A missing-key path
could theoretically avoid that private closure, but it must preserve live
context-bind replacement, key substitution, debug effects, hash interfaces
and all existing-binding callbacks. It cannot decide a miss before the live
import initializer runs. This is not permission to skip binding initialization.

The old D1296 physical-allocation recording was joined offline to its **exact
original source**, not to the current similarly named native file. Every
recorded site lies inside a generated procedure-switch region; all core
site bytes sum to the original 210,519,320-byte total. The only counted site
in `core-bind!__%` is original line 18876, `___ALLOC_CLO(4UL)`:
473,990 executions, **22,751,520 physical bytes**. It includes all counted
binding calls, not only imports or proven missing-key calls.

| Original core lexical region | Recorded physical bytes |
| --- | ---: |
| core-quote-syntax | 73,462,560 |
| core-apply-user-macro | 56,519,160 |
| core-expand-expression | 28,672,440 |
| core-bind! | 22,751,520 |
| core-expand-block | 15,498,944 |

The closure bytes are 1.3916% of the old recording's eight-unit
1,634,955,056-byte total. This is neither an elapsed-time fraction nor an
estimate against Gambit's process-statistics allocation metric. The sample
does not include expander/module's import-record/binding allocation sites;
the table therefore cannot establish their complete allocation budget.
These old, instrumented observations are not current frozen-host measurements.
The original core source hash differs from the current retained file, so a
line-number join against the latter would be invalid.

| Question | Decision |
| --- | --- |
| Correct direction? | Private callback materialization is a real operation, distinct from required fresh binding objects. It still needs missed-key eligibility and live callee guards. |
| Already explored? | Existing constructor/initializer contracts do not measure this callback allocation. This is an offline join of existing allocation evidence, not another constructor-fusion experiment. |
| Worth implementing now? | NO as the next major-gain candidate: the largest eligible byte saving is smaller than the counted total, with no exclusive CPU budget or current-profile coverage. |
| Expected benefit? | No supported seconds or factor. The 1.3916% byte share cannot be promoted to a speed forecast. |

Exact inputs: original core C SHA256
`f0436cf04a48cea28ed353c60c36fca9889836be76fef78d79fb6d23adb8c108`;
`.data/d1296-primitive-allocation-sites/mcp-counts.gerbil__expander__core.90337.tsv`
SHA256 `0877f62fe42062ae96b3acd04d75b8217388234c01e540f1f821c417ac59bd20`;
old report SHA256
`e0dae76b98535ae4c5a92322282de61a5b4568246472c1db24f7ce03ac568e54`.
No compiler, runtime or consumer was changed. No new performance campaign ran.

## Bounded Syntax-Length Hypothesis: Not Admitted

The new source hypothesis was narrower than the denied zero-suffix marked-tail
cursor: `expander/stxcase.ss:365-368` generates `(fx>= (stx-length target)
rlen)` for a nonzero suffix. A prefix predicate could avoid traversing an
entire long target just to establish that lower bound. It must not replace
the public length result or change hygiene, callbacks, or cyclic-input behavior.

The existing standard-library diagnostic now supports an optional length
observer and original source-module expansion. It delegates once to the
original procedure, excludes its explicit calibration from workload counters,
checks and restores the global procedure, and preserves four ordered phases.
No production helper or native candidate was implemented.

Three bounded waves used the unchanged frozen host, with four concurrent
jobs on the currently observed 12 physical cores:

- `.data/d1510-stdlib-length-budget-v1/`: original installed interfaces.
- `.data/d1510-stdlib-source-length-budget-v1/`: original source with observer.
- `.data/d1510-stdlib-source-length-control-v1/`: matched source without observer.

All twelve fresh processes completed their four phases, identity check and
final `OK`. These are import/expansion diagnostics, not standard-library test
suites or full clean/build/test qualification. The interface wave's inventories
match the existing original interface control exactly for all four modules.
Its observer has zero workload hits; that alone is not zero-cost evidence.

| Original source | Observed import calls | Returned length sum | Maximum length | Observed original-call wall sum |
| --- | ---: | ---: | ---: | ---: |
| std/make | 70 | 70 | 2 | 0.000025272 seconds |
| std/test | 0 | 0 | 0 | 0 |
| std/encoding/json | 0 | 0 | 0 | 0 |
| std/list/list | 51 | 67 | 2 | 0.000013590 seconds |

All other phases had zero observed calls. These clock sums are near the timer's
resolution, include observer measurement effects and are not CPU budgets or
whole-workload upper bounds. Counts cover reached global calls, not necessarily
every native internal call; they also do not distinguish the nonzero-suffix
guard from other length consumers. No long traversal is established here.

Matched source controls have exact export/native-module inventory parity for
all four modules, unchanged source hashes and unchanged binary identity.
Do not substitute an installed-interface inventory for that control:
`std/list/list` has 77 interface exports but 53 source exports in both source
runs. The 24 additional interface names end in generated `__%`, `__0` or `__@`
forms. This mismatch is retained; it is not evidence of an observer regression,
nor permission to normalize away exports in a candidate acceptance test.

The existing exact-source native-line sample also has no rows in carrier
lines 277890-277940, the lexical `gx#stx-length` region. This absence cannot
establish zero execution, missing caller work, or a complete current MCP budget.

| Question | Decision |
| --- | --- |
| Correct direction? | Avoiding unnecessary full traversals is generic execution reduction, but the measured source paths do not establish a costly long-target guard. |
| Already explored? | The nonzero-suffix length precheck is distinct from the closed zero-suffix cursor. Only diagnostic coverage was added; that cursor was not reopened. |
| Worth implementing now? | NO. The reached source calls have maximum length two; no independent-standard-library major-gain budget is demonstrated. |
| Expected benefit? | No supported seconds or factor forecast. Do not turn tiny observer clock sums or unobserved native paths into an end-to-end prediction. |

Focused diagnostic tests: **38 passed**. No new cold build or complete MCP test
was run, and no new speedup is claimed. Historical retained cold results remain
47.771713 / 47.824226 / 47.927094 seconds; historical first-compile results are
4.850866 / 4.573628 / 4.592897 seconds. The earlier full-test completion was
105.750982 seconds, but later unchanged-host strict 112-second runs were denied;
stable full-test acceptance remains open. The 5 / 50 / 112-second whole-task
gates were not relaxed. This hypothesis is not eligible for a production patch
or another complete performance campaign from the evidence above.

## Dynamic Binding Scope: Semantic Admission Boundary

Current command-path inspection reconfirms that retained `main.ss:207-221`
imports the selected tool's interface and evaluates its exported main.
The frozen HOME's `bin/gxtest` is a symlink to `gerbil`. A separate native
`gxtest` now exists in `.data/gxtest-next-ci-source/build/bin/`, but that HOME
has a different Gambit header/runtime lineage (its header selects multiple VMs).
It was not substituted into the frozen acceptance run. AOT construction,
direct native invocation and `gerbil test` command dispatch remain distinct
evidence. Neither the rejected external dispatcher nor the rejected runtime-only
interface bypass was reopened. No concurrent AOT/CI work was edited.

The subsequent source investigation examines **binding**, not the retained
parameter getter or the denied cache-promotion/shared-result proposals:

- `core/more-sugar.ss:70-79` recursively lowers Gerbil `parameterize` to nested
  `call-with-parameters` thunks. Later value expressions run inside prior scopes.
- `runtime/control.ss:31-38` delegates the single binding to `##parameterize1`.
- `_thread.scm:5636-5652` (one of the SMP/non-SMP source branches) runs a parameter's set filter before
  entering its new dynamic environment. Ordinary procedure parameters use
  `dynamic-wind`, including their before/after setter calls.
- `_thread.scm:5758-5791` creates a fresh parameter/value pair, copies the
  persistent environment insertion path and creates a new dynamic-environment
  vector for each ordinary binding.
- `_kernel.scm:1355-1376` installs/restores that environment and all three
  thread-local parameter cache slots around the thunk. Removing that restoration
  or mutating a shared saved environment is not an admissible batching scheme.

This is not the same expansion as Gambit's `##parameterize-build`: its generated
outer `let` at `_nonstd.scm:202-245` evaluates parameter/value expressions before
the nested calls. A Gambit-only source fixture therefore cannot establish the
Gerbil macro's later-value semantics. A source rewrite that hoists all Gerbil
value expressions would change behavior, even with ordinary identity-filtered
parameters.

`tests/parameter_binding_contract.ss` now tests the actual Gerbil macro through
the unchanged retained binary. The existing owned-process recorder executed
12 concurrent processes, matching this host's 12 physical cores. Each passed
17 checks, **204/204 total**, with exit zero and final
`PARAMETER-BINDING-OK 17`. The fixture covers later-value and later-filter
visibility, duplicate parameters, ordinary procedure setters/restoration,
exception and escape restoration, multiple values, inherited child-thread
state, continuation reentry and final original scope. This is focused original
semantic evidence, not a candidate speed result or complete std/MCP suite.

Receipt: `.data/d1510-parameter-binding-contract-v1/report.json`.
Fixture SHA256:
`0d750930ddbe98f0688951e0fedda2fc8be7ca26441a0a8c06319ba3e863050b`.
Frozen binary SHA256 remains
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.

| Question | Decision |
| --- | --- |
| Correct direction? | Fresh dynamic-scope construction is real generic execution/allocation, but observable value/filter ordering and continuation snapshots cannot be removed. |
| Already explored? | Scope batching is distinct from getter entry, cache promotion and activation-local getter result storage. Those closed implementations were not reused. |
| Worth implementing now? | ANALYZE ONLY. The 204 original checks reject blind hoisting/flattening; no reached count of safely fusible scopes or removable allocation budget exists yet. |
| Expected benefit? | No defensible seconds/factor. The existing `___H___thread` sample has 4,682,061 self cycles (0.866468%), but excludes kernel transitions, caller closures, allocation/GC and unobserved paths, so it is not a complete binding budget. |

Any future guarded scope transformation needs both a reached removable-work
budget and the same contract on a Darwin-only candidate before performance
acceptance. No binding optimization, ABI change, new toolchain compilation,
cold build or full test wave was performed in this investigation. The retained
historical three metrics and 5 / 50 / 112-second gates above remain unchanged;
full stable test acceptance is still open.

## Reached Binding Boundaries And Probe Sensitivity

The existing stdlib diagnostic's `--binding-budget` wraps the actual
`call-with-parameters__1` global. It delegates the original binding operation,
records the interval before its thunk starts and after its thunk finishes,
preserves multiple values, and verifies/restores the original global before
emitting the four phases. Started/entered/returned counts must agree before
normal boundary accounting is accepted. Nonlocal/reentered observations do not
become complete normal-return budgets merely because a process exits zero.

Two four-job waves used original source modules, the same frozen binary and
12-core hardware discovery, without changing any production runtime:
`.data/d1510-stdlib-source-binding-budget-v1/` and `...-v2/`.

| Source module | Reached calls, all four phases | v1 observed entry + return | v2 observed entry + return |
| --- | ---: | ---: | ---: |
| std/make | 16,108 | 0.021323 seconds | 0.032536 seconds |
| std/test | 2,619 | 0.004086 seconds | 0.004148 seconds |
| std/encoding/json | 12,985 | 0.521904 seconds | 0.022631 seconds |
| std/list/list | 7,895 | 0.023175 seconds | 0.026590 seconds |

These are interposed elapsed intervals, not exclusive CPU or uninstrumented
costs. They exclude the thunk's body interval but include filters, measurement
overhead, possible collection and scheduling. The large JSON difference is
probe sensitivity, **not** a runtime speedup or evidence that all the v1 time
is removable. No seconds/factor forecast follows from these two different
diagnostic methods.

v1 used four `##process-statistics` calls per binding and retained a negative
JSON eval entry-byte delta of **-2,009,912**. Its original JSON report remains
`qualified: false`; it was not overwritten. Offline review verifies the normal
return counts, final `OK` and source inventory separately from that invalid
physical-allocation inference. The parser now preserves signed raw deltas and
reports their nonnegative status instead of inventing a zero value.

Exact retained source explains the metric boundary:
`_kernel.scm:3999-4050` allocates a 20-element F64 statistics vector and places
`___bytes_allocated` in slot 7. `mem.c:359-369` includes stack occupancy in
`words_movable_objs` and `bytes_occupied`; `mem.c:7509-7523` recovers stack/heap
pointers and combines occupied bytes with the accumulated offset and still
objects. This is not a physical constructor-site allocation counter. The exact
cause of the particular negative interval was not isolated, so do not label it
a proven GC bug or subtract it as an allocation saving.

v2 uses the existing `##get-bytes-allocated!` primitive with one four-slot
snapshot vector per call, avoiding statistics-vector allocation and OS
statistics calls at every boundary. It still observes the same stack/heap/still
metric and adds its own closures/value handling. Its result keys explicitly say
`AllocationMetricDeltaBytes`, and `physicalAllocationBudgetQualified` is always
false. Nonnegative v2 samples do not make the metric a physical-byte budget.

All four v2 source runs have completed counts, final `OK`, unchanged source and
binary hashes, and exact export/native-module inventories matching their
original source controls. Installed-interface inventories are not substituted
for source controls. Both observer versions additionally ran the original
17-case Gerbil binding fixture in 12 concurrent processes: **204/204 value
checks passed per version**, including multiple values, exception/escape,
custom setters, threads and continuation reentry. These checks validate the
observed results, not every possible continuation inspection or a full test
suite. Latest focused parser/CLI tests: **46 passed**.

| Question | Decision |
| --- | --- |
| Correct direction? | Reached binding transitions are generic, but the thunk body and raw stack-sensitive byte metric cannot be counted as removable scope construction. |
| Already explored? | This is a reached scope-boundary diagnostic, not a new getter/cache/result-storage implementation. Those closed candidates remain closed. |
| Worth implementing now? | NO to scope batching from these data. There is no current physical allocation-site budget, safe-fusion count or supported major wall-time opportunity. |
| Expected benefit? | Unknown; do not promote v1/v2 differences or total binding counts to a speed prediction. |

No production candidate, compiler run, cold build or full MCP test wave was
launched. Historical first-compile 4.850866 / 4.573628 / 4.592897 seconds,
cold build 47.771713 / 47.824226 / 47.927094 seconds and the earlier complete
105.750982-second test remain historical anchors, not newly measured results.
The later strict test DENY and the 5 / 50 / 112-second whole-task gates remain
unchanged. Current full stable acceptance is incomplete.

## Original Thread Constructor Census

The earlier eight-unit D1296 physical allocation census explicitly preserved
`_thread.o` unchanged and did not count its constructor sites. The binding
observer's stack-sensitive byte metric cannot fill this coverage gap.

| Question | Decision |
| --- | --- |
| Correct direction? | Count actual generated thread heap advancement on independent stdlib roots before deciding whether dynamic binding is a major target. No package-specific transformation. |
| Already explored? | The old constructor census omitted this object. This extends its diagnostic coverage, not the rejected getter/cache or scope-batching implementations. |
| Worth doing? | YES to measuring constructor words; NO to changing dynamic-environment representation from an unqualified wall-time estimate. |
| Expected benefit? | Unknown. Constructor counts alone prove neither removable allocations nor package build/test seconds. |

`experiment.py runtime-io --candidate allocation-sites` rebuilt the unchanged
original thread object with its original GNU GCC command, including its `-O1`
policy. The control matches the archived original object byte for byte. The
private probe overrides only `___ALLOC`: evaluate its word count once, record
the original generated source line, then perform the original heap advancement.
Overflow and dump failures reject the diagnostic. Single-VM, single-threaded,
one-processor Darwin/GNU guards exclude unsupported shared counter execution.
Every other archive member is verified byte identical and ordered identically.

Object receipt: `.data/d1510-thread-physical-allocation-object-v1/report.json`.
The original archive and frozen baseline were not modified.

The first isolated relink failed sandbox hardware discovery. The second was
rejected by the whole-binary control hash: current Homebrew discovery emitted
OpenSSL `3.6.5` instead of the frozen executable's literal `3.6.4` RPATH. The
remaining byte differences were UUID/signature metadata. Neither difference
was normalized away. The framework now extracts validated ordered RPATH load
commands from the frozen executable and passes them explicitly with GNU GCC's
`-nodefaultrpaths`. The v3/v4 original controls reproduce the **whole frozen
binary hash exactly**. v4 also retains original candidate source identities in
the composed input hash graph. This is reproducible diagnostic linking, not a
production RPATH optimization or permission to substitute dependency versions.

Native receipt: `.data/d1510-thread-physical-allocation-native-v4/report.json`.
Diagnostic binary SHA-256:
`7f8ad9dbcb2a6484eebccd2f127596d3822e4d0fec5039cddf435f0bcb6f4ab7`.

Four independent source roots ran concurrently through the existing stdlib
fixture. Each completed import, eval, cached import, cached eval, context
identity and final `OK`; each export inventory matches its original source
control exactly. The v1/v2 raw workload receipts remain parser-denied because
the initial parser omitted nested constructor anchors. Original `gambit.h.in`
confirms that vector/structure allocation occurs at `END_ALLOC`, and closures,
continuations and boxed flonums invoke the same primitive through nested macros.
The corrected parser requires these explicit original anchors. No third workload
wave was run: the retained v2 TSVs were requalified offline with the unchanged
binary/source hashes, original exit codes and exact matched inventories.

| Source root | All counted thread words | Dynamic-let words | Env-insert words |
| --- | ---: | ---: | ---: |
| std/make | 953,616 | 274,104 | 238,812 |
| std/test | 420,631 | 106,140 | 120,344 |
| std/encoding/json | 1,176,791 | 270,612 | 273,764 |
| std/list/list | 593,762 | 166,764 | 157,920 |

Evidence: `.data/d1510-stdlib-thread-physical-v2/*/parsed-allocation.json`.
These are machine-word constructor counts, not `get-bytes-allocated` deltas.
They include startup, fixture and all four phases in the original process; no
per-phase subtraction, total-runtime coverage or removable-byte claim is made.
Other generated units and runtime allocation functions bypassing this object's
`___ALLOC` are excluded. Do not compare these totals directly to an unmatched
historical MCP allocation wave or treat probe wall times as A/B performance.

The 17-case original Gerbil binding fixture also passed on the diagnostic
binary in 12 concurrent processes: **204/204**, all exit zero and final markers.
Receipt: `.data/d1510-thread-physical-binding-contract-v1/report.json`.
Focused framework/parser tests: **85 passed**.

Source attribution correction: the single-VM header is not proof that the Scheme
generator selected the non-SMP source branch. The original make recipe's Scheme
generation prelude uses `enable-smp`. Both branches must be considered; the
actual retained generated C identifies dynamic-let at its `___PH_PROC` block
near line 10437 and env-insert near line 10635. The measured allocation sites,
not a guessed source feature branch, determine the table above.

The next optimization decision must establish which persistent path allocations
can be removed while preserving nested filters, continuation reentry and thread
inheritance, and measure their execution contribution. The 53.8% share of counted
thread words in the make root is **not** 53.8% of macro expansion or wall time.
No runtime optimization was admitted, no cold/full-test retry was used to select
a favorable result, and the historical 4.57-4.85 / 47.77-47.93 / 105.75-second
anchors and later strict 112-second test DENY remain unchanged.

## Persistent Path Copy And Writable Binding Cells

The retained generated env-insert body gives four distinct allocation sites:
10715 creates a leaf; 10727 copies an ancestor after left recursion; 10741
replaces an existing parameter's node; 10753 copies an ancestor after right
recursion. Each allocates a three-element vector, advancing the heap four
machine words. These original sites were joined to the already qualified raw
census; no new runtime workload or timing comparison was needed for the join.

| Root | New leaves | Existing-key replacement | Left ancestor copies | Right ancestor copies | Mean ancestor copies per insert |
| --- | ---: | ---: | ---: | ---: | ---: |
| std/make | 4,971 | 17,871 | 11,011 | 25,850 | 1.614 |
| std/test | 4,463 | 4,382 | 8,458 | 12,783 | 2.401 |
| std/encoding/json | 7,805 | 14,746 | 16,779 | 29,111 | 2.035 |
| std/list/list | 4,239 | 9,658 | 8,611 | 16,972 | 1.841 |

The terminal and ancestor counts are actual constructed nodes, not a claim
that these trees are balanced or that the mean bounds the maximum depth.
They establish actual traversal copying budgets in these original processes.
No observed value-equality, fusible-scope count or CPU-time ceiling follows
from the existing-key replacement column.

Source inspection establishes an important constraint: the tree nodes are
persistent, but their parameter/value pairs are **writable**. The original
`dynamic-set!` mutates the selected binding pair with `set-cdr!`; this operation
also appears in the retained generated C around 10382-10430. `_thread#.scm`
describes dynamic environments as attached to continuations/threads, and the
environment's other fields are mutable as well. Sharing an old binding merely
because the old and incoming values compare equal is therefore unsound: an
assignment inside the nested binding must not modify its outer binding.

The original Gerbil contract now includes equal-valued mutable binding and
nested equal-valued binding isolation/restoration. All **21 assertions passed
in 12 concurrent original frozen processes: 252/252**, exit zero and exact
final markers. Receipt: `.data/d1510-equal-binding-contract-v1/report.json`.
Fixture SHA-256:
`d71a40fb02d187db9f09f2cafb0f5cda36e83f5a79463061134a43eb8f281ea4`.
The earlier 17-case fixture hashes/results remain historical; they are not
silently relabeled as this stronger 21-case inventory.

| Question | Decision |
| --- | --- |
| Correct direction? | Persistent path allocation is real; public writable binding isolation must be preserved. |
| Already explored? | This join and equal-valued assignment contract add evidence without rerunning closed caches or scope batching. |
| Worth implementing? | NO to blanket equal-value binding elision or pair reuse. A different ownership/escape analysis needs a new eligibility budget and full continuation/thread contract before implementation. |
| Expected benefit? | No supported wall-time prediction. Even eliminating ancestor copies hypothetically is not eliminating dynamic-let, all thread allocation or all expansion. |

No production code, toolchain, cold build, MCP full-test or performance limit
changed in this investigation. The retained binary/archive hashes are still
the frozen ones. The three historical metrics and the incomplete stable
112-second full-test gate remain explicit, not substituted with 252 component
assertions.

## Current Carrier Census Construction: Not Qualified

The old eight-unit constructor census cannot be joined blindly to current
carrier lines or promoted to a current-profile exclusive allocation budget.
The current common host contains the relevant runtime, core and syntax code,
so the constructor diagnostic was extended to that exact generated source.

| Question | Decision |
| --- | --- |
| Correct direction? | Measure actual current common-host constructor work before proposing an intermediate-elimination transformation. |
| Already explored? | The original carrier source/object parity and old allocation census exist, but not the current common-host word census. Reuse the diagnostic framework; do not rerun rejected factory-cache, hash-probe or modulo-removal candidates. |
| Worth doing? | A diagnostic coverage extension only; source lexical weights still do not establish removable factories. |
| Expected benefit? | Unknown until the probe is qualified; no package seconds or speedup forecast. |

`compiler-frame --allocation-sites` now validates an unchanged original
control object before building a private counter object. It excludes debug
sidecar and shared-parameter-result transformations and disables bulky frame
and RTL dump artifacts. The stdlib runner accepts a content-locked original
allocation source, while retaining completed native-composition and binary
identity checks. Lexical summaries now explicitly require procedure switch
body coverage instead of assigning an outside-body line to the preceding
procedure.

The first construction used original GNU GCC 16, original `-O1` and retained
source `.data/d1510-carrier-control-source-parity-v2/gerbil-link.c` with frozen
reference `.data/d1510-source-loader-linked/gerbil-link.o`. The original
control compilation reached its **300-second diagnostic deadline**, was
terminated/reaped, and the controller exited one. No control object was
produced; no probe was compiled, linked or executed. This is a construction
failure, not a measured MCP cold build or rejection of an optimized runtime.
The raw `completed=false` receipt does not contain a stopReason field because
that controller was loaded before the new explicit timeout handler. Preserve
the raw report rather than backfilling it with fields it did not emit.

Evidence: `.data/d1510-carrier-allocation-object-v1/report.json` and its empty
control compiler log. No retry, extended deadline or performance admission.
The earlier byte-identical carrier/object evidence is not erased, but it does
not turn this unfinished diagnostic construction into a qualified probe.

The accompanying regression run recorded **77 passed / 1 failed**: the
parent-exit cleanup test observed a parent killed by the deadline instead of
having already exited. Its fixture did not establish the scenario named by
the test. The fixture now waits for actual normal parent termination before
returning its Popen handle; the descendant still holds stdout, and the same
0.3-second whole-operation deadline must kill/reap that process group. No
production executor or deadline was changed. The first failed run remains
negative evidence, not a pass obtained by widening a timeout. The full focused
regression after this precondition correction passes **86 tests**.

No frozen binary/archive, production patch, std/make, std/test, MCP source,
consumer assertions or 5/50/112 gate changed. Stable full-test qualification
remains open; historical 47.77-47.93-second cold builds are not replaced by
diagnostic compiler time. The next action must not repeat this unchanged large
control build merely hoping for a faster completion.
