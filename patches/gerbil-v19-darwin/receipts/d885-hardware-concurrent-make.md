# D885: hardware-sized concurrent startup and std/make tests

Date: 2026-10-03. This adds a real concurrent build/test baseline using the
D884 binary. It admits no new performance patch.

## Hardware and Concurrency

Live hardware discovery reports model `Mac14,10`, 12 physical CPUs,
12 logical CPUs and 32 GiB memory. The runner selects `os.cpu_count()`;
on this machine it sets `GERBIL_BUILD_CORES=12` and passes `parallelize: 12`
to `std/make`. The previous two-job full-toolchain setting is not reused.

Startup uses two bursts of twelve independent processes per scenario:
runtime readiness and readiness after importing `:std/make` and `:std/test`.
Each burst has verified process-lifetime overlap. A pipe reader timestamps
the ready line directly; timing is not rounded to the process polling period.
The concurrent workload uses the newly built source-local toolchain and the
existing Bazel SDK/dependency environment, with real GNU GCC 16 guarded by
predefined macros. Its package root and generated sources stay under `.data`.

## Real Build/Test Contract

The Gerbil entry imports `:std/make` and `:std/test`. Fourteen modules include
thirteen independent leaves and one dependent join; each leaf expands a
macro into 64 functions using the actual standard iterator library.

All three `std/test` cases pass:

- Cold build: real native module outputs exist and the imported function
  returns the expected result.
- Warm no-op: no compile log/jobs and no native timestamp changes.
- Source-mtime invalidation: the changed leaf and dependent join are
  scheduled, their SSI/static-source timestamps advance, and unrelated
  modules retain both dependency and native timestamps.

The dependency checks follow upstream `std/make-test.ss`. Identical source
rewrites need not change a dependent linker object's timestamp; that is not
evidence that invalidation failed. Native output existence is still required.
The runner observes **12 simultaneous GNU GCC cc1 processes**, not merely
twelve configured workers. Final `D885-OK`, three `CASE-OK` markers and process
exit zero are required.

## Observations, Not Speedup Admission

Final output: `.data/d885-hardware-concurrent-make-v5/`.
Report: `report.json`; native/GCC/test output: `parallel-make.log`.
Gerbil staging: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

| Measurement | Observed Seconds |
| --- | ---: |
| Runtime-ready median, 24 concurrent launches | 0.352 |
| Make/test import-ready median, 24 concurrent launches | 1.178 |
| Cold parallel build | 14.113 |
| Same-process warm no-op | 0.007724 |
| Dependency invalidation build | 1.926 |

Startup scenarios are separate bursts, not paired subtraction or an A/B
optimization experiment. Peak GCC concurrency is a sampled lower bound.
Representative intact GCC time-report rows show parsing around 10 percent
and optimization/code generation around 89-90 percent. Reports from parallel
children can interleave; no per-module attribution or aggregate share is
claimed. GGC allocation is not peak resident memory.

Host load starts at approximately 14.55/15.31/17.52 and ends at
18.52/16.22/17.78, exceeding the 12-CPU performance gate. Therefore
`qualified: true` means the concurrent functional contract passed;
`performanceQualified: false` remains explicit. These observations neither
prove a new speedup nor establish a macOS/Linux differential root cause.

The harness separates next-candidate evaluation into startup/import cost
versus cold native compilation. Same-process no-op is already very small;
optimizing that path alone cannot establish a cold-build improvement. Existing
Reflection conclusions and rejected batching/Jumps/flag experiments remain
in force. No toolchain source optimization is promoted by this receipt.

Earlier directories preserve test-entry mistakes (module import syntax and
the overly strict native-linker timestamp assumption), not valid performance
comparisons. The final run uses a fresh root and unchanged expected results.

Replay from the project root:

```sh
python3 patches/gerbil-v19-darwin/tests/run_concurrent_make.py \
  --source .data/d884-patched-staging/source \
  --output .data/NEW_HARDWARE_CONCURRENT_RUN \
  --repeats 2
```
