# D1613: widen actual builder CPU capture without weakening product gates

The preceding turn made progress with a verified actual builder capture and
exact current carrier mapping, but hardware samples covered only 0.402 seconds.
This turn closes that sampling gap, not the acceleration objective.

## Diagnostic Entry Gate

The installed xctrace CLI documents --notify-tracing-started, a Darwin
notification sent when recording has started. An isolated diagnostic dependency
pauses only the own gxi child in its constructor when an explicit private gate
path is supplied. The outer Gerbil process, GSC and normal invocations are not
paused. Original D1590 carrier/registry/317 objects, static objects and RTS remain.
The dependency is Darwin/GNU/non-Clang guarded; no product binary is replaced.

The controller registers a unique notification before attachment, checks actual
child parentage and libproc-resolved executable SHA, then resumes that PID only
after the start notification. Paused time remains counted in the unchanged
ten-second real-output and thirty-second prefix budgets. Cleanup sends CONT
before TERM and reaps owned groups, so a failed observer cannot leave a stopped
builder behind. No synthetic product progress or deadline extension is used.

D1610's initial notification control fails before compilation or workload
execution because notify delivery is asynchronous. D1611 waits for the actual
control event within a separate bounded two-second API check; this is not a
product-output grace period. The control passes, then compile/link and actual
MCP clean succeed with zero project native images. Subsequent driver hardening
also tolerates an incompletely published marker and verifies stopped state;
the original successful D1611 report is not rewritten to claim that later check.

Staging is freshly checked and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. Original MCP head, Bazel GNU GCC
environment and twelve physical workers remain. No consumer or installed
toolchain source changes.

## Real Startup And Wider Hardware Data

| Diagnostic boundary | Time from build launch |
| --- | ---: |
| Verified builder attachment requested | 0.911185 s |
| Profiler-start notification, then CONT | 4.123610 s |
| Literal first compilation | 8.630974 s |

The output gate passes, but the entry pause and profiling perturb the execution.
Do not subtract the pause to manufacture an uninstrumented speed result.
The build deliberately stops/reaps with exit 70 after first compilation; this
is not a complete build, nor a pass of the 55-second performance ceiling.

The sampler succeeds and exports 11,435 Running rows with 10,062,163,921 active
cycle weights. Native UUID/function-start/SHA checks validate 10,026,639,359
cycles, with 154,587 additional non-function native-section cycles. Actual row
timestamps span 4.506716 seconds, versus the previous 0.401846-second burst.
This covers execution after the entry resume through the first-line termination
region. It excludes outer-process work, pre-constructor dyld work and does not
pretend to provide a perfectly instantaneous first-line sample cutoff.

| Function | Share of all captured active cycles |
| --- | ---: |
| coalesced Scheme host | 33.55% |
| mark_array | 16.24% |
| mark_array constprop clone | 12.42% |
| GC hash lookup | 5.24% |
| existing context helper 11 | 4.39% |
| movable-object scan | 3.18% |
| garbage_collect_pstate | 2.57% |

The wider result supports the existing GC-only ceiling rather than promoting
the prior short burst's much higher GC fraction to whole-prefix evidence.
Counts, wall times and CPU cycle shares remain separate observations.

## Reuse Current Exact DWARF Proof

D1612 reuses D1608's current debug object only after checking its complete text,
symbolic relocation, original object and generated source identities again.
The executed diagnostic image UUID/SHA and actual function start are checked.
All 1,151 coalesced-host PCs map, with zero unmapped cycles and exact agreement
between per-PC weights and function self-cycle totals. No debug recompilation
or nearest-label attribution is used.

| C macro category | Share within host, not whole CPU |
| --- | ---: |
| IF | 21.61% |
| arity equality | 13.90% |
| shared END_M_HLBL | 10.25% |
| POLL | 8.84% |
| JUMPRET | 7.51% |

For example, arity checks are only about 4.66% of all captured cycles, and
JUMPRET about 2.52%. These categories include many procedures and compiler
assigned shared lines, not one removable operation. Do not repeat rejected
return outlining, entry tuning, hash scans or GC variants as a several-fold
solution. A new source optimization must demonstrate substantial eliminated
executed work across this wider distribution, preserve polls/GC/rebinding and
escaping identity, then pass real first-log, <=55-second full build and tests.

Private evidence: `.data/d1610-gated-first-cpu/` (pre-workload API failure),
`.data/d1611-gated-first-cpu/`, `.data/d1612-gated-host-lines/` and their private
source scripts. Twelve existing CPU-provenance tests pass. No real test suite
or complete toolchain is newly qualified. All owned sessions are terminal.
No production optimization, release patch, commit, push or completion claim.
The goal remains active.
