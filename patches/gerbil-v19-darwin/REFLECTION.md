# Gerbil v0.19 Darwin build reflection

This document is the decision boundary between one experimental round and the
next.  A patch is not promoted because it compiles, passes focused tests, or
improves observability.  It must address the measured owner of the cost and
survive the admission gates below.

## Current D875 decision

The D874-corrected `0007+0008` candidate now has a complete isolated AOT
build, but its first performance prerequisite failed. An identical-binary POO
control measured 12.577 and 13.283 seconds (`+5.62%`); the latter also missed
the unchanged 13.13-second absolute gate. Both arms built and stayed below the
10-second silence limit. The host load was above its 12 logical CPUs after the
run, so this cannot qualify a candidate comparison or establish the cause of
the drift. Stop before revised-binary POO/MCP A/B and retry the same control
only in a stable host window. See
`receipts/d875-revised-candidate-aot-and-aa-gate.md`.

D876 makes that stop condition executable: strict local Darwin runs opt into
`--max-host-load-per-core=1.0`, gating the 1- and 5-minute load before any
clone or build. The current host was rejected immediately at 29.997/23.626
against a 12.0 limit. This is qualification-only; it neither changes the
candidate nor supplies missing A/B evidence. See
`receipts/d876-host-load-preflight.md`.

## D873 decision

The four-patch release stack is unchanged. D866 (0007+0008) repeated a
material MCP executable-closure win in both strict build orders, but did not
clear POO qualification: an unchanged original-versus-original POO control
drifted from 12.788 to 21.393 seconds on this host. Both sides of every
real-consumer run built successfully and respected the 10-second output gate.
The control is a test-validity failure, not permission to weaken a performance
gate or a proof of D866 non-regression. Keep D866 outside the release workflow
until the POO control is stable and the original/candidate comparison clears
the existing gates. See `receipts/d873-dual-consumer-requalification.md` for
the exact A/B data and binary identities. Do not reopen OS-thread, worker-count,
or `std/make` queue hypotheses as substitutes for this qualification.

## Patch 0002-0007 convergence verdict

The seven-patch investigation stack has converged to three active review
slices. Patch 0001 remains the independently admitted Gambit Darwin spawn
change. The former Gerbil Patches 0002-0007 are replaced by:

1. one compiler-owned, host-derived streaming worker pool that starts lazily
   on first native submission and closes at the official
   `execute-pending-compile-jobs!` boundary; and
2. one compile-time Darwin driver branch that exposes the executable static
   object closure and its final barrier link to that pool.

The converged candidate does not change `std/make`. It contains no report
struct, `make/contexts`, duplicate build-entry cache, shared slot API, cleanup
expansion, generated bootstrap edit, or non-Darwin driver branch. Submission
parameter capture is part of the executor itself because it is required for
correct deferred native work, not an independent performance patch.

The decisive controlled comparison used both real consumers and changed only
the executor lifecycle:

| consumer | deferred batch | minimal streaming | delta |
| --- | ---: | ---: | ---: |
| Gerbil POO at `22c1948` | 16.45 s | 13.49 s | -17.99% |
| Gerbil MCP at `9a5c35e` | 99.20 s | 79.58 s | -19.78% |

This falsifies the intermediate hypothesis that the Darwin closure DAG makes
producer/native overlap unnecessary. It also shows that the overlap belongs in
the compiler executor: preserving official `std/make` still beats the earlier
83.69-second full experimental stack by 4.91% on MCP. Against the frozen
175.19-second MCP external baseline, the converged candidate is 54.58% faster.

The atomic executor gate passes host-budget selection, bounded concurrency,
follow-up draining, parameter preservation, and first-error propagation. Both
real repositories build; the MCP arm64 Mach-O passes version and initialize.
The four pre-existing MCP output-contract failures remain explicitly non-green.

The libgerbil closure-manifest work remains a useful, separately owned
experiment, but it is removed from the active patch stack until a same-revision
clean end-to-end A/B proves it independently. Historical patches and receipts
remain available in Git history; they are evidence, not deployable authority.

## Round 3 verdict: dependency-graph patch not admitted

The rejected patch file has been removed from the applicable stack. This
section is the evidence receipt for that deletion, not an implementation that
can accidentally be included in the final pull request.

The 120-module fixture contains 100 independent modules and a 20-module chain.
Both variants used the same Gerbil revision, compiler, worker configuration,
sanitized Darwin environment, and generated artifacts.

| measurement | V19 baseline | experimental Patch 3 | delta |
| --- | ---: | ---: | ---: |
| cold build | 29.832 s | 30.505 s | +2.26% |
| warm build | 0.482 s | 0.447 s | -7.14% |
| native jobs | 240 | 240 | 0 |
| first Gerbil compile event | 0.373 s | 0.400 s | +0.027 s |
| last Gerbil compile event | 0.450 s | 0.464 s | +0.014 s |
| first native-job event | 1.384 s | 1.414 s | +0.030 s |
| last native-job event | 29.764 s | 30.428 s | +0.664 s |

The warm result is only 35 ms and does not admit a cold-build regression.  The
patch changes `std/make.ss` by 366 insertions and 88 deletions but does not
reduce cold wall time.  Its bounded thread topology may still be a useful
resource-safety property, but that property needs independent thread-count and
peak-RSS evidence.  It is not a performance result.

## Root-cause decomposition

The V19 pipeline currently has three ownership layers:

1. `std/make` discovers module dependencies and schedules Gerbil compilation.
2. `gerbil/compiler/driver` emits Scheme files and calls `add-compile-job!` for
   native work when parallel mode is active.
3. `gerbil/compiler/base` retains those native jobs until `std/make` has
   completed the whole build graph and calls `execute-pending-compile-jobs!`.

The scale receipt shows that dependency discovery and Gerbil code generation
are not the dominant cost.  The experimental graph was ready in 22 ms and the
last Gerbil compile event appeared at 0.464 s.  The 240 native jobs then occupied
the build until 30.428 s.  Replacing per-module coordinators with a Kahn queue
changes scheduler shape but leaves the dominant native-job topology intact.

The global drain is a real architectural barrier, but removing it can overlap
only the short Gerbil generation interval in this fixture.  It cannot by itself
explain or eliminate roughly 29 seconds of native work.  The larger question is
why two separately launched native jobs per trivial module dominate the build
on Darwin.

## Observability round: root phase identified

Verbose level 3 now emits machine-readable `build-observe` records for the
official V19 Gerbil scheduling lifecycle, native queueing/execution, worker
construction, progress, and total build wall time. Verbose level 9 retains
individual compiler invocations. The benchmark receipt parses those records
and derives ratios rather than treating the terminal transcript as the
authority. Observability is isolated as Patch 0003 and does not carry the
rejected dependency graph, dependency cache, or Kahn scheduler.

The 120-module, 12-worker cold receipt reports:

| measurement | value |
| --- | ---: |
| dependency graph | 120 nodes / 19 edges / 23 ms |
| initial ready width / critical path | 101 / 20 |
| native jobs / peak active | 240 / 12 |
| native wall / total build wall | 28,754 / 28,841 ms |
| native wall share | 99.698% |
| aggregate execution / mean execution | 327,721 / 1,365.50 ms |
| aggregate queue / mean queue | 3,408,884 / 14,203.68 ms |
| native worker utilization | 94.978% |
| worker construction | 0 ms |

This falsifies worker construction and dependency-graph traversal as dominant
costs. It also bounds the maximum benefit of merely overlapping the Gerbil and
native phases to roughly 87 ms in this fixture. The first dominant owner is the
240 native compilation units themselves: twelve workers remain busy, but each
trivial unit averages 1.37 seconds and the queue averages 14.2 seconds. The
next round therefore changes no `std/make` graph algorithm. It must decompose a
native job into `gxi -> gsc`, `gsc -> C compiler`, compilation, and
link/process-launch costs, then test batching or process-runtime changes at the
layer that owns the measured component.

The first stage decomposition used actual generated Scheme from Gerbil POO V19
and the pinned Homebrew `f0badc7`/GCC 16 toolchain. Three sequential samples
per size gave these ranges:

