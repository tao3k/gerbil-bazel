# D1420: actual first-window process-family CPU boundary

## Purpose

D1375's original profiler covers only part of the official first-log interval.
Running-cycle percentages cannot alone establish the full wall-time balance.
This diagnostic fills that accounting gap, not a new optimization baseline
campaign and not a Linux comparison prerequisite.

The canonical remote `v0.19-staging` was rechecked live and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. The common isolated toolchain is
`.data/d1391-runtime-object-source/build`; Gerbil binary SHA-256 is
`a398d0b2e3200019a1542a0fea8b101062a76118f82dcba30f580b481a608e5a`.
It includes the qualified existing object-reuse candidate, not pristine upstream.

## Measurement

A fresh independent clone of the original MCP fixture ran real `gerbil clean`
and `gerbil build` with 12 hardware-derived workers and the Bazel environment.
Clean returned zero and left zero project native images. No Scheme source,
Gambit source, compiler flags, installed library, or executable was changed.

The observer reads only the owned process tree through Darwin libproc. It
retains 275 snapshots, including the cumulative counters immediately after
reading the literal first compile line and before sending any stop signal.
The final read lag is 0.388 milliseconds. Both observed Gerbil processes remain
alive at this boundary. CPU of short-lived, already-reaped descendants is
accounted through child counters; no observed live descendant is counted twice.

| Quantity | Seconds |
| --- | ---: |
| First `... compile util/compat` | 5.994397 |
| Process-family user CPU | 5.405883 |
| Process-family kernel CPU | 0.541036 |
| Process-family total CPU | 5.946919 |
| Observer CPU, separate from product | 0.041388 |
| Parent Gerbil self user CPU | 0.961145 |
| Build-script Gerbil self user CPU | 4.440653 |

The build child was born approximately 1.176816 seconds after the parent.
No post-stop cleanup time contributes to these CPU values. The build was
deliberately stopped at the first line; this is not a full build/test receipt.
Sampling and boundary read lag can perturb observations, so this is diagnostic
accounting, not an uninstrumented timing win or exclusive per-function profile.

## Retained failures and unit admission

D1417 stopped at a child-inventory unit check. Apple libproc's
[implementation](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)
returns PID counts from `proc_listchildpids`, not bytes. Its failed receipt is
retained; it contains no admitted first-log measurement.

D1418 reached the actual boundary and retained complete raw snapshots, but
its admission incorrectly required all reaped-child CPU counters to be zero.
Its displayed CPU seconds also used an incorrect nanosecond interpretation.
It remains `qualified=false`; those displayed derived CPU values must not be
used. The unchanged raw counters are admitted separately by D1419, without
rerunning the workload.

Apple's [task-rusage implementation](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c)
fills CPU fields from task timing. D1419 converts Mach ticks with the live
timebase, numerator 125 and denominator 3. An independent owned-process
`getrusage` calibration measures 0.200008 seconds versus converted libproc
0.200030 seconds. Final family accounting includes reaped-child CPU under
the retained no-live-descendant-double-count gate.

Raw evidence: `.data/d1418-prefix-family-cpu/report.json` and `samples.json`.
Corrected admission: `.data/d1419-prefix-family-cpu-admission/report.json`.
Harnesses: `.data/d1417-prefix-family-cpu.py` and
`.data/d1419-admit-prefix-cpu.py`. Failed records were not overwritten.

## Consequence

In this actual normal first window, user execution dominates; the family CPU
sum is close to the complete wall interval. This does not prove a precise
exclusive wait fraction, a specific Darwin/Linux causal difference, or the
same behavior during every intermittent loader stall. It does rule against
treating a several-second loader/fork wait as the dominant cost in this run.

The remaining execution optimization must primarily reduce the build child's
actual work. Existing kernel-wait and load-packing failures do not become
successes. Existing passive allocation records select hypotheses but cannot
alone qualify an official-prefix allocation-elimination candidate. No new
performance patch or full toolchain qualification is admitted. The main
first-log and concurrent real-test goal remains active and unachieved.
