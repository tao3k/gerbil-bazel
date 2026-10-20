# D970 Guarded Trace Progress, Not Startup Qualification

The main gate remains the first actual MCP compilation after official clean.
Neither reordered output nor an import-only timing closes that gate.

## Scope

Latest staging was verified at Gerbil
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, with Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f` and unchanged MCP
`9a5c35e275e5d6847ff421151bb224f2eae177c1`.
GNU GCC 16, existing O1 generated-code options, and hardware-derived 12-way
capacity are retained. Consumer Scheme code and std/make are unchanged.

This is an isolated generated-GVM prototype, not yet a Gambit source patch or
a rebuilt and qualified full toolchain. Its compile-time guard restricts it to
Darwin, GNU/non-Clang, single-host label-values, single-threaded single-VM and
three argument registers. Other configurations execute original code.

## Execution Contract

Read-only static call chains guard live global bindings and the full procedure
descriptor selected from mutable dispatch vectors. Type fields are read live;
there is no result cache. Misses execute unchanged original instructions.
Success commits registers and active original frames, retaining original
continuation descriptors. Initial traces do not cross safepoints or allocations.

The original native contract and 12 concurrent candidate executions pass.
Actual guarded-path counters are required, alongside strict original-output
equality. Tests include function/vector rebinding, nonprocedure errors, type
descriptor mutation, GC, continuations and threads.

## Bounded Performance Evidence

All four paired preparation runs import the same 187 real MCP modules:

| Order | Runtime | User CPU (s) | Wall (s) |
| --- | --- | ---: | ---: |
| A | Original | 4.747228 | 5.236388 |
| B | Candidate | 4.345953 | 4.939197 |
| B | Candidate | 4.153899 | 4.561375 |
| A | Original | 4.751042 | 5.242877 |

Mean user CPU falls approximately 10.51%. Official clean followed by a real
build produces its first compilation at 5.440856 seconds. That observation was
deliberately stopped at the first log: it is not a full build/test pass, a paired
official speedup, or resolution of the startup objective.

## Further Candidates

D971 adds original safepoint checkpoints and opaque original-method handoff.
An interrupt checkpoint materializes original registers, parameters, frames and
resume descriptor before entering the original stack-limit handler. Countdown
heartbeat and debug-stack-limit configurations retain original code.
Twelve concurrent native probes each execute forced interrupts and actual GC;
one records 205 checkpoints, 11 forced interrupts and 11 GC callbacks.

D972's shortest-guard selection chooses cold branches: paired mean CPU rises
from 5.074285 to 5.311566 seconds. It is rejected, not promoted. D973/D974 extend
coverage and correct empty branch guards; no speedup is claimed before their
real workload qualification. No candidate here is added to the release stack.

Evidence stays under `.data/d970-guarded-trace-fallthrough-*`,
`.data/d971-guarded-trace-poll-contract-v2/`,
`.data/d972-guarded-trace-selected-*`, and `.data/d974-guarded-trace-checkpoint-*`.

## D977-D980 Actual Coverage And Remaining Gate

D977 extends the chain through original dispatch after restoring the original
stack continuation. Its paired preparation CPU results remain modest:
5.919138 / 5.337133 / 5.185735 / 5.894987 seconds, in A/B/B/A order,
approximately 10.93% mean reduction. All four runs prepare 187 modules and
exit zero. It does not meet the requested large startup improvement.

The D978 counter-only binary records 31996096 attempts and 31743532 successes.
The core resolution site records 30375132 attempts and 30375115 successes;
the standalone hash-get entry records 601 attempts and 601 successes. These
prove real coverage, not proportional CPU attribution or performance of the
instrumented binary. The candidate contract includes a sustained hit batch
and retains per-iteration GC stress. Twelve native executions pass; one records
913 checkpoints, 46 forced interrupts/GC callbacks and 205 successes.

A global-process-query monitor blocked during the first D977 official probe;
that overrun is not admitted as a first-window receipt. The monitor now queries
only its direct child. A subsequent clean rejects 550 residual native images.
A fresh local checkout at the same MCP HEAD, followed by official clean,
confirms zero images and records first actual compilation at 6.570136 seconds.
It is deliberately stopped thereafter. A sampled window includes the common
GVM host and GC marking, but is not complete CPU attribution.

D980 retains every original virtual-FP safepoint condition. Because the trace
has no heap writes or allocation and has not committed registers/frames, a
trigger can restart unchanged original instructions instead of retaining cold
checkpoint materialization state. Original handlers, maps and resumptions
remain in those instructions. Countdown/debug configurations stay excluded.
Original plus 12 concurrent forced-interrupt/GC native probes pass; performance
qualification is recorded below. No full toolchain, full MCP build/test, or
release-patch promotion is claimed.

## D980-D982 Bounded Results

D980 A/B/B/A preparation user CPU is 5.301580 / 4.327364 / 4.143461 /
4.955821 seconds, approximately 17.41% mean reduction. D981 checks maximum
virtual stack depth at both ends of the bounded read-only region; its paired
CPU is 4.925498 / 4.089614 / 4.078499 / 5.052155 seconds, approximately 18.14%.
These are separate paired workloads, not interchangeable official first-log
receipts, and neither closes the objective.

D982 follows the original call shell up to, but not through, the existing C
gc-hash lookup instruction. It executes that instruction unchanged and does
not cache lookup results. Paired preparation CPU is 4.595768 / 3.815436 /
3.814493 / 4.571385 seconds, approximately 16.77% reduction. Native original
plus 12 concurrent candidates pass, including movable keys and explicitly
required Scheme rehash. GC KEY_MOVED (4) and Scheme NEED_REHASH (32) are
different flags; the fixture does not falsely infer the latter from GC alone.

## D983 Experimental Prefix Cache

The next isolated prototype memoizes only validated read-only prefix words.
All observed input words are checked; lookup keys remain live and the original
C lookup still executes on every hit. Conservative mutation fences invalidate
on unknown instructions and global or heap writes. Every external common-host
entry invalidates as well, covering GC, RTS and non-coalesced code. Stamps
permanently disable after unsigned wraparound; cached words are never roots.
Only the existing single-threaded Darwin/GNU configuration admits this path.

The v5 native contract passes original output comparison and 12 concurrent
executions, requiring actual cache hits. Same-host vector/global mutations,
changing lookup contents, forced interrupts/GC and explicit NEED_REHASH writes
are covered. This is not yet a performance success, source patch, full toolchain
or official MCP build/test qualification. Generation failures are retained as
failures: parameter-check syntax and multiline macro boundaries were corrected
before performance admission.

D983's real paired preparation CPU is 5.892776 / 4.679701 / 4.269651 /
4.815278 seconds (A/B/B/A), approximately 16.42% reduction; host load changes
substantially within that run. Official clean on a fresh unchanged MCP checkout
records first compilation at 6.656688 seconds and then deliberately stops.
The startup goal remains open.

D984's counter-only binary explains why the cache adds no benefit: zero real
cache hits across 32979564 attempts and 31743545 completed traces. Main site 73
records 30375132 attempts, 30375107 completions and zero cache hits. Leading
stale-prefix reasons are pure SYMBOLP at stx line 534 (10666655), external host
entry (9633911), pure FIXPOSITIVEP at core line 12482 (7206336). Key-slot
collisions at site 73 contribute 2900357 further misses. Native fixture cache
hits therefore cannot stand in for real-workload cache coverage.

D985 corrects pure-predicate fences using their actual header definitions,
while retaining unknown operations, actual writes, external entries and lazy
rehash invalidation. Original and twelve concurrent mutation/GC/rehash probes
pass. The candidate binary and real MCP performance gates are still pending.
Evidence: `.data/d983-epoch-prefix-*`, `.data/d984-epoch-prefix-*`,
`.data/d985-epoch-read-fences-*`.

D985 still does not close the gate: paired CPU is 4.736844 / 3.994400 /
4.261187 / 4.754445 seconds, about 13.02% reduction, and official first
compilation is 6.650 seconds. The epoch-cache lane is not promoted. D986's
attempt to combine it with kernel code fails native compilation because the
prototype fences do not preserve arbitrary embedded C control flow. The
combination remains prohibited by the CLI. Broader foreign-callback mutation
qualification also remains open for the epoch prototype.

## D987-D988 Uncached Lookup And Return

D987 executes the existing C lookup once within a bounded trace and folds its
read-only return chain. Main core coverage reaches frame delta zero, instead of
materializing the lookup shell's eight-word frame first. A post-lookup miss
materializes the exact state just after that original instruction and resumes
there; it never restarts the lookup. Pre-lookup misses keep the original root.
Entry/exit stack-trip checks remain; dynamic-runtime configurations are excluded.
There is no epoch cache, lookup-result cache or mutation-fence instrumentation.

Original plus twelve concurrent native probes pass, including the subsequent
restoration-folding variant. Paired CPU is 5.730682 / 4.544590 / 4.446641 /
5.504951 seconds, about 19.98% reduction. Official clean on another fresh
unchanged MCP checkout records first compilation at 6.374 seconds, then stops.
This is still not the requested startup improvement or full build/test receipt.

D988 outlines bounded traces into normal native helpers with an explicit GNU
O3 attribute; the original GVM carrier stays O1 and consumer flags stay unchanged.
Helpers have distinct pre-effect and post-effect failures, export only required
words, and propagate only exact equal-word facts established by successful
guards. Cold snapshots keep their earlier facts. Native original-output
comparison and twelve concurrent mutation/GC/rehash executions pass. A real
gxi builds and passes standard imports; actual MCP performance is pending.

Evidence: `.data/d986-epoch-kernel-contract/`, `.data/d987-inline-lookup-*`,
`.data/d988-outlined-lookup-*`. No new candidate is promoted to a release patch.

D988 paired CPU is 5.971413 / 4.725854 / 4.880970 / 6.192015 seconds,
approximately 21.02% reduction. Its official first compilation is 10.583
seconds during substantial load. Neither this nor the CPU result solves the
startup objective. Outlining is not promoted.

## D989-D990 Correctness Audit Before Cache Admission

The mutation-fence audit finds a separate prologue defect: placing an extra
statement between IF_NARGS_EQ and GET_REST changes the macro's trailing else
binding. Existing output comparisons did not establish that control-flow
contract. Historical epoch performance samples are therefore not sufficient
for promotion regardless of their timings. Argument-processing macros now
remain unmodified; an external handler return still invalidates the epoch.

The prototype now rejects arbitrary embedded C control flow and foreign
callbacks instead of splitting them with barriers. Exact bounded constant
result blocks consisting solely of FIX constants and register assignment are
recognized separately. Tests cover preserving the rest-parameter else,
rejecting calls and arbitrary C, and accepting only constant-result blocks.
All 29 focused tests pass. The corrected native reference and twelve candidate
executions pass actual cache hits, mutations, GC and required rehash. D990's
counter-only real-workload coverage is pending; no performance claim follows.

D990's corrected real-workload counter completes all 187 imports. It records
32979570 attempts, 31743545 completed traces and only 14236 cached prefixes.
Main site 73 records 30375132 attempts, 30375104 completions and all 14236 cache
hits. The last invalidation is external host entry for 27468558 prefix misses;
key collisions contribute 2972887. This rejects epoch caching as a substantial
startup solution in the current execution domain. No timing of this diagnostic
binary is admitted as performance evidence.

D991 reuses the existing native entry counter for Gambit std, the dominant
remaining external host in D948. It is a new procedure-level attribution, not a
repeat of already recorded host totals or optimization-level comparisons.

D991 resolves 41896194 std host entries: parameter closures created by
make-parameter account for 32723842 (16361861 procedure entries and 16361981
returns). Reverse and length contribute 4132799 and 2171981 respectively.
These counts include entrances from hosts omitted by the earlier selected
caller counter; they are not a CPU-share measurement.

D992 adds a caller-side prototype for zero-argument global calls. It recognizes
the exact original primitive parameter closure descriptor, requires the
original dynamic-ref binding, excludes special parameters, checks maximum
virtual stack depth and reads only the existing current-thread binding cache.
Every custom getter still executes. The setter and parameter representation
are unchanged; misses execute the unchanged call. It introduces no independent
parameter-value cache. The original and twelve native candidates pass at least
300 real hits, getter effects, multiple values, exceptions, setters, nested
dynamic contexts, rebinding, GC and twelve Scheme threads per process.

D993 expands to the original three-slot cache with precisely the same swap
and shift rules as dynamic-ref. The stronger second/third-slot fixture and
twelve native candidates pass. The first cache1-only real SDK binary is still
compiling; neither candidate has a real MCP timing or full-toolchain receipt.
Evidence: `.data/d991-std-label-*`, `.data/d992-parameter-entry-*`,
`.data/d993-parameter-three-slot-contract/`. The startup objective remains open.

D992's cache1-only paired CPU is 6.226221 / 5.626104 / 5.352801 /
5.655877 seconds, approximately 7.60% reduction. Its first compilation is
24.151 seconds during high load. The first observation overlaps part of the
CPU diagnostic; it is retained as an uncontrolled observation, not a paired
wall-time performance receipt.

D994 puts the three-slot parameter recognition into a separate bounded O3
native helper and combines it with outlined lookup/return traces. Original
plus twelve candidates pass both hit gates, actual GC, rehash, getter effects,
multiple values, exceptions, nested bindings and threads. Strengthened slot
counts are 299 / 1 / 1, proving all three paths execute rather than only their
fallbacks. Paired CPU is 6.021662 / 5.047245 / 4.977016 / 5.985820 seconds,
approximately 16.51% reduction. A subsequent separate official first compile
is 29.598 seconds under high load. This is not a startup solution.

D995 adds an exact captured-self guard: closure code identity alone is not
sufficient when low-level closure mutation changes the self binding used by
the original dynamic-ref call. Original plus twelve candidates pass a mutation
fixture that redirects captured self to another live parameter and requires
that parameter's value to flow through the original getter. The original
representation is unchanged. All 31 focused tests pass. D995's corrected SDK
binary, actual MCP coverage, full build/test and source integration remain
unverified. Historical parameter timings do not qualify the strengthened gate.

Evidence: `.data/d994-parameter-native-trace-*`,
`.data/d995-parameter-self-guard-contract/`. No new candidate is promoted.

D996-D998 stop stacking local fast paths and add diagnostic-only native PC
landmarks to original GVM labels. This is not a speed transformation: inline
assembler emits only exported labels, with no machine instruction or memory
clobber. It can still perturb code layout and optimization. Every observation
is explicitly excluded from performance comparisons. Other platforms retain
the original generated code. All 35 focused tests pass.

Upstream `v0.19-staging` is rechecked directly and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. Hardware remains 12 cores and 32 GiB.
The combined diagnostic translation unit hits its 300-second compile limit;
the retained cc1 observation shows only 29.61 CPU seconds after 227 wall
seconds. That failure is preserved, not called a compiler or startup gain.
The same 16326 landmarks in the original eleven separate modules compile
with hardware-derived parallelism. Native std/make/std/test import passes;
original GSC remains byte-identical. No new Scheme/source patch is admitted.

The official clean/build first-window diagnostic passes clean but fails its
60-second observation cap under load 167-187. It reaches no first compilation
line. Its bounded sample includes 990/1571 main-thread samples under dlopen,
including synchronous dyld remote/debugger notifications. Sampling itself may
contribute to this waiting; this is an inference, not an independently proved
root cause. It does not supersede D895's separate native-loading/GC timers,
D890's startup boundary, or the original eight-second baseline. No system
security or debugger policy is changed.

D998 therefore samples the original 187-module preparation after actual
progress, at modules 12 and 86, rather than repeating an A/B timing matrix.
All 187 modules finish with IMPORT-OK and exit zero; both samples exit zero.
Neither contains the preceding synchronous dyld notification path. In the
listed self-sample groups, GC marking contributes 345/1327 and 438/1518;
identified GVM blocks contribute 363 and 451. The largest individual identified
procedure contributes 30 and 59 samples respectively. Groups below five are
omitted by sample, and these windows are not whole-startup CPU attribution.
They show distributed execution rather than a single dominant counted callee.
The diagnostic's reported CPU includes sampler processes and is not a speed
measurement. The startup goal, source integration, complete toolchain and
real MCP build/test qualification remain open.

Evidence: `.data/d996-native-pc-profile/`, `.data/d997-native-pc-profile/`,
`.data/d997-native-pc-first-window/`, `.data/d997-native-pc-summary.json`,
`.data/d998-native-pc-preparation/`.

D999-D1003 test a C-runtime-only GC hypothesis rather than another small GVM
leaf specialization. Original mark_array tail-marks a copied pair's car;
the queued scanner deliberately skips that field. The candidate tail-marks
cdr and changes both ordinary and fast pair scanners to scan car instead.
These coupled changes preserve scanning of both fields. The guard requires
Darwin, GNU/non-Clang, 64-bit, single-threaded/single-VM and one processor.
Other configurations retain the original field choices; no heap policy,
consumer flags, Scheme source, object layout or native ABI is changed.

Original and modified GNU syntax checks pass. The isolated mem.o, archive and
native relink pass with unchanged GSC. Native preprocessing confirms the
candidate branch is actually enabled. D999-D1001 baseline fixture setup fails
on unavailable imports/base exports and positional TestConfig construction;
these are retained fixture failures, not candidate GC failures. D1002 follows
the staging gxtest API. Original plus twelve concurrent candidate processes
pass two real std/test cases, each including twelve Scheme threads, shared
nodes, both car/cdr cycles, mutation, closures, continuations and live hash
keys. Each log includes MODULE-OK, HARNESS-OK and final GC-PAIR-TAIL-OK.
This is bounded semantic coverage, not complete collector conformance.

MCP preparation completes all 187 unchanged modules in each ABBA run. User
CPU seconds are 6.567988 / 6.626402 / 6.491634 / 6.540077. Candidate mean is
6.559018 versus control 6.554033: no execution-cost gain. Traversal reordering
does not remove the live copying/scanning work. The candidate is rejected,
not promoted, and no expensive full-toolchain or official first-log claim
follows. The seven-to-eight-second startup objective remains active.

Evidence: `.data/d999-pair-tail-original-syntax/`,
`.data/d999-pair-tail-source/`, `.data/d999-pair-tail-build/`,
`.data/d999-pair-tail-contract/`, `.data/d1000-pair-tail-contract/`,
`.data/d1001-pair-tail-contract/`, `.data/d1002-pair-tail-contract/`,
`.data/d1003-pair-tail-cpu/`.

D1004-D1006 retain the original collector algorithm and field visitation order
but batch strong GC-table key/value fields through a private descending
stride-two marker. Original mark_array and non-Darwin/debug/multi-processor
paths remain. No heap policy, weak-reference policy, Scheme source, consumer
flags or ABI changes. Native GNU syntax, isolated mem.o/relink and std/make,
std/test imports pass; original GSC is unchanged. Upstream staging is rechecked
and remains the recorded 1cfb032 commit.

The native fixture is strengthened to 1024 live object keys with growth and
one-third deletions. Original plus twelve candidate processes pass MODULE-OK,
HARNESS-OK and the explicit final success marker; each retains the twelve
Scheme-thread and graph/cycle/continuation cases. Preprocessing confirms the
new batch branch is enabled. This is bounded correctness evidence, not full
weak/finalizer conformance or a startup result.

All 187 unchanged MCP modules complete in each ABBA run. User CPU seconds are
5.984443 / 5.821977 / 5.881908 / 6.016410. Candidate mean 5.851943 versus control
6.000427 is approximately 2.48% lower. This is insufficient for the requested
substantial startup fix, so the candidate is rejected and not promoted.
No official first-log or full-toolchain speedup is claimed.

Subsequent source review corrects the generator to retain the original int
index conversion even for oversized tables. A numeric regression test covers
descending visitation and conversion cases. The tested D1004 binary predates
that generator correction; its qualification does not transfer to newly
generated source. Rebuilding a rejected candidate solely for performance is
not justified. All 38 focused tests pass with the corrected generator.

Evidence: `.data/d1004-strided-mark-generation/`,
`.data/d1004-strided-mark-source/`, `.data/d1004-strided-mark-build/`,
`.data/d1005-strided-mark-contract/`, `.data/d1006-strided-mark-cpu/`.

D1007-D1008 add counters to the original marker, without changing its copying,
forwarding, visitation or weak-object algorithms. Darwin/GNU, single-VM,
single-processor and eight-byte-word guards limit the diagnostic. GNU syntax,
native mem.o/archive/link and framework imports pass, with original GSC retained.
Three generator tests verify that removing the added hooks reconstructs the
original marker exactly. Instrumentation is not a timing candidate.

All 187 MCP module preparations complete and the counter invariants hold:
75,524,454 marker calls, 52,633,995 single-cell calls, 197,833,368 visits,
126,142,235 allocated-object visits, 43,237,938 copies, 50,984,834 forwarded
pointer repairs and 31,914,212 permanent-object visits. Copies include
21,132,499 structures and 17,994,753 pairs; copied bodies total 193,481,516
words. Counts do not establish CPU shares or distinguish repeated copies of
the same surviving object from distinct objects.

D1009 reads the existing native process-statistics primitive on the original,
uninstrumented runtime after the same 187-module preparation. Its field layout
is verified from `_kernel.scm`, not consumer diagnostic recipes. Process user
CPU is 5.839921 seconds; GC user CPU is 1.199264 seconds (approximately 20.5%).
There are 27 collections, 4,403,969,272 allocated bytes, latest heap capacity
1,180,049,480 bytes and latest live data 515,622,744 bytes. These are one workload's
native statistics, not an official cold-build or paired speed result. They cap
the potential of collector-only optimization for this preparation; even
eliminating all GC cannot solve the requested major startup acceleration.
No speculative heap or copying policy is promoted. Two parser regressions
cover exact layout and missing/duplicate/nonfinite/wrong-length trailers.

D1010 extends instructionless native-PC landmarks to original `_kernel`,
`_std`, `_eval` and `_thread` C using original official compiler commands.
This specifically addresses the RTS attribution missing from D998 rather than
repeating its eleven Gerbil units. All four original-flag GNU objects compile,
archive/relink/import smoke passes, and GSC remains unchanged. There are 19,988
native landmarks. Native sample profiles must match the exact candidate binary
hash; runtime source hashes must also match before attribution. Diagnostics
remain distinct from speed measurements.

D1011 completes all 187 real module preparations with two eight-second sample
windows, starting after module 14 and module 112. All sample processes exit
successfully. Listed self-samples are 6,159 / 6,222; RTS-landmark samples are
574 / 418. The largest identified RTS process group is kernel-handlers at
117 / 102, followed by dispersed parameter, dynamic-environment, apply and
evaluator groups. Unchanged Gerbil stx/core and GC are the largest individual
execution groups. This does not identify a previously hidden dominant RTS
callee. These bounded summaries omit groups below five, can be influenced by
the sampling observer and landmark code layout, and are not full CPU-share
measurements. The reported process CPU includes sampler work and cannot
qualify performance. No official first-log or complete toolchain result follows.

The source-search focus therefore returns to the generated GVM execution
mechanism across stx/core, rather than another small native primitive or GC
micro-optimization. Existing private argument-register bridge, outlining and
guarded-trace receipts remain rejected/bounded as recorded; they are not
retroactively promoted. The seven-to-eight-second objective remains active.

D1012-D1015 test a distinct private calling convention: PC, FP and five GVM
value registers occupy fixed ARM64 callee-saved registers across registered
private hosts. Public host signatures, label layout, GSC and VM memory layout
remain unchanged. A shared assembly entry saves the native caller context once;
normal returns restore it, and legacy tail exits restore it before branching.
GC/FFI state synchronization remains. Darwin/GNU/ARM64/single-VM/one-processor
guards exclude other platforms. This is an isolated prototype, not a patch.

D1012 fails native compilation because original overflow builtins take the
address of a GVM result register. D1013 uses a same-typed ordinary temporary
for the same builtin, retaining its overflow-result write before returning its
original condition. All eleven original-O1 units compile, relink and pass
framework imports. Original GSC is unchanged. Native disassembly confirms the
96-byte context entry/exit and a frame-free start that tail-branches after
loading fixed state. This does not establish whole-program ABI conformance;
global register conventions also require callback, signal and nonlocal-exit
care as documented by GCC.

D1014's original-GSC/old-ABI fixture passes on the baseline and twelve native
candidate processes. Each passes 992 assertions including 330 explicit GCs,
C callbacks, exception escape and continuations. D1015 completes all unchanged
187 MCP preparations in ABBA order. User CPU seconds are
5.545931 / 5.440417 / 5.307921 / 5.530217. Candidate mean is 5.374169 versus
baseline 5.538074, approximately 2.96% lower. The broader fixed-state mechanism
still does not produce the requested substantial gain. It is rejected, not
promoted; no expensive full toolchain or official first-log run is justified
by this result. Heap/GC statistics remain separately recorded in each run.

Evidence: `.data/d1012-fixed-gvm-registers/`,
`.data/d1013-fixed-gvm-registers/`, `.data/d1014-fixed-gvm-interop/`,
`.data/d1015-fixed-gvm-cpu/`.

D1016-D1017 check another unrecorded Darwin boundary without changing scheduling:
the runtime installs thread affinity but does not explicitly set QoS. The first
native fixture fails because the current SDK's pthread_get_qos_class_np uses
three arguments and returns status, not the class directly. The corrected
original-GSC fixture reads the returned class and propagates API failure as a
negative value. Baseline plus twelve independent original VM processes all
report requested QoS 33, the installed SDK's QOS_CLASS_USER_INTERACTIVE value.
This does not show a background/utility requested class and does not justify
changing priority. The API reads requested QoS, not an effective core residency
measurement. No affinity or scheduling candidate is introduced. Evidence:
`.data/d1016-darwin-qos-probe/`, `.data/d1017-darwin-qos-probe/`.

Evidence: `.data/d1007-gc-mark-generation/`, `.data/d1007-gc-mark-count-build/`,
`.data/d1008-gc-mark-counts/`, `.data/d1009-native-gc-share/`,
`.data/d1010-rts-native-pc-source/`, `.data/d1010-rts-native-pc-build/`,
`.data/d1011-rts-native-pc-preparation/`.

Additional evidence: `.data/d977-guarded-trace-restored-*`,
`.data/d978-guarded-trace-count-*`, `.data/d979-guarded-trace-first-window/`,
`.data/d980-guarded-trace-restart-*`.

D1018 repeats no timing comparison: it captures a longer diagnostic PC window
in the already qualified Gerbil-only symbol binary. All 187 preparations pass.
Source-line inspection finds an attribution limitation: several frequently
sampled nearest labels actually point into the shared `___END_M_COD` exit,
not the procedure named by the preceding assembly landmark. These counts must
not be presented as semantic per-procedure CPU shares. Evidence:
`.data/d1018-gvm-long-pc-preparation/`.

D1019-D1025 explore a new, unqualified transactional pair-allocation trace.
The previous read-only tracer cannot cross fresh allocation. This candidate
reserves a bounded heap region, preserves individual restart polls, publishes
register/stack state only at successful completion, and restores the heap
pointer before falling back to untouched original code on a failed guard.
It permits only fixed-size CONS/XCONS, not existing heap mutation, callbacks,
closure allocation, or an external effect. Its branch remains Darwin/GNU-only.
Static path analysis is not runtime coverage and not acceleration evidence.

Initial dispatcher-only roots and unsupported pure reads produce zero sites.
After broadening unique global-call roots and modeling the relevant pure
reads/static pair constants, D1023 finds twelve real source sites: five core,
one module, six stxcase; each allocates three heap words and removes three to
five calls. D1024 fails native compilation because a terminal static procedure
label is emitted as a Python analysis object. The generator now translates it
through the native descriptor encoder; a focused regression is added and all
27 guarded-trace unit tests pass. D1025 is the repaired native diagnostic build.
Its initial compile reaches the 300-second wall budget without a compiler
error. The unchanged retained C is resumed under the existing 600-second
budget; native GNU compilation, link and standard imports pass, with GSC
unchanged. The resume receipt, not the failed initial receipt, establishes
native qualification. No startup gain, allocation rollback qualification, or full
toolchain success is claimed. Evidence: `.data/d1019-transactional-pair-traces/`,
`.data/d1020-transactional-pair-traces/`, `.data/d1021-allocation-static-refusals/`,
`.data/d1022-allocation-static-read-coverage/`, `.data/d1023-allocation-static-predicate-coverage/`,
`.data/d1024-transactional-pair-native/`, `.data/d1025-transactional-pair-native/`.

D1026 runs the diagnostic binary on the real MCP preparation: 187 modules,
exit zero, 381588 attempts across ten reached sites, **zero successes**.
This rejects the candidate as an acceleration; no uninstrumented timing or
full build follows. Counted wall time is not a speed claim under host load
179. Source inspection finds selected paths that test a freshly allocated
pair as null. D1027 adds path-local fresh-pair and constant-boolean facts,
prunes impossible branches, and excludes debug heap-limit mode. Static coverage
is eleven sites, not runtime proof. The original read-only mode is unchanged.

A further bounded model permits only fresh fixed-size closures (at most
sixteen captured fields and sixty-four total trace heap words). It requires
owned setup, every field exactly once, and completed initialization before
trace commit; incomplete reads and existing-object setup are refused. Its
branch additionally requires no low-level closure trampoline and the original
one-word closure/subtyped layout. All 48 focused tests pass; this new model is
not native-qualified. D1028 finds 58 static sites. D1029 retains the actual
native PROCEDUREP check on a correctly encoded static label rather than
refusing that operand; it finds 71 sites. Other continuation-as-data operations
remain refused. All 49 focused tests pass.

D1030 builds the new diagnostic candidate with first-failed-guard counters
and site-to-condition metadata, so zero hits can be diagnosed from actual
runtime branch failures rather than static guesses. Its explicit compile wall
budget is 900 seconds; original default budgets, consumer flags, GSC and core
capacity are unchanged. Native GNU compilation, link and standard imports pass;
GSC remains unchanged. D1031 completes all 187 MCP preparations, exit zero.
The exact-binary joined coverage records 700177 attempts and 177110 successes
across thirteen sites, accounting for 531432 modeled fused virtual calls. Thirty-four entry-capacity
fallbacks are recorded separately from first-failed guards. This establishes
real execution, not performance or exhaustive rollback correctness. The two
largest core sites still have zero hits, predominantly failing data-shape
guards; several other large sites choose the less-used side of syntax-wrapper
checks. Coverage does not justify claiming the substantial startup gain.

D1032 extends the bounded model to fixed fresh structures and known calls up
to sixteen arguments. Structures require complete, nonduplicated fields and
cannot poll, call or nest allocation before completion. The original native
argument registers/stack expressions are preserved; no new calling convention
is introduced. All 53 focused tests pass, including known four-, six- and
sixteen-argument calls and incomplete/nested structure rejection. Static real
source coverage is eighty sites, nine involving fresh structures and nineteen
involving fresh closures; the maximum selected allocation is six words. This
extension is not native-qualified. No first
log or full-toolchain acceleration is claimed.

Priority remains the measured tens-of-millions execution boundaries, not the
small successful allocation coverage. Source inspection establishes a separate
unimplemented hypothesis: the default parameter get-filter is identity;
the current parameter shortcut still tail-calls that getter, crossing an
external host and invalidating a prefix epoch. Both native identity bodies
only return their single argument. A future shortcut must recognize the exact
original primitive getter, preserve SELF/nargs/continuation state, and retain
all custom getters and captured-self checks. This is a source hypothesis about
cache invalidation, not a claim that identity itself consumes dominant CPU.
No new parameter or cache implementation is qualified by this inspection.
Evidence:
`.data/d1026-transactional-pair-counts/`, `.data/d1027-allocation-static-type-facts/`,
`.data/d1028-allocation-static-fresh-closures/`,
`.data/d1029-allocation-static-procedure-labels/`,
`.data/d1030-transactional-allocation-native/`,
`.data/d1031-transactional-allocation-counts/`,
`.data/d1032-allocation-static-structures-wide-calls/`.

D1033-D1037 examine the parameter/epoch hypothesis without changing Gerbil,
consumer modules, compiler flags, or Linux behavior. Exact original identity
primitive getters can return directly, while custom getters retain the native
call path. SELF, nargs, captured-self and the original factory are checked.
Live getter replacement, multiple values, exceptions and rebinding the global
identity cell remain observable. D1033 fails its expected-output gate after
adding a counter marker; it is not a qualified candidate. The repaired D1034
passes the original baseline and twelve concurrent native candidate processes,
each also exercising twelve Scheme threads. This establishes correctness of
the bounded identity shortcut, not a startup improvement.

D1035 passes the semantic assertions but fails the separate requirement for
at least one hundred real prefix-cache hits: it records zero. That failure is
preserved. Inspection of the original dynamic-ref implementation explains a
coverage hole: unbound defaults are read from the current descriptor and are
not inserted in the three thread cache slots. The shortcut previously fell
back at every such read. The new opt-in path performs the original bounded
environment-tree lookup, preserving hash-collision ordering and the original
three-slot update on bound hits. It checks the original env-lookup binding,
falls back on unsupported nodes, and does not memoize default values. Cache
slot writes invalidate the prefix epoch; read-only slot-one/default reads do
not. No allocation or callback is introduced in the lookup.

D1036 passes the original native baseline and twelve concurrent candidates,
including live default setters, colliding parameter hashes, environment-lookup
rebinding, getter effects, GC and thread isolation. One candidate records
10645 parameter shortcuts, 10322 identity returns, 10004 default lookups,
37 environment-tree hits and 7996 actual prefix-cache hits. These fixture
counts are not MCP coverage or CPU shares. All 56 focused Python tests pass.
D1037 builds a diagnostic runtime for real MCP coverage, with a separate
parameter-counter sidecar and an explicit 900-second native compile budget.
Its result and the real-MCP measurement are pending; no seven-to-eight-second
startup resolution, performance gain or full-toolchain qualification is claimed.
Evidence: `.data/d1033-parameter-identity-contract/`,
`.data/d1034-parameter-identity-contract/`,
`.data/d1035-parameter-identity-epoch-contract/`,
`.data/d1036-parameter-env-epoch-contract/`,
`.data/d1037-parameter-env-epoch-count-profile/`.

D1037 subsequently passes GNU compilation, link and standard imports, with
GSC unchanged and no consumer flag changes. D1038 completes 187 real MCP
preparations, exit zero. The diagnostic sidecar records 16159871 parameter
shortcuts, all original identity getters: slots 564052/3103263/10288418,
75715 defaults and 2128423 environment-tree hits. The categories sum exactly
to the shortcut count. Main core-context site 73 has 30375565 attempts,
30375444 successes but only 14177 cached prefixes. Last-invalidating reasons
include 15455697 thread-cache writes, 11978617 external host entries and
3005368 same-epoch collisions. Thus this candidate does not solve cache
coverage. Diagnostic CPU/wall values are not performance evidence, especially
under host load 148. No uninstrumented acceleration is claimed.

The next bounded hypothesis separates the epoch for parameter cache-slot
writes from the general mutation epoch. Original header writes are exactly
thread fields 25/26/27. Only statically proven low-field prefixes can ignore
that narrower epoch; matching, unknown, negative, nested uncertain indices
and unknown read operations remain sensitive. A native layout guard checks
word/tag/body offsets and the original field constants; other layouts retain
general invalidation. All other effects, global changes, external entries and
GC guards retain the existing global epoch. Wraparound disables affected
caches. The classifier does not assume object identity or current-thread
identity, so cached cross-thread reads are not excluded from protection.
All 41 focused trace/parameter unit tests pass at the initial classifier stage.

D1039 passes baseline and twelve native candidates, but inspection finds
that the added thread-slot fixture never became a cached prefix. It therefore
does not qualify the new field-sensitive protection. D1040, D1041 and D1042
preserve explicit static-coverage gate failures. D1043-D1044 inspect generated
paths: the existing trace selector only accepts identity-result returns, so
a direct field-value return is not a relevant fixture. D1045 changes the
fixture to an identity branch controlled by the actual slot-25 value, keeping
the key fixed across real parameter-cache rotations. Qualification remains
pending. No first-log or full-toolchain result is claimed. Evidence:
`.data/d1038-parameter-env-epoch-counts/`,
`.data/d1039-thread-field-epoch-contract/`,
`.data/d1040-thread-field-epoch-contract/`,
`.data/d1041-thread-field-epoch-contract/`,
`.data/d1042-thread-field-epoch-contract/`,
`.data/d1043-field-trace-static/`, `.data/d1044-thread-trace-refusals/`,
`.data/d1045-thread-field-epoch-contract/`.

D1045 subsequently passes its explicit cached-slot-25 generation gate,
original native baseline, and all twelve concurrent native candidate runs.
The fixture holds keys fixed, rotates three bound parameter slots, and compares
an identity-result branch controlled by the actual thread slot against a direct
read. Low-field prefixes and slot-sensitive prefixes retain separate epoch
requirements. Unknown operations stay conservative. Diagnostic attribution
also distinguishes thread-only stale misses from general mutation misses;
thread-only writes do not overwrite the last general-mutation reason.
All 43 focused trace/parameter/allocation-count unit tests pass. D1046 is the
fresh full diagnostic runtime build for the real MCP coverage check, with the
same 900-second compile budget, unchanged GSC and unchanged consumer flags.
Its qualification and real-MCP coverage remain pending. These are correctness
and coverage gates, not proof of a startup speedup.

D1046 passes GNU compile/link/import gates. D1047 completes all 187 MCP
preparations, exit zero. Main site 73 records 30375565 attempts, 30375523
successes and 5048854 cached prefixes (5060379 across all sites). The narrower
thread epoch removes the prior thread-slot invalidation reason, but cached
coverage is still only about one sixth of main attempts. Remaining reasons
include 14339945 external reentries, 4093117 CONS fences and 3684231 main-site
collisions. No performance claim follows from this diagnostic.

Source inspection verifies CONS/XCONS as fresh heap writes without an in-macro
GC or callback, and FIXASHL/NULLP as pure operations. A further prototype keeps
fresh-allocation fences as explicit metadata but makes them no-ops only in the
supported ordinary native layout. Closures require immediately preceding
constant allocation, matching target/size, contiguous complete unique fields,
and no intervening instruction; unowned, interrupted, duplicate or effectful
setup retains general invalidation. Handles, debug heap-limit mode and closure
trampolines retain the conservative fence. Existing-object modifications are
unchanged. All 45 focused unit tests pass. D1048 passes the baseline and twelve
concurrent native candidates, including real slot-sensitive cache protection,
getter effects, mutation and GC fixtures. D1049 passes GNU compile/link/import
gates with 1218 proven fresh-allocation fence sites, unchanged GSC and consumer
flags.

D1050 completes 187 real MCP preparations, exit zero. Main cached prefixes
increase only to 5895159 (5953301 across all sites), from 30375565 attempts.
The roughly 846000 additional main hits are insufficient for the substantial
startup claim; no uninstrumented performance or official first-log claim is
made. External reentries now explain 19297030 stale-prefix events, exposing
previously masked invalidations rather than a growth in proven CPU cost.
Further priority is the already-recorded large external primitive paths, not
more small epoch tuning. D991 records 4132613 procedure entries attributed to
##reverse and 2171950 to ##length; these are entry counts, not CPU shares.
Their original list source is read: primitive length scans pairs; primitive
reverse allocates fresh pairs; public variants additionally force/check list
tails. A bounded proper-list shortcut would have to retain public effects,
long/improper-list fallback, heap/stack/interrupt guards, exact primitive
identity, fresh reverse results and old native ABI. No such shortcut is yet
implemented or qualified. Current remote v0.19-staging is rechecked and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. Evidence:
`.data/d1046-thread-field-epoch-count-profile/`,
`.data/d1047-thread-field-epoch-counts/`,
`.data/d1048-fresh-allocation-epoch-contract/`,
`.data/d1049-fresh-allocation-epoch-count-profile/`,
`.data/d1050-fresh-allocation-epoch-counts/`,
`.data/d991-std-label-observation/std-label-summary.json`.

D1051-D1053 implement a separate opt-in bounded primitive-entry experiment,
not another result cache. Only exact original length/reverse/type primitives
can succeed; indirect targets must be pure register/stack/closure reads.
Unknown functions and unsupported targets retain the original call, without
duplicating a target expression that could call foreign C. Proper lists are
bounded at 64 pairs, ancestry at 128 descriptors, with explicit stack/heap
guards and ordinary Darwin/GNU/native-layout requirements. Reverse still
allocates fresh original-layout pairs. Long/improper lists and unsupported
type shapes retain original behavior. The native kernel body is checked: its
type loop reads descriptor fields directly and has no user getter dependency.

D1051 passes the baseline and all twelve native semantic assertion runs,
including improper private-list fallback and mutable type fields, but fails
the coverage gate because type shortcut hits are zero. Generated GSC code
has already expanded direct type calls; its remaining external type calls
need a first-class primitive entry. D1052 adds exact-identity guarded indirect
entries and a dynamic method-vector fixture, including replacement by an
effectful user function. It passes baseline and twelve concurrent candidates;
one candidate records 195 length hits, 195 reverse hits, 1803 type hits and
6240 freshly allocated reverse pairs. It also retains the existing real
slot-sensitive epoch, getter and GC contracts. All 50 focused unit tests pass.
D1053 is the fresh complete diagnostic runtime build, with a separate
`.primitives` counter sidecar. Real MCP coverage, uninstrumented CPU pairing,
official first-log latency and full build/test remain pending; no substantial
startup gain is claimed. Evidence:
`.data/d1051-bounded-primitive-contract/`,
`.data/d1052-bounded-primitive-contract/`,
`.data/d1053-bounded-primitive-count-profile/`.

D1053 subsequently passes GNU compile/link/import gates with unchanged GSC
and consumer flags. D1054 completes 187 MCP preparations, exit zero. Actual
shortcut counts are 2200401 lengths, 4111882 reversals and 1882596 reverse
pairs, but **zero type shortcuts**. Main prefix hits reach 10357169, with
10507579 across sites; coverage does not establish the required substantial
startup reduction. This remains diagnostic-only, with no paired uninstrumented
CPU, official first-log or full build/test qualification.

The zero type count is a concrete ownership gap: the prototype modifies only
the eleven selected Gerbil-generated units, while native Gambit callers remain
original. Inspection of original `_eval.c` finds actual one- and two-argument
indirect primitive entries, including register/stack/closure targets, and its
module-wide declarations already contain heap, frame and all five registers.
The next investigation must evaluate the Gambit interpreter/RTS entry coverage,
rather than declaring the selected-unit shortcut complete or adding more
small epoch tuning. No RTS entry modification is implemented yet. A runtime
unit override must preserve original library compilation flags/old native ABI,
keep GSC and baseline homes isolated, and distinguish each unit's diagnostic
counters from the existing coalesced sidecar. Evidence:
`.data/d1054-bounded-primitive-counts/`,
`.data/d935-staging-source/src/gambit/lib/_eval.c`.

### D1055-D1057: original interpreter coverage is not the dominant opportunity

An isolated `_eval.c` override preserves original generated metadata, register
declarations, fallback jumps and ABI. The source makefile proves this generated
Scheme library unit uses `FLAGS_OPT=-O1`, not `FLAGS_OPT_RTS=-O3`; the experiment
therefore explicitly retains O1. It adds 168 guarded call sites and keeps the
qualified D1053 carrier objects unchanged. The unit-specific diagnostic writes
`.primitives-eval`, never overwriting the carrier's `.primitives` counter.

D1055 compiled, linked and imported std/make, std/test and std/build-script.
D1056 executes the contract through original `##eval`: baseline plus 12 concurrent
candidate processes each pass 3,256 assertions, including 0-80 element lists,
fresh reverse pairs/shared elements, improper private-list fallback, GC, inherited
and direct structure checks and mutable type fields. Candidate sample coverage:
582 length, 855 reverse and 1,802 structure fast entries. This is semantic and
coverage qualification, not performance qualification.

