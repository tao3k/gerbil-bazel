# Frozen V4 Patch Packaging And Polish

The best MCP measurements remain unchanged: first compile 4.003500–4.049027
seconds; three complete cold builds 37.365152 / 37.406373 / 36.466995 seconds;
one complete test pass 87.409175 seconds, 39 files and 965 cases.

`mcp-v4-driver.series` records the exact driver extension order
0014 / 0015 / 0019 / 0020 / 0021. `d1510-mcp-v4-patch-lock.json` binds every
patch digest, measured helper and native digest source, the runtime prerequisite
and active performance policy. It excludes the generated-C dispatcher prototype
and unrelated consumer changes. Existing patch bytes were not modified.

Current performance ceilings are 4.5 / 42 / 97 seconds, following the latest
about-ten-percent policy with upward rounding. Historical receipts are immutable.
The later 99.545633-second complete test is a correctness pass but fails the
current performance gate. This packaging is not a claim of repeated test stability
or generic ASCENT performance admission.

## Native Replay And Safety

Private receipt `.data/d1510-mcp-v4-patch-replay-polish-v1`:

- Copy only five source files from the existing owned composition fixture.
- Reverse all five patches, then check and apply them in declared order.
- Compare all five resulting files with the frozen source fixture.
- Compare the installed helper with the actually measured v4 helper and native
  digest C with its tracked test source.
- Result: `MCP-V4-PATCH-REPLAY-OK`, exact byte parity.

`.data/d1510-mcp-v4-toolchain-polish-v1`: all five native toolchain controls pass.
`.data/d1510-mcp-v4-safety-polish-v1`: all six native safety controls pass.
Patch identity, preparation, cold watchdog and full-test admission unit suite:
47 tests pass.

Follow-up polish replay `.data/d1510-mcp-v4-patch-replay-polish-v2` also
passes exact source and measured-helper byte parity. The focused suite now
passes 50 tests. Additional checks bind the runtime prerequisite and native
digest source to the measured stack, preserve every cold sample and raw receipt
digest, require all 39 files / 965 cases, and derive the active ceilings from
the maximum recorded baseline with ten-percent upward rounding. Patch bytes
remain unchanged. These checks are packaging regression controls, not a new
timed MCP build or complete test run.

Preparation polish selects the frozen hardened v3 shell helper automatically
when native digests are requested. A regression test checks that transformation
produces the exact measured v4 helper digest. Non-native preparation retains its
previous default; explicit helper selection still wins. An invalid generated-C
preparation request now fails before creating its output directory.

## Rejected New Prototype Kept Separate

`.data/d1510-generated-c-mcp-entry-trace-v1` remains diagnostic-only and DENY.
First log was 4.194709 seconds; the complete-build watchdog stopped it at
42.023055 seconds, with child reaping confirmed. Its trace contains 447 GSC
entries over the whole observed build, not timestamped pre-first-log attribution.
Complete build/test times are unknown. It is not added to the measured patch
series and cannot inherit the baseline's performance claim.

## Fail-Closed Replay Preflight

The patch lock now also records the measured `gambuild-C`, shell helper and
native digest executable identities. Replay checks patch order and every patch
and driver digest before creating its output directory. Missing files, symlinks,
changed bytes and path traversal are rejected. The checker is a reusable
framework module; it has no MCP package paths or business logic.

`.data/d1510-mcp-v4-patch-replay-polish-v3` passes both `PATCH-LOCK-OK` and
`MCP-V4-PATCH-REPLAY-OK`, including exact source and measured-helper byte parity.
The focused patch-lock, progressive-gate and complete-test admission suite passes
31 tests. The retained raw cold/test report hashes also still match the locked
checkpoint. This is a packaging check, not a newly timed build or test run.
All five patch bytes, the runtime and the three performance ceilings are unchanged.

## Delivery Boundary

### Replay Correction

The v1/v2/v3 replay assertions did not establish that `git apply` performed its
edits: when invoked inside this repository's ignored `.data` subdirectory, Git
could silently skip patch paths outside its current repository-relative prefix.
Their byte comparisons remain comparisons, not proof of reverse/apply execution.
The previously stronger replay claim is withdrawn.

The replay checker now initializes a separate Git root in its fresh owned source
fixture. `.data/d1510-mcp-v4-patch-replay-polish-v4` passes actual reverse/apply.
v5 additionally requires all three patch-created files to be absent after
reversal, before applying the five patches again. It passes exact reconstructed
source and measured-helper parity. No frozen patch/runtime bytes changed.

### Current Packaging Verification

The latest replay is `.data/d1510-mcp-v4-patch-replay-polish-v6`. It passes
the content-lock preflight, actual reverse deletion, forward application and
exact source/helper parity. Its `identity.log` contains only relative patch and
source names, not personal absolute paths. This changes receipt formatting only;
all five locked patch digests remain unchanged.

The focused patch-lock, three-time-gate and progressive-controller suite passes
44 tests. Both retained raw report digests and the measured Gerbil binary digest
were rechecked against the locks and still match. No new timed MCP run is claimed.

Reviewable bundle:

- `mcp-v4-driver.series`: exact five-patch application order.
- `receipts/d1510-mcp-v4-patch-lock.json`: patch and measured driver identities.
- `receipts/d1510-mcp-v4-performance-lock.json`: measured samples, correctness
  counts and active 4.5 / 42 / 97-second ceilings.
- `tests/check_mcp_v4_patch_replay.sh`: isolated source reconstruction.
- `tests/experiment_framework/patch_lock.py`: reusable identity verification.

Run the identity check from the repository root:

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-mcp-v4-patch-lock.json \
  --driver .data/d1510-static-reuse-driver-v4/bin
