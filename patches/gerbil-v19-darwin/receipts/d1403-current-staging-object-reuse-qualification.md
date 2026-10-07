# D1403: current-staging object reuse, real MCP and concurrent tests

## Identity and isolated build

Canonical `v0.19-staging` is checked before and after qualification:
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. Gambit gitlink remains
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. The local D935 control is not
an unpatched upstream or Linux control. Both roles use its existing GNU GCC
16, SDK/Bazel environment, GSC and macro-tracking policy.

The frozen source profile's four Gerbil patches are used. The D935 source
is APFS-cloned without hard links into `.data/d1391-runtime-object-source`;
only 0007 and 0008 are added to its existing 0002/0003 compiler changes.
The final three changed sources match D1390's clean, pinned replay byte for
byte. Original binary, GSC, gambuild-C and protected source hashes remain
unchanged. No Homebrew installation, consumer source, HTTP code or Gambit
optimization flag is changed.

| Official stage | Elapsed | Result |
| --- | ---: | --- |
| stage1 | 223.231 s | pass |
| stdlib | 525.444 s | pass |
| libgerbil | 274.658 s | pass |
| tools | 8.849 s | pass |

These are toolchain build durations, not performance comparisons. The
output-dependency contract passes before and after the remaining stages,
including late subscription, multiple dependencies, duplicate/unknown
producers, and propagation of a raised `#f` without running its dependent.
Candidate Gerbil SHA256:
`a398d0b2e3200019a1542a0fea8b101062a76118f82dcba30f580b481a608e5a`.
Build receipts: `.data/d1392-runtime-object-build/report.json` and
`.data/d1394-runtime-object-toolchain/report.json`.

## Strict, independent-fixture MCP ABBA

Each role has an independent fresh checkout of unchanged MCP
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. Actual `gerbil clean` must
exit zero within 30 seconds and leave zero project native images. Actual
`gerbil build` has a 10-second real-output silence gate and 180-second
total bound. All four builds use 12 cores, finish linking the executable,
and preserve the checked consumer source hashes. This is project-cold,
not OS-page-cache-cold or a kernel-policy causal experiment.

| Order | Role | Clean | First compile | Whole build |
| --- | --- | ---: | ---: | ---: |
| A | D935 control | 2.604 s | 6.058 s | 71.459 s |
| B | Reuse candidate | 2.463 s | 5.934 s | 59.335 s |
| B | Reuse candidate | 3.143 s | 5.968 s | 57.729 s |
| A | D935 control | 2.707 s | 6.090 s | 80.224 s |

Mean build: **75.842 to 58.532 seconds, 22.824% less** in this local ABBA.
Both orderings have a whole-build gain. Mean first compile: **6.074 to
5.951 seconds, only 2.025% less**. The major first-log cost is not fixed.
Clean time is separate, not included in the whole-build column. Retain the
individual runs and their variation; do not infer a universal speed ratio.

Raw receipt, logs, fixtures and hashed saved executables:
`.data/d1396-mcp-runtime-object-fresh-ab/`.

## Actual executable and concurrent test checks

All four saved, hash-matched MCP executables pass initialize, tools/list,
and `gerbil_eval` of `(+ 1 2)` using private stdio. The actual result is
`Result: 3`, matching `tools/eval.ss`. Original responses are saved before
assertions. Each RPC has a five-second output gate and each batch a
90-second bound. Servers are deliberately stopped and reaped. This is
protocol/arithmetic smoke qualification, not the full MCP test suite.
Receipt: `.data/d1400-mcp-protocol-reuse/report.json`.

Both roles pass 12 concurrent runtime starts, 12 concurrent std/make and
std/test imports, and the three actual std/test cases for cold build, no-op,
and dependency invalidation preserving unrelated modules. Strict mode uses
reader-recorded real output times, not changing process/CPU snapshots.
Largest recorded gaps are 4.358 s candidate and 4.144 s control, within
the five-second gate. Peak observed GCC frontends are 11 and 10; workers
are configured to 12, but full simultaneous utilization is not claimed.
Receipts: `.data/d1401-candidate-exact-progress/report.json` and
`.data/d1402-baseline-exact-progress/report.json`.

The small pure-module fixture does not prove performance non-regression:
forward-order totals are 14.647 s control / 15.358 s candidate, and the
reverse-order totals are 17.166 s candidate / 16.567 s control. All semantic
cases pass, but these numbers must not be presented as a pure-library win.
No full std/test suite or actual `gerbil test` package suite is qualified.

## Retained failures and release decision

D1391's copy attempt selected GNU cp, which rejects APFS `-c`; the retry
uses macOS `/bin/cp`. D1393's continuation incorrectly reverse-checks
overlapping individual patches; final-source equality fixes that precheck.
Their receipts remain; neither attempt starts the remaining build stages.

D1395's shared-fixture ABBA is excluded: two clean attempts time out;
one candidate clean/build completes in 20.732/54.252 seconds with first
compile 5.911 seconds; the following control clean leaves 550 native images.
Source `make-clean/spec-outputs` removes interfaces/static Scheme files,
not all native artifacts. Fresh fixtures fix measurement isolation without
changing or relaxing clean. The 54.252-second best is not substituted for
the independent-fixture mean or the historical approximately 56-second line.

D1399's arithmetic assertion wrongly expects bare `3`; both controls and
candidates fail that harness assumption after successful initialize/list.
D1400 corrects the source-backed format and retains complete responses.
No binary or server response is repaired.

Keep the frozen candidate in Git, but keep default release enablement held.
Current evidence establishes a real local complete-MCP build benefit and
bounded functional checks, not elimination of startup cost, full test-suite
closure, Linux/Darwin causal isolation, or pure-module performance parity.
