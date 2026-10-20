# Gerbil v0.19 Darwin build patch stack

This directory carries the local validation stack for the Gerbil v0.19
Darwin build work. The current MCP-qualified bundle is the content-locked
six-patch safety series; general release and complete ASCENT admission remain
pending. Historical stacks and later experiments stay separate from this bundle.

## Current Frozen MCP Checkpoint

Use [the frozen six-patch safety bundle](receipts/d1510-frozen-safety-bundle.md)
for the current MCP-qualified checkpoint: first logs **4.038 / 3.980 / 3.950
seconds**, cold builds **36.414 / 35.552 / 37.770 seconds**, and complete tests
**86.924 seconds, 39/39 files and 965/965 cases**. The fixed ceilings are
**4.5 / 42 / 97 seconds**. These are retained measurements, not new runs.
Packaging polish preserves the measured implementation bytes and also pins the
entire identity receipt, including timings, tool identities and admission scope.
The snapshot reconstruction entry point also pins that entire receipt before
parsing or creating a fixture; the check is not confined to regression tests.
The regression contract rejects replacement driver, runtime, GSC and raw evidence
identities as well as patch contamination. The six-patch series is the promotion
boundary: later candidates need fresh complete correctness and performance
qualification before being added, even when component checks show a HIT.
The [actual frozen ASCENT ABI contracts](receipts/d1510-frozen-ascent-abi-contracts.md)
now pass 22 backend controls and two existing-object source ABA controls with
the selected Multiple-VM GSC/header pair. The missing-object ordinary fallback
has a separately reproduced source ABA defect and is **not** covered by that
reuse guarantee. The initial aggregate harness failed its unsupported missing
dispatch assertion; this is not a passing complete ASCENT qualification.
The [six-patch ASCENT source-change control](receipts/d1510-frozen-ascent-source-change.md)
now passes 30 Cases with a fresh entry and 70 object HITs / two MISSes.
Its whole time is 70.03 seconds versus 71.32 seconds for proof population;
lower user CPU is not a new end-to-end speedup or complete Suite admission.
The [native compiler interval record](receipts/d1510-ascent-native-phases.md)
separates preparation, link generation and object costs on a real 70-HIT run.
It is diagnostic evidence, not a faster candidate or complete ASCENT admission.
The [retained entry feasibility control](receipts/d1510-retained-entry-objects.md)
proves regenerated-C object HITs, source-change MISS and native execution, but
has not yet qualified a cleanup change or whole-consumer speed improvement.

### Historical Five-Patch Reference

The historical five-patch composition is 0019 + 0020 + 0021 (after 0014/0015).
Its three complete MCP cold builds are **37.365 / 37.406 / 36.467 seconds**,
with first compile logs **4.049 / 4.044 / 4.004 seconds**. Complete testing
of the first cold-built artifact took **87.409 seconds**, with all 39 files
and 965 cases passing; this is one complete test run, not three.

[The v4 checkpoint](receipts/d1510-static-object-reuse-v4-checkpoint.json)
binds the exact helper, native digest backend, runtime and raw reports.
[The v4 qualification](receipts/d1510-static-object-reuse-v4.md) records its
scope. This is the historical five-patch reference, not the current safety bundle.
It remains opt-in: independent ASCENT package-cold regression is still DENIED,
and this checkpoint itself does not qualify full ASCENT suites.

