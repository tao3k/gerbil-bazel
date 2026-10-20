# D1483: hashed-order SIMD probe bursts rejected

## Scope and source mechanism

D1172 established that the prior eight-slot full-table scan never executes
in the actual MCP preparation; about 73 percent of reads use 9-32-slot tables.
This experiment does not enlarge that full-scan limit. It changes only
Gambit's existing C hash-table read loop, preserving the initial hash position,
descending linear probe order, wraparound, and first key/UNUSED termination.

After the original primary-slot check and original lazy rehash, a four-slot
burst is allowed only when step2 equals two and all four slots fit before the
table's lower boundary. Ordinary keys and empty markers are compared in
parallel, then the earliest match in the original descending order is chosen.
If all four miss, the original cursor advances past exactly those four slots.
Boundary crossings, reserved query keys and unsupported configurations retain
the scalar path. Setters, allocation, table layout, weak-table processing,
hash mixing, GC and Scheme sources remain unchanged. No lookup-result cache
or mutation/rehash fence relaxation is introduced.

The gate requires Darwin, genuine GNU/non-Clang, AArch64, single VM,
single-threaded VM, one processor, eight-byte words, the existing ordinary
subtyped-body layout and no handles. The intrinsic operations use the
[Arm Neon interface](https://arm-software.github.io/acle/neon_intrinsics/).
This is not evidence that SIMD or hash probing explains the Darwin/Linux gap.

## Native construction and controls

Inputs remain Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, and common home
`.data/d1391-runtime-object-source/build`. GNU GCC 16 and 12 physical workers
come from the existing Bazel environment. Only private mem.o and its copied
RTS archive are replaced; all Gerbil objects and consumer GSC are retained.
The original mem.c/mem.o/archive/GSC hashes remain unchanged.

Original official mem.o compilation options are obtained from its Make rule.
Native preprocessing confirms the burst gate is enabled. Mem compilation,
archive replacement/indexing, native linkage and std/make/std/test/build-script
imports pass. Uninstrumented candidate binary SHA-256:
`a06f0877eec56b93cb8f098731d835c096b217e7d0577234a966f8d8b91f8215`.

Two native differential controls pass:

- 200,000 four-slot arrangements compare SIMD termination against a scalar
  descending scan, including key/UNUSED ordering and deleted slots.
- 512,000 complete-table reads compare the candidate to the exact unchanged
  original scalar function body, compiled alongside it for this control only.
  Capacities are 3, 5, 9, 11, 17, 31, 32 and 127; cases include wraparound,
  hit, miss, deletion, false values and reserved query keys.

The second control uses synthetic native table representations and no moving
GC or weak finalizers. It is not complete collector/weak-table conformance.
The original scalar clone is absent from the performance binary.

## Actual MCP first-log ABBA

Each of four independent unchanged MCP fixtures at
`9a5c35e275e5d6847ff421151bb224f2eae177c1` underwent official clean, with
zero native images afterward. Builds were deliberately stopped after the
literal `... compile util/compat` line. Original ten-second output and
thirty-second first-window gates were kept.

| Role | First compile seconds |
| --- | ---: |
| Baseline | 6.065616 |
| Candidate | 6.189523 |
| Candidate | 6.028603 |
| Baseline | 6.307385 |

Means: 6.186500 versus 6.109063 seconds, about 1.25 percent. Ranges overlap.
No major or stable startup win is admitted. The terminal build status 70 is
the intentional first-line stop; these are not completed build receipts.

## Actual executed coverage and added reads

D1480 is a separately compiled counted binary, never a timing control.
D1481 runs actual clean and first-log build with that binary. Its counters
also include outer CLI execution, clean and termination cleanup; they do not
measure the exclusive prefix or CPU shares.

Across the four completed process records there are 34,928,221 read entries
and 23,156,541 selected bursts. The largest gxi record alone has 31,409,493
reads, including 22,923,556 in the 9-32-slot capacity bucket, and 13,596,288
bursts. These are actual execution counts, not inference from preprocessing
or a toy fixture.

That gxi record's bursts read 54,385,152 physical key slots while original
early termination requires 41,786,505 logical burst slots: about 30.15 percent
extra key-slot reading within the selected bursts. Values are interleaved and
also physically loaded. This measures added work; it does not independently
prove instruction latency or explain the observed wall result.

The D1480 scalarSlots hook accidentally matches a nested result-load statement
before the intended original scalar-loop statement. It does not cover every
fallback read and includes repeated match-result loads. Do not use scalarSlots
to derive total original probe visits. Calls, capacity buckets, burst counts
and logicalBurstSlots use independent hooks and remain admitted by their
invariants. The private generator now matches the full original line exactly
for future builds; the retained D1480 binary and raw counters are not rewritten
or silently promoted to the corrected generator's coverage.

## Actual concurrent tests and independent repetition

D1479 and D1482 each run four ABBA waves of twelve real
`gerbil test -v 5 test/unit/regex-test.ss` processes. Every process returns
exactly 19 CASE-OK records, final OK, unchanged source hashes and exit zero:
96 processes and 1,824 cases total. Five-second real-output and 90-second
total gates are unchanged. These are the regex suite using prebuilt project
libraries, not the full MCP suite or OS-cache-cold testing.

| Run | Baseline mean completion | Candidate mean completion |
| --- | ---: | ---: |
| D1479 | 2.151408 s | 1.949591 s |
| D1482 independent repeat | 1.969741 s | 2.048218 s |

D1479 overlaps this agent's native differential compilation and is not
admitted as an isolated timing comparison. D1482 starts after all local
construction/diagnostic jobs end. Its candidate is about 3.98 percent slower.
The initially lower test mean does not survive independent repetition; no
stable test acceleration is admitted.

## Decision and durable evidence

Reject four-slot SIMD bursting as the requested first-log/test accelerator.
The new path reaches real workloads, but coverage is not sufficient evidence
of acceleration, and batching adds reads past original termination. Do not
freeze this candidate, increase its burst width, or claim a full toolchain
qualification. No production profile, consumer/std source or installed
toolchain changes. Existing spawn/object-reuse/preprocessing gains remain.
The major startup/native-test objective is still active and unachieved.

Private sources and receipts:

- `.data/d1476-hash-burst.h`, `.data/d1476-hash-burst-control.c`
- `.data/d1476-hash-burst-runtime.py`
- `.data/d1476-hash-burst-runtime/report.json`
- `.data/d1477-hash-burst-first/report.json`
- `.data/d1478-hash-full-probe-control.py`
- `.data/d1478-hash-full-probe-control/report.json`
- `.data/d1479-hash-burst-real-tests/report.json`
- `.data/d1480-hash-burst-counted-runtime/report.json`
- `.data/d1481-hash-burst-counts/report.json`
- `.data/d1482-hash-burst-real-tests-repeat/report.json`
