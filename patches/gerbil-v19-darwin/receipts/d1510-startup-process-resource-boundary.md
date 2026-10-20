# D1510 Startup Process Resource Boundary

No new optimization is admitted. The historical 47.771713 / 47.824226 /
47.927094-second cold builds remain the anchor, not a fresh current pass.
The gates remain first actual compilation 5 seconds, full cold build
50 seconds and full test 112 seconds.

## Current Unchanged Controls

Both current frozen-binary cold controls clean successfully to zero native
images. They produce no first compile before the unchanged deadline:

| Attempt | Clean seconds | First-log deadline observation | Full build | Full test |
| --- | ---: | ---: | --- | --- |
| current-three-gates-v1 | 10.353893 | DENY at 5.032836 | Unknown | Skipped |
| current-three-gates-v2 | 5.243340 | DENY at 5.045489 | Unknown | Skipped |

Both groups are killed/reaped with terminal exit -9 and no cleanup errors.
These are deadline observations, not first-log times. The second unchanged
attempt is not a new candidate or an optimization result. A separate clean
resource diagnostic exits zero: 2.25 seconds real, 0.71 user, 0.37 system,
5,236,450,608 instructions and 2,133,164,617 cycles. It is not build timing.
The varied clean times do not by themselves identify their cause.

## General Read-Only Observation

The existing process executor now accepts an optional resource reader,
disabled by default. The Darwin reader uses the installed SDK's rusage v4
layout and libproc, without runtime injection or Scheme source changes.
It records kernel counters for the owned process and optionally its isolated
process group once per second. It neither writes product stdout nor changes
deadlines, output recognition, command identity or terminal cleanup.
Observed runs are explicitly diagnostic-only and not performance-qualified.

CPU/time counters are Mach ticks, converted through mach_timebase_info.
The SDK-layout/reader/process tests pass 23 cases. An actual self-process
calibration records 0.200047 seconds process CPU and 0.200034 decoded CPU,
ratio 0.999934, with timebase 125/3. This validates the conversion on this host,
not every OS release or process accounting contract.

[XNU task resource collection](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c)
separates task CPU, runnable time, instructions and cycles.
[Task power collection](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/task.c)
sums runnable timers across threads, including terminated-thread totals.
[Scheduling source](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/sched_prim.c)
starts that timer on becoming runnable, retains it across dispatch, and stops
it on blocking. Thus runnable time is not pure executing CPU or a direct
I/O-wait counter. These current upstream sources are interpretation guidance,
not proof of the installed kernel's exact revision or external contention cause.

## Executed Root And Child

The first build-prefix diagnostic records the actual root process. At
2.030911 seconds it has 0.692974 seconds CPU and 5,233,925,549 instructions.
By 4.051958 seconds CPU is only 0.693373 and instructions 5,234,561,103.
The root is therefore not continuing heavy execution throughout that silent
interval. Its live child is outside that first reader's scope.

The follow-up samples the actual same process group, not other machine jobs.
At 3.039172 and 4.048740 seconds it observes one root and one live child.
They have different process-start identities and the same native image UUID.
No group/member read errors occur. At the latter sample:

| Process | CPU seconds | Runnable seconds | Instructions |
| --- | ---: | ---: | ---: |
| Root | 0.877329 | 2.879649 | 5,289,771,146 |
| Live child | 0.261795 | 1.227767 | 1,824,320,398 |

Root CPU barely changes after the earlier 3.039-second sample while child CPU
and instructions grow. This selects the live child startup/import path for
the next execution-cost attribution; do not continue assigning the entire
silent interval to root Scheme expansion. Runnable-minus-CPU differences are
task-level counter differences, not a measured removable wall-time fraction,
exclusive syscall delay, exact host-load attribution or a Linux comparison.

Both diagnostic builds are stopped at the 5-second gate, with terminal -9,
reaped groups and no cleanup errors. No full build or test duration exists.
Neither a dormant QoS hypothesis nor a denied native tool handoff is reopened.

## Build Script Import Prefix

The spawn observer identifies the active child as the unchanged `build.ss`.
The two observed root `spawnp` calls (git and build.ss) total 0.003125 seconds;
no root fork is observed. Child injection coverage is incomplete, so this is
not an all-descendant process-creation claim.

