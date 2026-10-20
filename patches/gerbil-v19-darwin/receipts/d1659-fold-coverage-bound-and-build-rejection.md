# D1659: fold coverage bound rejects another narrow optimization

## Identity And Completed Build

The canonical origin's actual branch `v0.19-staging` is freshly queried and
remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`. Queries using the incorrect
branch name `staging` return no reference and are not identity confirmation.
The same GNU GCC 16/Bazel environment, original MCP head, common D1391 GSC/RTS,
object-reuse configuration and twelve physical workers remain selected.

D1649 initially prefers constructor-self-recognition for both extents, selecting
states 16/41 instead of 3/35. D1652 real first-write counters show zero hits for
all eight clauses. This rejects changing the previously hit single-wrapper
selection. The preliminary D1648 construction fails during sandbox hardware
discovery before compiling; it is not a benchmark.

D1653 therefore retains single-wrapper state 3 and changes only the
two-wrapper selection to state 41. Candidate SHA256 is
`59fa53330353382afeddef35e55cdcd0711aa07b5d57b1556af0b0af2a8112b6`.
Construction and framework imports succeed. D1654 then completes an actual
uninstrumented, fresh-project MCP clean/build:

| Measurement | Seconds |
| --- | ---: |
| Clean | 2.993890 |
| First literal compile | 5.497921 |
| Complete build | 63.367271 |

Clean/build exit zero, native images after clean are zero, checked source hashes
are unchanged, and the executable is produced. The unchanged 55-second gate
fails. The historical D1513 52.617045-second candidate mean is not replaced.
There is no matched causal speed ratio or admission of startup success.

## Real Concurrent Contracts

D1655 passes twelve native starts and twelve make/test imports, followed by
real std/make cold/noop/invalidation builds and std/test assertions, including
final SUITE-OK and D885-OK. Cold/noop/invalidation phases are
12.272269/0.016694/1.782147 seconds. Fixture wall time is 15.641505 seconds;
maximum genuine output gap is 3.203247 seconds under the original five-second
gate, with eleven peak observed GCC frontends. These are candidate-only
workflow controls, not evidence of a test acceleration or full MCP test suite.

## Actual Failure Location

D1656 adds counters immediately before each existing guard without changing
its predicate or target. Fragmented-line/dual-fd controls pass. D1657 samples
the actual builder child PID 30434 and freezes counts at the successful first
compile write. Diagnostic binary SHA256 is
`a4e08568a3eff3eb98b81da6723ce0b8ea4df29fa48a3fd0195bb5d2de58baab`.
The first compile is 5.776900 seconds, followed by deliberate exit 70; it is not
a completed-build or uninstrumented performance result.

| Consumer | Single-wrapper successes | Entries reaching provider guard | Remaining two-wrapper entries reaching input-type guard |
| --- | ---: | ---: | ---: |
| core-expand1 | 678180 | 683704 | 5524 |
| core-expand-head | 680426 | 685953 | 5523 |

All 5524/5523 residual entries exit the guard requiring the input not to be a
wrapping object. None reaches the descriptor guard changed by this experiment.
Thus that real miss is input-shape coverage, not the later descriptor condition.
The single-wrapper clauses already succeed on 99.193156% of these observed
provider-guard entries; the difference is 11051 entries, including four that
do not reach the residual input-type guard. This is a coverage ratio within
these two consumers and heap-eligible observations, not whole-program CPU or
allocation coverage. It cannot prove a time bound for rare expensive paths.

## Analysis Scope And Decision

The default trace path limit stays 64. An explicit bounded analysis option
permits up to 1024 without changing statement, work, frame, allocation or poll
limits. D1658 requests 256 and obtains 136 completed/lowerable states per
consumer, 544 total. Some already-wrapped branches existed in the earlier 64;
others were beyond that cap. Therefore the cap alone is not the cause: choosing
one representative per heap extent also discards input-shape alternatives.
This remains a bounded audit, not exhaustive path or native qualification.
All 152 focused Gambit experiment tests pass with default-path parity controls.

Keep this as a negative coverage/performance result. Do not promote the ranking
heuristic or expand these two consumers as the promised major startup fix.
The next optimization must cover substantially more actual Scheme execution
or GC work, while preserving the existing object-reuse benefit and 55-second
complete-build ceiling. Runtime semantic guards, rebinding, continuation and
GC/poll fallback remain mandatory; no std/make/std/test or consumer edit occurs.

Private raw evidence is under `.data/d1649-self-typed-projected-fold/`,
`.data/d1650-self-typed-census-native/`, `.data/d1652-self-typed-first-census/`,
`.data/d1653-preserved-single-self-typed-fold/`,
`.data/d1654-preserved-single-real-mcp/`,
`.data/d1655-preserved-single-concurrent-make/`,
`.data/d1656-projected-fold-guard-census-native/`,
`.data/d1657-projected-fold-guard-first-census/`, and
`.data/d1658-expanded-fold-region-audit/`.

All owned sessions are terminal. No product backend integration, complete
toolchain rebuild, installation, commit, push or optimization completion is
claimed. The original goal remains active.