| generated Scheme | Scheme to C | complete dynamic object | GCC C compile | bundle link |
| --- | ---: | ---: | ---: | ---: |
| 82 B | 0.01 s | 0.29-0.30 s | 0.07 s | 0.04 s |
| 295 KB | 0.25-0.33 s | 2.22-2.34 s | 1.70-1.77 s | 0.04-0.05 s |
| 737 KB | 0.71-0.74 s | 3.25-3.60 s | 2.21-2.27 s | 0.04-0.06 s |

This moves the dominant subphase from generic `gsc` invocation to GCC C
compilation. Linking is negligible, and GSC process/front-end cost is material
only for tiny files. A separate 36-file small-C experiment retained the same
GCC flags and changed only concurrency: medians were 4.28 s at one worker,
1.61 s at three, and 0.82 s at twelve. Twelve-way execution therefore remains
the fastest tested wall-time choice; increased aggregate CPU/sys time is not a
reason to hardcode a smaller pool. The next experiment must explain or reduce
generated C volume or repeated native compilation work. Merely tuning the
worker count, batching GSC process startup, or changing the linker is rejected
as the next primary optimization.

## Rejected repair tactics

The next round must not:

- add cache thresholds, sleeps, fixed worker counts, or Darwin-only timing
  constants;
- treat progress logging as a speed improvement;
- accept a warm-path improvement as evidence for cold-build performance;
- move compiler-driver ownership into `std/make` or add another dependency
  parser;
- hide the phase barrier by renaming it or by starting more unbounded threads;
- combine several changes and attribute the result to whichever one was most
  recently edited.

## Architecture hypotheses for the next round

### H1: Darwin process creation is still material in the full build

Patch 1 now has a strict process-spawn microbenchmark and a controlled
full-stack A/B. Baseline and Patch 1 used the same actual V19 source snapshot,
generated C, configure arguments, prefix string, GCC 16, linker sysroot,
Gerbil source and observation overlay. The only source delta was Patch 1 in
Gambit `os_io.c` and its unit contract.

| measurement | V19 baseline median | Patch 1 median | delta |
| --- | ---: | ---: | ---: |
| total internal build wall | 28,853 ms | 10,465 ms | -63.73% |
| native wall | 28,765 ms | 10,370 ms | -63.95% |
| aggregate native execution | 278,751 ms | 123,172 ms | -55.82% |
| aggregate native queue wait | 3,398,185 ms | 1,226,986 ms | -63.89% |
| outer cold run | 29,251.96 ms | 10,925.58 ms | -62.65% |

Raw internal cold samples were 28,673 / 28,928 / 28,853 ms for baseline and
10,465 / 10,161 / 11,456 ms for Patch 1. All six performance receipts passed
their overlay, source-revision, cold, warm, artifact-count, and failure-path
assertions and validate against the receipt schema.

The median wall result is a 2.76x speedup and is consistent with the two-level Darwin
process-creation hypothesis: `Gerbil -> gsc` and `gsc -> GCC` both need the
patched runtime for the effect to appear. It also falsifies the previous
conclusion that GCC compilation alone owns the dominant cost; that stage
measurement included process-runtime overhead from the old fork path.

This round also exposed a source-authority trap: a Git archive of Gambit
`dcd677c` contains older pre-generated `type-34` C, while the working V19 tree
uses `skip-worktree`-hidden `type-35/pinned` C. A revision string alone is not a
toolchain identity. The admitted A/B therefore snapshots the actual generated
C and records executable identities.

SSI artifacts are byte-identical across variants. Raw Mach-O object hashes are
not stable even across repeated baseline runs because UUID and temporary-path
metadata differ, so raw native SHA-256 is not a valid semantic-equivalence
gate. The patched toolchain additionally loaded and checked the values of all
120 built modules; the qualification took 110.74 seconds and continuously
reported module progress. Patch 1 has passed performance admission. Final patch
admission still requires either a normalized Mach-O comparison or a matching
baseline consumer receipt; raw nondeterministic hashes will not be accepted as
proof or as a reason to reject the result.

### H2: native work needs an explicit bounded executor lifecycle

The compiler layer, not `std/make`, should own native-job submission and
execution.  A candidate V19 API would establish one bounded executor session,
submit native jobs as Scheme generation completes, propagate the first error,
drain follow-up work, and join all workers at the session boundary.  `std/make`
would own only dependency readiness and the lifetime of that public session.

Before implementation, the design must prove that executable/link jobs and
module object jobs preserve their ordering contracts.  It must also prevent two
independent pools of `N` Gerbil and `N` native workers from silently creating a
2N runnable set.  If one shared admission budget cannot be expressed without
moving driver internals into `std/make`, the design is rejected.

This can remove the global stage barrier, but the current fixture bounds its
likely wall-time benefit to roughly the pre-native interval.  It is an
architecture cleanup, not yet the primary performance hypothesis.

### H3: per-file native invocation is the dominant Darwin cost

The scale build launches 240 native jobs for 120 trivial modules, with about
29 seconds between the first and last native-job events.  The compiler driver
currently invokes `gsc` once for each generated Scheme file.  The next source
study must determine whether V19/Gambit can compile an admitted batch of
independent files while preserving each expected object, diagnostic identity,
flags, and incremental invalidation boundary.

No batching patch is written until those semantics are demonstrated by a
minimal command-level experiment.  If Gambit necessarily links or otherwise
changes output semantics for multiple inputs, the hypothesis is rejected
rather than patched around.

The first minimal experiment used two independent Scheme files on the pinned
`f0badc7`/Gambit `dcd677c` toolchain.  One multi-input `gsc` invocation emitted
two independent `.o1` files.  Each file was byte-identical to its separately
compiled control:

| output | separate SHA-256 | multi-input SHA-256 |
| --- | --- | --- |
| `alpha.o1` | `b2cd5c8d9e9041a2effb1c8aef7cd40d6a880d70ae4336ad1bd19a95fd8a4d98` | same |
| `beta.o1` | `f38a421a48664948309f84cb82d022c94120648f7fc9553febd2159dc1680d92` | same |

Five repetitions of two separate invocations took 3.40 seconds; five
repetitions of one two-input invocation took 3.24 seconds.  This establishes
only minimal output-boundary feasibility.  A 4.7% micro improvement is not an
admission result, and the experiment does not yet cover Gerbil-generated
files, production flags, chunk sizing, error identity, incremental rebuilds,
or interaction with the upstream-derived worker budget.  H3 remains open.

## D801 full-build phase ownership

The complete sanitized D801 cold build establishes that the bounded native
executor is active: the stdlib phase completed 800 native jobs with 12 workers,
zero errors, and peak concurrency 12.  Its 181.876-second native wall time is
therefore not evidence of an accidentally serial worker configuration.

The first dominant phase outside that executor is libgerbil startup.  A live
Darwin sample measured a 1.0 GiB process while nearly every sampled main-thread
frame was below `___dynamic_load` in dyld's `dlopen`, `mapSegments`, and
`fcntl` path.  The next falsifiable hypothesis is therefore:

> Reducing the number of independently loaded `.o1` images, while preserving
> module identity, incremental boundaries, failure identity, and generated
> artifacts, materially reduces Darwin libgerbil wall time and first-access
> `gxtest` latency.

This hypothesis belongs to the compiler output/loading boundary.  It must not
be repaired by changing the upstream-derived worker count, hiding the cold
sample, or weakening the ten-second observability contract.  The first
experiment must measure `.o1` image count, dyld time, peak RSS, libgerbil wall
time, and first-access test latency for an unchanged control and one bounded
batching/static-loading variant.

## D801 libgerbil closure projection

The Darwin sample attributed the silent libgerbil prefix to loading hundreds
of independent `.o1` images.  Source inspection then found that stdlib had
already imported the same module graph, but `build-libgerbil.ss` discarded
that graph and reconstructed its ordered static closure in a new process.

The first prototype moved the original closure algorithm into stdlib and wrote
an explicit versioned manifest.  It reduced the complete libgerbil target from
the 228-second D801 phase receipt to roughly one minute, but the stdlib target
grew to 58.76 seconds: its manifest projection still spent 27.76 seconds
walking the graph.  Instrumentation reported `contextHits=0` and
`fallbackImports=294`; an atomic one-module probe established that std/make
keys contexts as `std/assert`, while library imports use `:std/assert`.