The project-independent diagnostic probe runs the original build script via
the frozen sibling `gxi -L`, delegating the existing module-import, expander
evaluator and compiler callbacks without replacing their results. It emits
only side-channel files. This bypasses root package dispatch and adds observer
overhead: it is not an end-to-end timing or a performance-admission run.

The import-only prefix completes 90 top-level imports: 4.394204 seconds wall
and 2.336431 seconds CPU. Its standard-library root import accounts for
0.224787 wall / 0.214206 CPU; package-source root imports account for
4.169417 wall / 2.122225 CPU. Nested imports are inclusive and are not added
again. Unfinished imports at termination are not represented.

The aggregated phase probe records exactly 84 completed root imports in both
side-channel files, with 4.670305 wall / 2.335439 CPU. Within those same roots,
5,594 outermost evaluator calls account for 0.312662 wall / 0.232321 CPU and
5,594 outermost compiler calls account for 0.101913 wall / 0.053099 CPU.
The shared recursion guard makes these callback intervals disjoint, including
their nested work. Combined CPU is 0.285420 seconds, about 12.2 percent of
the completed import CPU. The remaining approximately 2.050019 CPU seconds
are not attributed to one function: they include reading, expansion, import
resolution and probe overhead. This does not establish a Darwin cause or a
removable fraction of total wall time. Raw per-call logging was replaced with
root-level aggregates to avoid thousands of diagnostic writes.

Both probes reach the unchanged five-second first-log gate and are denied
and reaped, at 5.018068 and 5.004971 seconds respectively. Full build and full
test are unknown/skipped. Artifacts are private under
`.data/d1510-build-script-import-prefix-v1/` and
`.data/d1510-build-script-import-phases-v2/`. There is no new admitted patch
or speedup; these measurements narrow the next source investigation to the
general module reading/expansion path rather than AOT configuration, root
spawn overhead or treating all source-import CPU as evaluator execution.

### Native Reader Component

The unified resources workflow can consume the completed import inventory
and invoke the frozen native `read-syntax-from-file` without expansion.
It requires every selected path to be an existing isolated source, one result
per selected file, finite nonnegative metrics, terminal zero and unchanged
source hashes. It reports a component scope and never qualifies a performance
patch. The original five-second component cap remains unchanged.

The first diagnostic uses a nonexistent `gx#read-syntax-from-file` binding
and exits 70 before measuring any file. This is a probe error, not a runtime
regression. The corrected probe uses the actual exported reader, matching
the call in generated `module~0.scm`. Its first complete run reads all 84
selected files, totaling 1,062 top-level forms, with 0.065370 seconds wall and
0.053620 CPU. The inventory/hash-validated run records 0.045457 wall and
0.042930 CPU, exit zero and unchanged sources. Whole diagnostic process time
is 0.144332 seconds; it is not a build, test or first-compilation time.

Evidence: `.data/d1510-reader-component-budget-v1/` retains the binding error;
`v2` and `v3` retain the corrected logs, with validated inventory/hash metrics
in the `v3/report.json`. The resource/framework tests pass 27 checks.

This component executes after prior imports have warmed file caches, without
the nested imports/GC history of actual expansion. Its duration must not be
subtracted from the earlier import totals as an exact exclusive cost. It
nevertheless does not support a seconds-scale parsing target on this file
set, and does not warrant another reader/whitespace or directory-cache
candidate. Native generated calls to module reading and module-begin
expansion use direct `___JUMPINT` transfers: mutating the corresponding
Scheme global variables would not reliably observe these retained call
sites. Do not publish a redefinition-based phase profile as native coverage.

Next source ownership remains general expansion and binding/parameter access,
not MCP business behavior. No existing denied context-cache, type-chain,
marker-inline or parameter-result candidate is reopened by this measurement.

## Evidence Files

Private logs/receipts remain under
`.data/d1510-retained-current-three-gates-v2/0-candidate/`:
`build-resource-prefix.json` and `build-group-resource-prefix.json`.
The first clean resource log is in the corresponding v1 directory.
Sampled group enumeration does not cover every short-lived or escaped
descendant. Reaped-child counters must not be added to live child totals
without a lifetime identity/accounting proof. No sampled process is relabeled
as a particular Scheme module from its executable name alone.

The frozen native binary is unchanged. No AOT, CI, production runtime,
consumer business source, timeout or test inventory is modified. There is
still no new admitted gain, complete current three-gate pass or publication.