The exact driver extension is frozen in [mcp-v4-driver.series](mcp-v4-driver.series)
and its [patch identity lock](receipts/d1510-mcp-v4-patch-lock.json). This series
depends on the separately recorded reader-whitespace runtime baseline; it is
not a complete latest-staging rebuild recipe. The generated-C dispatcher
prototype is deliberately excluded. Packaging polish must preserve the measured
helper/source bytes; behavior changes require new whole-consumer qualification.
Replay now checks the locked patch order, patch digests and all three measured
driver executable/helper identities before creating its fixture. It rejects
drift instead of silently testing a different stack.
The same preflight also locks the referenced runtime prerequisite, measured
checkpoint, performance policy and native digest source. Missing, altered or
symlinked evidence fails before replay; changing a gate is not silent admission.
Replay additionally requires the selected runtime directory and verifies the
actual measured Gerbil executable, not only the prerequisite receipt.
Replay and the identity CLI's `--evidence-root .` both check the original complete
cold-build and full-test report bytes before creating a replay fixture. This is
evidence preservation, not a new run.
The [packaging verification](receipts/d1510-mcp-v4-patch-polish.md#current-packaging-verification)
lists the reviewable bundle and verification command. Its isolated replay proves
actual reverse/apply execution; portable identity receipts omit personal paths.
The active [performance lock](receipts/d1510-mcp-v4-performance-lock.md) now uses
**4.5 seconds first log / 42 seconds cold build / 97 seconds complete tests**, with
about ten percent upward-rounded fluctuation allowance. Historical gates below
remain historical evidence, not admission thresholds for new candidates.

**Release blocker:** the frozen static-object helper has a reproduced transient
C-source read race. [The C-input safety record](receipts/d1510-static-source-aba.md)
shows a wrong object despite identical source hashes before/after preprocessing.
The five-patch series remains a measured reference, not general production
admission. A hardened replacement must bind GCC's actual input and pass fresh
correctness and whole-consumer performance gates; do not silently replace the
measured helper or inherit its timings.
The separate [0026 safety candidate](receipts/d1510-static-c-snapshot-candidate.md)
blocks that C mutation with exact ordinary-object parity, passes 22 native reuse
controls and executes 30/30 real isolated ASCENT Cases twice. Its separate MCP
follow-up passes three cold builds at 36.414 / 35.552 / 37.770 seconds and complete
tests at 86.924 seconds, all 39 files / 965 cases. The
[six-patch candidate series](static-c-snapshot-candidate.series) and
[candidate identity lock](receipts/d1510-static-c-snapshot-patch-lock.json) preserve
that evidence without altering the frozen five-patch reference. Complete ASCENT
closure performance and general release admission remain pending; these MCP
timings are non-regression evidence, not an attributed new speedup.
The [best-line guard polish](receipts/d1510-best-line-guard-polish.md) adds
explicit GSC identity verification and per-sample performance admission without
changing any measured patch bytes. Use `--performance` to check all three
ceilings and the complete test inventory; digest verification alone is not a
performance pass.

The same reconstruction checker accepts `snapshot` as its sixth argument and
the actual regular GSC binary as its seventh. This selects the six-patch lock,
requires GSC identity and all retained performance samples, then reverses and
reapplies the full six-patch series with exact measured-helper parity. Unknown
bundles are rejected; experimental patches cannot enter through this selector.
See [the frozen safety bundle](receipts/d1510-frozen-safety-bundle.md) for the
command and current verification boundary.
The frozen-contract tests also pin the six-patch order, complete test inventory,
three whole-task ceilings and MCP-only admission boundary. Polishing validation
must not replace measured patch bytes or promote incomplete experiments.

Experimental [0027 caller-bound C identity](receipts/d1510-bound-static-c-digest.md)
adds a per-object expected digest, including cold object creation. Actual
Scheme/native checks reject a different C definition after link preparation;
default-path safety and semantic controls pass. It remains outside both
measured series until caller integration and whole-consumer qualification.

Experimental [0039 producer recipe guard](receipts/d1510-producer-recipe-guard.md)
records the successful worker's copied compiler options and retains full backend
proof. Native controls prove same-recipe HIT and actual changed-option rebuild;
pending / failed / disabled metadata and concurrent publication controls pass.
This patch follows 0034, not the denied 0037 fresh-object bypass. Its isolated
ASCENT focused cold run passes 30 Cases at 110.32 seconds but has zero object
HITs: ordinary library-only std/make never activates the required static-object
producer and linking occurs in a later phase. This is a safety building block,
not a qualified cross-phase speedup; do not repeat that configuration or add
0039 to either frozen series based on the component controls.
The [frozen AOT recipe integration](receipts/d1510-producer-recipe-frozen-aot.md)
now preserves unselected compiler AST and optimized providers while passing
enabled/disabled native executor controls. Whole-consumer admission remains pending.
The [0043 compiler-prefix correction](receipts/d1510-native-compiler-prefix.md)
fixes a real native GCC recipe mismatch. Corrected MCP reaches 74 object HITs
but still fails the 42-second build gate; it is not part of the frozen series.
The [12-worker capture cost control](receipts/d1510-native-capture-transport-cost.md)
separates saved intermediate transport from full proof capture with 72 exact
object-parity checks; it is component evidence, not package admission.
Experimental [0044 object request coordinator](receipts/d1510-native-object-batch-coordinator.md)
stages native objects until whole-request validation and passes real failure,
external tool mutation and reverse-order concurrency controls. Gerbil routing
and both whole-consumer performance/correctness qualifications remain pending;
0044 is default-off and stays outside the frozen series.
Unpaired 0044 has a reproduced compiler-environment mismatch; the
[0045 explicit environment correction](receipts/d1510-native-object-batch-environment.md)
is required before any driver integration. Neither patch has package admission.
The [0046/0047 request-context polish](receipts/d1510-object-request-context.md)
preserves real configured GSC producer proof identity, per-job working directory
and source spelling. Its separate candidate series is byte-pinned; actual native
concurrency/environment controls and 34 focused checks pass. It has no new
whole-package timing and cannot replace the frozen six-patch checkpoint.
The [actual GSC request-cost ABBA](receipts/d1510-object-request-cost.md) now
**denies** the unchanged preparation-plus-coordinator performance route:
0.83/0.93 seconds ordinary versus 1.52/1.66 seconds candidate, with all 12
members HIT and exact object/proof parity. Do not integrate or repeat it unchanged.

The separate [member-independence control](receipts/d1510-generated-c-member-independence.md)
proves exact C and flat-link parity for 55 real modules after reverse generation
and a one-member change with only that member regenerated. It supports studying
finer invalidation than directory-wide proof groups, not admitting a member cache
yet. Complete ordered-link, transitive-read, tool, option, failure and concurrency
checks remain mandatory; its generation timings are not new consumer results.

The experimental [0040 member tool snapshot](receipts/d1510-member-tool-snapshot.md)
removes repeated tool hashing within one member request. A real 55-member
one-change component falls from 3.671 to 0.190 seconds with exact C/link parity;
cold population is unchanged and stable HIT is 0.101 seconds slower. Compiled
controls pass 11 checks and two concurrent processes; two mid-batch mutation
injections currently cover only the interpreted coordinator. Complete CLI,
failure/retry and whole-consumer qualification remain pending, so this experiment
does not enter the frozen series or imply a new MCP/ASCENT result.

Experimental [0041 CLI integration](receipts/d1510-member-closed-link-integration.md)
packages the compiled member coordinator, passes the real 55-module ordered
CLI/C/link controls, and passes compiled external-mutation/retry and concurrent
controls. An isolated actual ASCENT cold AOT run passes 30/30 Cases at 114.46
seconds within its focused component deadline. It is not a complete ASCENT or
MCP qualification; cross-group mutation safety and whole-consumer performance
remain pending. Neither 0040 nor 0041 enters the frozen six-patch safety series.

**0041 promotion is now denied:** a real cross-group include mutation published
a stale binding despite group-local checks. The separate
[0042 whole-request guard](receipts/d1510-member-link-request-guard.md) rejects
that interleaving and real private-tool replacement before binding, with exact
ordinary C/link parity on retry. Normal 55-module CLI and one-switch fallback
controls pass. Guarded MCP/full-ASCENT qualification is still pending; no previous
timings are inherited as new guarded-consumer results.

Experimental [0028/0029 closed-link handoff](receipts/d1510-closed-link-consumer.md)
now connects the bulk GSC consumer to Gerbil's per-object bindings. Real isolated
ASCENT entry rebuilds pass 30/30 Cases at 50.48 / 44.55 seconds, but reuse a
compiled library and are not whole-package cold admission. A qualification-only
driver loader proves active code identity; production AOT relinking and fresh
MCP/full-ASCENT gates remain pending. These patches do not replace either locked
measured series.

Experimental 0023/0024 provide explicit library-producer admission and compiled
Gambit reuse. Their [V11 record](receipts/d1510-planned-producer-v11.md) separates
passing mechanism/ABI/source-replay checks from failed whole-consumer gates.
They are **not** part of this frozen checkpoint or the release workflow. 0023
replaces, rather than follows, experimental 0022; 0024 applies only to Darwin's
Gambit source and has no Linux build qualification.

Experimental generated-C journals in V9/V11 have a reproduced transient-source
read race: copying a source before reopening its original path does not bind
the parsed bytes. [The snapshot-reader record](receipts/d1510-generated-c-snapshot-reader.md)
documents the counterexample and experimental follow-up 0025 (after 0024).
Those old binaries remain unqualified; 0025 is not in the frozen five-patch
series and has not received native-profile or complete-consumer performance admission.
The [native follow-up](receipts/d1510-snapshot-reader-native-v12.md) now records
compiled race/CLI/concurrency controls on both isolated ABIs and 55-module C/link
parity. Whole-consumer performance admission remains missing; the malformed
original component timing is not promoted to an acceleration claim.
The subsequent [real isolated ASCENT AOT attempt](receipts/d1510-ascent-snapshot-positive-denied.md)
hits the unchanged 135-second whole-task cap during library compilation. Its 80
producer records are not completed Cases or link adoption; this configuration
is DENY and remains outside the fastest series.

A separate [multi-entry Mach-O fixture](receipts/d1510-multi-entry-bundle-contract.md)
preserves default filename-derived entries, initialization order, mutable state
and repeated-load rejection with one rather than two physical images. Both
compiler ABIs pass; this is mechanism evidence only, not an admitted consumer
optimization or a change to the frozen series.
The [real ASCENT core follow-up](receipts/d1510-real-ascent-core-bundle.md)
preserves existing linker aliases and passes native module calls through the
ordinary Gerbil import path. Image reduction is repeatable, wall-time gain is
not; duplicate symbols are rejected before linking. Full AOT consumer admission
remains missing.

The [real V4 tool-upgrade scenario](receipts/d1510-ascent-v4-actual-tool-upgrade.md)
now checks actual private GNU GCC content changes through three direct ASCENT
AOT runs, each 30/30 Cases. Entry/object invalidation passes without deleting
receipts; the subsequent entry HIT still executes all Cases. This is a warmed
library safety qualification, not a new package-cold or full-suite speed claim.
The [source/concurrent-entry follow-up](receipts/d1510-ascent-v4-source-concurrency.md)
passes 30/30 Cases in each of two simultaneous calls after a comment-only source
change, with one rebuild and one admitted entry HIT. All 72 rebuilt objects miss
the cache, so object-reuse benefit in this configuration remains unproven.
The separate [proof-component diagnosis](receipts/d1510-ascent-v4-key-components.md)
now observes 70 HIT / 2 MISS after a comment-only change with unchanged tool,
environment and command components. Both direct AOT runs pass all 30 Cases.
This establishes real unchanged-closure reuse, not a new cold/full-suite win;
the diagnostic helper remains outside the frozen optimization series.
The [HIT cost and Multiple VM controls](receipts/d1510-static-hit-cost-multiple-vm-contracts.md)
measure four real object HITs and qualify 22 native component contracts using
the actual ASCENT GSC/header pair. This closes a harness ABI-selection gap;
it does not qualify complete ASCENT performance or add another optimization.
The [real malformed-source recovery](receipts/d1510-ascent-v4-failed-source-preservation.md)
also rejects Suite compilation before any Case runs, preserves the successful
AOT binary/receipt, and executes 30/30 Cases after exact source recovery.
Expected compile rejection is recorded separately from passing test correctness.
The [compiled closed-set generation probe](receipts/d1510-compiled-closed-generation-boundary.md)
verifies 55 real C outputs and complete Scheme/pinned-C link parity, with
closed HITs of 0.075–0.083 seconds versus ordinary generation of 3.35–3.82 seconds.
This is a component opportunity, not a full-consumer gain or admission of the
previously denied singleton-producer deployment.

Follow-up [MCP three-artifact testing](receipts/d1510-mcp-v4-three-artifact-tests.md)
records two complete passes (87.409 / 99.546 seconds) and a third DENY at
112.039 seconds. Stable three-run test admission is therefore **not met**.
[ASCENT full-suite qualification](receipts/d1510-ascent-full-suite-v4-checkpoint.md)
passes correctness in all three runs (94/94 modules), but its 982.01 / 516.22 /
355.33-second tasks are not performance admission. The existing upper workflow
has a separate serialized preparation cost; its changes are outside this stack.

### Historical 40-second checkpoint

`0019-gambit-darwin-static-object-reuse-candidate.patch` preserves the exact
tested v2 driver/helper and build/install wiring, after 0014 and 0015.
It is an opt-in Darwin/GNU candidate, not part of the default release stack.

| Metric | Historical D1510 | Frozen candidate |
| --- | --- | --- |
| First compile log | 4.851 / 4.574 / 4.593 s | 4.270 s |
| Complete cold build | 47.772 / 47.824 / 47.927 s | 40.042 s |
| Complete tests | 105.751 s | 91.040 s; 39/39 files, 965/965 cases |

The observed build reduction is approximately 16.2%. Preserve this measured
configuration, but do not attribute that reduction to object reuse: the cold
run had zero reuse events and was not a matched contemporary A/B.
The exact hashes, whole-task gates (5/50/112 seconds), and raw report hashes
are recorded in [the checkpoint](receipts/d1510-static-object-reuse-40-checkpoint.json).
[The qualification record](receipts/d1510-static-object-reuse-prototype.md)
separates passing MCP evidence from pending general production admission.
Later 0020/0021 experiments do not replace or rewrite this checkpoint.

## Four-patch release order

1. `0001-gambit-darwin-posix-spawn.patch`
   - owner: Gambit Darwin process runtime
   - scope: ordinary subprocess creation; pseudo-terminal creation remains on
     the existing fork path
   - evidence: controlled 120-module cold A/B improved the median from 28.853
     seconds to 10.465 seconds (`2.76x`)
2. `0002-gerbil-streaming-compile-executor.patch`
   - owner: Gerbil compiler native-job executor
   - scope: a host-derived fixed worker pool starts on the first native job and
     closes at the official `execute-pending-compile-jobs!` boundary
   - contracts: bounded concurrency, producer/native overlap, follow-up drain,
     first-error propagation, and submission parameterization
   - invariant: official V19 `std/make` source and graph algorithm are unchanged
3. `0003-gerbil-darwin-executable-closure-dag.patch`
   - owner: Gerbil compiler driver separate-linkage executable closure
   - scope: Darwin submits independent static objects and one final barrier
     link to the existing compiler executor
   - invariant: non-Darwin retains the official V19 single closure job
4. `0004-gambit-darwin-gcc-macro-expansion.patch`
   - owner: Gambit C compiler capability configuration
   - scope: Darwin with real GNU GCC only; Apple/LLVM and non-Darwin paths are
     unchanged
   - mechanism: disable GCC macro-expansion provenance tracking after the
     existing compiler capability probe; retain `-O1`, `--enable-gcc-opts`,
     `-pipe`, and all runtime code-generation flags
   - build invariant: the audited generated `configure` is touched after patch
     application so Gambit's make rules do not regenerate it with a host
     Autoconf version other than the upstream 2.69 baseline
   - evidence: the real MCP embedded object improved from 15.45 seconds to
     10.37 seconds; GCC frontend allocation fell from about 8.9 GiB to 97 MiB,
     and the Mach-O object remained byte-identical

The existing release-only FFI and AOT-tool patches are applied in addition to
these four Darwin performance slices. The release workflow records a digest of
that exact source, patch, and workflow set in its cache key, build receipt, and
immutable release tag. The 65.35-second complete MCP build in D804 is the best
recorded four-patch result, not a reproducible guarantee for another host or
revision.

## Darwin runtime closure patches

Two correctness slices follow the performance stack in the macOS release:

- `0010-gerbil-darwin-socket-address-contract.patch` initializes Darwin
  `sa_len`, passes matching native lengths to outbound socket syscalls, and
  keeps an `accept` EAGAIN sentinel out of accepted-fd setup. Linux `accept4`
  and non-Darwin sockaddr ABI behavior are unchanged. Its port-0 regression
  exercises the pending-accept path before connecting a client.
- `0011-gerbil-darwin-release-dynamic-linkage.patch` preserves release and
  optimized executable generation while avoiding unsupported fully static
  executable linkage on Darwin. Non-Darwin release linkage remains static.

The local qualification in
`receipts/d878-darwin-http-runtime-closure.md` covers the upstream atomic
socket test, a release AOT sockaddr probe, and the real ASP HTTP JSON suite.

## Observation-only patches, excluded from the performance release

Patches `0005` (build observability) and `0006` (test observability) remain
local investigation candidates. They are not applied by `publish-v19.yml` and
their later observed build cannot replace the four-patch performance baseline.

## Runtime Object Reuse Candidate

This is a performance candidate, not an observation-only patch. The frozen
`runtime-object-reuse.json` source profile orders `0002`, `0003`, `0007`, and
`0008`, verifies their hashes, and pins the current canonical staging source.
Replay it in a fresh project `.data` directory with:

```sh
python3 patches/gerbil-v19-darwin/tests/replay_runtime_object_reuse.py \
  --source-cache .data/d935-staging-source --output .data/runtime-object-reuse-replay
```

This checks source applicability only; it does not build a toolchain or admit
a speedup. Patch `0008` is mandatory for this profile to preserve library-only
output behavior. The output-dependency contract and real consumer gates must
pass before default release enablement. The latest replay receipt is
`receipts/d1390-runtime-object-reuse-profile.md`.

The subsequent current-staging toolchain build and real MCP ABBA are in
`receipts/d1403-current-staging-object-reuse-qualification.md`: whole-build
means are 75.842/58.532 seconds, with protocol smoke and strict concurrent
make/test cases passing. First-compile means are 6.074/5.951 seconds; the
startup objective and pure-module performance gate remain open. This local
qualification does not change default release enablement.

Reproduce the bounded concurrent contracts against an isolated built source:

```sh
python3 patches/gerbil-v19-darwin/tests/run_concurrent_make.py \
  --source .data/d1391-runtime-object-source \
  --output .data/runtime-object-reuse-concurrent-check \
  --native-binary --repeats 1 --strict-product-progress
```

The output directory must be fresh. Worker count follows the host CPU count;
the environment adapter reuses `gerbil/host_system.bzl` discovery and verifies
the GNU GCC 16 frontend before running the contracts.

Patch `0007` freezes the D851 Darwin executable-graph-scoped runtime-object
reuse candidate, layered after `0002` and `0003` on staging revision
`d801e7a1c7f77df421f638e62aaebe370f193c97`. It is preserved for replay
and review, **not** applied by the release workflow. In reversed-order real
consumer A/B, MCP cold builds improved from 72.130 to 60.690 seconds and from
74.727 to 59.555 seconds. POO native-warm builds had no demonstrated gain,
and one MCP attempt tripped the strict 10-second silence gate. The source,
test conditions, and failed admission gates are recorded in
`receipts/d851-executable-graph-scoped-runtime-object-reuse.md`; Git retention
does not imply release qualification.
The subsequent strict cold-build replay and the unresolved pre-build silence
boundary are recorded in `receipts/d853-mcp-silence-boundary-investigation.md`.
The isolated compiler-worker attribution is in
`receipts/d855-mcp-native-worker-attribution.md`; it is diagnostic evidence,
not an additional release patch or an uninstrumented A/B result.
The follow-up real generated-C atomic experiment is in
`receipts/d857-embedded-string-lowering-atomic.md`; its identical object
hashes and local GCC speedup do not yet qualify an end-to-end release patch.
The adjacent real MCP package gate for a smaller header-only variant is in
`receipts/d858-str8-header-package-rejection.md`; that variant was rejected
and was removed from the isolated installation after the measurement.
The following broad-tail/official-batch investigation is in
`receipts/d859-mcp-broad-tail-and-gsc-batch.md`; it also admits no new patch.
The representative GCC pass breakdown and constant-lowering rejection are in
`receipts/d860-gambit-ifd-constant-lowering-rejection.md`.
The GCC precompiled-header feasibility gate is in
`receipts/d861-gambit-header-pch-rejection.md`.
The ordinary-file string-lowering rejection and unqualified multi-threaded-VM
experiment are in `receipts/d871-d872-ordinary-string-and-vm-parallelism.md`.
The unchanged D866 candidate's strict dual-consumer requalification and
same-binary POO drift control are in
`receipts/d873-dual-consumer-requalification.md`.
The subsequent output-dependency contract correction for candidate `0007`
and its atomic-only gates are in
`receipts/d874-output-dependency-contract.md`; it has not passed a fresh
dual-consumer A/B.
The corrected candidate's isolated AOT rebuild and failed same-binary POO
control are in `receipts/d875-revised-candidate-aot-and-aa-gate.md`. Because
that A/A gate failed, no revised-binary POO/MCP A/B was admitted.
Patch `0008` restores the official pure-module output path after `0007`; its
order-balanced dual-consumer A/B is in
`receipts/d862-uninstrumented-dual-consumer-ab.md`. Patch `0009` is a separate
Darwin verbose-only module-index progress candidate. The real-consumer
pre-compile silence attribution and strict functional gates are in
`receipts/d867-module-index-silence.md`; `0009` is not a speed claim or a
release-workflow patch.

## Convergence decision

The former Patch 0002-0007 series was an investigation history, not six
independently admitted optimizations. It has been replaced by the two Gerbil
patches above:

- bounded executor, parameter capture, and streaming lifecycle are one compiler
  responsibility in Patch 0002;
- the measured Darwin executable tail is one driver responsibility in Patch
  0003;
- report structs, `make/contexts`, build-entry caching, slot admission,
  expanded clean semantics, and the `std/make` lifecycle rewrite are absent;
- the libgerbil closure-manifest experiment is not in the active stack until it
  has a same-revision clean end-to-end A/B independent of this consumer round.

## D801 evidence

Base revision: `d801e7a1c7f77df421f638e62aaebe370f193c97`.
Darwin builds use GCC 16 with Nix SDK/include/library variables removed and
`COMPILER_PATH=/usr/bin`. Worker count is supplied by the host/environment; no
source constant fixes it at 12.

| real consumer / candidate | measured wall | result |
| --- | ---: | --- |
| Gerbil POO, deferred batch executor | 16.45 s | build passed |
| Gerbil POO, minimal streaming executor | 13.49 s | build passed; `-18.0%` |
| Gerbil MCP, frozen pre-closure baseline | 175.19 s | build passed |
| Gerbil MCP, deferred batch + Darwin DAG | 99.20 s | build and binary passed |
| Gerbil MCP, minimal streaming + Darwin DAG | 79.58 s | build and binary passed; `-19.78%` vs batch |
| MCP largest generated C, GCC macro tracking on | 15.45 s | byte-identical baseline object |
| MCP largest generated C, GCC macro tracking off | 10.37 s | `-32.88%`; byte-identical object |
| Gerbil POO, qualified four-patch V19 AOT toolchain | 12.01 s | native-warm rebuild passed; `-10.97%` vs 13.49 s |
| Gerbil POO, observed host-derived 12-worker run | 13.13 s | native-warm rebuild passed; frontend 12.438 s |
| Gerbil MCP, observed host-derived 12-worker run | 81.03 s | build and binary passed; `+1.82%` vs 79.58 s |
| Gerbil MCP, missing `GERBIL_BUILD_CORES` | 393.33 s | excluded diagnostic; serialized Gerbil producer |

The final MCP candidate is `54.58%` below the frozen external baseline and
`4.91%` below the earlier 83.69-second full experimental stack. Its arm64
Mach-O executable passes version reporting and MCP initialize. The real POO
consumer returns to the established 13-second native-warm rebuild range
instead of regressing to the deferred-batch result.

The qualified Git-backed V19 toolchain also completed a real native-warm
Gerbil POO consumer rebuild in 12.01 seconds after excluding a 37.24-second
macOS first-access run. A later observed native-warm run, with the host-derived
12-worker setting explicitly present, completed in 13.13 seconds. These are
not empty-`.gerbil` cold builds: the consumer's native `clean` preserves
generated native artifacts. The equivalent unchanged MCP
run completed in 81.03 seconds, only 1.45 seconds (`+1.82%`) above the earlier
79.58-second candidate, and produced a valid arm64 Mach-O binary.

Real-consumer A/B admission is fail-closed: by default a candidate may not be
slower than its adjacent same-state baseline (`--max-regression-percent=0`).
For the POO native-warm lane, pass `--max-candidate-seconds=13.13` as the
absolute anti-drift gate; 12.01 seconds remains the best qualified milestone.
For strict local Darwin qualification, also pass
`--max-host-load-per-core=1.0`; this opt-in preflight rejects before any build
when either the 1- or 5-minute load exceeds the selected build-core budget.
It prevents an invalid sample but cannot turn a performance failure into a
pass. See `receipts/d876-host-load-preflight.md`.
An empty-`.gerbil` first-access run or an unrefactored POO source tree cannot
replace this baseline.

The 393.33-second MCP run is retained only as an excluded diagnostic: its
direct Make invocation omitted `GERBIL_BUILD_CORES`, so `std/make` used one
Gerbil producer. It is not an A/B candidate and must not be rerun as a
baseline. Phase evidence now rejects broad import/macro work as the primary
tail: all 561 import events accumulated 5.242 seconds and the maximum was 476
milliseconds, while the `main.ss` producer alone took 33.270 seconds. The next
gate therefore splits executable closure enumeration, `prepare-link`/`gsc
-link`, object submission, and final link without changing either consumer.
These phase events originated as temporary diagnostic instrumentation in D803.
Patch 0005 is retained for investigation but is outside the four-patch
performance release until an adjacent end-to-end A/B qualifies it.

The compiler atomic gate passes at two workers and covers host budget
resolution, peak concurrency, follow-up work, parameter preservation, and
first-error propagation. Historical MCP tests still contain four known
output-contract failures; they are baseline state and are not reported green.

Machine-readable evidence is in
`receipts/d801-converged-dual-consumer.json` and
`receipts/d803-frontend-dual-consumer.json`. Earlier receipts remain as the
audit trail for rejected hypotheses and attribution experiments.

## Admission gates

- Patch replay against D801 must pass without context drift.
- Gambit focused process tests must remain green.
- Compiler executor contracts run with 1, 3, and host-derived workers.
- The executor must propagate a raised `#f`, drain work submitted by a worker,
  retain submission parameters, and reopen cleanly after an error. The
  release workflow runs this contract against the built compiler, not merely
  against patch text.
- The Darwin executable closure records object success independently of the
  exception value; a failed object must never release the link barrier, even
  when the exception is `#f`.
- The Darwin process test covers environment, working directory, stderr
  redirection, child-specific `PATH` resolution, and missing executable on the
  built Gambit interpreter. Darwin `posix_spawnp` does not search the supplied
  child environment's `PATH`; only that bare-name/explicit-environment case
  keeps the original fork/exec path.
- Run tests separately before the final clean cold build.
- Validate both real consumers: Gerbil POO and Gerbil MCP.
- Record cold and warm measurements separately.
- A ten-second interval without progress is a failed or inadequately observed
  local gate.
- Do not install Homebrew or publish a new release until the exact release
  patchset and its independent consumer gates are stable.

See `REFLECTION.md` for the round-by-round evidence and rejected approaches.

## Retained D1510 fallback

The [D1510 fallback checkpoint](receipts/d1510-retained-56-baseline.md) retains
the D1878 first-compile record of 5.053081 seconds and complete MCP build of
56.255963 seconds. Its input lock and verifier prevent silent replacement by
later candidates. This is historical fallback evidence, not a new speedup
admission: the 55-second upgrade ceiling remains unmet. Private retained
artifacts are not uploaded by this checkpoint; Git alone cannot recover them.

## D1510 shell substitution candidate

The [build-only shell substitution receipt](receipts/d1510-shell-substitution-build-admission.md)
records a Gambit-only Darwin/GNU driver candidate on the original D1510 image.
Its three complete MCP cold builds are 52.499, 47.211 and 48.706 seconds;
the retained fallback lock remains untouched. Patch 0015 removes redundant
external command-substitution processes, not Scheme macro expansion. Full
test/startup admission remains false, so this is not an all-green release.

## Independent link-resource side patch

Patch `0017-gambit-darwin-balanced-link-resources.patch` retains a balanced
resource-union candidate for native Darwin/GNU GSC. The original portable
fold remains selected elsewhere. The [side-patch receipt](receipts/d1510-balanced-link-side-patch.md)
records exact native link-C parity and fewer resource comparisons, but no stable
wall-time, startup, test or complete-build admission. It is not in the default
construction/publication stack and does not replace D1510 plus 0015.

## Retained source-loader candidate

`0018-gerbil-darwin-generated-source-loader.patch` freezes the measured
generated-driver change on retained D1510 plus 0015. It applies to
`build/lib/static/gerbil__compiler__driver.scm`, not to upstream Gerbil source.
It avoids native compilation only for bounded, pure generated static loaders
on Darwin/GNU; runtime and macro bodies retain their native compilation path.
The native re-link recipe is `tests/replay_d1510_source_loader_native.py` and
its helper is `tests/d1510-source-loader-helper.scm`. The recipe requires the
retained local D1510 input artifacts; Git alone is not a full toolchain rebuild.

The [exact-profile repeat](receipts/d1510-source-loader-repeat-52-second-gate.md)
records complete candidate builds of 49.743 and 49.938 seconds. The historical
43.847/45.127-second results remain separate and were not reproduced here.
For this candidate line, target at most 50 seconds and DENY every individual
run above 52 seconds using `tests/admit_source_loader_repeat.py`. The historical
55-second policy is not rewritten. Full tests remain unqualified, and 0018 is
not in the default production/publication stack.

The paragraph above describes the historical source-loader candidate and its
then-52-second policy, not the current research selection. Continue from the
[frozen reader-whitespace checkpoint](receipts/d1510-reader-whitespace-47-baseline.md),
binary SHA256 `1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Its historical cold builds are 47.771713 / 47.824226 / 47.927094 seconds.
Current whole-task gates are first output 5 seconds, cold build 50 seconds,
and full test 112 seconds, without a per-file silence gate. The historical
105.750982-second 39-file/965-case test pass and two subsequent strict-test
DENYs remain separate; [stable 112-second acceptance is not established](receipts/d1510-112-test-guard.md).
Historical checkpoint manifests retain their original policies and verdicts.
These local receipts do not admit the candidate to production or make Git
alone a complete toolchain reconstruction. Consult the
[four-question preimplementation review](receipts/d1510-mainline-research-accountability.md)
before selecting another mechanism; do not use activity, counts or component
ratios as end-to-end progress.
