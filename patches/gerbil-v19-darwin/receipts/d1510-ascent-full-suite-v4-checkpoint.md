# ASCENT Full Native Suite: v4 Checkpoint

## Scope And Admission

Three direct `just test-native-suite auto` runs used the isolated checkout at
21e3638687d42ecfc36acebb28991987435ebc60 and the same v4 object-reuse helper.
Each run retains the original 1 GiB heap, native deadlines, module isolation,
75 parallel / 19 exclusive module plan, and hardware-derived 12-worker pool.
No Python process launches or supervises these native tests. Python only reads
their terminal exit status, native output, time file and generated registry.

| Run | Complete Native Task | Modules | CASE-OK Events | Entry Cache | Object HIT / MISS |
| --- | --- | --- | --- | --- | --- |
| 1 | 982.01 s | 94/94 | 852 | MISS | 17 / 58 |
| 2 | 516.22 s | 94/94 | 852 | MISS | 75 / 221 |
| 3 | 355.33 s | 94/94 | 852 | HIT | 0 / 0 |

All three native commands exit zero and pass exact module-inventory admission.
852 is the count of emitted CASE-OK events, not a separately deduplicated Case
inventory. The same 94 registry paths are verified byte-identical across runs.
This replaces the earlier single-Suite coverage boundary of 30 Cases, not its
historical timings. It is **correctness qualification only**, not three cold
builds, a matched performance A/B, or general acceleration admission.

Run 1 extends an already prepared positive-plan library to the complete suite;
it is not a from-zero toolchain/dependency build. Run 2 and run 3 retain its
owned outputs. No manual source/options/compiler/coverage/timeout adjustments
are made between the three commands. The suite can create its own generated
support artifacts; run 2 rebuilt ascent-support-study-output before proceeding.
Run 3's lower total is an existing upper entry-cache
hit, not evidence that v4 object reuse accelerates this full command.
The prior v4 package-cold regression remains DENIED.

## Where The Time Went

The first two phase estimates use second-resolution filesystem timestamps
captured before the next run rewrites the generated registry. They are not
monotonic phase instrumentation and must not be presented as precise timings.

| Boundary | Run 1 Approximation | Run 2 Approximation |
| --- | --- | --- |
| Start through generated registry publication | 818 s | 324 s |
| Registry publication through AOT executable publication | 103 s | 97 s |
| Executable publication through command completion | 61 s | 95 s |

The final interval also includes native coordinator admission after Cases.
Full preparation calls two library layers (85 production / 149 support modules)
and then 94 separate Suite layer processes. At qualification.ss:292-296 the
library cache fast path explicitly accepts only a single requested test. Full
pools therefore always enter the for-each at :311-313. compile-test-layer! at
:140-147 synchronously invokes a separate gxi process using one shared
compile-layer.sexp file. The 12-worker Case pool starts only after preparation.

Isolation is intentional: the source records prior 1 GiB heap exhaustion when
accumulating Suite expansion contexts, including on Linux. This is not evidence
that the process-isolation policy itself is Darwin-specific or incorrect.
It does identify multiplicative exposure to startup/import/currentness costs.
Do not blindly parallelize the loop: shared spec and compiled dependency writers
need ownership-safe scheduling. Do not remove heap/deadline/coverage protection.

## Receipt And Isolation Identity

Raw runs: `.data/d1510-static-reuse-ascent-full-v4-round1`, `round2`, `round3`
(the latter names share the same full prefix).
Summary: `.data/d1510-static-reuse-ascent-full-v4-three-summary.json`.
Summary SHA-256:
`95099700e70b2dbc0bc206d9036d95b15463641c60f46cb7332fec2704b8067b`.
Registry modules.txt SHA-256:
`65eb1b294f7a157d2cec47f54b48a2191f41e4117ac1537335c4e70fcb980f86`.

Raw output SHA-256, in run order:

- `0fbb529f01a1e779d0988f2bf6cf721ff66ed8be8f41d174d4b5dec250a349ce`
- `7a47528d56e857a0cf3c43d28514306da15c02e50269e3c222628a73f03b97e5`
- `20c72c599eac90fd5549b1ffce83735d92baef0b65a4ae369905e9c7ea8e5caf`

ASCENT uses its qualified private installed-profile copy, not the MCP runtime
binary. Its Gerbil hash is bedfdae04633b2e2862b6083e7ab7cd20e20ca4d2b0823482cb8aa4e10c597af;
GSC hash is dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e.
The v4 helper hash matches the frozen MCP composition:
08d8ebe59d24a7098561c909c5b8e04c66aff78794d5f68f1cedddf1f2168646.

Post-series verification checks 1,992 toolchain and 2,809 dependency read-only
dynamic image references against their original SHA-256 inventories. Each
launcher checks the isolated tracked checkout stays clean. Active checkout and
shared dependency artifacts were not modified by this qualification.

The initial offline full-summary rejected run 1 because it required exactly
94 NATIVE-MODULES-OK lines; the suite's own nested native controls emit six
additional markers. The corrected reader requires exact planned/PASS module
coverage, exit zero, 94 final OK verdicts, sufficient native markers and no
failure markers. Its 10 focused tests cover missing/duplicate module coverage
and nested native markers. The original false-reject summary is retained.