```

Changed patch bytes require a separately identified candidate and new complete
consumer qualification; updating hashes alone does not admit a change.
Experimental 0022 and native generated-C work stay outside this bundle.

No global installation, active ASCENT checkout or shared dependency was changed.
No complete latest-staging toolchain rebuild, commit or push is claimed by this
receipt. The runtime prerequisite and remaining full-consumer gates are retained
explicitly rather than hidden by a merged or default-enabled patch.

## Linked Evidence Lock Polish

The identity preflight now checks the content digests of all three referenced
receipts (runtime prerequisite, measured checkpoint and active performance
policy), plus the native digest C source. This closes a packaging gap: previously
their consistency was checked by unit tests, but not by the replay preflight.
The generic verifier rejects changed or missing bytes, symlinks and parent-path
references. Optional evidence maps preserve compatibility with unrelated locks.

The focused patch-lock, three-time-gate and progressive-controller suite passes
55 tests. `.data/d1510-mcp-v4-patch-replay-polish-v8` passes actual reverse/delete,
forward application and exact source/measured-helper parity. The preceding v7
attempt selected a source tree without the composed helper; it failed copying
that prerequisite and is not counted as a replay pass.

All five optimization patch digests, measured driver identities, historical
samples and 4.5 / 42 / 97-second ceilings are unchanged. Experimental 0022–0024
remain excluded. This is packaging qualification only: no new timed package
run, repeated full-test stability, latest-staging rebuild or GitHub delivery is
claimed.

## Selected Runtime Identity Polish

The frozen lock now binds the actual measured Gerbil executable through
`runtimeFiles`. Replay requires the runtime directory as its fourth argument,
and rejects missing, changed or symlinked runtime files before creating output.
The generic verifier exposes the same check through `--runtime`; supplying a
runtime without a locked runtime identity is DENY. Identity is not a new timing
or correctness qualification.

Review before changing code: this is the correct packaging boundary because
patch identity alone cannot establish which runtime was selected. Earlier
preflight verified the prerequisite receipt, not the executable itself. The
change is worthwhile for preventing accidental baseline substitution; expected
speed improvement is zero. All five optimization patch bytes remain unchanged.

Verification: `.data/d1510-mcp-v4-patch-replay-runtime-lock-v1` passes runtime
and driver identity, actual reverse/delete and forward application, and exact
source/helper parity. The focused identity, three-time-gate and progressive
controller suite passes 75 tests. Both original raw cold/test report hashes
still match the performance lock. No new timed consumer run or GitHub delivery
is claimed.

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-mcp-v4-patch-lock.json \
  --driver .data/d1510-static-reuse-driver-v4/bin \
  --runtime .data/d1510-reader-whitespace-native-v2
```

## Raw Measurement Preservation

The generic identity verifier now supports optional `rawEvidenceFiles` and
`--evidence-root`. The frozen MCP lock records the two original complete
measurement reports, matching the immutable checkpoint hashes. Verification
rejects changed or missing reports, symlinks in the report path, absolute paths,
parent traversal and noncanonical separators. Unrelated locks remain compatible.

Review: this preserves the correct measured baseline; previous checks bound
summary receipts but required a separate manual raw-report check. It is worth
automating to prevent accidental evidence substitution. Expected performance
gain is zero. No optimization patch, selected runtime, recorded sample or
performance ceiling was changed. No MCP-specific logic was added to the verifier.

Focused identity, policy and progressive-controller checks: **87 passed**.
The actual measured driver, runtime and both raw reports pass together:

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-mcp-v4-patch-lock.json \
  --driver .data/d1510-static-reuse-driver-v4/bin \
  --runtime .data/d1510-reader-whitespace-native-v2 \
  --evidence-root .
```

Result: `PATCH-LOCK-OK patches=5 driver=True runtime=True evidence=True`.
Independent replay `.data/d1510-mcp-v4-patch-replay-evidence-polish-v1` also
passes actual reverse/delete, forward application and exact measured source
and helper parity (`MCP-V4-PATCH-REPLAY-OK`). Replay itself checks patch/driver/
runtime identity; the separate CLI above checks raw measurement identity.
This polish adds regression controls, not a new timed consumer run or a GitHub
delivery claim. The later failed performance samples remain DENY.

## Unified Replay Preflight

Replay now checks the two raw measurement reports as part of its mandatory
preflight, not as a separate optional manual command. The evidence root defaults
to the repository root, independent of the caller's working directory; a fifth
argument can select a preserved evidence root. Missing, changed or symlinked
reports fail before creating replay output. No patch, runtime, lock or gate
bytes were changed.

Review: this is the correct preservation boundary; the generic evidence checker
already existed, but replay did not invoke it. Integrating it prevents accidental
baseline substitution. Expected speed gain is zero. Five new shell-preflight
controls and the existing identity/policy/controller controls pass: **92 tests**.

Actual isolated replay `.data/d1510-mcp-v4-patch-replay-full-lock-v1` passes:

```sh
bash patches/gerbil-v19-darwin/tests/check_mcp_v4_patch_replay.sh \
  "$PWD/.data/d1510-mcp-v4-patch-replay-evidence-polish-v1/source" \
  "$PWD/.data/d1510-static-reuse-driver-v4/bin" \
  "$PWD/.data/d1510-mcp-v4-patch-replay-full-lock-v1" \
  "$PWD/.data/d1510-reader-whitespace-native-v2"
```

Results: `PATCH-LOCK-OK patches=5 driver=True runtime=True evidence=True` and
`MCP-V4-PATCH-REPLAY-OK`. The output path must be fresh on each replay.

The separate [C-input race receipt](d1510-static-source-aba.md) is a confirmed
release blocker in the frozen helper. Exact packaging parity preserves a measured
reference; it does not establish correctness under that mutation. A replacement
cannot inherit the old benchmark or be silently added to the frozen series.