D1057 real MCP prepares all 187 modules, exit 0. Additional interpreter hits are
only 42,616 length and 24,385 reverse, with zero structure hits and 60,399 reversed
pairs. User CPU 4.821784 seconds and wall 40.316661 seconds at host load about 68
are diagnostic-only, not controlled performance evidence. Reject this unit
override as a dominant first-log optimization; do not carry it into the proposed
production patch. The previously hypothesized interpreter type-call ownership
gap is disproven for this workload.

Evidence: `.data/d1055-bounded-eval-count-profile/`,
`.data/d1056-bounded-eval-contract/`, `.data/d1057-bounded-eval-mcp-counts/`.
The next gate is a fresh uninstrumented carrier build and interleaved real MCP
CPU/first-log measurements. The seven-to-eight-second goal remains open.

### D1058-D1063: uninstrumented execution and official first-log gate remain open

D1058 omitted the four additional sampled hot units and was refused by the
actual-static-coverage gate. No native candidate or performance claim results
from that failed configuration. D1059 retains all eleven original selected units,
79 bounded traces, precise thread/fresh-allocation fences, live parameter reads
and bounded primitive entries, but removes all diagnostic counts. Native build,
standard imports and unchanged original GSC hash pass. ABI and consumer flags
remain unchanged; this still is an experimental runtime carrier, not a release.

D1060 sequential A/B/B/A real MCP preparation (all 187 modules, all exit 0):

| Order | Runtime | User CPU (s) | Wall (s) |
| --- | --- | ---: | ---: |
| A | Original | 5.982138 | 42.666400 |
| B | Candidate | 4.863100 | 44.089667 |
| B | Candidate | 4.805377 | 45.602115 |
| A | Original | 5.854443 | 40.840513 |

Mean user CPU is about 18.32% lower, approximately 1.22x, not a multiplicative
startup solution. Wall time does not improve in this preparation sample.
D1062/D1063 additionally run official gerbil clean on the same isolated MCP
checkout and verify zero native images before each actual gerbil build. First
actual compilation is 49.822670 seconds original and 31.735923 candidate.
Host loads differ (original about 64 to 72, candidate about 68 to 60); this
single paired wall observation cannot establish a 1.57x startup improvement.
Both builds deliberately stop after the first real compilation and are not full
MCP build/test passes. No candidate is promoted and the seven-to-eight-second
goal remains active.

Evidence: `.data/d1058-bounded-primitive-uninstrumented/`,
`.data/d1059-bounded-primitive-uninstrumented/`,
`.data/d1060-bounded-primitive-mcp-abba/`,
`.data/d1061-mcp-first-log/`, `.data/d1062-bounded-first-log-baseline/`,
`.data/d1063-bounded-first-log-candidate/`.

### D1064-D1066: existing hash-probe gap closed, empty-table shortcut rejected

D1064 reuses the already built D965 diagnostic instead of rebuilding that
experiment. Real MCP preparation completes 187 modules: 31,416,253 hash reads,
4,749,250 hits, 26,667,003 misses, 77,668,913 probe steps and 1,602 lazy rehashes.
D1065 adds an entry-count observation only, preserving native hash policy.
D1066 repeats real preparation with that diagnostic: 8,166,028 calls see an
empty table, none hits; 18,500,975 misses concern nonempty tables. Address-based
hash layout changes the step histogram, so these runs establish ownership and
coverage, not speed. Empty-table bypass does not cover the dominant misses and
is not implemented as an optimization.

Evidence: `.data/d1064-existing-hash-probe-mcp/`,
`.data/d1065-empty-hash-probe-source/`, `.data/d1065-empty-hash-probe-build/`,
`.data/d1066-empty-hash-mcp-counts/`.

### D1067-D1076: lookup-return loop prototype, real coverage still incomplete

The opt-in Darwin/GNU carrier follows pure original GVM control flow after an
actual native hash read, and can export the exact VM registers/frame before
returning to the original next lookup. It does not cache lookup results or
change Scheme consumers. D1067-D1069 fail coverage/configuration gates and are
not qualified. D1070 passes original comparison and 12 concurrent native
contracts, including live false values, method mutation, GC and forced polls;
the sample actually executes 528 reentries. D1071 fails static coverage before
native compilation. D1072 qualifies a counted full carrier with unchanged GSC.
D1073 completes real 187-module preparation: the main site attempts 30,375,565
entries and completes 6,571,153 next-lookup transitions. Its 4.448144 seconds
user CPU is a single instrumented observation, not performance qualification.

The pure TYPEID/TYPESUPER matcher reads live type fields and preserves original
poll failure. Its helper has a 128-step bound and falls back without heap writes,
allocation or retained type results. D1074/D1075 pass original comparison and
12 concurrent contracts for inherited types, mutable super fields and a
140-level chain. Native fixture metadata records one lowered type-chain loop.
All 73 then-current focused Python tests pass.

D1076 compiles and imports the full carrier, but its real main reentry records
zero lowered type-chain loops. Inspection finds the selected branch is
unsatisfiable and the meaningful inherited path exceeds the prototype's six
poll-point budget. Therefore D1076 is not an inherited-hotspot optimization
result. No real MCP speedup, official first-log pass or production promotion is
claimed. The seven-to-eight-second goal remains active.

Evidence: `.data/d1070-lookup-loop-contract/`,
`.data/d1072-lookup-loop-count-profile/`, `.data/d1073-lookup-loop-mcp-counts/`,
`.data/d1074-inherited-lookup-loop-contract/`,
`.data/d1075-inherited-lookup-deep-contract/`,
`.data/d1076-inherited-loop-count-profile/`.

### D1077-D1079: bounded inherited-path coverage repair

Only the opt-in lookup-return prototype admits seven poll points instead of
six; other trace modes retain their original bounds. Selection prefers a
completed reentry containing the recognized live type-chain loop. A focused
test checks acceptance of the seventh point and refusal beyond it. All 74
focused tests pass. D1077 fails the original-output comparison because combining
the lookup and bounded-primitive fixtures exposed an expected-marker ordering
error. The exact order is corrected to match the Scheme fixture, without
removing any marker, exit-status or comparison requirement.

D1078 passes original comparison and all 12 concurrent candidate executions
with both fixture groups enabled. The selected inherited reentry records one
lowered type-chain loop and four poll points. This is semantic/coverage evidence
only. D1079 is the full counted carrier build; its real MCP coverage and timing
are not yet qualified at this checkpoint.

Evidence: `.data/d1077-inherited-loop-poll-native/`,
`.data/d1078-inherited-loop-poll-native/`,
`.data/d1079-inherited-loop-count-profile/`.

D1079 subsequently passes native compile/link and standard imports with the
original GSC hash unchanged. The real main reentry now contains one lowered
type-chain loop, seven poll points and 20 guards. D1080 fails before launching
MCP because the caller selected the profile directory rather than its isolated
source directory; no run or timing results from it. D1081 uses the correct
binary, completes all 187 modules and exits 0. Main coverage is 25,798,491
completed transitions out of 30,375,565 attempts, up from D1073's 6,571,153.
User CPU is 4.890311 seconds, wall 34.012500 seconds, host load about 64.
The runtime reports 1.262755 GC user seconds, 27 collections and 4,403,972,824
allocated bytes. This instrumented single run establishes actual coverage but
does not establish a large speedup or close the first-log gate. No promotion.

Evidence: `.data/d1080-inherited-loop-mcp-counts/` (pre-run failure),
`.data/d1081-inherited-loop-mcp-counts/`.

### D1082-D1083: outlined inherited lookup, performance gate pending

The existing bounded O3 native-helper carrier can now outline a completed
lookup-return reentry, passing its actual processor and frame pointers explicitly
when the live type-chain helper needs them. Other return branches remain in
their existing carrier; pre-read failure and post-read snapshot failure retain
distinct statuses and exact original resumption. No algorithm, cache, consumer
source or ABI change is introduced. This addresses optimization inside the
large generated GVM CFG, not the earlier rejected primitive-only outlining
measurement.

All 75 focused tests pass. D1082 passes original-output comparison and all 12
concurrent native contracts with inherited/mutable types, deep fallback, GC,
forced polls, parameter entries and bounded primitive fixtures enabled.
D1083 builds the corresponding uninstrumented full carrier. Until fresh real
MCP A/B and official clean/first-log measurements pass, this remains an
unpromoted execution-layout candidate and the startup goal stays open.

