# D1510 Counter Evidence And Shared Framework

No new runtime optimization, MCP acceleration or production admission. The
historical heavy cold-build anchor remains 47.771713 / 47.824226 / 47.927094
seconds, separate from the small independent standard-library fixture.

## Hardware Recording

One unchanged retained runtime process imports original std/make, std/test
and std/build-script. It exits 0 with final OK. CPU Counters recording and
exports complete; the binary and GSC remain unchanged. Evidence resides in
`.data/d1510-stdlib-counter-profile-v1/`.

Named process metrics admit 1,044 precise buckets and 917,741,379 recorded
cycles. The analysis excludes 975 coarse metric rows to avoid overlapping
one-millisecond and ten-millisecond accounting. Cycle-weighted normalized
named metric contributions are processing 26.05%, discarded 13.32%, delivery
24.99%, useful 35.64%.

These are normalized metric contributions, not removable wall-time fractions
or measured branch-miss rates. Core classes are not separated. Neither a
Darwin/Linux cause nor a predicted speedup follows from these percentages.
The recorder's 94.96-second capture/export lifetime is not product timing.

[Apple's CPU bottleneck documentation](https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks)
distinguishes delivery, processing, discarded and useful work, and recommends
correlating bottleneck observations with executed code. This source describes
metric interpretation, not a Gambit optimization result. Tool identity was
`xctrace version 16.0 (17F113)`; no exact installed-version bug-fix claim is made.

The same recording contains 513 running time samples matching precise metric
buckets. Native UUID/address/function-start validation admits 335 native leaves;
178 are external. Twenty-one samples are explicitly excluded. Leading leaves
include coalesced host (81), open syscall (55), mark_array (35), module fixup
(31), specialized mark_array (29), GC hash table set (27). One-millisecond
timer weights are not hardware cycle weights. Correlation with a bucket is
not instruction-level attribution or exclusive Scheme-procedure cost.

Recording report SHA256:
`ea03df7d01353a86ef65bfe27be245062633bda317d70d113b11f4a1bef9887f`.
Named metric export SHA256:
`9ca15bdccaea65fcc024944786599c9e2ad36ca6a2db4777bdafdfeb31ed849a`.
Time export SHA256:
`950047050ded732ac61923a2224cc2f2eec2080c40cd4adf9479db24892a337d`.

## Framework Migration

The user's requested consolidation introduces `tests/experiment_framework/`
and one `tests/experiment.py` CLI. Five current workflows use shared context,
owned-process execution or strict XML evidence handling: stdlib construction,
artifact verification, counter recording, metric summary and stack correlation.
Standalone commands remain available. Frozen historical scripts are unchanged.

The process executor retains whole-task 5/50/112-second limits and shared
concurrent test gating. It also fixes timeout cleanup when the parent has
already exited but descendants keep the stdout pipe open: a DENY still kills
the owned process group. Recorder finalization remains a distinct diagnostic
deadline; its shutdown grace does not extend any product performance gate.

Framework/gate checks pass 26 tests, including hard denial/reaping, child-group
cleanup after parent exit, canonical runtime home, persistent path isolation,
XML references/schema integrity, CLI dispatch and exact recomputation of the
original metric and stack summaries. Existing recording files are not changed
and hardware recording is not repeated to validate this refactor.

The unified artifacts command additionally verifies the existing independent
stdlib construction, using a fresh attempt-3 receipt. Its newly selected native
list/JSON images load successfully, final OK, exit 0, binary unchanged. This
verifier is not a new complete build or test measurement.

## Unified Cold-Run Admission

The unified stdlib command was also executed with a fresh output at
`.data/d1510-stdlib-framework-v1/`. Clean exited 0 in 6.032343 seconds.
Build produced no qualifying first compilation log by 5.004156 seconds and
was immediately DENYed against the unchanged 5-second gate. The process group
was killed and reaped, terminal exit -9, with no cleanup errors. Build did not
complete and the test wave was not started; no complete build or test time
can be reported for this attempt.

Source hashes, retained runtime SHA256, GSC SHA256, builder script SHA256 and
12-worker setting match the earlier successful stdlib-v3 fixture. This input
check does not establish the cause of the timing difference. Unit and artifact
load checks pass, but this fresh end-to-end attempt does not pass admission.
No repeated unchanged run, relaxed deadline or runtime-speedup claim is used
to hide the denial.

## Core Context And Native Frame Boundary

The existing unified `counter-stacks --context` analysis now emits a separate
immutable context report from the original recording, with no new recording
or runtime execution. Exact original leaf statistics remain unchanged.
Thirty framework, metric and gate checks pass, including synthetic P/E
coverage and rejection of conflicting or unidentified core labels.

Of the same 513 matched running samples, 348 have P-core labels and 165 have
E-core labels. Their timer weights are respectively 348 and 165 milliseconds.
Single-frame stacks account for 243 P-core and 126 E-core samples: 369/513
(71.93%) have no sampled caller. Core labels must match their numeric index.
The attached category contributions remain process-bucket proxies, not
per-core cycle measurements. This does not establish scheduler delay, a
Darwin/Linux cause, or a reason to repeat the rejected QoS route.

Context report SHA256:
`294a2711c1d4a9d143258d886467872e649e325a5a5adb20a1f984a3fbd49538`.

Bounded disassembly of the unchanged GNU-built runtime distinguishes the
actually sampled common host from the previously audited thin core/stx/mop
entry stubs. `gb_coalesced_host` at `0x1002f3f64` subtracts `0x2000` from SP
and saves registers, then enters by indirect branch at `0x1002f3fa0`.
That instruction has six timer samples. The ordinary marker's cell load at
`0x101482800` has twelve samples and its constant-propagated counterpart at
`0x101483130` has ten. Exported return-address low bits are masked to the
four-byte instruction boundary for this disassembly inspection.

Neither the frame size nor an instruction's sampled PC proves removable
execution time, register-spill cost, branch misses or memory-latency cause.
LLVM objdump only inspects the already GNU-built binary; it does not compile
with Clang. No marker-inline, heap-floor, host-splitting or return-outlining
candidate is reopened. The distinct common-host frame now requires an exact
source/temporary-lifetime audit before any transformation: shrinking an
unmeasured frame or changing the host-transfer protocol is not admission.

[Apple's profiling session](https://developer.apple.com/videos/play/wwdc2025/308/)
distinguishes periodic timer sampling, counter-triggered sampling and
processor execution tracing. This recording's timer weights cannot replace
instruction/cycle attribution. The original runtime and 47-second anchor
remain retained; no new complete build/test qualification follows here.

## Exact Common-Host Storage Origin

Original-source `compiler-frame` finishes with GNU GCC, the original O1 and
driver options plus stack-usage and RTL diagnostic flags. The output object
matches the frozen carrier object byte for byte:
`758c3dfd962ae0d5b4fc9631ad426173464076852e2c652c8d7fdcd0de6b646c`.
All original source, driver and reference-object hashes remain unchanged.
Evidence: `.data/d1510-common-host-frame-v1/`.

GCC stack-usage reports an 8,192-byte static common-host frame. Its expand
dump gives 398 partitions totaling 8,048 bytes: 397 `gb_answer` partitions
total 7,960 bytes, and one shared native-result partition totals 88 bytes.
Partition sizes are declaration storage accounting, not runtime allocation
counts or exclusive spill cost. This identifies a source ownership issue in
the existing parameter fast-path macro, not an unspecified GVM flag problem.

The private shared-result prototype retains the macro's existing
Darwin/GNU/non-Clang/single-host/single-VM/thread/processor and debug guards.
It replaces per-expansion result objects with one activation-local object,
not static storage or a parameter-value cache. The helper returns before
the macro consumes the result; value/getter are copied before any Scheme
jump, with no subsequent result access. Separate C activations have separate
storage. Getter, closure, special-parameter, stack-trip and fallback checks
are unchanged. This contract still requires actual semantic execution.

The first candidate-generation attempt rejects indented macro call sites
before compilation. Its failed receipt remains at
`.data/d1510-common-host-result-slot-v1/`; accepting spaces/tabs fixes the
parser, with an indented regression fixture. The second attempt uses a fresh
output rather than overwriting that failure. Thirty-seven focused framework,
metric, parameter-source and whole-gate checks pass; no runtime speedup is
established by these checks.

The second private candidate compile finishes with exit 0 and unchanged
original inputs. GNU stack-usage now reports 1,056 bytes for the same common
host, versus 8,192 original bytes. Candidate object SHA256:
`4802fa3e44716b04e7abbee1a01d86ba3d4aa34a79c85ef58838bb051dc2f893`.
Evidence: `.data/d1510-common-host-result-slot-v2/`. This is an 87.11% static
frame-size reduction, not an 87.11% execution-time reduction. It is not yet
linked into a candidate runtime or semantically/performance admitted. The
retained runtime is not replaced.

## Actual Retained-Recipe Denial

The shared-result object is privately linked with the frozen providers, reader
and original native objects. An independently reconstructed control is byte
identical to the retained runtime, all frozen input hashes remain unchanged.
Candidate runtime SHA256:
`e01df7791ae8620da7670eb89ee97768daaf3e2a556e8fdf801c4c0ef4801656`.
Evidence: `.data/d1510-common-host-result-native-v1/`. Construction is not
semantic or performance admission.

The existing original D1510 pipeline runs a fresh real MCP clean/build under
hardware-derived 12-worker concurrency, unchanged recipe and 5/50/112 gates.
Clean exits zero in 18.246280 seconds with zero project native images.
Build still has no first compilation log at 5.039110 seconds: immediate DENY,
SIGKILL and successful reaping, no cleanup errors. Full build time is unknown
and full tests are skipped, not counted as passed. No independent stdlib
performance campaign or repeated unchanged cold run is launched after denial.

| Measurement | Retained historical anchor | Shared-result candidate |
| --- | --- | --- |
| First compilation log | 4.850866 / 4.573628 / 4.592897 s | absent at 5.039110 s, DENY |
| Complete cold build | 47.771713 / 47.824226 / 47.927094 s | not completed |
| Complete 39-file / 965-case test | 105.750982 s historically; strict 112 repeats DENY | not executed |

Evidence: `.data/d1510-common-host-result-acceptance-v1/report.json` and
`progressive-admission.json`. The unified `three-lines` receipt locks the
candidate identity, records all three measurements, preserves the observed
stop and uses null for nonexistent complete times. Current CLI policy is
5/50/112; historical function callers retain their explicit/legacy 52 policy.
Thirty-nine focused tests pass, including current/historical policy separation
and rejecting incomplete rounds without inventing completed timing.

Decision: do not promote, deploy, repeat or expand this exact shared-result
storage candidate. Static stack reduction does not clear actual first-log
admission. This failed candidate does not replace the 47-second anchor and
does not establish a cause of the timing difference. No production patch,
commit or push follows from it.
