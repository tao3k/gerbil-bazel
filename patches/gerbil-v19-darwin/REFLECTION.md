# Gerbil v0.19 Darwin build reflection

This document is the decision boundary between one experimental round and the
next.  A patch is not promoted because it compiles, passes focused tests, or
improves observability.  It must address the measured owner of the cost and
survive the admission gates below.

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

This evidence changes the next hypothesis. It is no longer “make POO faster.”
The compiler needs an explicit, generic job-class contract so executable/link
closure work can be admitted as critical-path work without consumer-name
knowledge, fixed worker counts, a second executor, or producer starvation.
Before admission the implementation must prove bounded fairness, follow-up job
draining, parameter capture, first-error propagation, and identical artifacts.
The complete comparison then runs both consumers from a true clean boundary.

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