Evidence: `.data/d1082-outlined-inherited-native/`,
`.data/d1083-outlined-inherited-uninstrumented/`.

D1083 subsequently passes full native build, standard imports and original GSC
hash verification without diagnostic counters. D1084 sequential real MCP
A/B/B/A completes 187 modules and exits 0 in every run:

| Order | Runtime | User CPU (s) | Wall (s) |
| --- | --- | ---: | ---: |
| A | Original | 6.110655 | 48.096983 |
| B | Outlined candidate | 4.903554 | 48.349133 |
| B | Outlined candidate | 5.105075 | 49.382489 |
| A | Original | 6.289509 | 53.370215 |

Mean user CPU reduction is about 19.3%, approximately 1.24x. This does not
establish a major improvement over the earlier D1059 composition and does not
solve the startup objective. Host load is about 80-89 with five-minute load
about 90-94; wall observations are not a first-log qualification. Do not promote
this layout as a solution. D1085 proceeds to actual clean/build with first-window
function sampling to locate the remaining work; sampled timings are diagnostic,
not a new controlled performance result.

Evidence: `.data/d1084-outlined-inherited-mcp-abba/`,
`.data/d1085-outlined-real-first-window/`.

### D1085-D1088: sampled loader distortion and native path rejection

D1085 observes actual clean/build first output at 56.723 seconds, then stops
deliberately. Its wall-stack sampler causes dyld debugger load notifications;
these stacks are not on-CPU attribution and do not establish loader dominance.
The official zero-image clean gate passes, but no performance gate closes.

D1086/D1087 preserve native filesystem bodies and add Darwin/GNU-only cost
observation to `os_files.o` and `os_setup.o`. Native compilation and standard
imports pass. D1088 observes actual first output at 37.987 seconds without the
wall sampler. Two build processes accumulate approximately 0.481 seconds of
directory-normalization CPU and 0.116 seconds of file-information CPU. Getcwd
cost is nested inside normalization and must not be added again. Snapshots are
partial, measurement failures are zero, and this is not an A/B speedup result.
Reject a filesystem-policy rewrite as the dominant startup remedy. No realpath
replacement or directory cache is introduced.

Evidence: `.data/d1086-path-cost-source/`, `.data/d1087-path-cost-build/`,
`.data/d1088-native-path-real-first/`.

### D1089: exact-head Native CI changes the test optimization target

