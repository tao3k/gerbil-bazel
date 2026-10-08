# D1510 Native Procedure Budget Boundary

Read-only follow-up, not an optimization admission. No new workload, runtime
candidate, compiler invocation or performance baseline was produced. Retain
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
