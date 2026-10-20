# Real ASCENT Source Failure Preserves Admission

## Review

- Correct route: complete the real consumer failure contract, not just the
  isolated C compiler failure controls.
- Already explored: C object/proof preservation and real source/tool/concurrent
  success were qualified. Malformed Suite source followed by recovery was not.
- Worthwhile: static reuse must not execute an old admitted AOT entry when its
  current source cannot compile, or replace the last successful receipt on failure.
- Expected speed gain: zero. This is a safety qualification, not a new optimizer
  or a retry of the denied package-cold speed route.

## Owned Fixture And Actual Execution

The existing uninstrumented V4 private tool-upgrade fixture is used:
`.data/d1510-ascent-v4-tool-upgrade-v2`, pinned consumer HEAD
`21e3638687d42ecfc36acebb28991987435ebc60`. It uses its own Multiple VM toolchain,
private genuine GNU GCC and copied dependencies. No active ASCENT checkout,
global compiler or shared dependency is modified.

Before mutation, the positive-plan test retains its previously admitted
comment-only source identity. Two additional lines append an unfinished Scheme
`def`, producing a real reader error. All original Cases/assertions remain intact.
The launcher binds this exact tracked source diff before and after the failed run:
`c42920b1df59326d5a30b0e936097adad32bd17dc163a439270404948a6f42a9`.

The native qualifier runs directly through just/Scheme with the original heap
and a 135-second diagnostic whole-task cap. The failure occurs after successful
85/87-module preparation and before the requested Suite or executable is admitted:
`Incomplete form, EOF reached`. Exit status 70 propagates through the launcher.

The two owned malformed lines are then removed. The recovered source diff is
exactly the prior admitted comment-only fixture:
`19078bbc7f7979ac24c16c5b275fc47d3e5d2ed95f790edfe8ad557a04400dda`.
The recovery launch reports both library/entry HIT and actually executes all
30 Cases with final OK and exit zero; test results are not cached.

| Phase | Real | User | System | Native outcome |
|---|---:|---:|---:|---|
| Malformed Suite source | 16.91 s | 12.13 s | 3.51 s | exit 70; zero Cases; no final OK or entry HIT |
| Exact source recovery | 8.52 s | 6.55 s | 2.98 s | 30/30 Cases; final OK; exit 0; entry HIT |

Neither run invokes GSC object compilation or emits static-object HIT/MISS events.
These are failed-source/recovery scenarios, not cold builds or full test suites.
The 8.52-second result is existing upper-entry cache reuse, not a new speed gain.

## Byte Preservation

The successful binary and receipt have exactly the same SHA256 before failure,
immediately after failure and after recovery:

- `single-test`:
  `ad17a70b6e19a330859a6130b4e75f8cd2cf075590aecc7c3c1f56224f6da6c9`.
- `single-test.json`:
  `ff22111cbcd0b814a24f9d680dfa5938c2c3464b24dc3e97ac244e7edcbb5a01`.

The saved before-receipt also compares byte-for-byte equal after failure.
No `single-test.json.pending` remains. Restored test source SHA256 is
`96157b87887b496be7655bbf83a92998f04459ed524b9930ed1273ae2793fe6c`, matching
the previously admitted fixture. Recovery itself proves the native lane lock
was released; no lock deletion, manual successful-receipt deletion or binary
replacement was used to manufacture recovery.

## Modular Receipt Admission

`experiment_framework/native_receipt.py` now separately reads an expected typed
source-compilation failure. It never marks that failed run as passing Cases.
Admission requires a nonzero non-timeout/signal status, the specific expected
error, zero started/passed Cases, no final/suite/module/harness success marker and
no stale entry HIT. Seventeen new offline controls reject success, timeout,
signals, unrelated errors and stale-executable execution. The existing ten native
receipt tests remain passing: 27 focused checks total.
Combined receipt, selected-toolchain, trace, identity and progressive-gate
regression checks pass 129 tests.

Python only reads terminal receipts; it does not launch or supervise native tests.
Private evidence is `.data/d1510-ascent-v4-failed-source-receipt-v1`:

- `failed/output.log` SHA256:
  `7873210f85e2b984cbdec4072cf842bb4281724acad5a9d158d58ab1aff997e6`.
- `recovered/output.log` SHA256:
  `b3e62dd4558aad8649de6e12a470365ba160dca183565c4d4d96f9a0145c1545`.
- `rejected-summary.json`: `failureRejectionPassed=true`,
  `correctnessPassed=false` (zero test Cases ran).
- `recovered-summary.json`: `correctnessPassed=true`, 30 Cases.

The frozen MCP patch/driver/runtime/raw reports still pass their identity lock.
Its optimization bytes and active 4.5 / 42 / 97-second ceilings remain unchanged.
The earlier ASCENT package-cold regression remains DENY. Complete dual-consumer
performance admission is not proved, and the goal is not complete.
