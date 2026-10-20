# D1510 Research Exclusions

## Rule

Current selection is the retained reader-whitespace host, with historical
complete cold results 47.771713, 47.824226 and 47.927094 seconds. Current hard
gates are first real compile/output <=5 seconds, complete cold build <=50
seconds and the full 39-file/965-case test wave <=112 seconds. There is no
extra per-file/per-case silence gate. The original 105.750982-second complete
test and the subsequent strict 112-second DENY remain separate evidence;
neither is rewritten. See [the 112-second policy](d1510-112-test-guard.md).
The following older selections and thresholds are historical, not current
defaults or permission to widen a gate.

## Historical Policies

V8's Apple M1 greater-than-4-GiB indirect-call-distance result does not
reopen code relocation for the retained embedded core/stx/mop hosts: their
same-image executable section spans only 23,934,760 bytes. This exclusion is
limited to those same-image calls, not every dynamically loaded image or
every prediction mechanism. See
[the structured native layout audit](d1510-stdlib-rebuild-and-host-distance.md).

Continue from the original D1510 configuration plus admitted patch 0015.
Its recorded complete cold builds are 47.211369, 48.705787 and 52.498548
seconds. Do not replace this line with a 60/70-second candidate, add the new
multiple-VM profile, or reinterpret a failed candidate as the next baseline.
Any candidate complete cold build above 55 seconds is DENY.

For the subsequently retained source-loader candidate, the then-stricter
policy supersedes that ceiling: target at most 50 seconds and DENY any
individual build above 52 seconds. Its exact-profile repeat is
[49.743/49.938 seconds](d1510-source-loader-repeat-52-second-gate.md).
Continue from that unchanged candidate plus original 0015; do not mix in the
closed routes below. Full test qualification remains open.

That earlier runtime policy also required the first real compile line within
5.5 seconds and the complete test wave within 52 seconds. Violations kill the
owned process group immediately; cold DENY skips tests. See
[progressive runtime gates](d1510-progressive-runtime-gates.md).

## Experiment Admission

Read the evidence before starting another experiment. The following exact
routes are NO / IGNORE for further extension. Keep the negative receipts;
ignore the rejected implementation, not its evidence. A genuinely different
source mechanism requires an explicit explanation of why the prior rejection
does not apply. Renaming, composing or retuning a rejected implementation is
not a new mechanism.

## Closed Routes