User-provided [CI run 37192692593](https://github.com/tao3k/gerbil-parser/actions/runs/37192692593)
has PR head `f35b14193db7cfc89444b0f9a82b81c3862bc795`; checkout logs identify
the actual tested merge `eb8485f0b7d18ccc2339e6bf632785da81dd965a`. Both Native jobs
pass the same 74 modules and 583 cases using immutable Gerbil v0.19 release
`2591dcd`, not this experiment's latest staging toolchain. macOS is arm64,
GNU GCC 16, three detected cores; Ubuntu has four detected cores. Cross-platform
wall ratios are user-experience evidence, not controlled CPU attribution.

| CI boundary | macOS seconds | Ubuntu seconds |
| --- | ---: | ---: |
| Native tests step (rounded Actions step timestamps) | 273 | 113 |
| Sum of 74 module batches | 269.918 | 111.741 |
| Batch start to first CASE marker | 254.386 | 91.732 |
| First CASE marker to batch completion | 15.533 | 20.009 |
| Native MODULE-LOAD trace union | 138.068 | 16.515 |
| Nested INTERFACE-IMPORT trace union | 95.107 | 51.788 |

The driver starts one fresh `gxi` per module sequentially. Event-strategy,
native-language-benchmark, follow-partition-language and Bash module batches
have ratios 3.19-3.40x. The largest cumulative difference occurs before test
cases, including module admission and source expansion. MODULE-LOAD intervals
include initializers and trace-output effects: they are not pure dlopen CPU.
Likewise, before-CASE time is not a count of pure macro-expansion seconds.
Interface trace pairs are similar (294,565 versus 294,713), not identical.
Keep actual suite cases, exit propagation, final OK, GC and silence gates intact.

Source inspection finds an independent loader-policy difference: Gambit uses
`dlopen(cpath, RTLD_NOW)` without an explicit visibility flag. Darwin defaults
to GLOBAL, Linux to LOCAL. The current Apple SDK also states that LAZY/NOW has
no effect with chained fixups. D1090 prepares an isolated Darwin/GNU-only LOCAL
candidate; it changes FFI visibility and is not a production patch. D1091 starts
before its clone finishes and fails before native compilation; no result.
D1092 retries only after preparation has completed. Neither compatibility nor
performance is implied by this hypothesis.

References: [Apple dlopen](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/dlopen.3.html),
[Linux dlopen](https://man7.org/linux/man-pages/man3/dlopen.3.html).
Evidence: `.data/d1089-parser-ci/`, `.data/d1090-local-loader-source/`,
`.data/d1091-local-loader-build/`, `.data/d1092-local-loader-build/`.

D1092 completes native compile/link and standard imports with original GSC
hash unchanged. D1093 compares original and candidate against the same library
home and unchanged real MCP build specification:

| ABBA order | Runtime | User CPU seconds | Wall seconds |
| --- | --- | ---: | ---: |
| A | Original | 6.120040 | 50.796224 |
| B | LOCAL candidate | 6.139354 | 32.303733 |
| B | LOCAL candidate | 5.788193 | 17.802598 |
| A | Original | 6.007521 | 25.520996 |

All four preparations import 187 modules, exit zero, allocate approximately
4.404 GB and perform 27 collections. Mean user CPU reduction is only about
1.65%, not a substantial optimization. Host load falls from approximately 124
to 74 across these runs; do not promote wall changes as a speedup. Reject LOCAL
as the main solution, particularly given its unresolved FFI visibility cost.
No production patch, official first-log qualification or full Native suite
qualification is produced by this candidate.

Evidence: `.data/d1093-local-loader-mcp-abba/`.

The checkout-identity receipt verifies byte-identical workflow, native-suite,
preload and native-test-driver sources at the tested merge and PR head. Splitting
load intervals by module-name shape gives phase (`~`) intervals 72.941 seconds
on macOS versus 14.924 on Ubuntu, and non-phase intervals 65.126 versus 1.592.
Both platforms report the same 691 distinct module names. Name shape is a
classification, not proof of the file extension actually selected. Gerbil's
unchanged loader searches numbered objects before `.scm`, then delegates to
Gambit `load`. Gambit source loads read all forms, clone the interaction CTE and
call `##eval-module`. Therefore the non-phase disparity makes source-wrapper
admission a concrete next attribution boundary; it does not justify calling all
MODULE-LOAD time native dyld work or bypassing CTE isolation. No CTE caching or
mutation-policy change has been implemented or qualified.

### D1094-D1097: interpreter attribution, observer gate not closed

Current upstream `v0.19-staging` is revalidated at
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. The initial ref queries used `staging`
and returned no matching ref; these are not latest-head evidence. No source
upgrade or switch to the immutable release used by parser CI occurs.

D1094 adds four observation boundaries to isolated Gambit `_eval.scm`: source
read, interaction-CTE clone, compilation and execution. It does not introduce
a cache or change load policy. Native timers use per-process CPU and monotonic
wall clocks; nested durations have separate inclusive and exclusive fields.
The first observer uses `dynamic-wind` to pair scopes on unwind. Both MCP
balance checks pass, from 370 to 374 top-level forms. MCP's Gerbil syntax
expander rejects Gambit's dotted primitive definition context; original GSC
full-header-context generation succeeds, as does native GNU syntax checking.

D1095 compiles the new EVAL object but fails linking: newly introduced observer
globals are absent from the old static Gambit metadata. It is not a valid
runtime result. Original flat/preload metadata generation is then applied in
the isolated source. D1096 compiles `_eval.o` and `_gambit.o` at original GNU
O1, links, imports std/make/std/test/std/build-script and verifies original GSC
identity. It is explicitly diagnostic-only, not performance-qualified.

D1097's real MCP preparation completes 187 modules and exits zero but fails the
four-boundary coverage gate. Read and clone counters are zero; compile and run
each complete 10,358 scopes, with zero timer errors and zero outstanding scopes.
Compilation records 0.305 user CPU seconds exclusive; execution records 5.772.
These are observer-bearing boundary measurements, not pure interpreter CPU or
proof of a particular Scheme procedure being dominant. Execution encompasses
callbacks, macro processing, GC and any uninstrumented nested work.

An explicit native `##load` contract against the exact same binary prints
SOURCE-CONTRACT-OK and CONTRACT-RETURN-OK, exits zero and observes one read and
one clone, plus compilation/execution. All four boundaries are exercised there,
with zero errors or outstanding scopes. This distinguishes lack of execution of
the two instrumented paths in the MCP sample from a completely inactive meter.
It does not prove that every possible source read or CTE operation is absent.
Do not build a CTE-clone optimization from these zero counts.

The observer allocates approximately 9.268 GB and performs 28 collections versus
the preceding original preparation's approximately 4.404 GB and 27 collections.
Reject precise cost proportions or acceleration claims from this disturbed
sample. A passive boundary observer without a dynamic-wind environment must be
checked next, retaining strict timer/progress/exit gates. No optimization or
full first-log/test qualification is produced by this step. All 79 focused
Python tests pass; these are not substitutes for native suite qualification.

Evidence: `.data/d1094-source-cost-source/`, `.data/d1095-source-cost-build/`,
`.data/d1096-source-cost-build/`, `.data/d1097-source-cost-mcp/`.

### D1098-D1101: passive boundaries remove allocation disturbance

D1098 replaces the observer's dynamic-wind scope with begin/call-with-values/end
without changing the dynamic environment. Multiple values are returned through
`##apply ##values`. Nonlocal exits do not have valid timing in this mode; any
unclosed or mismatched native scopes remain a rejection, not a relaxed gate.
MCP before/after balance checks pass, full original GSC header-context generation
passes, and original flat/preload static metadata is regenerated. D1099 builds
only original-O1 EVAL plus its static metadata, passes native framework imports
and preserves original GSC hash. It remains diagnostic-only.

D1100 runs both original and observer against explicit Gambit source loading
and two returned values. Exact stdout, empty stderr and successful exit match.
The observer executes all four timer boundaries with no errors or outstanding
scopes. This qualifies observation paths and value semantics, not performance.

D1101 completes real 187-module MCP preparation and exits zero. Native process
statistics record 4,406,655,648 allocated bytes and 27 collections, versus about
4,403,971,544 and 27 in D1093's final original run. The observer's allocation
disturbance falls to approximately 0.061%, unlike the dynamic-wind observer's
9.268 GB. No comparable wall-time acceleration is claimed: load is about 110.

Source read and clone remain unexecuted in the two specific instrumented paths;
the all-four-boundaries coverage gate still rejects D1101. Compile and run each
close 10,358 scopes, with zero counter errors or open scopes. Exclusive user CPU
is 0.319791 seconds for compilation and 5.712023 for execution. This does not
make all execution interpreted, nor all macro expansion part of compilation:
the long execution scope also contains compiled macros, GC and any work outside
the other boundaries. Do not infer a native procedure's CPU share from these
regions or introduce a CTE-clone cache from zero counts. Next attribution must
be on-CPU inside the execution region, rather than wall stacks or nearest GVM
label symbols. No production optimization or first-log gate closes here.

All 80 focused Python tests pass. Evidence:
`.data/d1098-passive-source-cost/`, `.data/d1099-passive-source-cost-build/`,
`.data/d1100-passive-source-cost-contract/`, `.data/d1101-passive-source-cost-mcp/`.

### D1102: original-runtime hardware CPU samples narrow the execution target

Instruments CPU Profiler runs the unchanged D935 native binary on the same
187-module MCP preparation expression. Target output completes all modules;
the trace TOC independently records target exit(0). Native image UUID and SHA
match the original binary. No Gambit observer or candidate environment is used.
Allocation is 4,403,969,800 bytes with 27 collections, close to the earlier
original run. User CPU is 5.948578 seconds; GC user CPU is 1.266365 seconds.
These are diagnostic workload statistics, not an official clean/build result.

The exported hardware event is CORE_ACTIVE_CYCLE with one-million-cycle PMI
sampling. The parser validates target PID, Running state, actual binary UUID,
and native LC_FUNCTION_STARTS plus exact function-start symbols. 18,570 rows
contain 15,742,947,031 weighted cycles; one shutdown row has zero weight and
is retained as a separate count. Native dyld stubs are counted as executable
sections, never assigned to the preceding function. 13,668,335,734 cycles have
validated local native-function attribution; 4,366,615 are native-section
cycles. Unknown stacks and external-image samples remain in the denominator.
Four focused function-boundary/stub/unknown-name tests pass.

Self-cycle shares are 11.56% expander core, 10.86% expander stx, 10.08%
mark_array and 7.81% its constprop clone. Other significant hosts include runtime
mop (4.73%), hash (4.50%), table (4.38%) and native gc_hash_table_ref (4.35%).
Kernel is only 2.43%; EVAL is 2.10%. Thus the previous execution-region timer
does not identify interpreter CPU, and kernel transition counts do not make
kernel the remaining dominant CPU cost. GC-only gains remain capped by D1009;
the rejected D999/D1004 collector experiments should not be repeated.

The hottest core PC is its actual native host entry. Disassembly shows state
loads followed by an indirect branch; subsequent hot PCs include the entry's
global-table load. This is bounded native-instruction evidence, not assignment
to a particular Scheme/GVM procedure. Hardware sampling skid and host contention
also prevent treating one sampled instruction as an exact stall measurement.
Next work should quantify the actual entry regions across native hosts and
inspect generated host/state-transfer code against the already tested D1012
private-calling-convention design before selecting a different codegen change.

The same record's actual native-host prefixes account for 6.88% of all sampled
cycles within the first 16 bytes, 7.95% within 32 bytes and 13.85% within 64
bytes (13.90% within 128). These are byte regions, not exact semantic entry
costs; some include initializers or ordinary body code. Even this broad prefix
region does not support a several-fold improvement from host-entry work alone.
The next candidate must address recurrent body work across compiled hosts,
not repeat private-register entry tuning based on the single hottest PC.

The attempted dSYM extraction warns about stale object timestamps and a missing
link object. It is not used for fine source/line attribution. The recording's
wall duration is not a speedup, and hardware cycle shares are not CPU seconds.
No optimization, official first-log gate, full build, or Native-test gate closes
here. Source/test consumer behavior remains unchanged.

Evidence: `.data/d1102-original-mcp-cpu-profiler/` (trace, original target log,
TOC, exported CPU table, image metadata and `cpu-summary.json`).

### D1103-D1105: exact original source mapping and remaining candidate CPU

D1103 fails before compilation because the sandbox refuses Bazel's hw.memsize
discovery. D1104 uses the same configured environment after approval. Only
debug objects for original core and stx are compiled; no binary is relinked,
original source/object files are unchanged. Both objects' entire __text bytes
and symbolic text relocations match their original objects exactly. Text SHA:
core `dd7a0eb5fe5f4d34958aa3b207d7ed9bb72f27776a652d466429cd92a54ace2a`,
stx `98d9c8b86f8bef96a8becc8da6d294f20a4b0e30ea916f3826f439f6db0c49dd`.
This closes the stale-dSYM attribution limitation for these two units only.

Seven core body PCs and three stx body PCs have successful exact-offset DWARF
lookups. Core maps to the shared END_M_SW exit and context-resolve's hash-get
preparation, argument setup and type checks. Stx maps to END_M_SW, syntax-e's
structure test and stx-pair?'s argument check. These are actual generated-C
lines, not nearest Scheme/GVM labels. They do not by themselves establish
exclusive procedure CPU costs. Existing D912/D916 entry/exit experiments and
D1079/D1083 lookup-chain coverage preclude repeating them as new hypotheses.

D1105 therefore profiles the already built, uninstrumented D1083 candidate,
keeping the original D935 library home, GSC, consumer source, flags and real
187-module expression. Its native build receipt and current GXI/GSC SHA are
checked before launch. All 187 modules complete; exported TOC confirms target
exit(0). Native user CPU is 4.776292 seconds, GC user CPU 1.253798, allocation
4,403,968,728 bytes, 27 collections. This is remaining-cost diagnosis, not a
new controlled speed measurement or a first-log result.

15,118 Running rows contain 11,880,763,915 hardware-cycle weights. The matching
native image's function-start metadata validates 9,949,093,242 cycles;
1,637,148 are non-function native-section cycles, seven zero-weight rows are
separate. Remaining self-cycle shares: gb_coalesced_host 32.18%, mark_array
12.79%, its constprop clone 9.34%, gb_trace_native_11 4.63%, gc_hash_table_ref
4.47%, kernel 2.91%, EVAL 2.65%, type-chain helper 1.81%, parameter helper
1.70%. Do not transfer the original host proportions to this carrier or assign
its merged function's interior by nearest labels. D1106 proceeds to byte- and
relocation-identical DWARF mapping of the existing coalesced link object.

The latest upstream v0.19-staging ref is rechecked and remains the recorded
1cfb032 commit. Five CPU-attribution/provenance tests and all 88 focused Python
tests pass. Official first-log, full-toolchain and real Native-suite gates remain
open; no consumer-source edits or production patch promotion occur.

Evidence: `.data/d1103-original-native-hot-map/`,
`.data/d1104-original-native-hot-map/`, `.data/d1105-existing-candidate-native-cpu/`.

D1106's existing coalesced-link debug compilation exceeds its independent
300-second build-only wall budget and is terminated. At 221 elapsed seconds,
the live GNU cc1 has consumed 29.38 CPU seconds and about 987 MB RSS. This is
verified contention during a diagnostic build, not a runtime performance result.
The process group is terminated and a subsequent check confirms all five
recorded GCC/assembler processes are gone. The retained report is unqualified;
no DWARF mapping or candidate-body source attribution follows from D1106.
Original runtime binary and source are not relinked or edited. The next mapping
attempt should reduce debug metadata to the line information actually needed,
still requiring entire text and symbolic relocation identity, instead of
promoting any incomplete object or guessing procedure ownership. All 91 focused
Python tests pass, including three exact-symbol/text/relocation parser tests.
Evidence: `.data/d1106-candidate-coalesced-hot-map/`.

### D1107-D1111: complete native line weights, no speculative hotspot ownership

D1107 uses GNU -g1 to retain line tables without local-variable debug metadata
([GCC debugging options](https://gcc.gnu.org/onlinedocs/gcc/Debugging-Options.html)).
It still exceeds the 300-second diagnostic build budget and is terminated;
the five recorded GCC/assembler processes are subsequently confirmed gone.
No incomplete object or timing result is admitted. Review of the successful
D1083 build receipt reveals that its 19,721,269-byte link input originally used
a 900-second compilation budget. This is a build-only constraint, independent
of all product startup/output gates.

D1108 binds diagnostic compilation to that successful original receipt. Its
qualified/ABI/compiler/consumer-flag boundaries, actual binary SHA, source size
and bounded original budget are checked before starting. Minimal debug
compilation completes in 346.506 seconds without changing the running binary.
Entire original/debug __text dumps and symbolic relocations match. Text SHA is
`74dd55dcfa0dd8b945d24697077498af18e32a335a07af649caccffe2d621c85`;
generated C SHA is
`b8528229b29ab3d25f77324a548ee7521abd5a25b0a4cc99bc68e6974d68f1bf`.
Twelve exact body-PC DWARF lookups pass. This is code-attribution qualification,
not build or runtime acceleration.

The hardware table is re-aggregated, without rerunning either workload, to
retain all validated native PCs rather than only the first hundred. A line
parser respects exact DWARF address intervals and end_sequence boundaries;
duplicate-address rows have zero length, and missing/overlapping/unterminated
sequences or multiple implicit compilation units are rejected. Mapping requires
current binary UUID/SHA, original/debug text and relocation identity, complete
function cycle-weight accounting and source hashes. Older original-unit maps
use the successful D1083 receipt's reused-original object and C hashes rather
than silently trusting current source text.

D1109 maps all 473 original core PCs; D1110 maps all 330 original stx PCs.
There are zero unmapped weighted cycles in either host. D1111 maps all 1,521
candidate coalesced-host PCs, again with zero unmapped cycles. Compiler-assigned
source lines are grouped by their first macro token. Candidate host shares:
IF 20.97%, IF_NARGS_EQ 12.33%, JUMPRET 9.63%, POLL 7.72%, END_M_HLBL 7.69%,
SET_R1 5.82%, JUMPGLONOTSAFE 5.51%, SET_R0 5.18%, SET_STK 4.99%, END_M_COD
2.76%. These percentages are of this host, which accounts for 32.18% of the
complete recording's self-cycle weights. They must not be presented as whole
program CPU percentages or exclusive semantic operation costs. Shared dispatch
glue remains shared; no nearest GVM labels are used to assign it to procedures.

The IF lines include syntax-wrap, import-/alias-binding, pair, structure and
procedure tests, plus ordinary boolean conditions. The largest individual IF
line is only about 1.51% of the host. This supports a cross-cutting generated-code
approach rather than another isolated predicate, arity or kernel tweak. It does
not choose a production design yet. Actual first-log, full-toolchain and Native
suite gates remain open. No Gambit runtime source or consumer source is changed
by these diagnostics. All 96 focused Python tests pass.

Evidence: `.data/d1107-minimal-coalesced-hot-map/`,
`.data/d1108-receipt-budget-hot-map/`, `.data/d1109-original-core-line-cycles/`,
`.data/d1110-original-stx-line-cycles/`, `.data/d1111-candidate-line-cycles/`.

## D1112-D1118: Pure Branch Trees, Bounded Native Contract Only

The hardware evidence above motivates a cross-cutting candidate: factor
compatible readonly trace paths into native branch trees, including computed
results and readonly predicates, rather than selecting only identity-result
success paths. The optional prototype is off by default and guarded by the
existing Darwin/GNU configuration gate. It does not allocate, cache results or
cross unknown effects. It exports exact modeled GVM state before resuming the
original instruction. Existing selected trace entry points are preserved.

D1112 source-only planning finds 3,698 roots, 57,468 pure paths and 551 bounded
fused trees in the eleven retained original generated C units. These are static
counts, not workload coverage or speed evidence. Integration currently caps
supplementary trees at 256; it requires actual workload coverage before a
performance claim.

Retained failed contract attempts identify harness defects, not runtime wins:
D1113 invalid negated `block` declaration; D1114 preamble evaluated before
`gambit.h` established binding mode; D1115 wrong internal `##load` arity;
D1116 `.o` treated as source instead of Gambit's `.o1` binary extension;
D1117 binary linker identity included the extension. No failure is converted
to a pass and no semantic checks were removed.

D1118 generates the fixture with the unchanged original GSC and compiles both
variants with real GNU GCC 16. The original baseline and all twelve concurrent
candidate `std/test` runs exit zero with explicit final success. Each candidate
records 522 tree entries and 517 actual successful leaves. The fixture checks
computed results, pair mutation, GC, global procedure rebinding, exceptions,
multiple values and continuations. Eight static trees are emitted. All 104
focused Python tests pass. This is bounded semantic qualification only, not
MCP first-log, full-toolchain, parser Native CI or performance qualification.

Evidence: `.data/d1112-pure-tree-source-coverage/`,
`.data/d1113-pure-tree-native-contract/` through
`.data/d1118-pure-tree-native-contract/`.

## D1119-D1122: Retained Composition and Real MCP Coverage

D1119 is deliberately stopped before compilation: the command omitted the
eleven-unit selection. D1120 is deliberately stopped during compilation: it
omitted the inherited lookup-return option, changing old trace selection from
14 to 12. Both remain unqualified; they cannot support an A/B comparison.

D1121 restores the exact existing D1083 composition. JSON equality checks
confirm unchanged original object/source receipts, all 14 original trace
records, parameter-entry sites and bounded-primitive sites. It adds 256 pure
trees across eight modules. The C unit is 21,579,212 bytes, below the existing
24-MiB cap. Native GNU GCC 16 compilation, link and standard imports succeed;
original GSC SHA stays unchanged and neither ABI nor consumer flags change.
The resulting binary is diagnostic, not a performance candidate.

D1122 completes the unchanged real 187-module MCP preparation, exit zero.
Native counters record 22,626,355 new-tree attempts and 17,943,283 successful
leaves; 87 sites are attempted and 57 have successes. Counts are structurally
valid (three integer columns and hits no greater than attempts). The largest
site is expander `stx`, parsed-body-relative line 770, with 11,902,134 hits.
Other million-hit sites are in `runtime/mop`. The old main lookup reentry still
records 25,798,501 hits out of 30,375,565 attempts.

Diagnostic process user CPU is 4.768753 seconds and wall time 24.793437 seconds
under host load about 53. Native process statistics record 4.452179 user CPU,
1.185569 GC user CPU, 27 collections and 4,403,970,168 allocated bytes. These
are single instrumented-run facts, not controlled improvement claims.
Coverage is now proven; performance, official first-log, complete build and
parser Native suite qualification remain open. Latest upstream
`refs/heads/v0.19-staging` remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

Evidence: `.data/d1119-pure-tree-mcp-counted/`,
`.data/d1120-pure-tree-mcp-counted/`,
`.data/d1121-pure-tree-inherited-counted/`,
`.data/d1122-pure-tree-real-mcp-coverage/`.

## D1123-D1127: Performance Rejected and Official Clean Crashes

D1123 is the uninstrumented variant: native build and standard imports pass,
GSC/ABI/consumer flags remain unchanged. All original trace/input metadata and
all new-tree metadata match D1121. D1124 compares it against existing D1083
using shared home, libraries and GSC. Every ABBA run prepares 187 modules and
exits zero. User CPU is 5.143812 / 4.884633 / 4.582902 / 4.805597 seconds;
candidate average is only about 4.8% lower. Wall time is 28.828609 / 32.912878 /
25.438234 / 25.522795 seconds and does not improve. This is not a substantial
speedup and cannot close the startup or Native-test goal.

D1125 runs official `gerbil clean/build` with D1083 as current reference.
Clean passes; first compile occurs at 53.721290 seconds, violating the existing
10-second silence gate. First-window termination then exceeds the five-second
TERM wait; final cleanup KILLs and waits for the process. Receipt stays failed.
This is not the earlier normal seven-to-eight-second baseline and no budget
is relaxed. D1126 candidate fails even earlier: official clean exits SIGSEGV.
It is a correctness failure despite successful bounded fixtures/preparation.
Neither complete build nor Native suite is qualified, and no patch promotion
is allowed.

D1127 validates the actual macOS crash image UUID and PC/frame consistency,
then maps the PC using a retained-source GNU GCC 16 `-g1` object. Whole text and
symbolic text relocations are identical to the original candidate object.
Native host offset 440,088 maps to retained `gerbil-link.c` line 266,671:
`cast` executes `JUMPRET(STK(2))` after frame adjustment. The crash decodes
tagged fixnum 388 as a continuation pointer; this is native fault evidence,
not hardware-cycle or nearest-GVM-label attribution.

An overlapping-stack-copy hypothesis is rejected by a passing regression:
the existing STK reader already snapshots physical input. A separate pending
stack-write regression fails: new pure-tree effect leaves used return-only
liveness filtering before an ADJFP, dropping stores to future frame slots.
The narrow prototype fix retains all modeled stack stores at original-effect
resumption, and keeps completed-return filtering. All 108 focused tests pass.
Official clean reproduction is still required to establish crash closure.

Evidence: `.data/d1123-pure-tree-inherited-uninstrumented/`,
`.data/d1124-pure-tree-best-runtime-abba/`,
`.data/d1125-pure-tree-reference-first/`,
`.data/d1126-pure-tree-candidate-first/`,
`.data/d1127-pure-tree-clean-crash-map/`.

## D1128-D1130: Pending-Store Fix Passes Original Clean Reproduction

D1128 repeats the unchanged original-GSC/GNU fixture: baseline and all twelve
concurrent candidate std/test runs exit zero, each candidate with 517 real
tree hits. D1129 rebuilds the full corrected uninstrumented eleven-unit
carrier. The C unit is 21,716,665 bytes; build, link and standard imports pass
with unchanged GSC and ABI. The original fourteen trace records remain intact.

D1130 repeats the previously crashing official `gerbil clean` on the same MCP
project/head, home and twelve-core environment. It exits zero, reports actual
clean completion and leaves zero project native images. This is bounded closure
of that crash reproduction, not first-log, complete build, Native CI or speed
qualification. The `clean-only` observer keeps the existing 30-second clean
deadline and records an explicitly distinct correctness-only scope.

No new production patch is promoted. The earlier pure-prefix-only experiment
does not meet the required substantial-acceleration threshold. Source now shows
the dominant new stx tree resumes at `BEGIN_ALLOC_STRUCTURE` rather than
completing the full construction/return path; successful prefix counts alone
cannot stand in for reduced end-to-end work. A subsequent design must address
the actual remaining allocation/effect/dispatch path while retaining dynamic
rebinding, GC, exact stack state and Darwin/GNU-only boundaries. The startup
goal remains active and unachieved.

Evidence: `.data/d1128-pure-tree-pending-stack-native/`,
`.data/d1129-pure-tree-pending-stack-uninstrumented/`,
`.data/d1130-pure-tree-pending-stack-clean/`.

## Native Test Experience Remains A Separate Required Gate

The user again identifies job 111408043087 in run 37192692593 as a required
Darwin test-acceleration workload. A fresh read-only GitHub Actions API query
confirms both Native jobs succeeded and the test-step timestamps still give
273 seconds on macOS versus 113 on Ubuntu (2.42x overall). The D1089 retained
logs show individual module batches at 3.19-3.40x; these are not the aggregate
ratio. Reuse that existing phase analysis rather than rerunning the CI study.

The retained driver executes one fresh process per module sequentially. Of the
269.918 seconds of macOS module batches, 254.386 seconds precede the first CASE
in each batch (94.2%). The corresponding Ubuntu values are 111.741 and 91.732
seconds. The summed post-first-CASE intervals are 15.533 and 20.009 seconds.
This makes repeated pre-case admission a priority; it does not prove that all
pre-case time is macro expansion, nor isolate the operating system from runner
and release/toolchain differences.

Required performance closure keeps the original 74 modules, 583 cases, native
preload behavior, explicit child exit propagation, final GC and final OK.
The existing five-second real-output silence and ninety-second per-batch
limits must not be relaxed. Compare the unchanged driver and package artifacts
under one shared library home, replacing only the Darwin/GNU Gambit runtime.
Report per-module start-to-first-CASE, complete-suite wall time and process
CPU separately. Maintain the hardware-derived twelve-worker std/make/std/test
contract as a separate concurrency gate; making the originally sequential CI
driver parallel is not evidence of reduced Gambit execution cost.

The current fresh-branch source model remains default-off and is not yet
connected to a native candidate emitter. Four new tests cover completed fresh
pair branches with negative tail-frame adjustment, rejection of external
writes and partial structures, exclusion of other trace execution modes, and
heap-budget/incomplete-closure rejection. All 112 tool regression tests pass.
No native runtime speedup, full parser suite qualification or first-log
qualification follows from these source-model tests. The previous pure-prefix
candidate's 4.8% preparation CPU reduction remains insufficient.

Evidence: `.data/d1089-parser-ci/analysis.json`,
`.data/d1089-parser-ci/native-suite.ss`,
`tests/test_gambit_trace_tree.py`.

## D1131-D1132: Fresh Allocation Trees Pass Bounded Native Rollback Contract

The default-off supplementary fresh-tree experiment combines bounded branches
with the existing fresh-object model. It reserves the maximum path heap demand
before execution, requires complete constructors before allocated returns, and
restores the original heap cursor on every late guard miss. Existing-object
writes, partial structures/closures and allocated effect-resumption paths are
rejected. Darwin/GNU, word-layout, single-VM and poll exclusions remain explicit.
The original read-only/lookup trace selection is retained separately.

D1131 compiles and executes the original fixture successfully; candidate
semantic assertions also return success but the receipt fails its deliberate
requirement for a guard miss after actual allocation. The only selected tree
guards global identity before its allocation. Its rollback count is zero, so
this attempt is not qualified. Inspection identifies the unsupported CAAR
read (the Gambit header defines it as CAR of CAR), which cuts the pair branch.
Supporting that exact read only in fresh mode admits the intended full paths.

D1132 compiles the original GSC output and candidate with real GNU GCC 16.
The baseline and all twelve hardware-derived concurrent candidate std/test
processes pass explicit CASE-OK, HARNESS-OK and final native-contract markers
and exit zero. Four generated trees each complete allocation on both paths.
Each candidate records 526 entries, 516 hits and 18 heap words actually rolled
back after local allocation. The fixture exercises object freshness/aliasing,
mutation, GC, global rebinding, multiple values, exceptions and continuation
escape. This is a bounded correctness/rollback contract, not a startup or
complete Native-suite performance result.

Diagnostic runtime counters additionally distinguish completed allocated
returns and committed words from generic prefix hits. Counter parsing rejects
duplicate/out-of-range sites and impossible heap totals. All 115 tool tests
pass. Latest upstream staging still resolves to
`1cfb032c7a1612637da6205f5f8a15683eba3ba0` in a fresh read-only ref query.

Evidence: `.data/d1131-fresh-tree-native-contract/`,
`.data/d1132-fresh-tree-caar-native/`.

D1133 completes source-only analysis of all 3,698 original roots: 33,858
modeled paths, 1,244 multipath roots and 34 bounded fused fresh trees. The
previously dominant stx body-relative line 770 now has twelve modeled paths,
ten completed allocated returns, with maximum five heap words. Unlike the
previous pure-prefix leaf, these constructor paths finish the structure and
return rather than resume at BEGIN_ALLOC_STRUCTURE. This is static source
coverage, not real workload hit counts or exclusive CPU attribution.

D1135 extends the fixture with genuine Gambit define-type structure construction,
non-tail computation, field mutation, distinct result objects and GC. Original
and all twelve concurrent candidate std/test processes exit zero. Five selected
trees include a complete structure path with peak frame four. Each candidate
records 528 entries, 518 hits and the same eighteen rolled-back heap words.
Performance remains unqualified.

Evidence: `.data/d1133-fresh-tree-source-coverage/`,
`.data/d1135-fresh-tree-structure-native/`.

## D1134-D1136 And D1138: Real MCP Allocation Coverage, Not Speed Qualification

D1134 builds the complete diagnostic eleven-unit carrier with GNU GCC 16,
then links and passes standard imports. Its C size is 19,930,989 bytes. All
original object metadata and fourteen inherited trace records are identical
to D1083. GSC retains SHA256
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`;
ABI and consumer flags remain unchanged. The candidate runtime SHA256 is
`f5654841a75bef38adcb76c7f6d0f949f5626be6da739f64da5c1ae3e3fd5472`.

D1136 runs the unchanged real MCP build specification preparation: all 187
modules prepare, IMPORT-OK is present, and the process exits zero. Native
counters record 12,661,517 completed allocated returns across nine sites,
63,029,656 committed heap words and 57,295 rolled-back heap words. Site zero,
stx body-relative line 770, contributes 11,901,081 completed allocated returns
and 59,505,405 committed words. Thus the previously prefix-only hot site now
really executes complete allocation/return paths, not merely static branches.

The single diagnostic sample reports child user CPU 4.763446 seconds and wall
31.886770 seconds at host load about 69. Native process statistics give user
CPU 4.479783, GC user CPU 1.206233, 27 collections and 4,403,972,280 allocated
bytes. These are instrumented observations, not a speed ratio. In particular,
the experiment preserves gross allocation volume: completing constructors in
the fused path does not itself remove the large allocation/GC cost. Controlled
uninstrumented comparison and official first-log qualification remain required.

D1138 uses this binary with the original shared home and runs official MCP
clean at the original project head and twelve-core environment. It exits zero
and leaves zero native project images within the unchanged clean gate. This
does not qualify official build, Native-suite latency or performance. No
production patch is promoted.

Evidence: `.data/d1134-fresh-tree-inherited-counted/`,
`.data/d1136-fresh-tree-real-mcp-coverage/`,
`.data/d1138-fresh-tree-counted-clean/`.

## D1137-D1140: Fresh Constructor Fusion Rejected As The Startup Solution

D1137 builds the uninstrumented carrier, links and passes standard imports.
Diagnostic mode is false, C size is 19,925,994 bytes, GSC is unchanged, and
original objects, inherited trace records and all 34 fresh-tree models match
D1134. Runtime SHA256 is
`4d1ef4ceae0d2355cf62bc5a4cd294086d10f0ad089a433be5d8774b1780d19a`.

D1139 compares the candidate with the existing best D1083 runtime, not a
weaker original binary. The same library home, GSC and real 187-module MCP
specification are retained. Every run prepares 187 modules and exits zero.

| ABBA order | Runtime | User CPU seconds | Wall seconds |
| --- | --- | ---: | ---: |
| A | D1083 best | 5.015550 | 50.914653 |
| B | Fresh fusion | 4.940738 | 45.072219 |
| B | Fresh fusion | 4.731819 | 43.543367 |
| A | D1083 best | 4.977480 | 41.010218 |

Mean user CPU drops from 4.996515 to 4.8362785 seconds, approximately 3.21%.
This is insufficient for the requested substantial startup acceleration.
Wall averages differ by about 3.60%, with host load approximately 78-85;
they do not justify a stable latency claim. The millions of completed
constructor paths demonstrate execution coverage, not a large avoided cost.

D1140 repeats official clean/build observation with the uninstrumented
candidate and original MCP head. Clean passes; the first actual compile is
37.511933 seconds after build start and fails the unchanged ten-second real
output gap gate. Build is deliberately stopped after that observation and is
not complete. This contended-host sample must not be described as a regression
from a normal-load seven/eight-second baseline; it directly fails the current
qualification gate nevertheless.

Reject this candidate as the solution and do not promote a production patch.
Fusing dispatch through the constructor while preserving essentially all
allocation work did not produce the required gain. The next source design
must remove substantially more actual work, rather than repeat this constructor
fusion or promote its static/hit counts. Official first-log, complete toolchain
and full Native-test acceleration remain unachieved. All commands from this
experiment have reached terminal state.

Evidence: `.data/d1137-fresh-tree-inherited-uninstrumented/`,
`.data/d1139-fresh-tree-best-runtime-abba/`,
`.data/d1140-fresh-tree-candidate-first/`.

## D1141-D1147: Caller-Scope Allocation Removal

The canonical five-register observation boundary in D1141 retains every
allocation in the 34 previously selected fresh trees. Constructor fusion
alone therefore does not prove that any object can be removed.

The original staging source supplies a narrower, concrete observation boundary:
`stx-car` and `stx-cdr` call `syntax-e` and select one field of its result.
The Gambit compiler's normal result register is R1; `gen-return` records only
the result variable in its normal return frame. Multiple values use a VALUES
object, not an invented second-result register. The source model additionally
preserves live stack stores and snapshots the actual saved stack return operand;
it does not assume that this operand equals incoming R0.

The first caller audit stopped on unsupported IF_GOTO instructions and generic
calls whose procedure was already a known local label. D1143 retains these
stop reasons. The default-off caller model now handles those cases, propagates
fields of its own freshly allocated pairs, and scopes its existing two-visit
limit by saved continuations. Other modes retain their previous behavior.
Unresolved providers, effects, incomplete constructors and the total work,
statement, frame and path limits still stop analysis.

D1146 reaches complete caller returns across the fold/mark helper calls.
Selected paths allocate 16 heap words but retain only five at the caller
boundary. Eleven words belong to intermediate marks/pair/unreturned wrapper
objects. Other modeled paths reduce 11 to five, 11 to zero, or six to zero.
The analysis is bounded and incomplete: each caller reaches the 64-path limit;
these are not all possible inputs and are not real-workload frequencies.

D1147 explicitly rewrites the 128 modeled caller paths. The scalarizer removes
only complete owned constructors, substitutes proved owned field reads,
preserves escaping nested objects and identity guards, rejects dangling
references and does not scalarize closures. All 128 source rewrites pass a
second allocation-inventory audit. This is source evidence, not a runtime or
performance result. All experimental functionality remains opt-in.

Evidence: `.data/d1141-fresh-object-escape-audit/`,
`.data/d1143-stx-caller-stop-reasons/`,
`.data/d1146-stx-caller-continuation-scope/`,
`.data/d1147-stx-caller-scalarized-source/`.

## D1148-D1150: Real Native Scalarization Contract

D1148 compiles the original and scalarized Gambit fixture using the isolated
GNU GCC 16 environment. Original execution and 12 concurrent candidate
`std/test` runs pass explicit CASE-OK, HARNESS-OK and final success checks.
Each candidate executes 516 scalarized returns and reports 1,548 elided heap
words. No actual post-allocation guard rollback was exercised in this first
fixture; it must not be claimed as rollback qualification.

D1149 adds an identity observer after the retained allocation and rebinds it
to a GC-performing procedure. This makes the candidate miss a global binding
guard after allocating the retained object. The original and all 12 candidates
pass; each candidate executes 517 scalarized returns, reports 1,551 elided words
and rolls back three actually allocated words. The original positive rollback
gate is enforced. Fixture assertions also cover independent object identity,
mutation, structures, GC, rebinding, exceptions, values and continuation escape.
The scalarized branches are guarded by Darwin/GNU, layout and poll-mode checks;
the original code remains the fallback. No Linux path or consumer source is
changed. The 132 tooling tests pass.

D1150 emits two compatible source trees for the original staging stx-car/cdr
callers: 32 guarded paths each, maximum retained heap five words, 63 tree nodes,
and 583/709 emitted lines. stx-car paths elide six to eleven words; selected
stx-cdr paths elide eleven. Unsupported/unselected inputs retain the original
fallback. These trees have not yet been built into the complete runtime.

This contract is not the parser's full Native suite and proves no acceleration
ratio. D1089's retained CI comparison remains the test-performance motivation:
273 versus 113 seconds overall, with selected test batches around 3.19-3.40x.
Different CI core counts and the release-versus-staging distinction remain.
No CI research is repeated here. Real MCP dynamic coverage, allocation-byte
reduction, best-runtime ABBA, official first-compile latency and complete parser
Native execution remain required before promoting a production patch.

Evidence: `.data/d1148-scalar-caller-native/`,
`.data/d1149-scalar-caller-native-rollback/`,
`.data/d1150-stx-caller-emission/`.

## D1151-D1153: Complete Runtime, Zero Real MCP Elision Coverage

The upstream v0.19-staging head is rechecked as
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. D1151 builds the complete counted
scalar-caller runtime with the existing GNU GCC 16 environment, O1/O3 settings,
11 original units and the unchanged 900-second C compilation budget. It links
and passes standard imports. Original object/source hashes and all 14 inherited
trace records match D1083. Two opt-in scalar caller trees are added, separately
from the rejected supplementary fresh-tree experiment. C size is 19,773,008
bytes. Runtime SHA256 is
`a614f92ca7c7d7d25656da6b7a8184f92bf56d7f717175690994a32349e0ac70`;
GSC remains `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.

D1152 uses the real 187-module MCP specification with the original library
home and GSC, overriding only the runtime binary. All 187 modules prepare,
IMPORT-OK is present and the process exits zero. However, stx-car's tree is
entered 460,851 times and stx-cdr's tree 31 times, with zero successful scalar
returns at either site. The separate scalar counter reports zero elided words.
Native allocation remains 4,403,970,584 bytes, with 27 GCs and 1.251792 seconds
GC user CPU. Child user CPU is 4.916130 seconds and wall time 50.580115 seconds
under load around 91. This is coverage evidence, not a valid speed comparison;
official clean was separately running near the end of the diagnostic.

D1153's official MCP clean passes at the recorded head with 12 physical cores
and zero native images remaining. It is a correctness gate, not first-compile
or complete-build performance qualification. All commands have terminated.

Reject the currently selected trees as an acceleration candidate. Do not build
an uninstrumented comparison or promote a patch on the strength of the toy
Native contract or source-only allocation reductions. The bounded enumeration
selected nested-wrapper paths; inspection also finds branches requiring a
positive STRUCTUREDIOP test followed by a non-structure case for the same word.
The actual Gambit header defines STRUCTUREDIOP with an explicit structure check,
so those particular branches are infeasible. Other emitted branches are not
proven infeasible, and the counters do not identify the first failed guard.
Path selection and predicate facts need correction or direct miss evidence
before attributing the zero coverage to one cause. The two caller entry counts
also do not by themselves account for the 11.9 million allocations previously
observed at the dominant wrapper constructor. Tooling tests now total 134 and
pass; the first-log and substantial Native-test acceleration goals remain open.

Evidence: `.data/d1151-scalar-caller-inherited-counted/`,
`.data/d1152-scalar-caller-real-mcp-coverage/`,
`.data/d1153-scalar-caller-counted-clean/`.

## D1154-D1163: Predicate Facts And Whole Mark-Fold Boundary

D1154 adds default-off caller predicate facts. Positive STRUCTUREDIOP implies
STRUCTUREP and the corresponding type-id equality; positive pair/structure
tests are mutually exclusive. Facts follow readonly SSA definitions and remain
path-local. Negative STRUCTUREDIOP does not imply a non-structure. Contradictory
paths are pruned without dropping their valid siblings or changing other modes.
D1155 changes only the experimental caller traversal to breadth-first, keeping
the same 64-result, 20,000-work and statement/frame/visit limits. Short one-call
returns now enter the bounded set instead of only nine-to-eleven-call paths.
D1156's original and 12 candidate Native contracts pass, including real rollback.
This repairs source coverage; it is not a new real-MCP performance result.

The D1152 workload enters the two getter roots 460,882 times in total. At the
selected trees' maximum eleven removed words, even 100% coverage would remove
at most 5,069,702 words or 40,557,616 bytes, approximately 0.920933% of the
recorded 4,403,970,584 allocated bytes. This is a workload-specific allocation
opportunity bound, not a CPU-time bound or proof about other inputs. These
getters alone cannot establish a large allocation-cost reduction.

The wider source boundary is stx-wrap/stx-rewrap's entire mark fold. A temporary
wrapper may be constructed and then cancelled by a subsequent mark, returning
the original payload. D1157 starts after the poll and loses the known local
operator label; unresolved generic calls prevent meaningful allocation paths.
D1158 starts at the original arity-checked entry, including the actual operator
setup, and reaches allocated returns. Initially guards still observe the owned
wrapper itself. D1159 substitutes owned, completed structure fields and rewrites
STRUCTUREDIOP to its type-id comparison, without inventing object identity.
Ten guarded paths per fold now eliminate a five-word intermediate wrapper
entirely. Escaping five/ten-word returns remain allocated. The emitted source
trees have 19 nodes and 237/201 lines; there is no new complete runtime yet.

D1160-D1161 retain an important coverage failure: Native assertions pass but
the selected fast paths are still pair-only. The generated fixture's generic
binding check for unchecked-structure-ref is outside this model. D1162 uses
fixed extended core bindings, matching the direct primitive context used by
Gerbil's generated C; mutable user procedures still retain binding guards.
It generates a fully elided four-word structure tree. D1163 adds an explicit
coverage gate for that fixture's four-word structure, separate from aggregate
pair hits. Original execution and all 12 concurrent std/test candidates pass.
Each candidate records 519 scalarized returns, 1,559 removed words including
eight structure words, and three actual post-allocation rollback words.
The typed-payload assertions preserve result values, object identity, GC and
rebinding behavior. This proves the narrow structure transformation executes;
it does not prove the mark-fold path frequency or startup/test speedup.

Real MCP coverage for the whole folds, uninstrumented best-runtime comparisons,
first compile, complete staging toolchain and full parser Native qualification
remain open. All commands in this series have terminated.

Evidence: `.data/d1154-stx-caller-predicate-facts/`,
`.data/d1155-stx-caller-breadth-first/`,
`.data/d1156-scalar-caller-facts-bfs-native/`,
`.data/d1157-whole-mark-fold-escape/`, `.data/d1158-whole-mark-fold-entry/`,
`.data/d1159-whole-mark-fold-owned-fields/`,
`.data/d1160-owned-structure-guard-native/`,
`.data/d1161-owned-structure-direct-field-native/`,
`.data/d1162-owned-structure-extended-native/`,
`.data/d1163-owned-structure-elision-required/`.

### D1164-D1169: reject canonical mark-fold elision; qualify live small-table reads

The actual `gx#apply-mark` implementation reduces adjacent identical marks:
an equal head is popped, otherwise a different head is pushed. Starting from
the syntax-e initial mark, this preserves the no-adjacent-equal invariant.
The source-only D1159 allocation-elision tree requires equal first and second
marks, so it cannot be the main canonical syntax-e mark-fold optimization.
This does not prove all public stx-wrap inputs or current-expander-marks are
canonical. Do not generalize this rejection to every caller.

D1164 uses the actual compiled apply-mark, not a copied implementation.
D1165 passes all 9,841 three-symbol streams through depth eight in each of
12 concurrent std/test processes, with explicit final success and exits.
This finite Native check accompanies the source induction, not a formal
proof for arbitrary unsafe objects or a performance result.

Existing D1064 counts identify 31,416,253 hash reads, including 26,667,003
misses and 77,668,913 probe steps. They motivate a different default-off
experiment: compare the current keys in tables of at most eight slots with
NEON and return the current value. No result cache, retained GC roots,
mutation fence relaxation, Scheme change or consumer change is introduced.
Large tables, reserved query keys and pending KEY_MOVED rehash use the
original C routine. The gate requires Darwin, AArch64, real GNU GCC and the
qualified single-VM/single-thread ordinary word layout; Linux and Clang
remain unchanged. Valid unique-key GC hash-table representation is required.
Real table-capacity coverage and speedup remain unknown.

D1166 rejects a fixture reader error for the unavailable absent literal.
D1167 and D1168 fail in the original baseline, before candidate testing.
D1168 assertion 522 and generated C identify missing setter execution when
the low-level primitive's result is ignored in this fixture. D1169 performs
writes explicitly through the original C setter instead. This is a fixture
repair, not a production compiler fix or a performance improvement.

D1169 original execution and all 12 concurrent candidates pass identity,
live value mutation/replacement, deletion, GC, forced lazy rehash, large-table
fallback and a kept-alive weak key/value pair. Each candidate reports 538
read entries, 530 selected scans, 201 hits and 329 misses. These are narrow
semantic and path-coverage receipts, not full weak-table qualification or
MCP/test startup performance. The 137 Python tests also pass after adding
the default-off runtime builder options.

Evidence: `.data/d1164-canonical-mark-contract/`,
`.data/d1165-canonical-mark-native/`, `.data/d1166-small-hash-scan-native/`,
`.data/d1167-small-hash-scan-native-delete/`,
`.data/d1168-small-hash-scan-numbered/`,
`.data/d1169-small-hash-scan-explicit-writes/`.

### D1170-D1171: remove SIMD stack-copy cost; runtime coverage pending

GNU GCC disassembly of D1169 shows stack stores and an ld2 reload introduced
by the array/deinterleave spelling. The revised alias-safe implementation
copies directly into two vector values and combines their key lanes.
D1171 disassembly instead shows direct vector loads, register lane combining
and comparisons without a helper stack frame. Original execution and all
12 concurrent Native candidates pass the same contract again.
This is instruction-shape evidence, not startup or Native-suite speedup.

D1170 starts a default-off isolated runtime on the best uncached outlined
lookup/parameter/primitive carrier. It adds scan counts and capacity buckets
at <=8, <=32, <=128, <=512 and larger slots. Original compiler, libraries,
11 original objects and 14 existing trace sites must remain unchanged.
Counters are diagnostic only; an uninstrumented paired benchmark and the
official first-compile and complete parser Native gates remain required.

Evidence: `.data/d1170-small-hash-scan-runtime-counted/`,
`.data/d1171-small-hash-scan-register-loads/`.

D1170's generated C contains the register-load version qualified by D1171.
The original-object hash lists match D1083 exactly, and both have 14 traces.
The initial builder diagnostic flag omitted the new count option; D1170's
top-level `diagnosticOnly: false` is therefore incorrect, while its nested
`smallHashScan.counted: true` correctly identifies instrumentation. Retain
that original receipt rather than silently rewriting it. The builder flag
is corrected for subsequent runs. D1170 must never be admitted as an
uninstrumented performance comparison. Coverage parsing validates all nine
counters and their sums; 139 unit tests pass.

### D1172: real MCP rejects the eight-slot scan candidate

D1170 completes GNU GCC compilation, native linking and import checks;
GSC remains unchanged. D1172 runs the actual MCP 187-module preparation,
checks final IMPORT-OK and exit zero, and validates the complete scan counters.
There are 31,379,584 reads but **zero selected scans**. Capacity buckets are
0 / 22,925,595 / 2,672,711 / 818,455 / 4,962,823 for <=8 / <=32 / <=128 /
<=512 / larger slots. About 73.06 percent of calls use 9-32-slot tables.
The fixture proves a path that this actual workload never takes. Reject the
eight-slot candidate as a startup optimization; do not make an uninstrumented
copy or a production patch for it. Do not enlarge the scan limit and assume
speedup: a longer physical scan can cost more than the original hashed probes.

The diagnostic completes in 57.686 wall seconds / 5.112799 process user CPU
under host load about 83; native workload user CPU is 4.787110 seconds, GC
user CPU 1.252455 seconds, allocation 4,403,971,240 bytes and 27 collections.
These are single instrumented-run receipts, not paired speed evidence or the
official first-compile boundary. Full parser Native acceleration and the
seven-eight-second clean/build objective remain unachieved.

Next source work must address the actual 9-32-slot hash representation or a
larger proven startup cost, preserving lazy rehash, mutation and weak-table
semantics. No consumer or std/make changes are made. All build and test
processes in this series have terminated; 139 unit tests pass.

Evidence: `.data/d1172-small-hash-scan-mcp-coverage/`.

### D1173-D1177: scalarize before opaque operations without predicting callbacks

Upstream v0.19-staging is rechecked on October 5 and remains `1cfb032`.
The source confirms Gerbil's default GC table size hint is 16, explaining
D1172's zero eight-slot coverage. More importantly, existing D1105 attributes
only 4.47 percent of remaining self cycles to gc_hash_table_ref. The call
count is not a dominant CPU share; do not promote a larger SIMD scan merely
because it covers more calls.

D1173 extends the source-only caller audit across the original core, stx and
stxcase units, retaining existing per-root work/step/guard/path bounds.
It audits 1,197 roots, 15,490 paths and 3,397 complete returns; 46 roots have
some potentially elidable words. These are bounded source findings, not a
proof of runtime frequency or a whole-program escape analysis.

Inspection identifies a concrete model limitation: the original effect
boundary requires zero modeled heap allocation. This excludes allocated
prefixes before unknown callbacks even when their constructors are complete.
A separate default-off caller-boundary mode stops before the original opaque
operation. It requires complete constructors, no preceding external effects,
and materializes all registers and all stack stores, including positive
offsets pending an original ADJFP. It never executes or predicts the callback.
Original mutation/GC/unknown operations resume at their original instruction.

D1174 examines 141 stx roots: 4,042 admitted paths include 2,422 original-effect
boundaries. Of 38 positive source roots, 726 prefix paths have potential
elision. Map, fold, for-each and related traversals expose three-to-six-word
opportunities. These counts do not imply aggregate avoided allocation.

D1175 fails candidate C compilation because the fixture's original host does
not declare R3. D1176 preserves the original declaration set: an absent,
unchanged register is read from processor state and is not written as a new
host local; changed absent registers are refused. No ABI/register convention
or consumer change is introduced. Original execution and all 12 concurrent
GNU GCC std/test candidates pass. Each records 1,030 entries, 1,026 actual
prefix completions, 3,078 elided words and three real speculative rollback
words. Assertions cover exactly-once callback counts, escaping pair identity
and mutation, explicit GC, callback/procedure rebinding, multiple values,
exception escape and call/cc. This is a narrow Native contract, not full
callback/signal conformance or performance qualification.

D1177 emits 16 explicitly selected stx prefix sites and 26 original-effect
resume points on unchanged original sources. Per-prefix elision is three to
six words; retained allocations remain where observed. All 142 unit tests
pass, including pending-store retention, no execution of unknown operations,
original host register declarations and non-mutating carrier edit planning.
D1178 starts an isolated counted runtime on the existing best carrier; its
11 original objects, 14 prior trace sites and original compiler must remain
unchanged. Real MCP allocation reduction, paired uninstrumented timing,
official first compile, full toolchain and full parser Native gates are open.

Evidence: `.data/d1173-hot-caller-owned-audit/`,
`.data/d1174-stx-owned-prefix-audit/`, `.data/d1175-scalar-prefix-native/`,
`.data/d1176-scalar-prefix-native-original-registers/`,
`.data/d1177-scalar-prefix-source-emission/`,
`.data/d1178-scalar-prefix-runtime-counted/`.

### D1178-D1180: real scalar-prefix coverage rejects this selection

D1178 completes the isolated GNU GCC counted runtime within the existing
900-second compile budget. Linking and standard imports pass. All 11 retained
original object hashes and all 14 inherited trace records match D1083; GSC
is unchanged. The 16 new prefix sites remain diagnostic-only and default-off.

D1179 runs the actual 187-module MCP preparation, not a synthetic contract.
All modules prepare, IMPORT-OK is present and the process exits zero. The
selected prefixes receive 1,923,141 entries but record zero completions and
zero elided words. Allocation is 4,403,971,240 bytes with 27 collections,
exactly unchanged from D1172. Reject this prefix selection as an optimization;
no uninstrumented rebuild or production promotion is justified.

The diagnostic records native workload user CPU 4.673875 seconds and GC user
CPU 1.233798 seconds, process wall 58.915436 seconds, process user CPU
4.979638 seconds and system CPU 0.851646 seconds. Host load is approximately
79-89 and an official clean runs concurrently. This is neither a paired
performance comparison nor evidence of first-compile or Native-test gain.

D1180 runs official gerbil clean on the same MCP head. It exceeds the existing
30-second clean budget and fails qualification. There is no reported crash,
but no correctness or timing pass either. Contention does not convert the
timeout into a successful gate, and no timeout is relaxed. The supervisor
terminates and reaps its process group; a subsequent process inventory finds
no surviving candidate or test child.

All 143 unit tests pass after tightening absent-host-register observation
refusal. That tightening does not alter these 16 sites: their original stx
host declares all five registers. Native fixture success remains a separate
semantic receipt and cannot override zero real-workload coverage. Official
first compile, complete toolchain and full parser Native acceleration are
still open.

Evidence: `.data/d1178-scalar-prefix-runtime-counted/`,
`.data/d1179-scalar-prefix-mcp-coverage/`,
`.data/d1180-scalar-prefix-official-clean/`.

### D1181-D1183: distinguish missed source shapes from useful speed candidates

Inspecting D1178's emitted stx-car tree shows an outer syntax-wrap prerequisite
and non-pair/box or nested-mark branches; it does not cover the ordinary direct
wrapped-pair path intended for temporary-pair removal. Zero workload hits alone
cannot say whether the original inputs never satisfy the outer prerequisite or
which subsequent guard rejects them. No input-frequency conclusion is drawn.

D1181 is an assumption-only source query on unchanged original C. It seeds two
predicate facts: the incoming argument is a syntax-wrap and its AST-e field is
a pair. It generates no runnable candidate and its assumptions are not runtime
guards. With unchanged work/path/visit limits, car and cdr each admit 64 complete
return paths, all potentially elidable, up to 11 words. Prefix mode admits 64
paths with 63 positive paths each. This identifies bounded path-selection loss,
not real coverage, semantic qualification or acceleration. The existing getter
allocation upper bound is too small to make this alone the requested solution.

The audit also finds unnecessary branches testing whether static, original
procedure descriptors are procedures. The default-off fresh-caller model now
folds PROCEDUREP only for descriptor addresses whose original label metadata
is exactly DEF_LBL_PROC. Unknown input values, unrecognized addresses and return
labels are not assigned this fact. All other analysis modes stay unchanged.
This changes the experimental source model, not the Gambit ABI or consumer code.

D1182 repeats the affected stx source audit after this rule change. It retains
141 roots and 38 positive roots, with 4,117 paths, 4,032 admitted paths and
2,377 original-effect boundaries. It does not uncover a new large-cost target;
do not build another full runtime just from this source-count change.

All 144 unit tests pass, including procedure/return/unknown-address separation
and default-mode exclusion. D1183's original and 12 concurrent GNU GCC Native
contract processes all exit zero. Each candidate records 1,030 entries,
1,026 completions, 3,078 elided words and three real rollback words. These are
narrow semantic checks, not the full parser Native suite or timing proof.
All commands are terminal. The startup and Native performance goal remains open.

Evidence: `.data/d1181-wrapped-pair-source-audit.json`,
`.data/d1182-static-procedure-stx-source/`,
`.data/d1183-static-procedure-prefix-native/`.

### D1184-D1187: actual referenced Native preload, not another CI comparison

The referenced parser PR head is cloned locally into `.data/d1184-parser-ci-source`
at `f35b14193db7cfc89444b0f9a82b81c3862bc795`, without copying dirty consumer edits.
The CI preload, Native suite, exit binding and five-case test-style owner remain
byte-identical to Git. D1089 already contains the CI comparison; no repeated CI
timing study is needed. The selected owner requires std/test, not parser package
installation. Only its original exit-child-process binding is compiled locally.

D1185 accidentally uses gxc's version option `-v`; exit zero produced no object,
and preload fails with module-not-found. This is a preparation failure, not speed
or runtime evidence. The supervisor now uses `-V` and requires all generated
artifacts. D1186 compiles successfully, but the observer's normal shutdown exceeds
the unchanged five-second silence gate after its prefix marker. It fails and its
process group is reaped. D1187 uses the CI's existing native `_Exit` policy instead
of weakening the watchdog. Both original and observer prefixes then exit zero.

Original prefix: 8.550454 seconds wall, 1.153268 seconds native user CPU,
0.088143 seconds GC user, 14 collections, 293,326,376 allocated bytes.
Observer prefix: 7.788035 seconds wall, 1.104094 user, 0.081027 GC user,
14 collections, 295,300,064 bytes. These are diagnostic observations, not an AB
speed result. Periodic balanced source-cost snapshots report no read/clone calls
and only 320 compile/runtime calls. `_Exit` bypasses terminal counter collection;
these snapshots cannot qualify whole-prefix cost coverage or prove all read/clone
cost absent. All receipts explicitly refuse performance and full-suite claims.

### D1188-D1190: Native loader hotspot and current-input image prototype

D1188 hardware CPU profiling observes the actual unchanged Native prefix with
the original staging runtime. It admits 101 interface events, 3,347 running
samples and 2,580,743,150 weighted active cycles. The target exits zero. Process
statistics remain close to the original observation: 1.125264 user CPU seconds,
0.082851 GC user seconds, 14 collections and 293,347,280 allocated bytes.

D1189 resolves XML stack references and attributes inclusive weighted cycles:
55.970589% contain dlopen and the actual Gambit `___dynamic_load` caller;
54.598175% contain dyld Atlas frames inside dlopen. These overlapping percentages
must not be added. The deduplicated self symbol belongs to dyld, not Scheme.
This is a substantial Native-specific target, distinct from earlier MCP execution
and GC targets. It does not justify reviving the rejected RTLD_LOCAL candidate.

Apple's primary [ExternallyViewableState source](https://raw.githubusercontent.com/apple-oss-distributions/dyld/main/dyld/ExternallyViewableState.cpp)
shows Atlas generation/activation in addImages; the
[dlopen implementation](https://raw.githubusercontent.com/apple-oss-distributions/dyld/main/dyld/DyldAPIs.cpp)
provides the corresponding loader context. This source explains the observed
stack; the main branch is not proof of exact installed OS source identity.
No private OS feature toggle or kernel notification bypass is proposed.

The old D892 aggregation is not reused: only 48 of 104 original images and 49
Scheme sources match current inputs, and its GSC differs. D1190 regenerates all
269 Native-closure C units from current original staging SCM, header and GSC,
using 12 physical-core GNU GCC workers. It groups collision-free original module
entrypoints into four images (213/41/13/2). Original per-module linker and Scheme
initialization entrypoints are retained; consumer SCM, interfaces, runtime ABI,
gxi and GSC binaries remain unchanged. Literal generated C constructor/destructor
attributes are refused; this is not complete FFI/header/unload conformance.
Candidate prefix import passes. The isolated alias/image layout is a default-off
prototype, not yet a Gambit source patch or a qualified production optimization.

Upstream `v0.19-staging` is rechecked at
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit input remains
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. No Homebrew installation is changed.

Evidence: `.data/d1185-parser-native-admission-cost/`,
`.data/d1186-parser-native-admission-artifact-gate/`,
`.data/d1187-parser-native-prefix-original-exit/`,
`.data/d1188-parser-native-prefix-hardware-cycles/`,
`.data/d1189-native-loader-stack-attribution.json`,
`.data/d1190-current-native-image-packing/`.

### D1191: real unchanged five-case Native ABBA passes, broad gates remain open

All four sequential original/candidate/candidate/original batches pass exactly
five CASE-OK events, status zero, final GC, NATIVE-SUITE-OK and terminal OK.
Original runtime and compiler hashes plus all 269 original image/source hashes
are validated before testing. The Native child and outer supervisor retain
five-second actual-output silence and 90-second wall budgets. The first CASE-OK
timestamp is measured from the actual event, not an earlier preload log.

User CPU seconds: original 1.558738/1.547294, candidate 0.807568/0.790155.
The local paired mean decreases 48.56% (about 1.94x). First case times are
7.349260/5.931316 versus 6.676882/3.039796 seconds; means 6.640288 versus
4.858339 seconds, a 26.84% decrease. Total wall means are 7.169825 versus
5.337948 seconds. Host load varies around 46-49 with longer averages near 59-66;
large wall variance prevents a stable cold-latency or CI-wide multiplier claim.
This is real Native test evidence, not synthetic fixture timing, but covers one
five-case owner, not all 74 owners or 583 cases. No full-toolchain, full Native,
MCP first-compile or production-patch qualification is claimed.

Evidence: `.data/d1191-parser-native-image-abba/`.

### D1192-D1195: hardware concurrent cases pass and loader hotspot disappears

D1192 launches 12 real unchanged Native batches concurrently, matching physical
cores. All 12 exit zero, complete 60 total cases, and pass the same GC/final-OK
contract. Batch wall is 10.702898 seconds, aggregate parent/child user CPU
10.458892 seconds and system CPU 5.050013 seconds. Per-process first-case times
are 9.139863-9.954028 seconds, longest actual-output gap 2.716111 seconds. This
qualifies concurrent semantics and progress, not a paired concurrency speedup.
Per-process resource deltas are deliberately omitted because child rusage is
shared across concurrent jobs; only whole-batch resource totals are meaningful.

D1193 runs official MCP clean with this same isolated image layout. It exceeds
the unchanged 30-second clean budget with an empty clean log. Its process group
is terminated and reaped. No build first-compile measurement or MCP improvement
is obtained. This failure is retained, not renamed a successful preparation or
excused by host load (approximately 58-65). The Native gain cannot close the
separate MCP startup goal.

D1194 profiles the same Native prefix against the packed current-input home,
with original runtime/compiler and validated source identities. Target exits
zero with its actual marker and statistics: 0.487863 user CPU seconds,
0.252652 system seconds, 0.097319 GC user seconds, 14 collections and
295,908,856 allocated bytes. This diagnostic is not a wall-time benchmark.
There are 1,434 Running samples and 1,051,624,422 weighted active cycles.

D1195 uses a reusable stack-reference attribution tool, tested for overlapping
categories, binary references, Running-state filtering and invalid weights.
The candidate's dlopen-inclusive cycles are 14,191,275 (1.349462%), versus
1,444,457,150 (55.970589%) in the original profile. Atlas-inside-dlopen cycles
are 650,360 (0.061843%), versus approximately 1.409 billion (54.598175%).
Different sampling intervals and contention preclude treating absolute sampled
cycles as a controlled throughput benchmark. Nevertheless the almost absent
loader stack, unchanged executable, comparable allocation, real paired test
CPU result and preserved test contract support the proposed mechanism: fewer
new Mach-O images remove actual dyld work, not merely reorder test messages.

The source-integration boundary is still unresolved: Gambit must retain separate
module entrypoints and initialization, compatible FFI visibility, immutable input
identity, output-image hash locking, replacement/invalidation and unload behavior. `link-flat` is not an
automatic substitute because it aggregates Gambit module linking semantics,
whereas this prototype keeps every original load entrypoint. A production
Darwin-only Gambit integration, complete toolchain build, full 74-owner Native
suite, and successful real MCP clean/build/first-log measurements remain open.
No std/make, std/test, GXPkg, HTTP or consumer source is changed.

Evidence: `.data/d1192-parser-native-image-concurrent/`,
`.data/d1193-current-native-images-mcp-first-log/`,
`.data/d1194-packed-native-hardware-cycles/`,
`.data/d1195-packed-native-loader-stacks.json`.

### D1197-D1199: official MCP parent-load gap, not a Native-only solution

The previous goal turn is progress: it produces real Native ABBA/concurrency
results and a mechanism-changing loader profile. It does not close MCP startup.
Current staging is rechecked again at `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

D1197 captures a two-second live sample within the unchanged official clean
30-second budget. There is no build.ss child at the sampling boundary; the
official gerbil parent is still loading its tool. Of 1,755 wall-clock samples,
1,705 are under `___dynamic_load -> dlopen -> Loader::mapSegments -> fcntl`.
These are waiting/wall observations, not 97% active CPU. The clean still times
out; no timeout extension, successful-clean or first-compile claim follows.
The process group is reaped. No exiting GC or std/make execution is established
as the explanation for this particular failed clean window.

Original `src/gerbil/main.ss` maps build and clean to the gxpkg tool; its original
clean procedure emits a message before launching build.ss. The live image list
already contains many unaggregated tool/dependency images beside the four Native
groups. Thus packing only the Native admission closure is insufficient for this
actual official parent path. This source inspection authorizes no GXPkg or HTTP
edit; it identifies additional immutable Gambit image inputs to the experiment.

Apple's primary [Loader.cpp](https://raw.githubusercontent.com/apple-oss-distributions/dyld/main/dyld/Loader.cpp)
places signature registration and a library-validation fcntl in mapSegments.
That is consistent with the observed stack, but the sample does not identify
the exact fcntl command and upstream main is not exact installed-OS identity.
No signature-validation bypass or private security setting is proposed.

D1198 collects the larger original startup closure but fails diagnostic JSON
parsing: a real deprecated-module warning follows its JSON line. Exit zero is
not accepted as a build or preparation pass. A distinct structured closure marker
now selects exactly one JSON payload instead of assuming the last line is JSON.

D1199 observes 394 original image inputs. A newly conservative dependency parser
refuses GNU's default RPATH commands after object compilation, so this candidate
does not qualify or link. The old executor waits for queued jobs before reporting
that failure. Future runs preflight dependencies before submitting compilation
and cancel queued futures on errors; existing negative receipts are retained.

The dependency reader now explicitly covers strong absolute LC_LOAD_DYLIB
dependencies. Weak/reexport/upward/lazy dependencies and relative dependency
names remain refused. RPATH behavior is not inferred from this dependency set;
the prototype explicitly reports `rpathSemanticsQualified=false`. Output images,
original aliases and strong dependency unions are hash-locked for subsequent
tests. That is stronger artifact identity, not universal FFI qualification.
All 157 supervisor/source unit tests pass at this checkpoint.

Evidence: `.data/d1197-packed-images-official-clean-stack/`,
`.data/d1198-current-official-tools-image-packing/`,
`.data/d1199-current-official-tools-image-packing/`.

### D1200-D1203: wider image candidate fails MCP timing and exposes recipe gap

D1200 completes 394 current-input units into five images (301/60/22/9/2),
with 12 physical-core workers. It reuses 269 completed D1190 Native objects
only after unchanged original image/SCM/compiler/header inputs and byte-exact
regenerated C checks; 125 additional units are compiled by GNU GCC. New C/object
and image hashes, aliases and original strong dependency sets are recorded.
The historical D1190 object digests were not locked in its original receipt;
these new digests do not retroactively strengthen that historical boundary.
The wider original-tool import marker passes, but this is still an experimental
import smoke, not full semantic, Native, FFI, RPATH or performance qualification.

D1201 validates this image inventory and runs official MCP clean/build. Clean
passes and leaves no project native images. First real compile is 28.632101
seconds, and maximum output gap 28.631921 seconds violates the original ten-second
gate. The build is deliberately terminated/reaped at that first compile; it is
not a complete build. Host load is approximately 56-60. No improvement claim,
timeout extension or successful startup qualification follows from this result.

Inspection reveals six undefined macro-variable warnings in the regenerated
Native/tool candidate, absent from the original Native prefix log. They affect
gerbil/runtime/thread~0, std/os/device~0 and std/format/reader~0. Existing five-case
Native success covers only the executed subset; it cannot establish these other
code paths are correct. The historical loader-cycle removal is an observation,
not permission to promote a candidate with an incomplete generation recipe.

Original build sources show `_gambit#.scm` macro inclusion, and the separate
static compilation path includes the gerbil-separate-compilation feature. The
experimental C regeneration omitted that macro input. D1202's first source audit
fails because Gambit compiler options placed after `-e` are treated as interpreter
options. D1203 places module/output options first, then macro evaluation options;
all three affected modules generate C without the undefined-macro warning.
This is a real source recipe check, not a runtime or speed result.

The corrected helper is shared by source auditing and default-off image building.
Future Native/MCP image tests now require the original macro-input mode and a
hashed image inventory. Unchanged generated C may reuse the already built object;
changed C must be compiled afresh. Candidate import also rejects remaining macro
warnings. This changes only isolated backend experiment tooling, not Gerbil SCM,
std/make, std/test or package/HTTP code. Full compiler-option/optimization parity,
production Gambit-only integration, full suites and the startup goal remain open.
All 159 unit tests pass after adding compiler-option ordering checks.

Evidence: `.data/d1200-current-official-tools-image-packing/`,
`.data/d1201-official-tools-images-mcp-first-log/`,
`.data/d1202-original-gambit-macro-recipe-audit/`,
`.data/d1203-original-gambit-macro-recipe-audit/`.

### D1204-D1206: corrected Native result survives, MCP first-log still fails

D1204 regenerates every one of the 394 original C units with the macro input and
separate-compilation feature. 391 byte-identical C/object pairs are reused from
D1200; precisely the three affected modules change and are GNU-recompiled. Five
images are linked and hash-locked again. The actual extended Native/tool import
exits zero with no undefined macro-variable warnings. Its measured native user
CPU is 0.606150 seconds, GC user 0.112360 seconds, 15 collections and 406,005,264
allocated bytes. This wider import is diagnostic, not a controlled speed pair.

D1205 runs real unmodified Native ABBA against this corrected candidate. All four
five-case batches pass original source identity, image hashes/aliases, five-second
silence, 90-second wall, status zero, final GC, NATIVE-SUITE-OK and final OK.
Original user CPU is 1.590925/1.591119 seconds; candidate 0.802664/0.840409.
The means are 1.591022 versus 0.821537 seconds (48.36% lower, approximately 1.94x).
First actual CASE-OK means are 6.662522 versus 4.765916 seconds (28.47% lower).
Total wall means are 7.083755 versus 4.955985 seconds. Host load is roughly 49-54.
The earlier omitted-macro recipe is no longer the basis of this local test result.
One owner/five cases still cannot qualify all Native, FFI or production semantics.

D1206 uses the same hash-locked, corrected candidate for real official MCP
clean/build. Clean passes and leaves no project native images. First compile is
25.238114 seconds, with the same maximum output gap; the ten-second gate fails.
The build is deliberately terminated/reaped at first compile, not completed.
Thus reducing the loader's demonstrated Native cost does not eliminate the real
MCP build-script wait. No clean-only result, Native CPU number or warning-free
import substitutes for that failed requirement. The next source target must come
from the remaining actual first-window execution, not more image-packing claims.

Evidence: `.data/d1204-macro-correct-official-images/`,
`.data/d1205-macro-correct-native-abba/`,
`.data/d1206-macro-correct-mcp-first-log/`.

### D1207-D1208: sample actual remaining build window and requalify concurrency

D1207 samples the real build.ss child at 3.411 seconds after official build,
not the parent clean or synthetic preload expression. Clean passes; first
compile is 23.166620 seconds and fails the unchanged ten-second output gap gate.
The two-second sample completes and the deliberate first-compile termination
reaps the group. This observation is diagnostic, not another speed baseline.

The sampled main thread has 1,704 wall-clock samples. The root `___run -> ___call`
subtree accounts for 748; its concrete frames include expander/core at generated
SCM line 1717, runtime/hash at line 4393, stx, symbol construction and other
original runtime/compiler code. Those two source locations respectively cover
binding resolution/core-expander application and the HashTable interface cast
for hash-get. They remain source-query inputs, not authorization to change Gerbil
SCM or evidence that a type specialization is safe. Another 176 samples lie in
dynamic loading, including notification waits and mapping; filesystem stat and
normalization also appear. Counts are temporal wall samples, not whole-startup
active CPU shares, and nested counts must not be added. The remaining startup
cannot be characterized as solely dyld Atlas cost or solved by the Native result.

D1208 launches 12 real unmodified Native batches with the corrected candidate.
All 12 pass, 60 cases total, with preserved status/final-GC/final-OK contracts.
Batch wall is 12.742016 seconds, aggregate user CPU 10.334961 seconds and system
CPU 4.823219 seconds. Longest actual output gap is 3.399722 seconds. First-case
times are 11.171785-11.820024 seconds under concurrency; no paired concurrent
latency improvement or full-suite qualification is claimed.

All 159 unit tests and diff whitespace checks pass. An authoritative process
inventory shows no surviving owned candidate build, Native test, macro audit or
MCP diagnostic child. Nothing is installed over Homebrew, committed or pushed.
The goal remains active: actual MCP startup, complete toolchain, full Native,
FFI/RPATH/invalidation, and production Darwin-only Gambit integration are open.

Evidence: `.data/d1207-macro-correct-real-first-window-stack/`,
`.data/d1208-macro-correct-native-concurrent/`.

### D1209-D1216: compose existing runtime and image gains; retain startup failures

D1209 composes the exact D1083 uninstrumented runtime with the corrected D1204
five-image inventory. GSC and the original header remain unchanged; runtime and
image digests, original SCMs and nested input receipts are checked. This is an
artifact composition, not a fresh complete source/toolchain build: the cloned
image source tree does not itself contain all D1083 runtime changes. D1211 adds
explicit original/runtime source references in a new manifest, without changing
any binary or retroactively strengthening D1209's historical report.

D1210 fails the real unchanged Native ABBA: the first original batch passes;
the first candidate has no output before the unchanged five-second silence gate.
Its process group is terminated/reaped and its empty log retained. D1212's
runtime readiness and original parent-import diagnostics subsequently pass.
D1214 additionally loads the byte-exact original Native parent source; all six
baseline/candidate diagnostic stages pass. These readiness markers are actual
diagnostic stages, not case output or a substitute for the failed original run.
They do not establish why D1210 failed or prove stable cold startup.

D1213 runs official MCP clean/build with the composition. Clean passes; first
actual compile is 20.608584 seconds, also the maximum output gap. The unchanged
ten-second gate fails. Observation deliberately stops/reaps at first compile;
no full-build, cold-start or speed qualification follows from that run.

D1215's post-diagnostic, unchanged Native ABBA passes all four five-case batches.
Original user CPU is 1.575650/1.570641 seconds; candidate 0.721348/0.749404.
Means are 1.573146 versus 0.735376, about 53.25% lower or 2.14x. Actual first-case
means are 6.477356 versus 3.365269 seconds. These are scoped local observations,
not proof that D1210's initial failure has been fixed. D1216's 12 hardware-worker
candidate batches pass 60 real cases, with batch wall 11.448689 seconds,
aggregate user CPU 9.542913 seconds and longest actual output gap 2.970332.
There is no paired concurrent latency claim or full parser CI qualification.

Evidence: `.data/d1209-runtime-image-composition/`,
`.data/d1210-composed-native-abba/`, `.data/d1211-composition-reference-manifest/`,
`.data/d1212-composed-native-startup-diagnosis/`,
`.data/d1213-composed-runtime-real-mcp-first/`,
`.data/d1214-composed-native-parent-source/`,
`.data/d1215-composed-native-post-diagnosis-abba/`,
`.data/d1216-composed-native-hardware-concurrent/`.

### D1217-D1219: expand to original staging standard-library Native owners

The new concurrent runner uses the same byte-exact parser CI Native harness and
eleven byte-exact staging standard-library test sources, rather than generated
toy cases. It keeps physical hardware capacity (12 workers), 90-second wall,
five-second actual output silence, explicit child status, final GC and final OK.
No standard-library source, test, package or HTTP implementation is edited.

D1217's original baseline fails `string/path-test.ss`: the unchanged assertion
at source line 167 expects `/etc/`, whereas Darwin returns `/private/etc/`.
The original child reports status 42 and the parent exits 70; ten other owners
pass. This pre-existing platform assertion failure is retained, not repaired or
converted to success. D1218 references that exact-head/source-hash failure and
admits only those ten owners for a named performance subset; its original wave
then fails the unchanged silence gate in `number/misc-test.ss`. That result too
remains a failure. No further owner or timeout is removed.

D1219 retains all four ABBA waves even if one fails, so a baseline failure cannot
prevent candidate execution. This run passes all ten owners in all four waves:
71 real cases per wave, 284 total, identical actual case identities. Each wave
uses a 12-worker pool; completed original cases retain every original gate.
Original user CPU is 16.922476/16.924869 seconds; candidate 8.219349/8.222338.
The paired means are 16.923673 versus 8.220844 seconds, about 51.42% lower or
2.06x. System CPU means are 5.185700 versus 4.090409 seconds. First-case means
across owners/waves are 13.875450 versus 11.387372 seconds, only about 17.93%
lower. Batch-wall means are 16.518013 versus 15.665234 seconds, roughly 5.16%
lower; one candidate wave is slower than either original wave. Host load is
approximately 58-67. Do not turn the twofold user-CPU gain into a twofold user
latency or whole-CI claim. Longest actual output gap is 3.427517 seconds.

This broadens local semantic and CPU evidence beyond the earlier five-case
owner, but remains a ten-owner subset excluding the explicitly failed original
Darwin path assertion. Initial cold silence failures, full parser Native CI,
complete toolchain, production Darwin-only Gambit integration and actual MCP
startup remain open. All 165 focused unit tests and whitespace checks pass.
Nothing is installed over Homebrew, committed or pushed; the goal is not complete.
Final remote staging recheck remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`,
matching the test source checkout. An authoritative owned-process inventory
confirms no surviving composition, Native or MCP diagnostic process.

Evidence: `.data/d1217-staging-std-native-concurrent-abba/`,
`.data/d1218-admitted-std-native-concurrent-abba/`,
`.data/d1219-std-native-all-waves-retained/`.

### D1220-D1222: actual MCP first-window active CPU and failed official ABBA

D1220 attaches the hardware CPU profiler to the actual official build.ss child
of the immutable D1211 composition, after official clean. Recording starts at
3.387153 seconds; the first real compile appears at 19.716867 seconds. The
unchanged ten-second output gate fails. The recording covers only a partial
pre-first window, not the whole prefix or a complete build. Sampler exit zero
is explicitly not the attached build's exit status: the build is deliberately
stopped/reaped. The summarizer accepts an attached process only with the typed
first-window receipt, matching PID, recording bounds and exact binary digest.

The 4,367 Running samples carry 3,610,075,557 active-core cycles. Coalesced host
accounts for 36.91%, mark_array and its constprop variant 26.25% combined,
native helper 11 6.81%, GC hash lookup 5.08%, movable-object scanning 3.20%,
kernel 3.19% and evaluator 2.49%. These are active CPU shares, not debugger wall
waits or a claim that changing one subsystem removes the full startup delay.

D1221 reuses the already generated D1108 DWARF mapping. The original and
relocated D1211 runtime bytes and recorded UUID match, and generated C/text
identities remain checked. No repeat debug compilation is needed. All 757
coalesced-host PCs map, with zero unmapped cycles. Within the host only, IF is
20.55%, JUMPRET 11.14%, arity equality 10.78%, POLL 8.26% and shared END_M_HLBL
7.69%. Ordinary individual source lines are small; this does not establish a
new isolated large optimization target. The shared end-label line is not a
single caller's cost.

D1222 runs official MCP ABBA without profiling overlap. Every official clean
passes. Original first compile is 45.896049 seconds in the first wave; its
second wave has no first compile within the unchanged 60-second observation
cap. Candidate first compiles are 31.669512 and 30.174660 seconds. All strict
ten-second gates fail; the first original stop also needs forced cleanup after
its termination wait. All owned process groups are reaped. The incomplete
original pair prevents a complete ABBA mean or speed ratio, rather than
turning a censored timeout into an acceleration result. No full build passes.
Host load is approximately 65-83, and is recorded rather than subtracted.

Evidence: `.data/d1220-real-mcp-first-window-hardware/`,
`.data/d1221-real-first-window-coalesced-lines/`,
`.data/d1222-official-mcp-first-window-abba/`.

### D1223-D1224: native compiler-context serialization refuses promise mutex

This is a feasibility diagnostic for avoiding repeated metadata construction,
not a restored cache, import reordering or a speed candidate. It imports the
real original std/build-script context and calls Gambit's existing
object->u8vector with an identity observer. Walk counters report actual visited
objects; no state is replaced and no registry is restored. A two-million-object
budget bounds the diagnostic, not production startup.

D1223 fails the unchanged five-second silence gate during probe setup, before
context readiness. It is not a serializer refusal and remains a failed run.
D1224 loads the diagnostic under the existing original Native interface tracer
and retains the same five/90-second silence/wall limits. It completes a typed
diagnostic after 1,280,335 visited objects, but serialization fails before any
encoded result: the exact irritant is `#<mutex ... promise>`. Gambit
`lib/_system.scm` explicitly rejects thread, thread-group, mutex and condition
variable structures in the serializer. The diagnostic's zero exit means that
the refusal was recorded, not that the context was serializable or faster.

No mutex is stripped, recreated or treated as pure data; doing so would need
separate synchronization, closure/type identity and restoration correctness
proof. No snapshot candidate or production Gambit patch is admitted from this
negative result. D1224 has wall 40.478597 seconds and maximum actual output gap
1.553462 seconds; these instrumented walk timings are not performance results.

Evidence: `.data/d1223-native-context-serialization-feasibility/`,
`.data/d1224-context-serialization-traced-load/`.

### D1225: Native real-output phase timestamps, failed expanded ABBA

The external supervisor can now retain timestamps for actual module-batch,
module-import, CASE-OK, harness-return and final-GC output. It generates no
child progress lines and changes no original test or preload source. The
original physical 12-worker pool and five/90-second gates remain unchanged.
The first sandboxed invocation cannot query hw.memsize and fails before any
test launch; the subsequent host-permitted invocation creates D1225.

All four waves are retained and fail qualification. Original waves each fail
number/misc-test.ss with child silence/batch error and parent exit 70. Candidate
wave one records a PermissionError in that owner's supervision/cleanup;
its raw child log also contains the original native-child silence error.
Candidate wave two fails the outer silence gate for values, ports, number
writer and number misc owners. No failure is converted to a pass, excluded
from admission or used to compute a whole-wave speed ratio. The authoritative
post-run process inventory finds no surviving owned process.

Only completed owners have returned phase receipts: nine/nine/six/nine in
ABBA order, so the following phase means are survivor diagnostics, not a
matched performance comparison. Original parent-to-batch-start means are
4.375692/4.424683 seconds. Child batch start to final pre-case module import
means are 18.225559/19.545683 seconds; import-to-first-case means are
1.054915/1.227638 seconds; after-first-case means are 0.537259/0.724480 seconds.
Candidate completed-owner phase means are respectively 4.048826/4.731425,
11.087905/8.871182, 1.008603/0.637867 and 0.415108/0.244013 seconds. Host load
is approximately 79-88. The timestamps establish that pre-case admission is
the large observed latency interval, but do not attribute it entirely to
active CPU or establish stable accelerated cold startup under this load.

The original gxtest prepare-module calls import-module with evaluation before
enumerating test-suite exports; the number/misc original source contains
many nested check expansions. Its failure before any CASE-OK is not evidence
of a slow executed test case. Source inspection is read-only, and no std/test,
gxtest, std/make, package or HTTP code changes. Real test latency remains an
open acceptance gate alongside official MCP first compile and full toolchain.
All 172 focused supervisor/identity tests pass. No production patch is promoted,
Homebrew installation replaced, commit made or push performed.

Evidence: `.data/d1225-std-native-real-phase-abba/`.

### D1226-D1229: deepen the proven image route, preserve weak-binding FFI

The user explicitly prioritizes the already demonstrated Darwin Native gain.
The next work therefore returns to immutable image aggregation, rather than
new serializer, isolated helper or repeated CI timing hypotheses. Earlier
D1188/D1194/D1195 already show the mechanism: original dlopen-inclusive active
cycles are 55.970589% versus 1.349462% with packing, and actual matched Native
test CPU nearly halves. Those receipts are reused, not reprofiled or promoted
to a whole-CI/cold-start multiplier.

D1226 audits the existing 394 original and five corrected packed Mach-O images
by parsing bounded load commands and nlist64 symbol tables. Input and packed
hashes remain locked. No symbol-table definitions are added or removed and no
original undefined symbol acquires a reported provider in another packed input.
There are no reported native initialization/termination section hooks. The
large group has two duplicate weak-runtime definitions, emutls_get_address and
emutls_register_common, supplied by original crypto/libcrypto and net/ssl/libssl
phase-zero images. Both original images carry WEAK_DEFINES/BINDS_TO_WEAK; most
other images do not, while their packed group does. This is not proof of a
semantic bug: normal weak coalescing and aggregate flag unions can explain it.
It identifies a conservative production-eligibility boundary worth retaining.
Every original and packed image also carries literal `@loader_path` RPATH;
equal strings do not establish equivalent resolution after relocation.

D1227 reuses all locked generated-C/GNU objects without Scheme regeneration or
new C compilation. It clones the original isolated toolchain and repacks only
392 ordinary inputs into five groups (299/60/22/9/2). The two weak-binding FFI
images remain original regular files, byte-identical, not aliases. The inventory
validator now checks their hashes/dependencies and refuses replaced/symlinked
or duplicate preserved inputs. This eligibility is Darwin-only experiment
tooling, not automatic production Gambit integration. Ordinary linking refuses
an output that newly gains weak-binding/initialization eligibility exclusions.
Original gxi, GSC, consumer flags and SCMs remain unchanged. The real original
Native admission prefix completes within unchanged five/90-second progress
limits; this is import/construction qualification, not test or speed success.

D1228 audits the new groups: all match their original architecture and Mach-O
flags (133), with no duplicate nlist definitions, no added/removed definitions,
no possible newly internal symbol providers and no native initializer hooks.
Symbol tables are not a complete export-trie/dyld binding proof. RPATH resolution,
FFI execution, unload/replacement, automatic source integration and full builds
remain open. No claim of additional acceleration over the existing packed
candidate follows from this eligibility change.

D1229 expands real std/test admission to four unchanged staging owners: digest,
cipher, pkey and local TLS socket. Each runs three replicas per wave in the
physical 12-worker pool, for 48 actual Native parent launches over four ABBA
waves. Original parser Native source, status/GC/final-OK checks and five/90-second
limits are unchanged. No internet-dependent SSL owner is selected; socket tests
use the original ephemeral loopback peers. All 48 attempts fail the initial
five-second silence gate, with empty logs and no CASE-OK; both original and
candidate fail. Host load is approximately 95-117. This supplies no executed
FFI assertion, semantic pass or acceleration ratio and is not dismissed as a
pass based on load. The authoritative owned-process inventory finds no survivors.

All 178 focused unit tests pass, including bounded malformed Mach-O parsing,
weak-image preservation and original-image hash/alias rejection. Latest remote
staging remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0` in this turn. No consumer
source, package/HTTP implementation, Homebrew installation, commit or push changes.
The goal remains active: known Native CPU gains are real, but stable cold
latency, execution of the expanded FFI cases, production integration, complete
toolchain and actual MCP first compile are still unproven.

Evidence: `.data/d1226-packed-original-linkage-audit/`,
`.data/d1227-ordinary-images-preserved-weak-ffi/`,
`.data/d1228-ordinary-linkage-post-build-audit/`,
`.data/d1229-original-crypto-tls-native-abba/`.

## D1230-D1235: Source-owned native objects, not a new speed claim

The next implementation supports the demonstrated image-packing route, rather
than another small runtime candidate. Candidate `0014` modifies only Gambit's
Unix dynamic driver and helper distribution rules. Object capture is off by
default and, when explicitly enabled, probes the actual compiler for Darwin,
GNU GCC and non-Clang macros. Nonmatching compilers retain the original dynamic
command. This guard is structurally tested; it is not a Linux native test pass.
The helper retains actual temporary GNU objects before the unchanged collect2
link, without regenerating Scheme/C or changing optimization and `-pipe` flags.
Content-addressed objects and reference files bind to both current image and
object SHA, with conservative regular-file/Mach-O identity admission.

D1231 fails: intercepting the assembler did not retain an object because GNU
GCC's `-pipe` command wraps cc1 and collect2, but not the assembler on the other
side of the pipe. The failure remains recorded. Capture was moved to collect2's
existing object inputs, keeping the established compile flags unchanged.
D1232 then compiles the same locked original staging `std/test/unit~0` C input
through original and candidate drivers. Both whole native image hashes equal
`48d1fb5f9085c612718c85ed465bf86d083bb504f05c32c321e16f9ffee43c2b`.
Relinking the retained object changes the whole image hash to
`20c0047f44bdfcf96382ecf62d028ac86a053081ad69fc6f02af1ed0ac0d0f32`;
native text and the bounded parsed linkage metadata remain identical across
all three. This is single-unit construction parity, not execution, speed,
full dyld semantics or full-toolchain qualification.

D1233 checks that the published source patch applies to original staging
driver/makefile inputs; it is a dry apply check, not an installed source build.
D1234's subsequent original-GSC dispatch check is explicitly invalidated after
log audit: inherited BUILD_DYN parameters still selected pre-generated C.
D1235 removes those overrides but fails its generated-C path check: Gambit
writes generated C beside its Scheme input, not beside the requested image.
Neither is accepted as source-dispatch qualification. The next check gives
each original/candidate invocation a separate byte-identical Scheme input.
All 185 focused unit tests pass at this point. Automatic packing, RPATH,
unload/replacement, real FFI assertions, cold MCP first compile and complete
toolchain qualification remain required. No source-capture timing is promoted
to acceleration; the capture hook itself is not the image-packing optimization.

Evidence: `.data/d1230-gambit-native-object-cache-source/`,
`.data/d1231-original-native-object-capture-parity/`,
`.data/d1232-link-input-native-object-capture-parity/`,
`.data/d1233-native-object-source-patch-apply/`,
`.data/d1234-original-gsc-native-object-dispatch/`,
`.data/d1235-clean-gsc-native-object-dispatch/`.

## D1236: Actual original GSC source dispatch

The revised diagnostic removes inherited BUILD_DYN overrides and gives each
concurrent invocation a separate byte-identical `module.scm`. Original GSC
uses the original Gambit macro include and separate-compilation feature,
generates `module.c`, and actually dispatches its selected gambuild driver.
Both newly generated C files match locked macro-correct SHA
`3ef179176c5fda03e5ee5c9fc97e2203c350bd4ce825b7eca2312ec9c1f2a094`.
The candidate command log selects this local `module.c` with the GNU wrapper;
it no longer selects the previously generated diagnostic C input.
Original/captured whole native images both have SHA
`94509753d33355a7b9885ef8764832493fb374f9fdb0bca703615f6487174960`.
Retained-object relink again differs as a whole image but matches native text
and bounded parsed linkage metadata. All three real commands exit zero.
The physical 12-worker pool handles two independent source compilations;
this does not pretend that twelve frontend jobs were launched.

This qualifies only original-GSC source dispatch and single-unit construction
parity. It does not qualify runtime execution, packing, cold latency or a full
installed toolchain. Capture remains default-off and performanceQualified=false.
The implementation direction remains reduced Darwin loader execution through
eligible immutable image aggregation, using actual original compiler objects.
Previously measured Native CPU gains are not a claim that the entire observed
Linux/macOS CI gap has this one cause. Evidence:
`.data/d1236-isolated-gsc-native-object-dispatch/`.

## D1237-D1241: Actual object aggregation and an early-loader failure

Previous goal turn classification: progress. It produced actual original-GSC
source-dispatch parity, not merely a plan or a new timing claim. This turn
extends that mechanism to original staging `std/make~0` and
`std/build-script~0`. Both independent original/captured compilations exit zero,
produce the locked original macro-correct C bytes, and match whole image hashes,
native text and bounded parsed linkage metadata. No consumer SCM is edited.

D1239 consumes the three actual source-driver cache manifests and retained
objects, checking current source/C/compiler/header/image/object hashes. A
conservative group refuses weak definitions, initialization hooks, non-System
direct libraries, duplicate definitions and new in-image symbol providers.
It links the three retained objects without Scheme or C recompilation. Link
exit is zero, with identical architecture/flags/RPATH, no added/removed external
nlist definitions, no duplicate/provider change and only absolute libSystem
dependency. This proves bounded construction, not full exports/dyld semantics.
The original import completes (17.323829 seconds, first output 2.827446); the
candidate fails initial five-second silence with an empty log. qualified=false,
importQualified=false and performanceQualified=false are retained.

D1240 removes an executable-inode confound: both library-home roles launch the
exact same original gxi, not byte-identical separately copied executables. The
original again completes (10.567064 seconds, first output 1.805257), while the
candidate still fails the initial silence gate. No ratio is calculated. This
contradicts an explanation limited to the copied executable; it does not by
itself identify a defective aggregate or attribute failure to host load.

D1241 observes three seconds of real startup stacks for those two roles while
keeping the original five/90-second product gates. Sampling output stays in
separate files; it does not create product progress. The original import passes,
while the candidate again fails without output. Of 2731 candidate main-thread
samples, 2728 are under dynamic_load/dlopen and 2712 are under
Loader::mapSegments -> SyscallDelegate::fcntl -> __fcntl. Thus this sampled
quiet interval is loader/kernel work, not macro-expansion execution. Samples
are wall-stack observations, not active CPU-cycle measurements or proof of the
complete cold-start interval. Apple dyld's public mapSegments implementation
contains the F_CHECK_LV library-validation call at that site; the installed
dyld command value is not established by this stack alone. See
[Apple dyld Loader.cpp](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/Loader.cpp).
No system security check is disabled or bypassed.

The three std units only load after the initial core images; the sampled
candidate already has original expander/sugar phase images loaded. Therefore
this narrow aggregate is insufficient for early-startup qualification. The
next action is the complete ordinary image closure, reusing previously locked
GNU objects and retaining all external-library images, not recompiling the
same source or retrying the three-unit timing until it passes. Automatic
production packing, complete toolchain, real cases and MCP first compile remain
open. All 193 focused unit tests pass, including observer-failure process
cleanup, no artificial product output and current-image symlink rejection.
Latest remote staging is still `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

Evidence: `.data/d1237-original-std-make-native-object-capture/`,
`.data/d1238-original-build-script-native-object-capture/`,
`.data/d1239-source-captured-native-image-aggregation/`,
`.data/d1240-shared-executable-captured-image-aggregation/`,
`.data/d1241-captured-image-quiet-startup-stacks/`.

## D1242-D1245: MCP failure prevents promotion

D1242 reuses locked original GNU objects without Scheme regeneration or C
recompilation. It preserves all weak/initializer images and every non-System
direct dependency image. Thus 391 ordinary images become five groups
(298/60/22/9/2); crypto/libcrypto, encoding/zlib and net/ssl/libssl remain
byte-identical original regular files. There are eight physical images for
the 394-input closure. Original executables, header, consumer flags and source
inputs remain unchanged. The real Native admission prefix exits zero, with
first output 4.181198 seconds and total 13.959756 seconds under unchanged
five/90-second gates. This is prefix admission, not executed-case success,
MCP first compile, a cold-start ratio or complete toolchain qualification.

D1243 directly runs official MCP gerbil clean/build with that candidate. Clean
exits zero in 11.070269 seconds and leaves zero project native images. Build
produces no real compile line in the 60-second first-window observation; its
ten-second product-output gate also fails. firstCompileSeconds=null,
qualified=false, performanceQualified=false and buildCompleted=false remain.
This is a serious failed end-to-end candidate, not an improvement supported by
the prior Native prefix. Observation time is not a relaxed pass threshold.
No host-load explanation is substituted for locating the quiet work.

D1244 executes the unchanged four crypto/TLS owners with three replicas each
in the physical 12-worker ABBA pool, retaining every wave and five/90-second
gate. All four waves fail. The second candidate wave completes five batches:
two cipher batches and three pkey batches, ten CASE-OK events with explicit
zero harness status, final GC and Native final OK. Other attempts fail silence
or exit nonzero. One candidate TLS batch executes and reports bind EINVAL at
original os/socket.ss:83, returning harness status 42 and parent exit 70.
Baseline waves never complete a batch; they cannot establish whether that
executed TLS error is baseline behavior or an aggregation regression. It must
not be waved away or excluded to make admission green. There is no accepted
ABBA ratio or full FFI qualification. All 193 focused unit tests remain green;
they do not contradict these real-product failures.

The user explicitly rejects the 60-second no-first-log result relative to the
earlier seven/eight-second behavior. D1245 therefore stops expanding owner
testing and runs a strict original-toolchain MCP control, with no candidate
image changes. Original gerbil clean itself has an empty log and fails its
30-second gate, before any build observation. This invalidates a current
matched first-compile comparison; it neither proves a candidate-only cause
nor excuses candidate failure. The original control must be made observable
before new performance claims or production promotion. No Homebrew installation
has been replaced. A separate promotion-status file marks D1242 rejected for
current MCP-startup delivery without rewriting its immutable prefix receipt.
No source-capture or image candidate is claimed to eliminate the seven/eight
seconds. The complete objective remains active and incomplete.

Evidence: `.data/d1242-system-only-startup-image-repacking/`,
`.data/d1243-system-only-official-mcp-first-compile/`,
`.data/d1244-system-only-crypto-tls-native-abba/`,
`.data/d1245-original-mcp-strict-regression-control/`.

## D1246: Original clean sampled before any build child

The unchanged original official clean again fails the 30-second gate. Its
two-second sample targets the official parent because no build-script child
exists at sampling time. Of 1804 main-thread samples, 737 are under Gambit's
getcwd_long_path/libc getcwd, largely stat/open syscalls. This is a short
wall-stack window, not on-CPU attribution or proof that directory normalization
accounts for the whole 30 seconds. The clean log contains sampling-tool output,
not a genuine product clean line; it must not count as product progress.

Source inspection identifies the existing normalization implementation:
save cwd with getcwd, chdir to the requested directory, getcwd again, restore
the old directory. Earlier D1088 already measured approximately 0.481 seconds
of normalization CPU in two partial build processes and rejected a filesystem
rewrite as the dominant startup fix. This new quiet-parent window does not
erase that prior evidence or justify an unqualified directory cache/realpath
replacement. No filesystem policy or consumer source is changed. Original
control observability and locating the candidate's actual MCP quiet stage
remain prerequisites; the failed candidate is still not promotable. Evidence:
`.data/d1246-original-clean-quiet-parent-stack/`.

## D1247-D1249: Reject silent startup; observe the official parent

D1247 runs unchanged original official clean without a sampler. It completes
in 14.522 seconds, with 2.039 seconds user CPU and 0.864 seconds system CPU
in reaped supervisor children. This is clean-only evidence, not restoration
of the earlier seven/eight-second first compilation or a matched speedup.
Resource accounting explicitly includes observer children when present;
it is not active-cycle attribution. Clean sampler output now goes to its own
log and cannot count as product progress.

Source inspection closes the proposed basename module-reference mismatch:
Gambit's dynamic compilation defaults derive the module reference from the
output basename without its extension and the linker name from the dynamic
output basename. The prototype's explicit basename names are consistent with
those defaults. This does not establish full original machine-code parity
or resolve the executed TLS failure.

D1248 fails before product execution because sandboxed hardware discovery
denies sysctl; its output directory contains no product receipt. D1249 runs
the isolated rejected candidate with the original strict output gate, not a
60-second observation allowance. Official clean completes in 19.298 seconds.
At 3.434 seconds into build, no qualifying build-script child exists, so the
sampler attaches to the actual official parent. Build fails the ten-second
silence gate without a real first compilation line. Across 1667 main-thread
samples in the short window, 599 are under getcwd_long_path, with stat/open
and other syscalls; VM/module expansion and packed module execution are also
present. These wall-stack counts are not a whole-window CPU attribution or
proof of a dominant filesystem fix. The 29.419-second combined observation
has 1.558 user and 0.989 system CPU seconds including its observers; it is
not a build-only CPU measurement.

The observer now selects the official parent when no actual build child
exists, and labels that target explicitly. Five focused observer tests and
all 196 unit tests pass. They do not qualify this failed product candidate.
No product/Gambit optimization, consumer source, Homebrew installation, or
output deadline is changed. D1242 remains rejected for MCP startup delivery.
Evidence: `.data/d1247-original-clean-wall-cpu-control/` and
`.data/d1249-rejected-candidate-quiet-stage/`.

## D1250-D1252: Original debug recipe was missing from image experiments

D1250's unchanged original official clean fails its 30-second gate before
build sampling. The supervisor reaps its owned process. Observed reaped-child
CPU is 1.903 user plus 0.800 system seconds, over 35.066 seconds including
cleanup. A separate read-only ps snapshot totals 1056 percent process CPU,
including 139 zellij processes at 661 percent and rustc at 132.3 percent.
This is a transient scheduling observation, not proof of exclusive cause or
permission to stop unrelated work. No comparable first-log ratio is admitted.

Apple's public Libc gen/FreeBSD/getcwd.c implementation already uses open,
F_GETPATH, fstat/stat identity checks and close before its generic fallback.
Replacing getcwd with F_GETPATH is therefore not a new large accelerator;
omitting identity checks would need separate semantic justification. No such
filesystem replacement is made. Source:
https://github.com/apple-oss-distributions/Libc/blob/main/gen/FreeBSD/getcwd.c

D1251 compares original installed __text directly against the earlier
source-capture images, rather than only comparing two regenerated controls.
All three differ: std/test/unit~0 is 1416 versus 1372 bytes, std/make~0 is
87736 versus 78856, and std/build-script~0 is 4332 versus 3964. A byte mismatch
alone is not proof of incorrect behavior, but disproves unchanged machine-code
inputs for these modules.

The source establishes a specific missing input: src/std/build.ss passes
debug: #t through std/build-std.ss to std/make; compiler/driver.ss adds
-debug-source, -track-scheme and -g. The image regeneration recipe omitted
these. Core build1 and tools/build explicitly pass debug: #f; applying std
debug options indiscriminately would also be wrong. Gambit's frontend makes
explicit debug-source enable compiler debug, and _gvm.scm refuses certain
instruction/block equivalences when debug information is present. Track-scheme
also emits C line directives. This is not merely a difference in symbol files.

D1252 regenerates and compiles three byte-identical original SCM sources using
the original GSC, original native driver and GNU GCC, with the missing std
options restored. A hardware-sized twelve-worker pool runs the three jobs.
All three generated __text sections now match the installed originals byte
for byte, including their sizes. This is actual construction evidence, not
performance or full metadata/FFI equivalence. No original installation changes.

Consequently, previous packed-image timing observations remain observations
of combined image aggregation and changed generated std code. Their attribution
to aggregation alone is withdrawn; neither those timings nor the default-off
object-capture patch prove the requested startup optimization. Immutable old
receipts are retained as negative/confounded evidence, not silently rewritten.
The prototype recipe now has an explicit original-std-debug-options mode,
scoped to std paths, records its use, and never advertises installed native
text parity from that flag alone. Legacy experiment mode remains explicit.
All 197 unit tests pass. A correctly controlled future packing experiment
must preserve original debug inputs and establish installed-code parity before
claiming an image-only gain or promoting a patch.

Evidence: `.data/d1250-original-quiet-stage-control/`,
`.data/d1251-installed-native-text-parity/`, and
`.data/d1252-original-debug-recipe-parity/`.

Remote v0.19-staging is revalidated at
1cfb032c7a1612637da6205f5f8a15683eba3ba0. An initial query for the nonexistent
staging ref returns no output and is not treated as head evidence; the actual
v0.19-staging reference matches the local source. All owned diagnostic and
construction processes are terminal, with no matching survivors. No patch
promotion, full toolchain qualification, commit, or push occurs.

## D1253-D1255: Installed-code parity extended; full reconstruction still fails

The image builder gains explicit installed native __text verification. Every
generated/reused GNU object is separately linked through the original native
driver and compared with the corresponding installed image before aggregation.
The original std debug recipe is enabled; no syntax-only O3 override is used.
The current-input 394-module closure is reused from its locked earlier receipt,
not rediscovered by repeating a startup benchmark. Twelve physical workers
remain the concurrency setting. Existing successful unit objects may be reused
from an otherwise failed build only after source/C/object hashes and original
compiler/header/macro identities match, and the new invocation repeats native
text verification. A failed build receipt never becomes full qualification.

D1253 records 100 passing unit comparisons, including all 85 non-std modules.
It fails the single-image parity link for std/crypto/libcrypto~0 because the
diagnostic omitted its installed image's OpenSSL dependency, not because a
machine-code mismatch was observed. The builder restores explicit original
non-System dependency paths for its parity links. Relinking the already-built
object with that dependency succeeds; both __text sections contain 65384 bytes
and have SHA-256 3cbbaac03107b39a25e04f756a453ac553e912ebb0c1db2b4c01a6c81b86969a.
This repair changes diagnostic construction only, not runtime or consumers.

D1254 fails immediately on a supervisor bug: reusing verified C inputs does
not create a new generation log, but warning validation tries to read one.
The observer is corrected to inspect the original generation log rather than
fabricating new progress or rewriting the failed receipt. D1255 reuses the
100 verified inputs and proceeds to 242 recorded successful comparisons.
It then fails a GNU object compilation's unchanged 180-second budget. Process
group cleanup raises EPERM and masks that timeout in the report's short failure
field; the retained traceback contains both failures. The supervisor now
records named invocation timeouts before cleanup and publishes a real failure
before waiting for other started workers to finish. No deadline is increased.

After D1255 is terminal, a separate artifact audit directly inspects all
253 separately linked images actually produced, including completed worker
results not admitted before the first future failure. All 253 match installed
__text byte for byte. This audit remains explicitly unqualified and does not
turn an incomplete build into success. Two started modules lack objects:
std/format/ioutil~1 (9355470-byte generated C) and
std/io/interface/socket~1 (12539955-byte generated C). No mismatch is found
among the checked images, but the remaining full closure is unproven.

No aggregate candidate is completed, no new MCP timing or Native speedup is
claimed, and no production patch is promoted. All 197 unit tests pass, which
does not override the real construction failures. An authoritative process
inventory finds no survivors matching D1255's isolated output. The next gate
is completing original-code reconstruction within the existing budget, then
conservative system-only packing and actual MCP/std verification. The requested
seven/eight-second startup remedy remains incomplete.

Evidence: `.data/d1253-original-debug-verified-official-images/`,
`.data/d1254-original-debug-verified-official-images/`, and
`.data/d1255-original-debug-verified-official-images/`, including
`terminal-artifact-audit.json` and the retained construction logs.

## D1256: Strict two-unit retry fails; metadata-cache shortcut rejected

Source inspection finds an explicit contract in gsc/_source.scm:
source->expression returns a fresh non-eq expression on every call. GSC's
_gvm.scm already passes generated debugging metadata through
debug-info-compact-using-sharing and the C backend already owns a metadata
sharing table. An actual unchanged GSC call uses two independently allocated,
equal nested lists/strings: input identity is false, compacted output identity
is true, and output content equality with the input is true. Its printed result
is (#f #t #t). No source-expression memoization or alternative metadata cache
is implemented; neither a missing sharing policy nor a safe large acceleration
has been demonstrated by this inspection.

D1256 retries only the two unfinished modules using the retained original-debug
C, original installed compiler/header/macro inputs, and original GNU O1 driver
with -g. Hardware pool capacity remains twelve, with two actual remaining jobs,
not an arbitrarily two-core build setting. Each native invocation keeps its
180-second budget. Both object compilations time out, neither reaches its link
or machine-code comparison, and the report remains unqualified with no speedup.
The explicit compiler commands are retained. A process inventory after terminal
completion finds no matching survivors. No original installation is modified.

The retained generated C has 120 ordinary strings totaling 3642 characters for
std/format/ioutil~1, and 110 totaling 3520 for std/io/interface/socket~1. The
maximum length is 32 in both; neither contains a string at the existing 4096
packed-emitter threshold. Thus the previously recorded large-string object
speedup cannot simply be applied to these two failures. This counting observation
does not establish which GNU compilation pass or other C construct dominates.
No compiler-option or timeout relaxation is used to manufacture a successful
full closure. The 253 successful earlier text comparisons remain partial proof,
not completion of conservative packing, MCP first-log, or Native qualification.

Evidence: `.data/d1256-original-debug-two-unit-retry/report.json` and its
per-unit native command logs; retained C remains in D1255.

## D1257: Correct construction-budget boundary; verification needs resources

The prior 180-second reconstruction bound was a new prototype default, not a
product startup/output requirement or the already successful large native
construction budget. Current D1083's authoritative receipt is qualified,
original O1, no ABI/consumer flag change, 19721269 bytes of coalesced C, and
compileWallBudgetSeconds=900. D1257 explicitly binds its two retained-unit
retries to that receipt's hash and budget. Original std debug/GNU compilation
options remain unchanged; MCP's ten-second and Native's five-second output
gates are not changed. The earlier 180-second failures remain failures, not
retroactive passes. Three budget-admission tests reject failed, changed-ABI,
changed-flags/O3, and arbitrary-budget references; all 200 unit tests pass.

The actual GNU cc1 sample for std/format/ioutil~1 is past preprocessing and
inside function optimization, including pass_ccp/constant propagation and
substitute-and-fold/dom-walker paths. This short wall-stack window does not
prove total active CPU attribution or a safe optimization of those passes.
At roughly 85 seconds wall time, the two cc1 processes have about 5.3 CPU seconds
each; later snapshots show approximately 29 CPU seconds at six minutes, and
the socket unit approximately 67.8 CPU seconds at 13 minutes 49 seconds.
These are observed resource/execution boundaries, not a timing speedup or
exclusive explanation of the original macOS/Linux gap. No priority change is
made, and Apple's assembler role is not a Clang C compilation experiment.

std/format/ioutil~1 completes original-recipe object compilation in
691.140 seconds and linking in 1.447 seconds. Its __text matches the installed
original byte for byte. This adds one validated original-code object; it does
not qualify the entire 394-module image candidate or performance. The other
unit, std/io/interface/socket~1, still times out at 900 seconds before linking.
D1257 remains unqualified and allSelectedUnitsPassed=false. No matching
construction processes survive after terminal completion.

A current read-only process snapshot totals 1145.7 percent CPU, including
139 zellij processes at 812.1 percent. No unrelated process is stopped. The
current machine cannot provide a completed original-code reconstruction and
stable matched product verification in this run. The same reconstruction
blocking condition has persisted across three consecutive goal turns:
D1255 full reconstruction fails, D1256 strict two-unit retry fails, and D1257
fails one unit even under the existing successful construction budget. Earlier
unchanged original MCP clean controls also fail before build observation.
Further repetition or arbitrary larger budgets would not establish the
requested startup improvement. A less-contended execution window/external
resource change is now needed for the remaining full reconstruction and actual
MCP/Native acceptance. The full objective is not completed, no patch is
promoted, and all failed/confounded receipts remain available.

Evidence: `.data/d1257-original-debug-reference-construction-budget/`, including
the actual per-unit commands, GNU cc1 sample, and terminal report.

## D1258: Resumed strict original control still fails before build

After resumption, the existing failed candidate and its rejection were
rechecked, without promoting partial Native results. A new official MCP
control uses the original D935 toolchain and locked D1061 project head, with
the unchanged clean 30-second and first-output ten-second gates. Original
gerbil clean times out after 30 seconds; build never starts. The terminal
report remains qualified=false and performanceQualified=false. Reaped-child
CPU is 2.171289 user plus 1.020353 system seconds, not build-only attribution.
A contemporaneous read-only process snapshot totals 1141.8 percent CPU;
138 zellij processes account for 797.8 percent. This establishes continued
contention, not exclusive causality for either original or candidate failure.
No matching owned product process remains after cleanup.

The same inability to obtain a qualifying original control or complete the
original-code reconstruction persists through three resumed goal turns:
resource revalidation, candidate-failure revalidation, and this actual strict
control. No startup improvement is admitted, no production patch is promoted,
and no deadline is relaxed. Further acceptance requires an external execution
window change; unrelated processes have not been terminated.

Evidence: `.data/d1258-original-strict-first-window/report.json` and its empty
product clean log. The full requested objective remains incomplete.

## D1259: Withdraw resource-only blocking inference; audit isolation

The user rejects attributing the failure to resource contention. The earlier
claim that an external resource change is the necessary next step is withdrawn:
CPU snapshots and failed controls do not prove that causal claim. Investigation
must also check modifications and diagnostic environment contamination.

All 394 original installed native image SHA values match the previously
recorded originals (391 ordinary and three preserved FFI images). None of the
391 ordinary image paths is a symlink. D1258 binary hashes also match the
original D935 identities. These checks rule out those particular file
replacements, not every runtime or environment regression. MCP tracked source
status is clean. No inherited GERBIL/GAMBIT/GAMB/DYLD variable names were found
in the invoking process at inspection time.

The observer explicitly repeats user and home library directories through
GERBIL_LOADPATH, although runtime initialization already appends both. No
causal speedup is attributed to removing this duplication. A minimal environment
without inherited research variables or GERBIL_LOADPATH runs original gerbil
version in 0.222239 seconds and official MCP clean in 2.779595 seconds, exit zero.
These terminal observations were returned directly by the command runner;
they are not a matched environment A/B result or full-build qualification.

The same minimal-environment official build is then observed under the original
ten-second first-output gate and 12-core setting. It produces no first compile
within 10.024439 seconds and is stopped and reaped. firstWindowPassed=false,
firstCompileSeconds=null, buildCompleted=false, performanceQualified=false.
No Gambit or consumer source changes are made. The failed candidate remains
rejected. The startup objective remains unresolved, and the quiet build phase
still requires diagnosis rather than a resource-only explanation.

Evidence: `.data/d1259-minimal-environment/probe.py`, `report.json`, `build.log`.

## D1260-D1261: Minimal official build reaches the real child

The minimal original environment is observed without changing production code.
D1260 records only original D935 library paths in the parent dyld log. No
direct child exists at 3.059 seconds; the actual gxi build.ss compile child
exists at 7.070 seconds. The product build log remains empty and the original
ten-second first-output gate fails. Diagnostic stderr is separate and never
counts as a product line. This establishes progress into the official child,
not a dead parent or successful first compilation.

D1261 observes an actual build child already present at 3.060 seconds and
samples that child for one second. The first-output gate again fails. Of 845
main-thread wall samples, 524 are below Gambit's ___dynamic_load/dlopen;
495 are below notifyDebuggerLoad, including synchronous remote notification
and atlas generation. This confirms the stage reached, not its unobserved CPU
share or an exclusive cause. Earlier receipts already warn that sampling can
introduce debugger notifications; this is not a newly established root cause.
Apple's source also explicitly gates remote notifications on an active monitor
and waits synchronously. No private notification bypass is proposed.

Source: https://github.com/apple-oss-distributions/dyld/blob/main/dyld/ExternallyViewableState.cpp

Both observations stop at the unchanged ten-second gate, retain null first
compile timing and performanceQualified=false, and leave no matching build.ss
compile process after cleanup. Parent startup and child native loading both
precede the first compile in this observation; neither is dismissed as resource
contention. No HTTP, std/make, std/test or Gambit production code is changed.

Evidence: `.data/d1260-minimal-loader-window/` and
`.data/d1261-minimal-build-child-stack/`.

## D1262: Close dependency-only batching of unchanged original bundles

A possible way to avoid expensive original-debug C reconstruction was to link
an umbrella image depending on the unchanged installed native images, allowing
dyld to admit dependencies together. This is not the existing object-coalescing
candidate and was checked before implementing a runtime preload policy.

All 394 original image headers have Mach-O filetype 8 (MH_BUNDLE). The original
gambuild-C FLAGS_DYN uses -bundle; FLAGS_LIB separately uses -dynamiclib.
GNU GCC 16 invokes the native linker for a minimal -dynamiclib command with
-needed_library pointing to original std/build-script~0.o1 and empty C input.
The command exits 1: the linker rejects MH_BUNDLE dependencies and accepts only
MH_DYLIB. Thus an ordinary dependency-only umbrella cannot batch these original
images without changing their representation. No image-header conversion,
private dyld manipulation or guessed compatibility workaround is attempted.

The route is closed in this form. Actual object-based aggregation still requires
the original debug recipe and original machine-code verification; old omitted-
debug objects cannot be admitted instead. Existing first-log failures remain
failures and no startup acceleration or full-toolchain qualification is claimed.
The failed link targets only `.data/d1259-minimal-environment/dependency-probe.dylib`;
original installed images and consumer source are unchanged.

## D1263-D1264: Same-source debug-tail relaxation lacks measured opportunity

Gambit's eqv-gvm-instr? rejects instructions carrying debug information before
comparing operations. A narrower possible relaxation would require identical
source-node identity, equal frames and matching instruction types, rather than
dropping debug-source. An observer wraps the original purify-procs and counts
cross-block last non-branch instructions satisfying those preliminary conditions
within each procedure. It delegates to the original optimizer without mutation.
It does not check operands, closure environment identity or branch compatibility;
the counts are only necessary-condition opportunities, not legal merges.

Original GSC, macro inputs, separate-compilation feature and original std debug
flags are retained. std/make~0 yields 974 debug tails and five preliminary pairs.
socket~1 yields 6441 debug tails and zero pairs; ioutil~1 yields 4448 debug tails
and zero pairs. Generation exits zero for all three. std/make generated C is
byte-exact to D1252; both large-module generated C files are byte-exact to D1255.
Socket C SHA is ff0e58a47a5529bab81b38f03d8fab82c3d7cf54ebba6ee86d8c683591016f61.
No production optimizer relaxation or debug-policy change is implemented.

The sampled same-node-tail relaxation is not supported as a substantial
acceleration route by these results. This is not proof that every debug-preserving
compiler optimization is impossible, nor a statement about actual first-log CPU.
All reports remain diagnostic-only and performanceQualified=false. Native
construction and MCP first-log/full-build acceptance remain incomplete.

Evidence: `.data/d1263-debug-tail-opportunity/` and
`.data/d1264-large-debug-tail-opportunity/`.

## D1265-D1266: Real first windows pass; outlined runtime is not the major fix

Existing source/cost evidence does not justify a new debug metadata cache:
sharing already exists and the older bounded native-load/GC CPU observation
does not account for the whole first-output delay. The previously constructed
D1083 uninstrumented outlined runtime is instead tested through official MCP
clean/build in the minimal environment from D1259. Original D935 libraries,
GSC, headers, consumer sources and settings remain selected. Candidate binary
SHA is 6c50ce6cad0d8bbb984e2d39bd0f0196aaa61b3ef8712e05c9a129e94e08dafc.

D1265 candidate clean completes in 2.454317 seconds and actual first compile
appears in 5.334660 seconds. That single pass is not a speedup admission.
D1266 then runs sequential uninstrumented A/B/B/A; each official clean precedes
its official build and each keeps the ten-second first-output gate and 12-core
configuration. All four first windows pass:

| Order | Runtime | Clean seconds | First compile seconds |
| --- | --- | --- | --- |
| A | Original | 2.248247 | 6.062911 |
| B | D1083 | 2.238024 | 5.637598 |
| B | D1083 | 2.331774 | 5.810144 |
| A | Original | 2.420885 | 6.565418 |

Observed first-compile means are 6.314165 versus 5.723871 seconds, only 9.35%
lower / 1.103x. No claim of stable causality or major startup elimination is
made from four wall-clock observations. Earlier original ten-second failures
are retained, not replaced or used as a denominator for a large ratio. Passing
first windows does not make this the required major optimization. All reports
keep buildCompleted=false and performanceQualified=false: observation deliberately
stops and reaps the process group after the actual first compile. No matching
build child remains. Full MCP compilation and concurrent native suite acceptance
are still outstanding; no production patch is promoted.

Live remote verification again returns v0.19-staging head
1cfb032c7a1612637da6205f5f8a15683eba3ba0, matching the original source identity.
Evidence: `.data/d1265-outlined-minimal-first-window/` and
`.data/d1266-minimal-first-window-abba/` (all four terminal reports/logs).

## D1267-D1268: Full MCP builds finish; full testing is not qualified

The user explicitly requires complete build and real gerbil test time, not only
first compile. D1267 therefore runs official clean/build to completion, then the
27 unchanged MCP test batches selected by the repository's run-tests script
(chunk files, unit directory, protocol file), in the physical 12-worker capacity.
Build keeps ten-second genuine-output gaps; each test keeps five-second gaps
and a 90-second wall cap. Product output is retained and forwarded, not hidden
until shell-script aggregation. No test source, package HTTP code or std/make
implementation is modified.

| Runtime | Clean seconds | First compile seconds | Full build seconds | Build exit |
| --- | --- | --- | --- | --- |
| Original | 2.388101 | 6.854674 | 69.440594 | 0 |
| D1083 | 2.733271 | 5.316666 | 106.990399 | 0 |

Both builds complete under the original output gate. This single sequential
comparison does not isolate causality, but it provides no complete-build speedup
evidence: the candidate observation is longer. The first-output improvement must
not conceal the complete duration. With the original script's default verbosity
three, original testing has 11 final-OK batches and 16 silence failures; candidate
has six final-OK batches and 21 silence failures. The elapsed 16.577332/19.912075
seconds includes premature failure and is not a successful-suite speed ratio.

D1268 uses the same just-built application for both test-runtime observations,
binding the completed build receipt and application SHA. It adds the same real
gxtest verbosity-five option on both sides to expose CASE/CASE-OK; this is not
a cold-build cycle comparison. Five/90-second gates remain unchanged. Original
records 372 CASE starts, 359 CASE-OK, nine passing batches and 18 silence failures
over 32.238513 seconds. Candidate records 721 CASE starts, 713 CASE-OK, 20 passing
batches and seven failures over 37.938991 seconds. Work completed differs, so
neither elapsed ratio nor CASE-count ratio is an accepted acceleration.

Two candidate batches execute assertion errors rather than timing out. Chunk-05
fails text-has? /src/ checks at lines 40 and 52; chunk-12 also has an executed
check failure. Both processes exit zero, so explicit error text, nonmatching
CASE completion counts and final-OK checks correctly reject them. Original
corresponding batches do not finish those checks in this observation; candidate-
only regression or baseline fixture failure is therefore not established.
All reports remain qualified=false/performanceQualified=false. There are no
matching owned project build/test processes after terminal cleanup verification.
Full-suite success and major end-to-end acceleration are still outstanding.

Evidence: `.data/d1267-mcp-full-cycle/` and `.data/d1268-case-visible-native/`.

## D1269-D1270: Stop packing detour; return to measured macro execution

D1269 attempts to reuse only D1255 original-debug verified objects, preserving
all other original images. Its first linked group is rejected by the linkage
audit: relative RPATH @loader_path remains, so the conservative admission rule
does not prove relocation-independent semantics. preparationPassed=false and
qualified=false. The script is terminal; no MCP build/test is started with this
candidate. No production installation or consumer code is changed.

The user explicitly redirects work away from loading/packing and toward the
actual macro execution cost. That detour is stopped rather than relaxing its
audit. D1267's 106.990399-second candidate complete build is not hidden by its
5.316666-second first output; the prior roughly 50-second original measurements
are retained as historical observations, not overwritten by the new 69-second
sample. No overall optimization has been established.

Existing low-disturbance D1101 attribution is the relevant starting point:
compile exclusive CPU 0.319791 seconds versus execute 5.712023 seconds across
10358 balanced scopes. Allocation matches the original within about 0.061%.
Those execution scopes include compiled macro callbacks, GC and nested work;
they are not pure interpreter CPU. D1102's original on-CPU attribution places
11.56% in expander core, 10.86% in stx, 17.89% in the two mark_array variants,
and significant body work in mop/hash/table. EVAL is only 2.10%. Source inspection
confirms setup-requirements-and-run invokes macro-code-run after loading demands.
No new CTE cache, HTTP change or interpreter-only optimization follows from this.

Further source work must address recurring native macro body work through the
Gambit backend/runtime, keep Linux and original debug semantics unchanged, and
be judged on official first output, complete build and complete successful
tests. Current observations do not establish a Darwin-versus-Linux causal
comparison or authorize claiming that all seven wall seconds are one compiler
stage. The requested objective remains incomplete and active.

## D1271-D1278: GVM allocation-use census narrows the PEA design

The preceding literature review changed the next action: inspect compiler IR
rather than expand the rejected generated-C trace architecture. A private
read-only observer wraps the original purify-procs and delegates unchanged to
it. Five real phase-zero hotspot modules are regenerated using original GSC,
original macro input and separate-compilation mode: expander core/stx and
runtime mop/hash/table. The actual physical-core budget is 12; five inputs
naturally use at most five workers. No product build/test or native compiler
performance experiment is implied by these source-generation observations.

D1271 fails at observer syntax; D1272 fails because primitive names are
strings, not symbols. Both are retained as failures. D1273 completes the initial
pair/structure census. D1274's additional self-test has an ill-placed define;
D1275 corrects it and passes five positive/negative scanner controls in every
module. These controls exercise field reading, alias copying, overwriting,
constructor containment and the unsupported boundary; they do not qualify
an optimizer. D1276's byte-parity check fails because the two output filenames
differ in generated linker-info comments. D1277 uses identical basenames in
separate directories and passes full C-byte parity in all five modules.

D1278 adds explicit list/vector/box constructor coverage, retains the five
controls and again passes full generated-C byte equality against unobserved
same-recipe controls. It observes 355 static constructor instructions:
242 cons, 47 list, 35 structure, 11 make-vector-small, 10 vector and 10 box.
For these constructors, the local scanner records zero subsequent owned field
reads before its first stopping boundary. 103 reach returning indirect calls;
103 are used by another cons/structure constructor. These are static site
counts, not runtime frequencies, eliminated bytes or speedup estimates. The
census is not all allocation kinds, all modules, or the full 4.404-GB workload.

The scanner intentionally stops at basic-block boundaries, other primitive
uses and closure instructions. It does not follow callees, match returns,
track nested allocated object fields, prove boundary liveness or infer that
every stopped object escapes. In particular, jump-nb-args false means a
transfer without an argument count, not proof of an internal CFG edge; the
earlier D1275 wording is corrected in D1277-D1278. No result allows deleting
constructors or bypassing continuation/GC/debug contracts.

This rejects implementing a local-block-only allocation elimination pass as
the proposed main solution. The next analysis must propagate nested-object
state and summarize proven callees/consumers; a producer's return alone cannot
prove that its intermediate object is externally observed. The existing
_ptree2.scm inlining budget and _front.scm known-procedure/liveness handling
are relevant integration points, not authorization to globally raise inlining
limits or assume global bindings immutable. Dynamic call targets and unsupported
control effects remain conservative boundaries.

The remote v0.19-staging ref is checked live and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0, matching the isolated checkout.
Original GSC SHA is locked to the recorded 9a1b842 digest. No production source,
consumer SCM, Homebrew installation or Linux path changes. All owned observer
commands are terminal. No performance candidate or completed objective exists.
Evidence: project .data/d1271-gvm-allocation-use through
.data/d1278-gvm-aggregate-allocation-use; current successful reports retain
compiler/source/observer identities, commands, controls and generated-C parity.

## D1279-D1287: Callee field-demand controls reject a small PEA shortcut

The prior GVM census changed the next action to parse-tree callee demand.
The new observer wraps original beta-reduce, scans before/after trees and
delegates unchanged. It resolves global functions only through original
global-single-def: a single definition with block compilation. Immutable
lexical functions are resolved only from immediately applied, exact-signature
lambda bindings. Unknown calls, mutable parameters, recursive summaries,
depth overflow and actual captured parameters remain unsupported boundaries.
This is a static demand classifier, not a complete escape proof or optimizer.

D1279 completes all five real hotspot modules with generated C byte-identical
to the existing unobserved controls, but incorrectly rejects immediately
applied let lambdas as captures. D1280's correction has a syntax failure;
D1281 fixes it. D1282 adds hard expected-count controls: direct field reading,
known global field-only callee and let-bound field reading are recognized;
captured objects, mutation, object return and unknown external callees are
not admitted. The original and observed control C remain byte-identical.

D1283 uses the corrected classifier on the five real modules. The after-beta
tree has 356 selected constructors, versus 301 before beta; this is static
inlining/code shape, not a claim of increased dynamic allocation. It records
zero field-only constructor-to-callee opportunities in the supported analysis.
For example, many unknown targets are make-class-type initialization calls.
Their static count does not establish their execution frequency or justify
targeting them as the main cold macro cost.

D1284 separately explores known callee results, rather than conflating return
and input-parameter demand. It initially classifies unused values as field-only;
its apparent result sites must not be interpreted as allocation opportunities.
D1285 separates those cases and adds an unused-object control. That receipt
fails its expected counts: original beta reduction already removes the unused
pair, leaving eight constructor sites before and seven after. D1287 hard-checks
that real before/after behavior and passes, including exact generated-C parity.

D1286 passes all five real modules with full generated-C byte equality after
the corrected unused-value classification. After beta there are only five
supported field-demand result sites: two __gc-table-e, two class-of and one
gx#core-context-shift. Another 25 result sites are unused-value demands, not
field reads. Source inspection finds __gc-table-e reads the table's stored
object and can visibly rehash it; class-of dispatches through the existing
type table; core-context-shift links any newly created phi context through
up/down mutations. These are not proven removable fresh intermediates. No
callee implementation is rewritten and no persistent/cached identity is
replaced with an invented temporary.

Decision: do not build a small field-only input/result pass and call it the
main PEA solution. The controls prove the classifier can recognize that pattern,
but supported real-source coverage does not establish an eligible accelerator.
This does not disprove full CFG/object-state/interprocedural PEA. It does require
actual executed allocation ownership before committing to a much larger pass;
static counts and the paper's unrelated benchmarks cannot establish reduction
of the recorded approximately 4.404 GB. Existing rejected caller traces remain
rejected, rather than being reintroduced under a new name.

Original GSC remains locked to its recorded digest; hardware concurrency is
12. All owned source-observer commands are terminal. No production source,
ABI, consumer SCM, progress gate or performance claim changes. Real MCP
clean/build and concurrent CASE-visible tests remain unqualified; the full
objective is incomplete and active. Evidence: project .data/d1279-ptree-field-demand
and .data/d1279-ptree-field-demand-results through
.data/d1287-ptree-unused-result-controls.

## D1288-D1296: executed allocation owners and accounting correction

A private observer overrides original ___ALLOC after original header inclusion,
counts executions/words by original C line and returns the original updated
heap pointer. It evaluates the operand once, retains reversibly injected C,
restores original line numbering and never calls Scheme during allocation.
Source/header/GSC/builder/object hashes and actual argv are retained. Original
configured GNU GCC 16/O1 gambuild-C is reused, without coalescing, trace
optimizations, debug removal or ABI changes. Hardware capacity is 12 cores;
the first five-unit build has only five independent inputs.

D1288 fails sandbox hardware discovery before construction. D1289 constructs
the observer and passes native imports plus pair identity/mutation smoke, but
fails workload admission: script-path dispatch invokes build.ss's main entry.
That accidental build stays under its private empty-user directory. D1290
reuses the binary with the correct gxi -e dispatch and byte-identical D1102
expression. All 187 PREPARED messages, MODULES 187, IMPORT-OK and exit zero pass.

D1291-D1293 retain fixture/environment failures: missing Gambit temporary,
reversed car/cdr field indices, and unresolved puts under inherited environment.
D1294 uses corrected field constants and the same Bazel-discovered environment.
Original and counted controls pass once-only n++, pointer expression result,
zero increment, pair contents and exact three-call/five-word count. These
controls and runtime observations do not qualify performance.

D1295 adds counted original EVAL to a private archive copy. D1296 adds original
_std and _kernel with two independent compile inputs at 12-core capacity. Every
other archive member is checked byte-identical to original. The three admitted
preparation runs have identical five-native-unit counts and all complete 187
modules. Final raw physical constructor byte totals are:

| Unit | Observed bytes |
| --- | ---: |
| expander/core | 210,519,320 |
| expander/stx | 915,047,800 |
| runtime/mop | 62,481,880 |
| runtime/hash | 6,192,144 |
| runtime/table | 30,758,952 |
| Gambit EVAL | 53,019,880 |
| Gambit _std | 91,557,080 |
| Gambit _kernel | 265,378,000 |
| Total for these units | 1,634,955,056 |

Largest site: original stx.c:4056 stx-apply-mark's fresh four-field syntax-wrap,
12,855,681 calls and 514,227,240 bytes. syntax-e's initial mark-list pair at
line 2699 contributes 128,521,296 bytes; its result pair at line 2764 contributes
123,136,176. Original _kernel.c:11261 is the rest parameter handler loop,
11,049,064 pairs and 265,177,536 bytes. Its allocating callee is not attributed
yet. These returned wrappers/pairs/lists are not proven removable objects.

Important correction: process-statistics field 7 is a different metric.
_kernel.scm stores ___bytes_allocated; mem.c words_movable_objs contains a factor
of two and both current heap growth and stack occupancy. bytes_occupied adds
still/deferred-still words; GC adds/subtracts it around collection, and
___bytes_allocated combines accumulated/current values with occupied still
words. D1296 field 7 remains 4,403,968,280 with 27 GCs. Informal 28%/37%
constructor-coverage arithmetic against roughly 4.404 GB is invalid and
withdrawn. Simply halving that metric is not exact physical attribution either.

Decision: follow syntax-wrap producer/consumer and rest-callee storage-use
contexts; EVAL allocation is not established as the main solution. No speed
ratio uses instrumented timings. Counts include initialization and cover only
these eight units, not all native/dynamic units, stack/still allocations or
continuation costs. No product clean/build/test is qualified.

Upstream v0.19-staging is checked live and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. Original GSC/header, installed Homebrew,
production and consumer sources remain unchanged. All owned sessions are
terminal. The goal remains active and incomplete. Evidence: private project
.data/d1288 through d1296 scripts, reports, original/instrumented C, objects,
archive parity and raw allocation counts.

## D1297-D1306: rest-entry ownership exposes implicit-list candidates

The rest-handler observer records its original temp1 entry label before the
unchanged pair loop. Gambit's setup.h declarations and subprocedure metadata
provide parent names and entry IDs; static C counters retain no movable Scheme
objects. A fixed 4096-slot table must have zero overflow. Source injection is
reversible and the original list construction/GC path is retained. Only the
private _kernel object is replaced in the existing counted archive; every
other archive member is byte-identical to the prior copy.

D1297 fails a nonunique source anchor shared with the keyword-rest handler.
D1298 tightens the anchor but lacks the official setup.h prototype. D1299
completes 187 modules, then fails an incorrect comparison of whole rest demand
to the prior ordinary-loop site count. D1300 adds same-run allocation counting,
but its admission mistakenly names the wrong GC-slow-loop source line.
D1301 admits the retained terminal observation without another run: all 187
modules and exit zero pass, table overflow is zero, and demand pairs exactly
equal ordinary-loop pairs plus GC-slow-loop pairs in that same process.
There are 11,049,064 ordinary pairs and two GC-slow pairs in D1300. The two
are real fallback construction, not resource interference or a timing excuse.

D1302 adds exact native subprocedure IDs, formal counts and bounded rest-size
histograms. Every histogram sums to its entry count; same-run ordinary plus
GC-slow pair equality passes. The measured principal entries are:

| Parent and entry ID | Calls | Rest pairs |
| --- | ---: | ---: |
| apply, 0 | 1,718,155 | 2,952,460 |
| gx#datum->syntax, 0 | 773,610 | 1,562,634 |
| __bound-method-ref, 5 | 1,330,692 | 1,330,692 |
| foldr, 0 | 407,196 | 1,256,509 |
| gx#core-apply-user-expander, 0 | 470,992 | 941,984 |
| string-index, 0 | 221,934 | 443,868 |

datum->syntax has 765,903 two-argument and 7,707 four-argument calls. foldr has
372,275 three-argument and 34,921 four-argument calls. core-apply-user-expander
and string-index each have only two-argument calls in this observation. The
bound-method-ref entry is the nested variadic closure, not its fixed-argument
outer factory; all its measured calls have one rest argument. Names without
entry IDs would conflate these distinct source procedures.

D1303-D1306 connect the entry shapes to original GVM comments. D1303 fails
sandbox hardware discovery. D1304 has incorrect original include/CLI ordering.
D1305 fixes generation but its backend-global rebinding hook never observes
entry calls; zero rows fail admission. It also uses a dynamic module recipe
which cannot establish original native C identity. These attempts are rejected.
D1306 uses the previously established purify-procs boundary and the original
static-unit recipe. stx, core, mop and util all have observer/control C byte
parity AND byte identity with original native C; five selected entry rows are
observed. Original GSC digest remains unchanged. Capacity is 12, with four
independent generation inputs, not a forced two-worker limit.

The observed arity wrappers have an immutable rest parameter, an immediately
applied length-binding lambda, fixnum count tests and tail apply branches.
The nested bound-method closure has an immutable rest parameter tail-forwarded
through known standard apply with captured method/receiver references. Some
helper references are marked mutable in the parse tree. A production pass
must preserve the actual GVM-resolved target operand, not infer immutability
from a readable helper name. Keyword/optional, escaping, mutated, captured
rest-list and unsupported branches require conservative fallback.

Decision: explicit constructor-only PEA missed implicit runtime entry lists.
Proceed toward a Gambit entry-level rest-list/arity-dispatch elimination pass,
with correct registers/stack arguments, closure targets, procedure checks,
multiple values, continuation/debug semantics and safepoints. No consumer SCM
case-lambda rewrite or std/make/std/test edit is authorized. No native prototype
or performance patch is qualified here; allocation-owner counts are not speed
ratios. All owned observer/generation sessions are terminal. Goal remains active
and incomplete. Evidence: private .data/d1297 through d1306 scripts, raw
callee/allocation tables, original/observed C and entry-IR logs.

## D1307-D1323: Native Rest Entry Prototype Reduces Work but Fails Delivery

Official v0.19-staging is rechecked through its upstream remote and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. The isolated compiler changes only
Gambit's C backend. Original RTS, header, configured GNU GCC flags and non-owned
native units are retained. No consumer SCM, std/make, std/test or HTTP changes
are made. Capacity is the measured 12 physical cores.

D1307 implements a generic structural proof, not a Gerbil-name allowlist:
immutable zero-required rest parameter, immediate length binding, fixed count
tests, known primitive APPLY, and fixed nonclosure helper targets proved by
Gambit's existing global-single-def/block-compilation rules. Each admitted
helper reaches a poll on a bounded copy-only straight-line path. Unsupported
predicates/targets stop selection; original materializing fallback remains.
The four original modules expose 58 selected wrapper entries, and observation
preserves original generated C byte-for-byte.

D1308 fails because PATH selects GNU cp rather than macOS clone-copy cp. D1309
builds the compiler unit but fails linking new globals against stale linker
metadata. D1310 regenerates library/executable linker metadata using the native
Makefile's structure and links successfully. D1311 rejects the prototype because
its debug guard incorrectly treats Gambit's default-enabled debug suboptions as
an enabled debug frame. The source proves debug-info-add! gates these suboptions
through debug?. D1312-D1315 correct this guard, construct the candidate and
complete the original 187-module MCP preparation workload.

D1316 reuses the admitted D1302 rest observer RTS and confirms its kernel object
identity. Its same-run callee sum equals ordinary-plus-GC-slow rest allocations.
Rest pairs decrease from 11,049,069 to 8,044,790: 3,004,279 fewer pairs and
72,102,696 fewer raw pair bytes. datum->syntax's 765,903 two-argument entries
no longer materialize rest lists; its 7,707 four-argument entries still do.
core-apply-user-expander's 470,992 entries and string-index's 221,934 entries
also disappear from rest construction. Standard apply's 1,718,155 calls and
2,952,460 pairs are unchanged. These are executed-work facts, not timing gains
or coverage of the process-statistics allocation metric.

D1317 semantic controls expose another guard defect: a debug declaration inside
a lambda body is absent from the outer procedure node's environment. Although
both executables produce the expected cases, the candidate wrongly optimizes
that debug wrapper; admission fails. D1319-D1322 check the complete wrapper
ptree for debug/environment-map observability, rebuild the native compiler and
pass 17 matched CASE controls, with one eligible wrapper and unchanged mutable,
observable-rest, required-rest and local-debug paths. Controls cover stack
arguments, multiple values, fallback identity/mutation, operand evaluation,
continuation escape and explicit GC stress; they are not exhaustive continuation
or Linux qualification. All four final enabled module C files match the files
used to build D1315, and disabled C matches original native C byte-for-byte.

D1323 runs unchanged official MCP clean/build and CASE-visible tests on an
independent durable project copy at head 9a5c35e275e5d6847ff421151bb224f2eae177c1.
It uses the corrected compiler and attested native candidate, with original
clean/build/test silence gates and 12-core capacity:

| Measurement | Candidate |
| --- | ---: |
| clean, exit 0 | 3.678884 s |
| first compile | 6.047644 s |
| complete build, exit 0 | 69.833692 s |
| concurrent test observation | 17.954768 s |
| admitted test batches | 2 / 27 |
| observed CASE / CASE-OK | 35 / 33 |

The 25 rejected test batches hit the 5-second silence gate; 23 never emit a CASE.
Their shortened observation is not a test speedup. No resource explanation is
asserted. The historical D1267 original first compile 6.854674 s and full build
69.440594 s are not a current matched causal control. The candidate still takes
about six seconds to first compile and has no demonstrated full-build win.

Decision: retain the semantic and actual-work evidence, but reject this candidate
as the requested startup/build/test delivery. Do not promote it to a qualified
production patch or redefine success around 72 MB elimination. Remaining standard
apply/rest forwarding and the larger syntax-wrap allocation surface still need
compiler-level proofs and materially stronger actual first-log/test results.
All owned build/test processes are terminal. The full goal remains active and
incomplete. Private evidence is retained under .data/d1307 through d1323.

## D1324-D1337: Closure Forwarding Is Real Work Elimination, Not Delivery

D1324 observes a generic immutable captured-target/rest forwarding pattern in
three MOP closures, preserving original generated C. D1325-D1330 construct an
opt-in Gambit entry transformation, retaining the fixed-arity rules. It forwards
incoming argument registers directly, with an optional captured receiver prefix,
for zero through three arguments. Larger arities retain the original rest body.
Targets must be procedures; mutable captures, debug/environment maps and
unsupported shapes remain unoptimized. No Gerbil procedure-name whitelist is
used. Requested stack polls retain the original entry and GC maps; the fast
arm contains no allocation or interrupt boundary. Activation additionally
requires Darwin/GNU, SINGLE_HOST, SINGLE_THREADED_VMS and no poll-countdown
heartbeat. Linux and consumer source remain untouched.

The initial D1326 compiler emits invalid C: IF_NARGS_EQ ends with else and the
final unsupported-arity branch lacks a statement. D1328's actual native compile
rejects it. D1329 inserts the missing empty statement; D1330 relinks the corrected
compiler. The failure remains recorded, not overwritten.

D1331 regenerates four actual modules. Disabled output is byte-identical to
original C in all four; enabled entry counts are stx 6, core 24, mop 13 and
util 18. D1332 passes 36 native semantic controls with original/candidate output
parity, including stack arguments, mutable targets, debug fallback, identity,
mutation, multiple values, nonprocedure/wrong-arity exceptions, unforced receiver
promises, multishot continuation restoration and explicit GC. These are bounded
controls, not full language or safepoint qualification.

D1333 builds the candidate native Gerbil with original GNU flags, original RTS
and unchanged non-owned objects, then prepares all 187 MCP modules. D1334 uses
the admitted original rest observer, with no overflow and same-run agreement
between callee counts and ordinary/slow rest-handler allocation counts:

| Rest work | Recorded original | Candidate |
| --- | ---: | ---: |
| allocated rest pairs | 11,049,069 | 5,383,407 |
| standard apply calls | 1,718,155 | 387,463 |
| bound-method forwarding closure rest calls | 1,330,692 | 0 |

The combined fixed-arity/closure candidate eliminates 5,665,662 measured rest
pairs, or 135,975,888 raw rest-pair bytes. This is not total-process allocation
coverage, a CPU speed ratio or an instrumented timing qualification.

D1335 performs a real isolated MCP clean/build and 12-physical-core concurrent
CASE-visible tests at head 9a5c35e275e5d6847ff421151bb224f2eae177c1:

| Actual candidate phase | Result |
| --- | ---: |
| clean, exit 0 | 2.875253 s |
| first compile log | 5.520614 s |
| complete build, exit 0 | 64.286971 s |
| concurrent test observation | 35.682357 s |
| passing test batches | 20 / 27 |
| observed CASE / CASE-OK | 721 / 713 |

Five test batches hit the unchanged 5-second silence gate. Two others emit
semantic errors despite exit 0. A focused original-runtime check of those same
two batches, on the same already-built application, reproduces the same three
failed checks: chunk-05's two /src/ source lookup expectations and chunk-12's
Binary expectation. Both runtimes report 22/24 and 24/25 CASE-OK respectively.
This is a focused regression control, not a clean-build baseline or proof that
all remaining failures are environmental. Gates remain failed. Historical
baseline timings do not establish a causal speedup for this run. The candidate
still spends 5.52 seconds before first compile and is not deliverable.

### Largest Constructor Now Has a Dynamic Return Consumer

D1336-D1337 observe only the original stx-apply-mark four-field constructor's
saved return label, leaving all original allocations and execution paths intact.
Source saves R0 in STK(1), advances FP by eight, then allocates the wrapper;
therefore STK(-7) identifies its saved continuation at that point. Removing the
instrumentation reproduces original C exactly. Original setup.c's descriptor
lookup functions read label/name metadata without Scheme allocation. The native
observer again prepares 187 modules, with no table overflow.

The measured constructor total is exactly the previous 12,855,681 calls and
514,227,240 raw bytes. Of these, 11,902,136 calls (92.5827%) return to __foldl1
subprocedure 2. Original util.c:6532 moves the returned R1 into the next loop
accumulator; it is not an unused or immediately discarded return. Saved return
labels identify continuation consumers, not necessarily immediate callers or
object lifetimes; tail calls and persistent nested wrappers remain relevant.

Decision: preserve the real rest elimination as an unqualified private candidate,
and prioritize callee summaries plus loop-carried nested-object state for the
dominant fold/wrapper chain. Do not repeat the rejected field-only/local-block
pass, assume every wrapper is removable, or borrow Java deoptimization. Growing
virtual chains and unknown callback targets may require materialization and can
limit partial escape analysis. No new qualified production patch is added.

The upstream v0.19-staging ref is checked live and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. All owned processes are terminal.
The full first-log/build/test goal remains active and incomplete. Evidence stays
in .data/d1324 through d1337, including rejected compiler/test results.

## D1338-D1345: Fold Lifetime Clarified, Projected Consumers Identified

These original-code observations answer missing ownership questions, not another
general baseline or a performance comparison. Only native stx's constructor/
branch points and saved continuations receive counters. Original RTS and all
other native objects remain unchanged. Instrumentation removal reproduces
original C byte-for-byte; no Scheme object pointers are retained across calls
or GC. Depth inspection is bounded at 256, with no measured capped entries.
Each observer prepares all 187 modules and terminates successfully.

| Original stx-apply-mark work | Calls |
| --- | ---: |
| total entries | 14,741,099 |
| fresh four-field wrapper allocation | 12,855,681 |
| matching-mark unwrap | 1,593,304 |
| syntax-quote passthrough | 292,114 |
| allocated wrapper with input wrapper depth 0 | 9,255,293 |
| allocated wrapper with input wrapper depth 1 | 3,600,388 |

This workload does not show an unbounded growing wrapper chain at the
constructor. It does not establish a general Scheme depth bound. D1164-D1165's
existing canonical-mark induction already rejects adjacent-equal elimination
as the principal canonical syntax-e-fold solution; no repeat of those semantic
stream tests is performed.

D1340-D1341 inspect the original fold frame only after matching __foldl1
continuation 2. Source saves its remaining list at STK(3) before FP+8, and the
producer adds FP+8; thus the live remaining list is at producer STK(-13).
The producer's saved current mark is STK(-5). Of 11,902,136 fold-owned wrapper
allocations, 9,285,804 finish the fold and 2,616,332 continue. None of the latter
has a next mark equal to the current mark. That rules out the measured
immediate-next-mark cancellation opportunity, not later consumption/escape.

D1342-D1343 follow the fold's saved outer return address: original __foldl1
stores R0 at STK(1), so it is producer STK(-15). All 9,285,804 finishing
allocations return to syntax-e continuation 6 (4,170,266) or 7 (5,115,538).
Original stx.c:2756-2764 shows these values become the two fields of syntax-e's
result pair. The result is not an unused fold return. Names are diagnostic
attribution only, not a proposed production allowlist.

D1344-D1345 additionally observe syntax-e's result-pair constructor. It saves
R0 at STK(1) before FP+8 and has not restored FP at continuation 7; its caller
is therefore STK(-7). The 5,130,674 observed pair returns exactly match the
existing 123,136,176 raw-byte constructor count, with no table overflow.
Largest consumers, aggregated by procedure name, are:

| Result-pair consumer | Calls |
| --- | ---: |
| syntax-split-splice->vector | 834,790 |
| core-expand-head | 686,235 |
| core-expand1 | 683,984 |
| contract Using %%app-dotted | 462,162 |
| rename-macro-expander apply-macro-expander | 308,302 |
| contract Using %%ref-dotted | 288,510 |
| stx-map1 | 255,643 |

The first consumer uses both fields and carries the tail through another loop;
its containers cannot simply be discarded. In contrast, original core.c:14857
and core.c:14799 have CAR as the first instruction after the respective
syntax-e returns. The unused CDR bindings in original core.scm are gone in
native code. These two sites account for 1,370,219 actual allocated pair
results, or 32,885,256 raw pair bytes. This is a specific executed opportunity
surface, not proof that all cdr-side work is pure, that all corresponding
wrappers can be deleted, or that removing those bytes solves startup.

Decision: prioritize projection-sensitive producer/consumer summaries and
return continuation specialization in Gambit IR, rather than an unbounded
virtual-wrapper-loop implementation or renewed canonical cancellation traces.
The compiler must preserve evaluation effects of unused fields; unknown or
rebound callees and non-pair results require the original behavior. Any unboxed
return protocol needs correct caller/callee ABI, frame/GC maps, debug state,
multiple values, continuations and materialization at unsupported boundaries.
No compiler transformation or production accelerator is implemented by these
observations. Consumer SCM, std/make, std/test and Linux remain untouched.

All owned processes are terminal. The full goal remains active and incomplete;
the last actual candidate first log is still D1335's 5.520614 seconds with
failed concurrent test gates. Evidence is under .data/d1338 through d1345.
