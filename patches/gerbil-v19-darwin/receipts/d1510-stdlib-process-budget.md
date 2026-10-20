# D1510 Original Standard-Library Process Budget

Diagnostic only. No candidate, speedup, production patch or new cold/test
baseline is admitted. Preserve the historical 47.771713 / 47.824226 /
47.927094-second cold anchor and whole-task 5 / 50 / 112-second gates.
The strict full-test DENY remains unresolved.

## Reached Original Execution

`run_stdlib_import_cost.py --process-budget` launches three fresh processes
for each of make, test, encoding/json and list/list. It uses the frozen
reader-whitespace host and selected runtime home, an empty package home and
no callback observers or evaluator replacement. No consumer package is used.
The original import, evaluation and cached-context identity checks still run.

The optional fixture samples `##process-statistics` immediately before and
after each original phase, before printing that phase's diagnostics. The
retained `_kernel.scm:3999` defines the sampled fields: process user/system/
real time, cumulative GC time and count, allocation count, VM faults and
latest-GC heap/allocation/live snapshots. The parser subtracts cumulative
fields only. Latest-GC fields remain snapshots, explicitly classified as
from this phase only when its collection delta is positive.

Statistics calls and timer evaluation have small nonzero costs; allocation
deltas include measurement allocations. The observations are not exact
application-only allocation counts. Phase CPU is process user plus system
CPU; GC CPU is its separately reported user plus system CPU, not wall time.
Latest-GC snapshots are not survival ratios or a per-collection history.
Fault counters come from `getrusage` in `os_setup.c:552`; no fault count is
interpreted as physical disk I/O or a causal Darwin loader diagnosis.

| Root library | Import CPU seconds, three runs | GC fraction of import CPU | Import allocation delta, approximate MB |
| --- | --- | --- | --- |
| make | 0.156508 / 0.175678 / 0.167112 | 19.22-20.47% | 116.95 |
| test | 0.152289 / 0.118740 / 0.129921 | 12.87-16.76% | 88.91 |
| encoding/json | 0.525462 / 0.511400 / 0.509659 | 10.27-11.71% | 231.42 |
| list/list | 0.109637 / 0.115397 / 0.094665 | 15.24-17.94% | 81.19 |

Original root evaluation has no GC during these twelve observations. This
does not exclude GC in different phases/workloads. The JSON import system
CPU component is about 0.18-0.20 seconds; it cannot be assigned to dyld, file
digest, allocator faults or scheduling from these counters alone.

## Decision And Evidence

All twelve processes exit zero with final OK and cached-context identity.
Each export/native-module inventory matches the corresponding original
Gambit split control. The binary SHA remains
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Selected parser regression tests: 26 passed. All child processes are terminal.
No cold build or full test is rerun from an unchanged candidate.

The data does not justify a new copying-marker micro-optimization as a
several-fold import fix: even elimination of this measured GC CPU would not
remove most import CPU. A generational collector would additionally require
mutation barriers and roots, not just a copying loop replacement. Existing
barrier, heap-floor and marker negative results remain closed. Allocation
avoidance can also reduce non-GC construction work, but has no admitted
candidate here and must preserve fresh context/binding isolation.

The next distinct target is the reached non-GC import execution, including
the material system-CPU component. Any native I/O/loading attribution must
measure original reached operations rather than assume that all system CPU
belongs to Mach-O. The current embedded-provider backend already calls
CommonCrypto SHA256; switching to that library is not an unimplemented win.
Removing its content-identity check or mapping mutable files unsafely is not
an eligible optimization.

Evidence: `.data/d1510-stdlib-process-budget-v2/report.json`, SHA256
`e95584c416b3e2005ae2c92607c2ff1d0a3e9456d9a27fcc7cef5fcc25b71bd1`.
Inventory comparison: `.data/d1510-stdlib-gambit-eval-split-control-v1/report.json`.
The v1 attempt fails sandboxed hardware discovery before any Scheme launch;
it is not a runtime failure or timing observation.

## Research Selection Correction

The subsequent Darwin page-dirty/generational-collector idea is not selected
for a prototype. This is an admission decision, not an executed negative
result for generational GC. The measured GC CPU share above is only about
10-20%; removing all of that measured CPU would yield roughly 1.11-1.26x on
these imports, not a several-fold startup improvement. This is an ideal CPU
bound for these observations, not a wall-time or whole-build prediction.

The [BDWGC porting directions](https://hboehm.info/gc/porting.html) describe
write-protection-based dirty-page tracking as support for incremental and
generational collection. They do not establish a Darwin cost diagnosis for
Gambit. The [BDWGC algorithm overview](https://hboehm.info/gc/gcdescr.html)
describes a mark-sweep collector; its dirty-page mechanism is not a drop-in
replacement for Gambit's moving collection. In the retained mem.c,
fromspace_offset exchanges section halves, and msection allocation requests
word-aligned heap storage, not exclusively owned VM pages. Page protection
alone therefore neither establishes a persistent old generation nor permits
skipping pointer relocation. No protection, allocator or signal change is
made. A future collector redesign would require a separately established
cost budget and complete ownership, mutation and relocation contracts.

The selection failure is broader than this idea: instruction counts,
allocation counts and high-frequency sampled functions identify reached work,
but do not establish a large exclusive elapsed budget. The later hash-cold-tail
candidate removed common-path frame instructions and passed focused controls,
then failed the actual first-compile gate. It is rejected, not an admitted
optimization. Further flag audits and unchanged MCP runs cannot substitute
for a new reduction in reached work.

The next candidate selection stays with non-GC import preparation, expansion
and evaluation in the independent standard-library dependency chain. It must
name the original execution being removed, its measured budget and required
freshness/effects before construction. Rebinding, initializer calls and
context isolation cannot be bypassed to obtain a faster sample. MCP remains
an end-to-end qualification workload, never an implementation special case.
Use the existing shared framework; add no standalone diagnostic script for
this correction. Construction and focused correctness checks are not speedup
admission. An eligible candidate must then pass independent library checks
and actual clean/build/full-test gates, with all three timings printed beside
the retained historical measurements. A gate failure terminates the owned
process group, leaves incomplete durations null and skips subsequent phases;
it does not by itself prove causal attribution to the source change.
