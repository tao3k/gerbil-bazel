# Frozen Darwin Static Snapshot Bundle

## Retained Complete MCP Results

| Sample | First compile log | Complete clean build |
| --- | ---: | ---: |
| 1 | 4.038430 s | 36.414237 s |
| 2 | 3.980393 s | 35.551924 s |
| 3 | 3.950160 s | 37.770491 s |

Complete tests: **86.924285 seconds, 39/39 files and 965/965 cases passing**.
There are three cold builds and **one** complete test run, not three test runs.
Whole-task ceilings are **4.5 / 42 / 97 seconds**, checked per sample without
averaging. These are retained local results, not fresh timings from packaging
or the GitHub runner.

## Composition And Configuration

`static-c-snapshot-candidate.series` freezes 0014, 0015, 0019, 0020, 0021 and
0026, in that order. 0026 binds GCC preprocessing to a private C snapshot and
closes the reproduced transient C-input race in the historical five-patch
reference. The implementation bytes and original timing evidence are unchanged.
No MCP-specific business code, scheduling changes or later experimental patches
are included. General release and complete ASCENT performance remain unqualified.

The entire receipt is pinned to SHA256
`a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2`.
It binds patch order/bytes, GNU helper and digest backend, actual measured
runtime/GSC, original raw evidence references and complete test inventory.
Malformed counts, changed tools, weakened limits and experimental contamination
are rejected. The historical five-patch receipt remains separate.

Consumer activation is **opt-in**: `GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1`, genuine
Darwin GNU GCC, with the locked reader-whitespace runtime prerequisite. This
series is a driver extension, not a complete recipe for regenerating every
embedded native-runtime optimization. The measured Single-VM MCP binary must
not be substituted into the independent Multiple-VM ASCENT profile.

## GitHub Compilation Scope

The existing source-toolchain CI now validates the locked six-patch series and
applies it on Darwin after configure. Dependent patches are prechecked in
composition and reversed before configure; each patch is no longer incorrectly
tested against an unpatched tree. All patch bytes participate in the source
cache identity. Linux patch selection remains unchanged.

CI builds the selected GNU-GCC, Multiple-VM staging source toolchain and verifies
the installed snapshot helper/native digest backend. It runs the frozen receipt
regressions plus actual source-built object parity, option/header invalidation,
tamper, failure and concurrent publication controls. The build itself does not
globally enable experimental reuse or invoke the release workflow.

The upstream `v0.19-staging` reference was checked at delivery and matches the
existing CI pin `1cfb032c7a1612637da6205f5f8a15683eba3ba0`. Its Gambit pin is
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. This source-construction CI is
**not** reproduction of the measured embedded MCP runtime, a new 35-second
MCP qualification, or full ASCENT admission. CI does not possess the local
raw timing artifacts; its retained-contract tests are labeled accordingly.

## Local Packaging Checks

The clean delivery checkout passes **100 frozen-contract tests** and **ten
source-provisioning tests**. The actual selected Multiple-VM toolchain passes
the same eight object contracts used by the new Darwin CI step. The original
frozen MCP driver/runtime/GSC/raw evidence/performance check passes separately.
No new whole-consumer timing is claimed by these packaging checks.

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-static-c-snapshot-patch-lock.json \
  --lock-sha256 a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2 \
  --performance
```

This command validates portable patch/receipt metadata and prints retained
samples. Add explicit selected `--driver`, `--runtime`, `--gsc` and
`--evidence-root` paths to verify the original local executable/raw identities.
