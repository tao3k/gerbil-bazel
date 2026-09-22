# D855: real MCP native-worker attribution on Darwin

Date: 2026-09-22. This is an **isolated diagnostic**, not an admitted
performance patch or an A/B timing result. No gerbil-mcp source or global
toolchain was changed. The D851 source was instrumented only under
`/private/tmp/gerbil-d846-full.qHfGgo/source`; its rebuilt `gerbil` binary
SHA-256 is `058b456de550d3c03273fdd5d6b47a704ed07e1e6ca1528664da49fad5df4dd2`,
not the frozen, uninstrumented D851 binary. The temporary changes add
`std/make` phase/producer events and compiler-executor job start/end times.
The source passed Gerbil-MCP balance checking and checkout-local `gxc -S`;
`make stage1`, then `make stdlib`, then `make tools` completed sequentially
with 12 build cores and the root Justfile's Darwin environment. The core
change caused a broad stdlib rebuild; that toolchain-build time is not a
consumer benchmark.

## Strict-gate outcomes

The first diagnostic attempt tripped the 10-second silence gate in MCP's
`gen_compat.py`, before `gerbil build`. A subsequent toolchain-import-only
qualification exceeded its 30-second total bound; direct `gxi` startup and
atomic `:std/make`, JSON, and SSL imports succeeded afterwards. Another
strict attempt, after successful import and `json/env` qualification, tripped
the gate after the `std/net/request` deprecation warning and before
`... build in current directory`: the warning was at 5.631 s and the
watchdog ended the run at 16.152 s. This interrupted attempt was reported
in the task command output; its temporary JSON pathname was reused by the
later successful run. Neither interruption is a completed build or a
release qualification. `gerbil pkg version` repeated ten times in the failed
clone and package-environment initialization completed normally, so the
pre-build stall remains intermittent and unlocalized below gxpkg dispatch.

The next strict cold run passed in 74.671 s with a 3.556 s maximum silence.
Its raw machine receipt is `/private/tmp/d855-mcp-native-jobs.json`, source
revision `9a5c35e275e5d6847ff421151bb224f2eae177c1`. Do not compare
its absolute wall time to the uninstrumented D851 A/B as a speedup claim.

## Package phase and worker evidence

Times below are from process start; the `std/make` phase clock starts at
6.544 s.

| Boundary | Time or duration |
| --- | ---: |
| Graph ready | 12.510 s (5.966 s after phase start) |
| Graph complete / native drain begins | 40.054 s (graph 33.509 s) |
| Last `compile-file` job ends | 68.718 s |
| Executable-object jobs start | 69.648 s |
| Native drain ends | 73.823 s (drain 33.769 s) |
| Final executable link job | 4.046 s |

The 187 module producers total 277.049 **worker-seconds**, overlapping on
12 workers; 561 serial import/expand completions total 6.348 s. The executor
emitted 741 job-end records. Of these, 734 are independently parseable;
seven lines interleaved with `std/make` output because the two loggers have
different output mutexes. The parseable records include 543 `compile-file`
jobs, 189 executable-object jobs, one prepare-link job, and one final link.
They account for 636.536, 5.802, 0.929, and 4.046 worker-seconds respectively.

From graph completion to the last `compile-file` end is 28.665 s. The
parseable `compile-file` intervals alone occupy approximately 340.745 of
the available 343.976 worker-seconds, or **11.89 of 12 workers on average**.
This is worker occupancy, **not CPU utilization**; the job clock includes
subprocesses, I/O, and small observation/logging overhead. The result argues
against idle executor workers as the dominant post-graph cause. Median and
P95 observed submit-to-start delays for `compile-file` are 15.472 and
26.249 s; these include ordinary queueing and can include dependency waits,
so they are not evidence of a blocked scheduler by themselves.

The longest job, `data/embedded~0.scm`, ran 37.841 s from 14.346 to
52.187 s. Its generated C is 11 MiB and dynamic object is 6.8 MiB. Other
long jobs include `lint~0.scm` (12.897 s) and `parse~0.scm` (9.891 s).
The Gambit configuration contains the admitted Darwin GCC
`-ftrack-macro-expansion=0` flag. The 37.841-second job overlaps other
work and ends 16.531 s before the last `compile-file`; it cannot be counted
as a 37.841-second wall-time opportunity. The entire late drain consists of
many occupied compiler workers, not one final object serialization.

## Follow-up boundary

Keep the D851 release hold and the hard 10-second package gate. The atomic
Scheme-to-C / GCC object / dynamic-link split and a candidate lowering of
large string constants are recorded in
`d857-embedded-string-lowering-atomic.md`. Do not infer a `std/make` scheduler
fix or change GCC optimization flags from this occupancy receipt alone.