Normalizing that boundary produced `contextHits=294` and
`fallbackImports=0`, yet projection still took 26.389 seconds.  This falsified
dynamic loading as the remaining owner.  The inherited DFS did not mark a
shared dependency until an entire root traversal completed, so diamond-shaped
imports repeatedly traversed the same subgraphs.  A per-root `seen` HashTable
reduced projection to 14 ms without changing global first-encounter ordering.

The optimized manifest is byte-identical to the pre-optimization control:
7,222 bytes and SHA-256
`aa60c38c15c49eadf62d7f37c35f5f29b1c8cefae875a51b5cee082c4dd607f9`.
The focused stdlib target fell from 58.76 seconds to 29.73 seconds, and the
complete libgerbil target completed in 62.62 seconds (72.5% below the earlier
228-second D801 phase receipt).  Manifest unit contracts, std/make one-worker
and parallel cases, and compiler executor concurrency/error contracts passed.
Three controlled warm std/make test samples were 7.77/7.98/8.13 seconds
(7.98-second median).  The 9.13-second first run after rebuilding std/make is
reported separately and is not used as the stable test-runtime result.
These focused runs admit Patch 0005 for integration testing; they do not
replace a clean end-to-end cold A/B.

Complexity removed: libgerbil no longer owns a second source of closure truth
or a second Darwin module-load pass.  Complexity added: a versioned manifest,
retained build contexts, schema/order validation, and per-root DFS visitation.
The next dominant phase is std/make's approximately 25-30 second import and
dependency scan, which remains visible and must be optimized independently.

The real Gerbil POO consumer exposed a separate configuration failure before
that algorithm can be judged.  `std/make` maps an absent
`GERBIL_BUILD_CORES` to zero and then clamps the worker pool to one.  Its
artifact-clean build therefore took 59.21 seconds and emitted module compile
events serially.  Selecting the machine's 12 physical cores dynamically made
the compile events burst immediately and reduced the deployed V19 build to
18.50 seconds.  This is a 68.8% configuration-path improvement, not a new
scheduler algorithm.  The default worker budget and the compiler executor's
independent default of one must be unified behind the same runtime-derived
source before package-local configuration can be removed.

With the worker budget held at 12, the D801 build-tree patch stack produced
two artifact-clean Gerbil POO builds in 13.66 and 13.65 seconds.  The stable
receipt reported 4.526 seconds for Gerbil compilation and 8.410 seconds for 64
native jobs (`peakActive=12`, zero errors).  That is materially below the
18.50-second deployed `f0badc7_1` consumer result, but the revisions differ;
it is integration evidence, not yet the required same-revision causal A/B.
The remaining consumer critical path is now the native phase, especially the
tail after the queue drains, rather than dependency graph construction.

## D801 streaming executor and clean-artifact closure

The next audit found that the applied patch stack still retained a global
pending-job list and drained it after the `std/make` graph.  The final D801
architecture replaces that duplicate authority with one compiler-owned
streaming executor session.  `std/make`, stage1, and Bach establish the same
session lifecycle; build producers and native jobs acquire slots from one
host-derived budget.  The Legacy pending-job API is absent from source and the
generated bootstrap compiler interface is synchronized with the source API.

The first apparent cold POO measurements were not valid cold samples:
`make clean` removed `.ssi` and static Scheme output but retained generated
`.scm`, `.ssxi.ss`, nested-module output, and successive Gambit `.oN` images.
There were 401 such accumulated files.  Patch 0006 derives the exact module
basename namespace and removes current-generation top-level and nested
artifacts without using a broad glob.  Its negative contract retains an
unrelated same-prefix `.scm` sentinel.  After the repaired clean, the POO build
produced 180 artifacts and no `.o2+` files.

The true clean trace reports 64 native jobs, `peakActive=12`, and no errors.
Per-job evidence rejects FIFO/LPT and fixed-worker tuning as the next primary
change: the longest units (`object~1`, `table-testing~0`, `trie~0`, and
`type~0`) have small queue waits relative to their 3-5 second GCC execution.
Per-entry evidence also shows Scheme-to-C generation in tens to hundreds of
milliseconds after the initial support layer.  `trie~0` arrives late because
of the real POO dependency chain, not a hidden `std/make` batch barrier.

The post-stage1 D801 source runtime completed the clean POO build in 13.262 s
internal wall time and passed the full POO harness.  The installed AOT runtime
identifies as `f0badc7`, two commits behind `d801e7a`; an owner-overlap audit
shows that those commits do not change any Patch 0001-0006 owned source file.
It can therefore launch the complete patched module stack for integration
validation.  The patch files remain one mandatory ordered stack even though
they are split for review commentary.

## Dual-consumer critical-path round

The complete D801 AOT runtime establishes a new two-consumer baseline. Gerbil
POO remains intentionally small and is used only to catch scheduler overhead
or semantic regressions. Gerbil MCP is the representative large graph: 551
native jobs complete with twelve workers and no compiler errors, but its
168.733-second executor wall contains one 121.032-second job. That long job is
submitted only after the executable closure has been generated, behind the
ordinary native-file stream, so FIFO admission delays the graph's final
critical path even while aggregate worker utilization is high.

This evidence changes the next hypothesis. It is no longer “make POO faster,”
but it also does not admit a generic scheduler change. Linux does not reproduce
the P0-scale delay, so queue topology alone cannot own the platform delta.

A direct Darwin isolation run established the actual boundary. Ordinary MCP
native jobs were essentially drained at 44.307 seconds. The executable job had
waited 23.444 seconds, but then executed alone for 112.070 seconds. Retaining
its static objects and deleting only the binary reduced the same closure build
to 27.270 seconds. Thus queue priority can recover at most part of the wait; it
cannot explain or remove the dominant cold execution cost.

The executable path owns a second artifact family: 187 generated static C
files and 187 static objects in addition to the normal module outputs. The C
input totals 57,870,587 bytes. Its largest unit is an 11,425,297-byte embedded
data module; the normal full build compiled it in 24.955 seconds under worker
contention, and isolated `gsc -obj` compiled it in 14.84 seconds. Disabling the
three GCC scheduler passes changed that to 14.47 seconds; overriding `-O1` with
`-O0` changed it to 14.14 seconds. Both flag hypotheses are rejected.

The same file expands through `gambit.h` to 101,577,428 preprocessed bytes.
Preprocessing alone took 18.04 seconds, while compiling the materialized
preprocessed stream took 4.90 seconds. The measured owner is therefore the
volume and duplicate compilation of Gambit-generated C in the Darwin
executable/static closure. The next experiment must reuse an equivalent
already-built object or reduce that generated closure while proving relocation,
module initialization, and artifact equivalence. It must not modify
`std/make` scheduling first.

### Darwin driver closure result

The first implementation overreached by adding a public executor job-group,
in-flight close semantics, and briefly a producer/native fairness policy. The
fairness policy had no root-cause evidence; the generic executor changes were
also unnecessary. Both were deleted.

The admitted candidate is a compile-time Darwin branch in
`gerbil/compiler/driver` only. After `gsc -link` generates the static C family,
the driver submits every object job followed by one dependency-barrier link job
to the existing executor before the producer returns. This preserves the
official executor close lifecycle and leaves the non-Darwin path unchanged.

On the 187-entry MCP clean build, the final driver-only candidate completed
740/740 jobs with twelve host-derived workers, `peakActive=12`, zero errors,
81.758 seconds internal wall, and 83.69 seconds external wall. That is 47.57%
below the 155.952-second attribution run and 51.55% below the frozen
168.733-second baseline. The result admits the measured-owner hypothesis while
rejecting broader `std/make` or executor redesign.

## Patch 0002-0007 convergence result

The required convergence is now implemented and measured. The previous six
Gerbil patches are not applicable files in the active stack. Their surviving
runtime behavior is expressed by the new Patch 0002 compiler executor and new
Patch 0003 Darwin driver DAG; all other experimental runtime surface was
removed.

