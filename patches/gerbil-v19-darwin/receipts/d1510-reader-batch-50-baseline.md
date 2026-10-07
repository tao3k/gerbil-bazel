# D1510 Darwin Reader Cold-Build Anchor

Scope: macOS, GNU GCC, 12 physical cores, isolated project-local `.data/`
toolchain. No Linux behavior change. This is a cold-build anchor, not complete
test or production admission.

The buffered ASCII reader batches a complete token using the existing readtable.
It validates the port buffer and cursor under the primitive lock, allocates the
destination outside the lock, then revalidates and copies under the lock. Unicode,
incomplete, long, and changed-buffer cases retain the original reader fallback.
This reduces per-character primitive locking; it does not change std/make order.

## Three Consecutive Cold Builds

| Round | First real compile log (s) | Complete build (s) |
| --- | ---: | ---: |
| 1 | 4.618989458 | 46.652867625 |
| 2 | 4.796290625 | 46.902629541 |
| 3 | 4.455518625 | 47.827904417 |

All three exited successfully, preserved source identity, and started after clean
with zero native images. No failed rounds were discarded or averaged away.
The exact binary, runtime objects, preparation sources, and reports are hashed in
`d1510-reader-batch-50-baseline.json`.

Hard gates for this candidate and subsequent candidates: first real compile log
at most **5 seconds**, complete cold build at most **50 seconds**. Deadline
violations kill and reap the owned process group. Explicitly requesting 52 seconds
for a new candidate is rejected. Only the retained historical 49-second candidate
can use its original 52-second policy for historical verification.

The three retained runs originally used a 5.5-second first-log watchdog. All
three observed first logs also satisfy the newly authorized 5-second guard;
the original raw reports are unchanged. Future runs enforce 5 seconds live.

The subsequent live 5/50 guard run had its first compile log at **4.793609375
seconds**, but reached the complete-build deadline at **50.037967500 seconds**.
It was **DENY**, killed with SIGKILL and reaped, with no complete-build time claimed.
This regression is retained, not discarded. `coldQualified` describes only the
three historical runs above; `latestGuardRunAdmitted` is false. The 50-second policy
is frozen, but current repeatability and overall production qualification are not
established. No second attempt was used to average away this failed run.

## Test Boundary

Reader semantic controls: 24 passed. Focused Python reader, selected-toolchain,
wave, progressive admission, and watchdog checks: 46 passed.

The latest complete 39-file MCP test wave took **49.604683583 seconds**:
**31 files passed, 8 were denied** by real-output-gap watchdogs. This is **DENY**,
not a successful gerbil test time. No assertion or watchdog was relaxed. Tests
remain unqualified and production admission remains false.

The selected-toolchain validator now reads one physical binary once after checking
all four tool aliases and rejects mutation during hashing. That is harness overhead
reduction, not evidence that Gambit eliminated the remaining test stalls.

## Verification

```sh
python3 patches/gerbil-v19-darwin/tests/verify_reader_batch_50_baseline.py
```

This checks the original frozen parent as well as the new cold anchor. Retained
local reports are required; the JSON uses project-relative paths only.
