# Static C Snapshot Safety Candidate

## Review

0026 fixes the reproduced C/GCC input race, distinct from 0025's Scheme reader.
Worthwhile because it prevents a wrong object; expected speed gain is zero.
It is a safety prerequisite, not a substitute for closed-set reuse optimization.
Apply after 0021. Keep it outside the five-patch frozen series until fresh
full-consumer admission. MCP ceilings remain 4.5 / 42 / 97 seconds.

## Implementation And Limits

GCC reads a private same-directory snapshot. A line directive and GNU macro
prefix map preserve logical names; source timestamps are preserved. Normalize
only synthetic main-input markers. Retain source/tool/options/environment/
object/proof guards and clean private inputs/work/locks. Existing Darwin and
default-off gates remain. Linux executes the original command before this work.

Rejected variants: relocated C plus `-iquote .` changed header filename macros;
an empty quote path lost header lookup. The frozen V4 helper also fails debug
object parity in `.data/d1510-static-c-v4-semantics-control-v1`. Therefore `-g*`
and explicit prefix-map options use the original uncached command with exact
byte/diagnostic parity tests. Transitive headers are not snapshotted. No full
immutable-header-closure guarantee or debug-option speedup is claimed.

- Patch SHA-256: `6149c542c8f1bb2409f3ad82ed396cb969800fbab5031a4c6e3d5e41707af971`.
- Helper SHA-256: `3b6b040aebcc87fcb4b3ab39907f82214c7ea55c6602ac1316128b3d06f38a4b`.
- `.data/d1510-static-c-snapshot-patch-replay-v1` reproduces exact helper bytes;
  preparation rejects a non-frozen base helper.

## Native Evidence

Matching ASCENT Multiple VM GSC/headers and genuine GNU GCC; terminal exit 0:

| `.data/` receipt | Evidence |
| --- | --- |
| `d1510-static-source-aba-protected-v4` | Restored-source race blocked, return 17, exact ordinary-object parity |
| `d1510-static-c-snapshot-semantics-v6` | Relative headers, filename/base/short-name macros, 2020 timestamp, line/include levels, debug/prefix-map fallback parity |
| `d1510-static-c-snapshot-object-controls-v1` | 8 real C/options/tamper/concurrency/header/failure controls |
| `d1510-static-c-snapshot-identity-controls-v1` | 3 source/helper/driver controls |
| `d1510-static-c-snapshot-safety-controls-v1` | 6 compiler/proof/warning/mid-flight mutation controls |
| `d1510-static-c-snapshot-tool-controls-v1` | 5 toolchain/platform/options controls |

Protected object/control digest:
`63bdabdf011323e437e0e25485d3406aef3b5de4b0e73159a3bfae76bf3e3d0b`.
Two early fixtures failed patch parsing before native execution; rejected
semantic variants are not passing samples.

## Real ASCENT Cases

COW workspace `.data/d1510-static-c-snapshot-ascent-v1` copies the frozen
project/toolchain/dependencies, uses private actual GNU GCC, and stays clean at
`21e3638687d42ecfc36acebb28991987435ebc60`. Direct Bash runs the consumer's own
`just test-native t/qualification/ascent-positive-plan-test.ss`, with 12 host
build cores and the existing 135-second component cap. No Python supervision.

| Receipt suffix | Complete | User / System | Correctness | Objects |
| --- | ---: | ---: | --- | --- |
| `ascent-receipt-v1` | 77.73 s | 107.73 / 41.38 s | 30/30, final OK, exit 0 | 72 MISS, 0 HIT |
| `ascent-receipt-v2` | 7.70 s | 6.47 / 2.31 s | 30/30, final OK, exit 0 | Entry HIT, no object calls |

Receipt prefix: `.data/d1510-static-c-snapshot-`. Offline extraction:
`d1510-static-c-snapshot-ascent-cases.json`. Original checkout remains clean;
original helper remains frozen, installed GCC equals the unchanged private copy.
These are positive-plan Cases, not all 94 Suites or package-cold performance.
The MCP follow-up below now passes its complete gates. Full ASCENT closure
performance and general release admission remain pending; no acceleration is
claimed and this patch cannot inherit old measured timings.

## Complete MCP Follow-Up

Fresh driver `.data/d1510-static-c-snapshot-mcp-driver-v1/bin` uses the same
candidate helper and the frozen MCP GSC, driver, digest backend and runtime.
The existing progressive framework performs real `gerbil clean`, verifies no
project native images remain, builds each fresh clone, then tests the first
exact cold-built artifact using the approved selected-toolchain fixture patch.
No new timing loop, MCP business changes or standard-library overlays were added.

| Metric | Frozen V4 reference | Snapshot candidate |
| --- | --- | --- |
| First compile | 4.049 / 4.044 / 4.004 s | 4.038430 / 3.980393 / 3.950160 s |
| Three complete cold builds | 37.365 / 37.406 / 36.467 s | 36.414237 / 35.551924 / 37.770491 s |
| Complete tests | 87.409 s, 39 files, 965 cases | 86.924285 s, 39/39 files, 965/965 cases |

All candidate source, exit, final-OK and exact Case inventory checks pass. Test
first output is 1.850754 seconds. Each cold task meets 4.5 / 42 seconds; the
complete test meets 97 seconds. Whole-task gates only: no per-file silence kill.
This is one complete test sample, not proof of three-repeat test stability.
All cold logs contain zero static-object HIT/MISS events, so these timings do
not establish a causal speed gain from 0026 or general static-object reuse.

Raw receipt root: `.data/d1510-static-c-snapshot-mcp-qualification-v2`.
Its `progressive-admission.json` records cold ALLOW, test ALLOW and qualified true.
The v1 launch failed before any build because sandboxed Darwin memory discovery
was denied; it is not a timing sample. V2 ran with that permission restriction
removed, unchanged configuration and the same hard gates.

The separate `static-c-snapshot-candidate.series` and
`d1510-static-c-snapshot-patch-lock.json` bind six patch digests, selected driver/
helper/digest/runtime, frozen policy and all three raw MCP reports. The original
five-patch lock remains unchanged. Candidate identities still match after the
run; the generic verifier reports six patches and driver/runtime/evidence true:

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-static-c-snapshot-patch-lock.json \
  --driver .data/d1510-static-c-snapshot-mcp-driver-v1/bin \
  --runtime .data/d1510-reader-whitespace-native-v2 --evidence-root .
```

Focused lock/policy/native-receipt checks: 64 passed. The new regression check
keeps the original five patch hashes, runtime, policy and partial-ASCENT admission
boundary intact. No GitHub delivery or latest-staging rebuild is claimed.