| Route | Decision | Existing evidence |
| --- | --- | --- |
| Whole-context completed-result memo | NO; do not widen the cache | [72.213895-second complete build](d1510-context-result-memo-rejected.md) |
| Symbol-key hash filtering | NO; do not extend into GSC | [62.443346-second complete build](d1510-symkey-hash-filter-rejected.md) |
| Grouped packed-string emitter | NO; atomic object gain is not admission | [60.991300-second complete build](d1510-reuse-audit-grouped-native.md) |
| Metadata-empty driver probe | NO; do not stack more work on this driver | [55.962595-second complete build](d1510-driver-extension-hard-denial.md) |
| Probe plus builtin filename quoting | NO; retain original 0015 | [57.918305-second complete build](d1510-driver-extension-hard-denial.md) |
| Naive official multi-input GSC batching | NO; no new batch layer | [1.01 seconds batched versus 0.78 separate](d859-mcp-broad-tail-and-gsc-batch.md) |
| Simple runtime object-producer fusion | NO for major-gain expansion | [About 4.16% producer-wave difference only](d1416-existing-advantage-extension-boundary.md) |
| Shared Gambit-header PCH or local header split | NO | [Per-module macros invalidate PCH](d861-gambit-header-pch-rejection.md) |
| Native CPU detection workaround or generic tuning sweep | NO | [Native detection works; tuning dumps agree](d1370-gnu-darwin-native-tuning-admission.md) |
| Further ordinary Gambit fork removal in this MCP path | IGNORE this hypothesis | [Actual census has zero fork calls](d1469-real-process-census-and-extension-boundary.md) |
| Claiming 189 logged object jobs are 189 duplicate compilations | IGNORE this hypothesis | [Freshness checks and 186 producer/object pairs](d1510-original-compile-job-closure.md) |
| Treating largest embedded C object as the whole-build tail | IGNORE this attribution | [Embedded finishes about 18.54 seconds before completion](d1604-task-identity-and-tail-boundary.md) |
| Grouped native image as a proven cold-start fix | NO to that claim | [Initial native-load failure remains](d1555-current-active-native-reuse-extension.md) |
| Native projection, expanded field elimination and canonical mark-fold dispatch | NO; do not widen these prototypes | [Retained negative timings and strict gates](d1510-progressive-runtime-gates.md) |
| Single-mark, zero-suffix marked-tail splice cursor | NO; do not retune or extend this candidate | [First-log runtime DENY, tests skipped](d1510-bounded-splice-cursor-denied.md) |
| Single-collector chunk enlargement and omitted publication/dequeue barriers | NO; do not repeat it as a new CAS or Darwin fence fix | [D968 candidate user CPU is about 2.15% higher](d968-single-collector-rejected.md) |
| Pair-tail traversal reordering | NO; do not repackage it as a short-array optimization | [D999-D1003 matched preparation has no CPU gain](d970-guarded-trace-progress.md) |
| Descending stride-two strong GC-table marking | NO; do not reconstruct the earlier batching candidate | [D1004-D1006 matched preparation improves CPU about 2.48%, insufficient for mainline admission; tested binary predates index-conversion correction](d970-guarded-trace-progress.md) |
| Single-processor forwarding CAS bypass on this retained host | IGNORE the inactive mechanism | [Original GC forwarding is already sequential](d1748-active-gc-forwarding-boundary.md) |
| Default GC heap-slack/floor increase | NO; do not retune the same heap-floor proposal | [D1753 over-ceiling builds and failed concurrent fixture](d1753-default-gc-slack-rejected.md) |
| Caller-inline single-cell no-copy marker entry | NO; counted opportunity is not performance admission | [D1873 actual build/test rejection](d1873-single-marker-real-build-test-rejected.md) |
| Static module registration as a seconds-scale target on the retained composition | IGNORE that unsupported attribution | [Measured initial phases are milliseconds](d1510-native-loader-boundaries-tested.md) |
| Low requested QoS as an established retained-VM cause | IGNORE the unsupported cause; no priority escalation | [D1017 already observes USER_INTERACTIVE](d970-guarded-trace-progress.md) |
| Serialization as a replacement for the already native phase body | NO to deployment from these controls | [Real body passes semantics but allocates more than native without stable gain](d1510-real-phase-import-boundary.md) |
| Directory caching/realpath or getcwd-to-F_GETPATH rewrite as the dominant startup remedy | NO; D1088/D1246/D1250 already constrain this route | [Reached stdlib CPU and old source evidence](d1510-stdlib-filesystem-budget.md) |
| Provider table lookup rewrite as a major-gain target | IGNORE the unsupported budget | [Existing provider-own intervals are sub-ms to about 1 ms](d1510-stdlib-filesystem-budget.md) |
| Append make~0/make~1/compiler-base~1 providers to the frozen host | NO; do not widen this composition from object parity alone | [Actual provider hits and focused tests pass, cold first-log gate DENY](d1510-provider-extension-cold-denied.md) |
| Cache Gambit interpreter compilation as a seconds-scale begin/startup remedy | IGNORE the unsupported budget; Gerbil expansion is a different boundary | [Existing preparation is ms-scale versus execution](d1510-preparation-and-register-boundary.md) |
| Enable local GVM variables as a newly missing Emacs-style frame optimization | IGNORE for the audited retained units; no register-flag sweep | [Real GNU preprocessor already selects local variables](d1510-preparation-and-register-boundary.md) |
| Enable C tail calls as a newly missing retained Darwin host-exit optimization | IGNORE that premise for audited units/path; no tail-call flag sweep | [Three GNU transcripts select exclusive proper tail calls; retained host has a native tail-transfer block](d1510-host-exit-branch-boundary.md) |
| Distributed computed-goto/external-host exits using distinct asm operands | NO; do not reopen from the retained host's small static BR count | [D916 increased native sites but failed the then-10-second first-log gate](d897-mcp-gambit-startup-candidates.md) |
| Shared activation-local parameter result storage | NO; smaller static frame is not execution admission | [8192 to 1056 bytes, but actual cold first-log DENY at 5.039110 seconds](d1510-counter-profile-and-framework.md) |
| Child-environment PATH resolver in a replacement RTS archive | NO for this deployment; do not repeat or retune the denied candidate | [13 process cases pass, actual cold first-log DENY at 5.004156 seconds](d1510-test-spawn-path-boundary.md) |
| Darwin actual-FD enumeration in closefrom's original fork cleanup | NO for this deployment; no retuning or admission from component durations | [19 contracts per role pass; actual cold first-log DENY at 5.049419 seconds](d1510-darwin-closefrom-denied.md) |
| GC-hash ref/set cold rehash tail helpers | NO; no stack-removal retuning or performance admission from instruction counts | [14 controls per role pass; actual stdlib first-compile DENY at 5.016912 seconds](d1510-hash-cold-tail-denied.md) |
| Fixed-width memcmp in Scheme-string symbol/keyword intern lookup | NO for this deployment; no widening into UTF-8 lookup | [8 controls per role pass; actual stdlib first-compile DENY at 5.007450 seconds](d1510-intern-string-compare-denied.md) |
| Twelvefold repeated optimizer metadata installation across std/make workers | IGNORE this attribution; do not add shared-state caching on this premise | [Real 12-consumer native build has 152 distinct metadata paths and builtin loaded once](d1510-optimizer-metadata-cost.md) |
| Two-word moving-GC copy-loop specialization | NO for this deployment; no wider unrolling or retuning | [9 moving-GC controls per role pass, real stdlib first-compile DENY at 5.014730 seconds](d1510-two-word-copy-denied.md) |
| Darwin CLI handoff to a separately linked native tool as an already-proven startup/build remedy | NO to replaying the old dispatcher deployment; an AOT list alone is not command-path evidence | [D862 native gxpkg handoff fails the real MCP startup gate](d862-uninstrumented-dual-consumer-ab.md) |
| Same-process runtime-only built-in tool dispatch bypassing interface import | NO; do not extend or retune this private bypass | [Actual MCP clean exceeds its 30-second safety gate; build/test skipped](d1510-runtime-only-tool-dispatch-denied.md) |
| Activation-local nargs state through the existing D/R/W protocol | NO; high operation counts and native register emission are not performance admission | [D1821 controls pass but complete build is 70.788101 seconds against its then-55-second gate](d1821-nargs-state-protocol-not-admitted.md) |
| Mach-O orderfile as a way to compact sampled instructions inside the common host | NO to that mechanism claim; whole-function movement preserves internal offsets | [28 sampled pages versus geometric lower bound 27](d1510-macho-hot-page-layout-boundary.md) |
| Direct symbol-only context-table replacement or standalone nonmoving-key rehash shortcut as the next major-gain candidate | NO from these data; do not compile on the permanent-symbol premise alone | [300 original key/effect contracts and 1.196893% sampled rehash self cycles](d1510-interface-architecture-transfer.md) |
| Unguarded terminal head-binding transfer across the live core-expander predicate | NO; preserve the caller's live re-resolution and do not treat the failed public-resolver wrapper as attribution | [408 original native contracts, including binding replacement in the reached predicate](d1510-head-resolution-live-boundary.md) |
| Blanket equal-value dynamic-binding elision or reuse of the parent's parameter/value pair | NO; equal initial values do not make writable scope cells interchangeable | [252 original assertions include nested equal-value assignment isolation; actual persistent path-copy census](d1510-native-procedure-budget-boundary.md) |