The deferred-batch intermediate proved why streaming cannot be deleted:
Gerbil POO took 16.45 seconds and MCP took 99.20 seconds. Holding source,
environment, worker budget, and Darwin driver constant, the minimal lazy
streaming executor reduced them to 13.49 and 79.58 seconds. Patch replay against
D801, atomic executor contracts, both real cold builds, and MCP binary startup
pass. This is the admission result summarized at the top of this document and
in `receipts/d801-converged-dual-consumer.json`.

Artifact cleanup and the libgerbil closure manifest remain outside the active
performance stack. They require their own correctness case and same-revision
end-to-end A/B before reconsideration.

## Ordered experiment matrix

Each experiment changes one owner at a time:

1. Close normalized native equivalence for the admitted Patch 1 A/B.
2. Baseline versus Patch 2 executor with Patch 1 held constant, recording wall
   time, maximum live threads/processes, and peak process-tree RSS.
3. A minimal compiler-executor lifecycle prototype, only after native ordering
   contracts are executable.
4. Extend the command-level `gsc` batching experiment to real Gerbil-generated
   files, distributing batches from the upstream-derived worker budget, before
   any Gerbil source change.
5. The surviving design on the real Gerbil POO V19 clean build and its atomic
   tests.

At least three cold samples are required for timing comparisons.  Report the
median and every raw sample; do not average cold and warm paths.

## Patch admission gates

A patch can enter the single gerbil-bazel pull request only when all of these
are true:

- its owner layer matches the measured root cause;
- the original and changed variants differ by exactly the intended variable;
- atomic failure, ordering, follow-up, and cleanup contracts pass;
- generated artifacts and expected native-job kinds are identical;
- the 120-module cold median improves materially without a warm regression
  being used to conceal a cold regression;
- thread/process cardinality and peak process-tree RSS remain bounded by the
  upstream-derived worker budget;
- the real Gerbil POO V19 consumer passes `clean -> atomic tests -> cold build`;
- no ten-second silent interval occurs in a local gate;
- the complete ordered patch stack applies to the pinned V19 source revision.

## Required reflection after every round

Every round must record:

1. the exact hypothesis and the single changed owner;
2. raw receipts and whether they falsified the hypothesis;
3. the first dominant phase or typed failure;
4. what complexity the patch added or removed;
5. the decision: admit, revise architecture, or delete;
6. the next experiment and its rejection threshold.

Passing tests closes correctness for the tested contracts.  It never converts
a falsified performance hypothesis into an optimization.

## D1267-D1270: Reject the startup-only interpretation

The real MCP full-cycle receipts reject the current outlined runtime as a
delivered optimization. Original clean/build reached first compile at 6.855
seconds and finished the build in 69.441 seconds. The candidate reached first
compile at 5.317 seconds but finished in 106.990 seconds. These are single
sequential observations, not a controlled regression estimate; nevertheless,
they establish no end-to-end win. Earlier approximately fifty-second builds
remain relevant historical evidence, not superseded by this slower candidate.
Neither runtime passed the concurrent Native-test gate. CASE-visible tests
also exposed assertion errors despite zero process exit status. First-log
improvement alone cannot qualify build or test acceleration.

The unsuccessful detour optimized loading/packaging and narrow native call
paths without removing the measured bulk execution work. D1101's passive
187-module preparation attributes 0.320 seconds exclusive user CPU to compile
boundaries and 5.712 seconds to execution boundaries, with approximately
4.404 GB allocated. Execution includes compiled macros, GC and callbacks; it
is not interpreter-only time or a measurement of every second before the
official build's first log. D1102 and the byte/relocation-identical D1109-D1110
native mappings locate distributed work in expander core/stx, object operations
and collection. Shared generated-C entry/exit lines are not exclusive Scheme
procedure costs. CI platform ratios alone do not isolate operating-system cost.

Source review identifies fresh intermediate objects in syntax-e and its
stx-car/stx-cdr callers, but this is not a new optimization: D1141-D1177 already
tested constructor fusion and bounded caller scalarization. Fusion retained
the original allocations; narrow scalarization did not materially reduce the
approximately 4.404 GB total. Likewise, existing register/entry experiments,
GC-only changes and optimization-level comparisons do not justify repetition.

The remaining actionable question is which actually executed constructors and
caller observation boundaries account for the bulk allocation and repeated
native body work, and whether Gambit can eliminate that work while preserving
freshness, mutation, identity, continuations, debug semantics and GC safepoints.
Static site counts, a selected trace's hit count or a local helper speedup do
not answer that question. Any new attribution must cover work missing from the
existing records rather than repeat their baseline measurements.

Production ownership remains Darwin/GNU-only Gambit backend/runtime. No
std/make, std/test, package HTTP or consumer SCM change is admitted. A candidate
must first reduce actual execution cost, then pass official MCP clean/build
and CASE-visible concurrent Native tests under unchanged progress gates.
Packing is stopped; no candidate from this round is performance-qualified.
Evidence: receipts/d970-guarded-trace-progress.md, D1101-D1110,
D1141-D1177 and D1267-D1270; private raw reports remain under project .data.

## Literature Review: Remove Work Before Lowering to C

The prior investigation stayed too long inside its bounded generated-C trace
architecture. Existing measurements should guide algorithm selection, not
trigger another general baseline campaign. The following primary papers were
checked against the pinned Gambit source and the rejected local experiments.
They provide optimization mechanisms, not evidence of a macOS-specific cause
or a promised speedup for MCP.

### First Priority: Partial Escape Analysis

