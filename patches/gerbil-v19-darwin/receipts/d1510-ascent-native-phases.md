# ASCENT Native Compiler Intervals

## Decision Review

This follows the six-patch identical-C reuse path, not the denied 0044-0047
request batching route. Reuse already produces 70 HITs / two MISSes, but does
not explain the remaining whole-task wall time. This diagnostic allocates that
time before proposing another implementation change. Expected direct speed
benefit is zero. No diagnostic recorder enters the frozen patch series.

## Actual Native Runs

Both runs use the isolated ASCENT project at commit
`21e3638687d42ecfc36acebb28991987435ebc60`, selected GNU GCC, Multiple-VM GSC,
the frozen six-patch helper and unchanged assertions. The native runner launches
Gerbil and `just` directly; Python only parses completed evidence. Each source
change is a comment that forces fresh entry admission. The comment is removed
afterward and the isolated tracked checkout is clean. No active consumer
checkout or shared dependency is edited.

| Run | Whole wall | User / system | Object HIT / MISS | Correctness |
| --- | --- | --- | --- | --- |
| Proof population | 80.27 s | 112.89 / 36.89 s | 0 / 72 | 30 Cases, final OK, exit 0 |
| Source-change reuse | 73.61 s | 73.01 / 32.00 s | 70 / 2 | 30 Cases, final OK, exit 0 |

Raw receipts are `.data/d1510-ascent-native-phase-populate-v1` and
`.data/d1510-ascent-native-phase-reuse-v1`. Both entries are MISSes; neither is
an unchanged-entry no-op. The reuse record passes the explicit 72-event,
minimum-70-HIT admission contract. This is a focused case, not all 94 Suites.

## Stage Evidence

The reuse run's monotonic interval is **73.686833 seconds**. Its bounds include
the runner's identity snapshot, whereas `/usr/bin/time` measures the native
task itself. The population run has no corresponding complete clock bounds.

| Disjoint stage | Seconds |
| --- | ---: |
| Preparation before GSC link generation | 35.308139 |
| GSC link generation | 5.870445 |
| Object stage | 21.313312 |
| Final compiler link | 0.206477 |
| Cases and post-run admission | 10.988460 |

Preparation contains **8.400279 seconds** covered by recorded compiler
intervals and **26.907860 seconds** outside them. Source inspection shows it
also includes consumer entry validation, library currentness and imports.
The uncovered time is not proven Scheme macro time or dyld time.

The object stage contains **21.307454 seconds** of GSC-object interval union.
Four GCC-object calls occupy a **15.144195-second union**; 144 preprocessing
calls occupy **5.718624 seconds**, and 144 tool queries **1.210640 seconds**.
These intervals overlap. GCC is nested inside GSC: do not sum role wall unions,
process durations or descendant CPU into a supposed task total. The last stage
includes admission work and is not a pure test execution measurement.

This changes the next investigation: inspect the actual remaining GCC-object
critical path and separately attribute the 26.91-second preparation gap. Do
not prioritize GSC link generation alone or repeat the rejected batching route.
No large optimization or macOS-specific root cause is proved by these intervals.

## Observer Boundary

`tests/native_phase_recorder.c` delegates the selected native compiler through
`posix_spawn`, records monotonic begin/end and `wait4` status/CPU, propagates
signals and preserves argument/environment forwarding. Trace rows contain
roles and numeric fields, not source arguments or personal paths. The offline
`tests/experiment_framework/native_phases.py` computes clipped interval unions.

Recorder proxies add process launches and change the selected compiler wrapper
identity. They are diagnostic-only; these timings cannot be compared as a
matched speedup against uninstrumented runs. Delegate hashes before/after are
identical. Post-run read-only image verification passes **1992 toolchain images**
and **2809 dependency images**. The recorded compiler proxy source was archived
before the separate clock utility was added; the proxies themselves did not
change between the two runs.

## Evidence Identities

| Reuse artifact | SHA256 |
| --- | --- |
| `events.tsv` | `969df73c0a813645bc1d8a8d5cd78b8f91627a92af96ab0709f7fdb1a72e3625` |
| `task-begin.ns` | `025a9f1521b7393231fc157f67b96a30a1ccec1e0df8f404289f8df5d5ffe5d7` |
| `task-end.ns` | `a93a354ef8f52f91d72f1f8001993f53d1495ee0c398150a537c6d17d77408f9` |
| Original `phases.json` | `1cd11dd46c634a4a1015fa0a67afa23683c10d17fad33a4a63f93629cacdea85` |
| Raw output | `4e79068f47d09db436b5152f14f41b46c3745de16acb073c93074fdd11caa986` |

Recorder source SHA256:
`39c4cbb8c816b096088bbbfcea96e73d26f853f8465211464acf118159c447a3`.
Compiler proxy SHA256:
`ff7f459d5cdba75b117ad11661f067ec44541b5cccc092a601c63a24310391f7`.
Clock utility SHA256:
`405fc34abf66cacb66edd8cbf037384f3723b4d64758e9e238084ce05fa50ab7`.
The extended stage-intersection summary is saved separately as
`phases-observed-v1.json`; the original summary is not overwritten.

Frozen MCP remains unchanged: first logs **3.950-4.038 seconds**, cold builds
**35.552-37.770 seconds**, complete test **86.924 seconds, 965/965 passing**.
Its ceilings remain **4.5 / 42 / 97 seconds**. This diagnostic neither promotes
a new patch nor qualifies complete ASCENT performance or general release.