These exclusions do not revoke the separately established 0001 process-spawn,
0007 object-reuse, 0004 GNU macro-tracking or 0015 command-driver benefits.
They reject the extensions listed above, not all possible work in those modules.

The later [GC array census](d1510-gc-array-length-boundary.md) is diagnostic
evidence, not permission to reopen the pair-tail, stride-two or single-cell
prototypes. Source inspection confirms that ordinary movable-object scans and
the pair fast path skip the first field already processed by tail marking.
Do not propose eliminating that alleged duplicate scan. Existing hardware
records' CountingModeSamples contain bottleneck remarks, not L1 data-cache
miss measurements; available mode names in trace metadata do not prove that
those modes actually ran.

## Source Boundaries Checked

The original compiler driver's Darwin static runtime path generates C, copies
it to the static path, compiles a PIC object and links the dynamic bundle from
that same object. Executable object jobs check freshness before compiling.
This agrees with the existing object-closure evidence. Do not remove those
checks or count the scheduled job names as proof of duplicate native work.

Generated C defines per-module symbol/global/label counts before including
gambit.h. This agrees with the existing PCH rejection; no new PCH experiment
is warranted. The selected original driver already places
`-ftrack-macro-expansion=0` in C_COMPILER. Moving the same option around is not
a new removal of preprocessing work.

The next admissible investigation must identify previously uncovered actual
work in the broad native tail, final executable closure or in-process Scheme
execution. It must demonstrate an equivalent output/semantic contract before
building a private candidate. No such new candidate or gain is admitted by
this exclusion review. Do not rebuild the toolchain merely to reconfirm an
already closed route.

Every candidate remains Darwin-only with real GNU GCC and the retained D1510
binary/runtime configuration, private persistent .data artifacts and
hardware-derived concurrency. Complete cold build, first compile and actual
tests remain distinct gates. No timeout changes or synthetic progress logs.

## Tool Entry And Register Review

Retained `src/gerbil/main.ss:201` handles gxi/gxc directly; its other tool cases
import the tool module, resolve main and apply it. The build/test aliases call
this same function. The current General AOT list supplies separate binaries;
it does not alter those command aliases or the retained binary. This source
audit is not a new startup measurement. User-owned AOT configuration and CI
remain untouched.

The old D862 handoff deployment and D1821 nargs protocol prototype already
contain actual failed runtime gates. Do not reconstruct them from their short
help-command times, regex subset success, source-site counts or emitted code.
Their historical limits and artifact identities are different from the frozen
47-second profile; no historical result is promoted to a current baseline.
No such candidate or workload is rerun by this review.