[Stadler, Wuerthinger and Moessenboeck, CGO 2014](https://ssw.jku.at/Research/Papers/Stadler14/Stadler2014-CGO-PEA.pdf)
tracks virtual objects and their fields through control flow. Only an escaping
path needs to materialize the object; a nonescaping path can substitute its
fields and omit allocation. The algorithm handles merged states and loop
entries and cooperates with inlining. Its Java results are not Scheme results.

Our existing gambit_fresh_escape.py audits complete isolated generated-C
regions, conservatively retains objects observed in final state or guards,
and refuses closure scalarization. gambit_scalar_caller.py selects bounded
return paths with explicit site/path limits. This is not a general CFG partial
escape analysis with state merges and escape-edge materialization. Expanding
its path limits alone would repeat the old code-growth problem, not implement
the paper's method.

The actionable design question is a compiler-IR allocation/use analysis with
callee summaries or bounded proven inlining, rather than more post-C trace
selection. The pinned _ptree2.scm br-app-inline already has an expansion budget;
_gvm.scm bbs-purify performs control-flow cleanup but its inspected pipeline
does not supply this object-state analysis. The exact insertion point remains
an implementation question: register/stack liveness and debug frames must be
recomputed correctly if a GVM pass changes values. Unknown calls, foreign
effects and continuation capture must conservatively materialize or reject
the transformation. Moving a Scheme object to an ordinary C stack allocation
is not a safe substitute. Start with proven pair/structure field operations,
not result caching, object interning or closure-layout changes.

The first admission test is meaningful reduction in actual executed allocation
bytes and user CPU on the recorded MCP workload, with equivalent outputs and
identity/mutation/continuation tests. If coverage remains negligible, stop;
do not promote static opportunities or constructor fusion as a runtime win.

### Secondary: Bounded Static Basic Block Versioning

[Melancon, Feeley and Serrano, ECOOP 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2024.28)
implemented SBBV in Gambit and Bigloo. It propagates execution-context facts
and specializes blocks to remove redundant checks. This addresses distributed
type checks visible in the original native mappings, without declaring all
code unsafe. The published average runtime gain is about 10%, not a several-
fold solution; high version limits can greatly increase generated C and C
compilation time. A low version/code-growth budget is therefore essential.

This is a secondary mechanism, potentially exposing field/constructor facts
for allocation elimination, not a reason to repeat O2/O3 flag experiments.
No assumption is made that the research implementation is already available
as an option in the pinned staging compiler.

### Interprocedural Precision Has a Scheme-Specific Limit

[Vardoulakis and Shivers, CFA2](https://arxiv.org/abs/1102.3676)
motivates precise matching of higher-order calls and returns instead of
conflating unrelated caller contexts. However, the paper explicitly excludes
first-class control operators such as call/cc. Its complete algorithm cannot
be imported as a correctness argument for Gambit's continuation behavior.
Use this insight to design bounded callee summaries, with unsupported control
flow remaining a hard conservative boundary.

Decision: prioritize the feasibility and real coverage of IR-level allocation
elimination, keep SBBV as a bounded supporting option, and retain Darwin/GNU-only
production gating. No performance patch was added by this literature review;
official full build and concurrent CASE-visible tests remain mandatory.

### Scheme-Specific Follow-Up: Storage Use and Demand-Driven Inlining

The authors' [Bigloo research page](https://www-sop.inria.fr/indes/fp/Bigloo/bigloo-5.html)
describes Serrano and Feeley's Storage Use Analysis (ICFP 1996) as supporting
higher-order functions, side effects and separate compilation without requiring
CPS conversion. Its applications include unboxing and allocation placement.
This is closer to the unsupported callee/object-containment boundaries exposed
by D1278-D1287 than a single-basic-block field-use test. The full paper could
not be retrieved in this review: the author's PDF was access-denied and the
linked PostScript unavailable. Only the authors' abstract is verified here;
its algorithm and continuation assumptions remain unread and unqualified.
Its reported numerical unboxing gains are not evidence for macro expansion.
Ordinary C-stack allocation is still inadmissible without Gambit-specific
continuation and GC correctness.

Waddell and Dybvig's [Fast and Effective Procedure Inlining](https://scholarworks.iu.edu/dspace/items/8ce10406-2bfc-4589-8cbe-cd97ced50d2a/full)
is a complementary lead. The indexed author report describes demand-driven
online inlining, with call-site argument information and simplification feeding
the decision. Full-text retrieval failed; no implementation detail beyond the
accessible abstract is assumed. In the pinned Gambit source, br-app-inline
clones a known procedure and charges its unreduced ptree size against an
expansion budget (gsc/_ptree2.scm). Simply increasing that budget is not this
algorithm and can worsen both C compilation and instruction-cache behavior.
An admissible experiment would connect proven callee/object-use information
to bounded specialization, not globally request more inlining.

The same Bigloo page describes Serrano and Boehm's Understanding Memory
Allocations of Scheme Programs (ICFP 2000): allocation-frequency and heap-use
tools applied to the Scheme compiler itself. This supports the next missing
measurement, not a repeat of the established phase timings: dynamically
attribute the recorded approximately 4.404 GB to allocation sites before
choosing a larger storage-use pass. Static constructor counts do not rank
executed byte volume. An allocation observer must preserve original generated
C, compiler flags and ABI apart from declared counting instrumentation; its
timings cannot serve as accelerator evidence.

Decision: retain PEA as the concrete full-text algorithm reference; investigate
Scheme storage-use summaries and optimization-driven bounded inlining as
supporting mechanisms. Do not assert a Darwin-specific cause from these papers,
promise their benchmark ratios, or reintroduce rejected local scalarization.
Any production implementation stays opt-in Darwin/GNU-only, with unchanged
Linux behavior and real first-log/full-build/CASE-visible test qualification.

### Allocation Metric Correction From Executed Native Sites

D1288-D1296 add an original-generated-C allocation observer. Five native
hotspot units and three Gambit RTS units complete 187-module preparation;
the counter is not an accelerator. The largest observed physical constructor
site is syntax-wrap creation in stx-apply-mark: 12,855,681 executions and
514,227,240 bytes. The kernel rest parameter handler constructs 265,177,536
bytes of pairs. These are allocation owners, not removable-object proofs or
exclusive CPU costs. Unknown callers, identity and mutation remain boundaries.

The source audit corrects the denominator used when selecting a pass. In this
pinned Gambit, mem.c words_movable_objs multiplies by two the previous memory
sections plus current heap growth and current stack occupancy. bytes_occupied
also includes still/deferred-still storage. ___bytes_allocated combines that
value with GC-maintained bytes_allocated_minus_occupied and occupied still
words; ##process-statistics stores it in field 7. The recorded approximately
4.404 GB is that accounting metric, not a tally of physical constructor bytes.
This formula does not by itself explain macOS/Linux performance differences.

The eight-unit constructor total is 1,634,955,056 raw bytes. Do not divide it
by field 7 and call that allocation coverage, or simply halve field 7 to claim
exact physical allocation. Earlier informal 28%/37% coverage estimates are
withdrawn. Prior raw-elided-word/field-7 ratios also mix accounting metrics;
their small elimination counts and failed product gates remain unchanged.
This correction does not qualify any rejected candidate.

Next selection must connect dominant executed constructors to consumers and
prove fresh intermediate elimination across the actual call boundary. EVAL's
53,019,880 observed bytes do not establish EVAL allocation as the main target.
No new O-level, consumer SCM, std/make or std/test change is admitted. No
performance patch is qualified by this census.

### Implicit Rest Lists Are a Different Optimization Surface

D1297-D1306 attribute ordinary rest-handler construction to native entry
labels and inspect their original GVM source nodes. This reveals work absent
from the explicit constructor census: the argument-list object is created by
the runtime entry protocol, not a cons instruction in the procedure's body.
A zero explicit-constructor opportunity count does not rule out its elimination.

Two concrete patterns now have dynamic/source evidence. Arity wrappers such
as datum->syntax, core-apply-user-expander, foldr and string-index accept all
arguments as a fresh rest list, compute its length and apply a helper selected
by that length. For datum->syntax, 765,903 measured calls have two arguments
and 7,707 have four; for core-apply-user-expander all 470,992 have two. Separately,
the nested bound-method closure forwards its fresh rest list to a captured
method with a captured receiver prefix; all 1,330,692 measured calls have one
rest argument. These are implicit-list consumers, not scalarizable syntax-wrap
objects. They can also incur dispatch/list-traversal overhead beyond allocation.

The prospective Gambit pass must operate before GET_REST constructs the list:
specialize proven fixed-arity branches or forward unobserved rest arguments
through the native calling convention. Preserve fallback materialization for
wrong arities, unsupported uses and keyword/optional cases. Do not hardcode
Gerbil function names as the production rule, assume imported helper globals
immutable, or globally substitute captured method targets. The actual resolved
GVM call operand, procedure checks, closure environment, argument registers,
stack arguments, multiple values, continuations, debug frames and safepoints
must remain correct. A target's source name alone is not a correctness proof.

Four observed entry-IR modules are byte-identical to original native generated
C. This validates observation, not the prospective transformation. No speedup
or completed objective is claimed. The next implementation is an entry-level
implicit-rest-list optimization, not a revival of the rejected generated-C
caller trace or a change to consumer case-lambda/std/make code.

### Rest/Apply Literature and an Executable Reference

The follow-up searches mechanisms for the already measured costs, not another
macOS/Linux timing survey. Three primary references narrow the implementation
decision:

- [Henry Baker, CONS Should Not CONS Its Arguments, Part I (1992), section F](https://www.plover.com/misc/hbaker-archive/LazyAlloc.html)
  explicitly discusses the cost of rest lists and their use by APPLY. Returning,
  storing or mutating the list prevents treating it as disposable argument
  storage. Its lazy stack allocation design is not a drop-in Gambit change:
  identity, tail recursion and continuation handling are explicit concerns in
  the paper. Borrow the elimination opportunity, not its storage architecture.
- [Abdulaziz Ghuloum, An Incremental Approach to Compiler Construction (2006), sections 3.17-3.18](https://www.cs.tufts.edu/~nr/cs257/archive/abdulaziz-ghuloum/incremental.pdf)
  describes the opposing rest-entry/list construction and APPLY/list unpacking
  operations. Arity dispatch can instead use comparisons and jumps. This is a
  calling-convention explanation, not a benchmark or a Gambit correctness proof.
- [Chez Scheme cp0.ss](https://github.com/cisco/ChezScheme/blob/main/s/cp0.ss)
  supplies a concrete implementation reference inspected during this review.
  find-call-lambda-clause/rest-clause makes known rest operands explicit through
  a list binding (lines 1506-1547). The level-2 APPLY handler recognizes known
  lists, immutable-list nodes and list construction, and residualizes evaluation
  effects while producing a call (lines 2369-2427). In contrast, the separate
  find-apply-lambda-clause path explicitly relies on level 3 to omit argument
  checks (lines 1548-1597); that unsafe assumption must not be imported. The
  upstream main link is a moving implementation reference, not a pinned local
  benchmark dependency or a claim of Chez/Gambit equivalence.

The source correspondence is precise: pinned Gambit's targ-gen-label-entry
(gsc/_t-c-2.scm:718-805) constructs rest arguments before executing the wrapper
body. D1306 exposes length/arity tests and APPLY in that body. A compiler rule
can connect the incoming argument count and operands to proven branches before
GET_REST, retaining the original body for unsupported cases. This is stronger
than increasing br-app-inline's budget: the inspected rule charges the original
procedure size before reduction (gsc/_ptree2.scm:1384-1432), whereas the desired
transformation removes the list round trip without cloning large helper bodies.

This is a candidate mechanism, not sufficient evidence for a several-fold
startup improvement. The 514,227,240-byte syntax-wrap site remains the larger
observed individual constructor. Its objects cannot be declared removable just
because they are short-lived; the previously reviewed partial escape analysis
requires field/use and escape-path proofs. Rest elimination is the narrower
first implementation surface with measured consumers, not a replacement for
that larger target or proof of macOS-specific causation.

Admission remains actual reduction of executed work and user CPU, followed by
unchanged MCP first-compile/full-clean-build and CASE-visible test gates. Preserve
unknown targets, observable rest lists, wrong-arity errors, stack arguments,
closure environments, multiple values, continuations, debug state and GC polls.
Production stays Darwin/GNU-only; Linux and consumer/std/make/std/test sources
remain untouched. This review adds no accelerator and claims no speedup.

### Follow-up: Analyze Containers Separately from Their Contents

The fixed-arity rest prototype is not the delivered startup solution. D1323
still reports first compile at 6.047644 seconds and complete build at
69.833692 seconds; most concurrent test batches fail the unchanged progress
gate. Reduced rest allocation does not establish a product speedup.

[Park and Goldberg, Escape Analysis on Lists](https://cs.nyu.edu/goldberg/pubs/pg92.pdf)
provides a useful distinction: a list's spine can remain local even when its
elements escape. Its analysis also derives sharing information; in-place reuse
requires more than lifetime information. Sections 3.1 and 4 use a typed
functional language, not full mutable Scheme with first-class continuations.
We may borrow the container/content distinction, but cannot import its safety
conclusion directly into Gambit or reuse observable syntax objects.

The source correspondence is broader than rest lists. In the pinned
src/gerbil/expander/stx.ss, stx-apply-mark returns a fresh syntax-wrap;
syntax-e subsequently traverses wrapper fields and builds marked pair/vector/
box results. A function-local analysis stops at the returned wrapper. The
next question is whether summaries of proven callees can retain a virtual
wrapper across these boundaries, distinguish wrapper identity from payload
identity, and materialize it only where actually required. The existing
514,227,240-byte constructor measurement selects this target; it does not prove
that any of those objects are removable. Consumer source stays unchanged.

[Stadler et al., Partial Escape Analysis, sections 5.1-5.4](https://ssw.jku.at/Research/Papers/Stadler14/Stadler2014-CGO-PEA.pdf)
supplies the missing control-flow mechanism: track allocation identity,
aliases and field values; merge states at joins; iterate loop states; and
materialize at unsupported operations. This is not merely a larger bounded
trace. For Gambit, unknown calls, observable identity/mutation, debug state
and continuation boundaries initially require materialization or rejection.
No Java deoptimization infrastructure is assumed to exist in Gambit.

Baker's [rest/APPLY discussion, section F](https://www.plover.com/misc/hbaker-archive/LazyAlloc.html)
still justifies eliminating a proven unobserved argument-list round trip.
It does not justify replacing arbitrary Scheme objects with ordinary C-stack
objects; the paper separately discusses tail recursion and continuations.
Closure forwarding remains a bounded candidate, not a reason to postpone the
larger constructor target indefinitely.

Decision: investigate compiler-IR callee/field-use summaries for the largest
measured producer/consumer chain before broadening the optimization. Admit a
transformation only after actual executed allocation and CPU fall, semantic
controls pass, and unchanged MCP first-log/build/test gates pass. Literature
does not establish Darwin causation or a several-fold improvement. Production
ownership and activation remain Darwin/GNU-only Gambit; no new production
patch is qualified by this review.

The next source observation narrows that decision. D1336-D1337 attribute
11,902,136 of the original 12,855,681 wrapper allocations (92.5827%) to the
saved __foldl1 continuation 2. It feeds the returned object into the next loop
accumulator, not just an immediate field read. Any proposed virtualization must
handle loop-carried nested objects, known callback targets and eventual identity
observation; growing virtual chains can force materialization. A larger local
trace budget or deletion of returned wrappers does not implement this analysis.
The new closure-forwarding candidate removes 135,975,888 raw rest-pair bytes,
but actual first compile remains 5.520614 seconds and concurrent tests fail
7/27 batches. It is not the requested performance delivery.

D1338-D1345 refine the loop inference rather than implementing it prematurely.
Observed constructor inputs have wrapper depths only zero or one; no continuing
fold allocation sees an immediately equal next mark. All finishing fold-owned
allocations become syntax-e's result-pair fields. The measured opportunity is
therefore downstream: core-expand-head/core-expand1 consume 1,370,219 newly
constructed syntax-e pairs through CAR-only native continuations. Prior
getter-only counts did not cover these core macro sites. A projection-sensitive
callee/return analysis may avoid containers and proven-effect-free unused
construction, but must preserve unknown bindings, exceptions and unused-field
effects. This evidence favors that analysis over arbitrary-depth loop widening
or the previously rejected canonical mark-cancellation trace. It is not a
transformation, allocation-elimination proof or performance qualification.

### Literature Follow-through: Representation Changes Across Calls

The user is right to ask for research-guided optimization. PEA and SBBV were
already reviewed above; rediscovering those titles is not progress. The missing
step is connecting a transformation's assumptions to the measured producer,
loop, and consumer, rather than adding another generated-C fast branch.

[Gill and Hutton, The Worker/Wrapper Transformation](https://people.cs.nott.ac.uk/pszgmh/wrapper-extended.pdf),
sections 3 and 8, separates the public representation from an internal worker
representation and simplifies conversions between them. For this workload,
the candidate application is a compiler-created worker carrying known syntax
fields through a proven producer/consumer chain, with ordinary Scheme objects
at observable boundaries. Merely returning CAR without allocating the outer
pair is a much narrower optimization: it leaves the two field-producing folds
and their wrappers intact. Scheme identity, mutation, eager evaluation,
exceptions and continuations prevent importing the paper's functional
equations as a blanket correctness proof.

[Chevalier-Boisvert and Feeley, ECOOP 2016](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2016.7),
sections 4.2-4.3, specializes function entries and call continuations. Its
continuation scheme uses lazy compilation and invalidation of speculative
return-type assumptions; it explicitly discusses the cost of dynamically
dispatching returns. This supports studying caller/callee information
propagation, not copying its JIT protocol into Gambit's AOT backend. A static
worker with proven targets and the original generic entry is preferable to
assuming a new return-descriptor ABI is automatically safe or profitable.

The private D1346-D1358 prototype is not such a worker transformation. Its
producer arm preserves both operand computations and only tries to avoid the
final cons. The eight original/candidate output controls pass in the final
run, but required caller-marker coverage fails: the fixture's tail ##car is
lowered to JUMPPRM rather than the immediate CAR instruction recognized by
the pass. Thus these controls do not establish execution of the complete
optimized protocol. There is no admitted allocation reduction, CPU gain,
first-log improvement, full toolchain result or production patch from it.
Stop treating descriptor tagging alone as the main optimization.

The next bounded design should combine worker/consumer summaries with the
[PEA state model, sections 5.1-5.4](https://ssw.jku.at/Research/Papers/Stadler14/Stadler2014-CGO-PEA.pdf):
allocation identity, alias and field state, control-flow merges and explicit
materialization. Begin with proven targets and reject unsupported cases,
rather than borrowing Java deoptimization. In Gambit, _ptree2.scm's
br-app-inline (lines 1384-1432 in the pinned source) is an existing bounded
specialization point. _t-c-2.scm's per-instruction emission is too late to
infer the full producer/consumer and effect chain on its own. The precise
pass placement and treatment of register/stack liveness remain unresolved.

Admission must first show that the transformation reaches the dominant
stx-apply-mark construction chain, not only the 32,885,256 raw pair bytes at
the two CAR-only consumers. Keep all unused-field effects and original
evaluation behavior unless separately proven removable. Unknown/rebound
targets, identity observation, mutation, continuation capture, debug and
unsupported GC boundaries require original execution or correctly rooted
materialization. Consumer names select evidence, never a production allowlist.

[SBBV, ECOOP 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2024.28)
remains secondary: sections 4.4.3-4.4.4 report roughly 10% average execution
improvement at low version limits, and substantial compilation growth at
high limits. It is not evidence for a several-fold macOS startup fix. None
of these papers establishes our Darwin/Linux causal difference or predicts
MCP speedup. No broad baseline rerun is needed to make this design decision.
Production remains Darwin/GNU-only Gambit, with unchanged Linux, consumer
sources and real clean/build/concurrent test admission gates.

### Scope Correction: Platform Mechanism Before Generic Optimization

The preceding worker/PEA proposal is a general execution optimization, not a
Darwin-specific explanation or solution. Enabling a generic transformation
only on Darwin does not make its mechanism platform-specific. The user has
explicitly corrected this research direction: first connect the recorded
excess cost to a Darwin platform mechanism, then select its mitigation.
The proposed D1359 IR observer is not pursued as the next main experiment;
its initial hardware query failed under sandbox before any GSC command ran.

Platform references must distinguish XNU/dyld/Mach-O behavior, the GNU GCC
Darwin target/ABI, and Apple CPU microarchitecture. The latter also exists
under Linux on Apple hardware and is not by itself an OS-specific cause.
Existing rejected flag, loader visibility, packing and GC experiments remain
negative evidence; a new reference does not authorize repeating them.

[Apple, Link fast: Improve build and launch times, WWDC 2022](https://developer.apple.com/videos/play/wwdc2022/110362/)
describes a concrete platform boundary: chained-fixup page-in linking is used
at launch, whereas later dlopen loads apply fixups during the dlopen call.
It also identifies image count as controllable loading work. This is a
platform technical reference, not a peer-reviewed paper or proof of our
remaining MCP bottleneck; current OS applicability still requires checking.

Our existing D1194-D1195 Native evidence connects image reduction to the
disappearance of dyld/Atlas stacks. Do not repeat that attribution campaign.
Conversely D1207 and D1267-D1270 explicitly reject extending that result to
the entire remaining MCP first-log window: Scheme execution still dominates
the passive preparation's user CPU, and packing did not deliver full-cycle
acceleration. Neither all MODULE-LOAD time nor all macro execution time can
be relabeled as dyld work.

Next source/literature work must state the exact Darwin difference it changes,
the existing receipt locating that difference in the relevant workload, and
why the already rejected candidate does not cover it. A missing platform
attribution is an unresolved research condition, not permission to assert
generic temporary-object elimination solves the Darwin penalty. No production
code or admitted optimization is added by this scope correction.

D1361 tests platform-hypothesis admission against actual original GNU GCC
preprocessing, not another workload benchmark. SINGLE_THREADED_VMS excludes
the pstate TLS getter; SETJMP uses the compiler builtin rather than BSD libc;
SUPPORT_LOWLEVEL_EXEC is absent, so ordinary Scheme heap allocation is not
the JIT executable-memory/cache-flush path; monotonic time selects
mach_absolute_time rather than a wall-clock fallback. These mechanisms cannot
be selected as the main optimization from platform literature alone.
The canonical git.cons.io staging is rechecked at the existing 1cfb032 head;
the older GitHub mirror is not a substitute. See
receipts/d1361-darwin-platform-branch-admission.md for scope, failures and
identities. No product acceleration or production change is established.

D1365 sharpens the platform gate rather than admitting another generic
optimization. Apple's published dyld source corroborates the kernel versus
in-process fixup boundary, but is not matched to the installed OS. Original
core/stx objects contain 2,167 host-label absolute relocations; object
relocations are not final dynamic fixup counts or measured loader cost.
Neither this count nor sampled load/store PCs establishes a major-cost fix.
The large temporary-object count also does not imply per-object Darwin
malloc calls: Gambit's small-object path bumps a heap pointer in msections.
See receipts/d1365-darwin-mechanism-research-gate.md. No Darwin-specific paper
proving this workload's several-fold acceleration has been found; platform
technical references are labeled as such, without replacing that missing
evidence with general compiler papers.

D1366 checks final linked fixups rather than extrapolating from objects:
core/stx label tables are in the chained-fixup main executable, not repeated
dlopen work. Reanalysis of retained D1102 stacks gives 4.897 percent dlopen
inclusive cycles for passive MCP preparation; categories overlap and are
not first-log wall-time attribution. Relative label tables are not admitted
as the next major-cost patch. D1367 separately verifies an actual Darwin VM
API boundary with GNU GCC: ordinary 2 MiB allocation/release succeeds, while
both explicit superpage requests return KERN_INVALID_ARGUMENT on this
arm64 host. The superpage-heap route is not pursued. See
receipts/d1366-linked-fixups-and-superpage-admission.md for exact scope and
retained reports. No runtime speedup, full build or test delivery is claimed.

D1368-D1369 checks the actual linked instruction pairs before selecting a
GNU Darwin PIC/visibility workaround. The hot core/stx entry loads address
the ordinary module-local lp pointer, not a GOT slot. All 2,155/227 paired
GOT references within those original host functions are already relaxed
from adrp/ldr to adrp/add in the final executable, with no unpaired GOT
page references. Symbol visibility is therefore not admitted as the next
major-cost optimization for these hosts. This says nothing about every
other dynamic image and is not an exclusive latency measurement. See
receipts/d1369-linked-got-cost-admission.md; existing sampled PCs are also
checked against final linked opcodes without another workload profile.

D1370 verifies another GNU Darwin boundary without a flag-sweep workload:
native detection works and resolves apple-m2, while default resolves
apple-m1. The installed compiler's default/native/explicit M1/M2 tuning
model dumps are byte-identical. This does not prove identical generated
code because ISA features may differ, but native alone does not replace
the hypothesized generic scheduling/cost model. No large acceleration or
Darwin OS cause is inferred from CPU names. See
receipts/d1370-gnu-darwin-native-tuning-admission.md; no production flags or
source are changed and no full toolchain rebuild is started for this premise.

D1371 audits evidence coverage before selecting another platform patch.
D1102 is original passive preparation, whereas D1220 is a partial actual
first window from a failed composition candidate; their costs and code
identities are not interchangeable. The user's exact CI has matching parser
head f35b141, but pins Gerbil release 2591dcd with Darwin-arm64/Linux-x86_64
assets rather than the current staging investigation. The whole Native steps
are 273/113 seconds, confirming a large disparity without locating one
exclusive startup mechanism. The passive dlopen percentage is not a bound
on official first-log wall time. See
receipts/d1371-existing-first-window-and-ci-coverage.md. No workload is
rerun, no existing disparity is dismissed and no source experiment is admitted.

D1372-D1375 adds actual original official-prefix evidence rather than another
passive-preparation comparison. Two old checkouts fail cold-image admission;
a fresh identity-matched checkout passes clean and output gates. D1375's
recorder-ready notification still does not prove complete prefix coverage.
Conservative timestamp truncation separates the actual build-child samples
from post-first diagnostic teardown. The prominent later Atlas stack runs
through Gambit cleanup_dyn_module, dlclose and dyld removeImages, and must
not be called first-log macro cost. Before the cutoff, core/stx and marking
remain substantial sampled CPU costs; no Darwin cause or speedup is inferred
from their shares. See receipts/d1375-original-official-prefix-boundary.md.
No production patch or full build/test qualification is claimed.

D1376-D1380 executes the previously untested lowopt recipe delta, without
renaming it a Darwin-specific algorithm. Actual core/stx code replaces many
direct branches to shared br sites with local br sites. An unchanged-source,
unchanged-GSC partial runtime binary is built and imports std/make/std/test.
The copied-home clean lane fails its original 30-second gate and remains
unqualified. The separate original-library-home first-window ABBA passes
strict gates but means are 5.956 versus 5.883 seconds, only 1.23 percent with
overlapping ranges. This does not satisfy the requested major optimization;
the candidate is not solidified into a product Patch or full toolchain build.
See receipts/d1380-default-lowopt-first-window-rejected.md for identities,
real commands, the failed lane and the admission boundary.

D1381-D1382 crosses the binary variable in D1378's copied-home failure:
the original binary also fails copied-home clean at 30 seconds, with a live
two-second stack sample concentrated in dyld mapSegments/__fcntl. All 1,992
inventoried native images are byte-identical; original-inode hardlinks at a
new path still take 16.092 seconds and show the same loader syscall boundary.
This does not isolate one signing/cache/policy cause or qualify acceleration.
Published dyld has library-validation fcntl in that path, but it is not the
installed OS source identity. No validation bypass or attribute removal is
performed. Do not call these copied-home delays macro/codegen regressions or
use them to promote D1380. The original prefix remains unresolved. See
receipts/d1381-d1382-copied-home-loader-boundary.md.

D1383-D1384 observes an original-home clean failure rather than extending
the copied-home conclusion by assumption. Both original clean attempts fail
their unchanged 30-second gate. In the second run, cumulative CPU is only
1.548 seconds at the roughly 25-second snapshot, and 167/183 short-stack
samples reach mapSegments/__fcntl. The installed dyld UUID matches the sample;
the matching call instruction passes command 0x62, identified by the SDK as
F_CHECK_LV. This fills the previously missing installed-command identity, not
the policy/provider/cache cause or ordinary successful first-window attribution.
Mach CPU tick conversion is calibrated against getrusage. No validation bypass,
new product patch, full build or acceleration claim is admitted. See
receipts/d1383-d1384-original-library-validation-boundary.md.

D1385 audits reuse before changing the loader: Gerbil's module state table
already avoids ordinary duplicate module loads, Gambit retains successful
dlopen handles until cleanup, and published dyld checks loaded paths/file IDs.
These do not prove no aliases exist, but do not admit a new handle cache as
the major-cost fix. Exit-only unload suppression cannot fix first-load
validation and has separate destructor/embedding semantics. An explicitly
unqualified original build-only diagnostic also fails the unchanged ten-second
gate before any output; successful-prefix counters remain missing. No live
named tracing tool is found, no product patch is added and no validation is
bypassed. See receipts/d1385-loader-reuse-admission.md.

D1386 narrows the validation window to an own-process native FD: original
std/net/uri~0.o1 is open near the F_CHECK_LV short sample. Its strict on-disk
codesign verification passes, so a signature-content repair is not justified.
Published XNU dispatches validation to registered policy callbacks, but the
installed provider and its latency remain unidentified. Exact-home/owned-PID
security-log filtering returns no events; broader Homebrew events are excluded.
Original clean completes in 21.507 seconds with short sampling, but subsequent
build fails the unchanged ten-second gate without output. No first-compile,
acceleration, product change or full-toolchain admission follows. See
receipts/d1386-validation-file-and-policy-boundary.md.

D1387 checks a distinct observation capability instead of repeating user-stack
samples: installed spindump supports target-only user/kernel capture, but live
sampling requires root and noninteractive sudo has no authorized credential.
Only the capability command's own process is targeted; no new Gerbil run or
capture is performed. Local scoped authorization is needed for this observation
route, not permission to change security policy. The missing kernel/provider
evidence is retained and no performance or product claim follows. See
receipts/d1387-kernel-observation-access.md.

D1585 corrects the prior parent-only native-load observations: the build.ss
shebang removes DYLD_PRINT_LIBRARIES, hiding 37 child-only module loads. A Gambit
observer records both processes; 317 current objects pass source/native parity.
Same-binary actual MCP regex tests pass 912 cases with about 1.91x observed
completion improvement, but every corrected first-log ABBA build fails its
unchanged output gate, and macro-heavy std/make also fails. Neither first-log
nor whole-toolchain success is admitted. Keep existing patches and retain this
prototype as research only. See receipts/d1585-family-native-reuse-and-first-log-gate.md.

D1589 proves executed reuse rather than selected coverage: outer 274 hits plus
three FFI loads, actual builder child 198 hits and zero native fallback. In the
successful instrumented clean/build prefix, all native events finish by +2.236
seconds but first compilation is +7.044 seconds. Preserve the approximately
4.8-second post-load interval as the next execution-cost target, not a resolved
startup claim. The enabled child's diagnostic stacks now expose expander/GC
execution. See receipts/d1589-executed-family-reuse-boundary.md.

D1596 combines the original retained guarded-outline carrier with all 317
family/regex objects, instead of the original carrier used in D1579. One real
MCP clean/build completes with first compile 4.642 seconds and complete build
68.562 seconds; this candidate-only row is not a historical baseline speedup.
Actual native wrapper/GC contracts pass, but both first-log controls fail, the
wider unit ABBA has twenty output-gate failures, and cold std/make fails. The
composition remains private research, not an admitted startup/toolchain fix.
See receipts/d1596-original-outline-family-reuse-composition.md.

The user fixes the real MCP project-cold complete-build performance ceiling at
55 seconds, relative to the retained D1513 candidate mean of 52.617045 seconds.
D1592's 68.561755-second build fails this ceiling even though its first compile
appears at 4.641963 seconds. Construction success and first-log improvement do
not override the complete-build gate. The private complete-build driver records
the 55-second gate independently of its 180-second diagnostic termination
budget; neither the ten-second build-output nor five-second test-output gate is
relaxed. See receipts/d1599-mcp-complete-build-performance-ceiling.md.

D1602 extends process-launch observation with diagnostic child reaps and CPU
usage. First compile is 4.932 seconds, but the real MCP build fails its existing
watchdog and cannot pass the 55-second ceiling. A matched 48-second GSC task is
almost entirely bounded by its downstream gambuild-C task, which records about
12.52 CPU seconds. Module identity/GCC phase and the cause of the historical
68-second build remain missing; do not promote this failed partial diagnostic
to a speedup or resource explanation. See
receipts/d1602-tail-task-lifetime-diagnostic.md.

D1604 completes the task-identity diagnostic: clean succeeds, first compile is
4.709 seconds and complete build 71.716 seconds, failing the 55-second ceiling.
All 1,482 observed launches match successful reaps. The long C task is the
already-investigated embedded string module; it ends about 18.54 seconds before
completion, followed by broad late compilation and the final closure object.
Retain D857/D858/D966 and D1416 boundaries rather than repeat their atomic string,
header or producer-fusion experiments. No new speedup or production patch is
admitted. See receipts/d1604-task-identity-and-tail-boundary.md.

D1606 returns to the exact original D1513 candidate binary as A and compares it
adjacently with the later 317-object composition B, sharing original compiler/
runtime inputs and twelve workers. Complete ABBA times are 83.238/74.532/74.694/
77.341 seconds; every construction succeeds but every 55-second performance
gate fails. In this batch B is faster, so unmatched historical 52.62 versus
68.56 does not prove composition-caused regression. Keep the historical D1513
reference and fixed ceiling; neither a release nor a resource explanation is
admitted. See receipts/d1606-original-outline-and-composition-adjacent-abba.md.

D1609 records the actual verified D1590 builder child after clean, with first
compile 4.819 seconds and unchanged output gate passing; build is deliberately
stopped, not complete. Hardware data spans only 0.402 seconds, so its GC-heavy
shares are not whole-window attribution. Old D1108 debug text differs by 44
bytes; a new current debug object passes complete text/relocation equality and
maps twenty native PCs. Preserve the short-window and existing rejected-route
boundaries. No optimization is admitted. See
receipts/d1609-current-first-window-cpu-and-exact-map.md.

D1613 uses the installed profiler-start notification to resume an entry-paused
own builder under unchanged output gates. Hardware rows now span 4.507 seconds,
not the earlier 0.402-second burst: coalesced host 33.55%, two mark_array variants
28.66% combined, GC hash lookup 5.24%. All 1,151 host PCs map through the current
byte/relocation-identical debug object. Arity/return categories remain modest
fractions of total CPU, not major removable single hotspots. Paused/profiling
wall time is not speed evidence and no complete build is admitted. See
receipts/d1613-entry-gated-wider-cpu-boundary.md.
