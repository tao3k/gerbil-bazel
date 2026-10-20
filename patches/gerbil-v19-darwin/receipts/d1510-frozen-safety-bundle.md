# Frozen Safety Bundle

## Review

Correct path: preserve the measured common Darwin implementation and its C-input
safety fix, not MCP-specific business behavior. The optimization and safety work
have already been explored and qualified for MCP. No experiments are added here.
Worthwhile polish: one reconstruction entry point now validates the six-patch
bundle, including the selected GSC, instead of requiring a separate manual safety
patch application. Expected extra speed benefit is zero; the benefit is avoiding
accidental substitutions and regressions.

## Preserved Measurements

| Metric | Five-patch reference | Six-patch safety candidate |
| --- | --- | --- |
| First compile log (s) | 4.049 / 4.044 / 4.004 | 4.038 / 3.980 / 3.950 |
| Complete cold build (s) | 37.365 / 37.406 / 36.467 | 36.414 / 35.552 / 37.770 |
| Complete test (s) | 87.409 | 86.924 |
| Correctness | 39 files, 965 cases | 39 files, 965 cases |

These are retained measurements, not fresh timings from this packaging change.
Each bundle has three cold builds and one complete test sample. All three active
whole-task limits remain **4.5 / 42 / 97 seconds**. A failed individual sample
cannot be averaged away. The original helper's confirmed C-input race prevents
general release admission; the six-patch bundle includes its 0026 correction.
Complete ASCENT qualification and general release admission remain pending.

The six-patch application order is frozen in
[`static-c-snapshot-candidate.series`](../static-c-snapshot-candidate.series).
The [content lock](d1510-static-c-snapshot-patch-lock.json) preserves the actual
patch, helper, runtime, GSC and raw measurement identities. None of those bytes,
the historical measurements or performance ceilings changed in this polish.
Experimental 0027 and later remain outside this bundle.

## Reconstruction

Run from the repository root with a fresh output directory. The source fixture
must contain the complete previously composed six-patch source, not only its
helper file. The output is an isolated Git root; reversal must remove the three
patch-created files before forward application and exact source/helper parity.

```sh
bash patches/gerbil-v19-darwin/tests/check_mcp_v4_patch_replay.sh \
  "$PWD/.data/d1510-frozen-safety-source-v1" \
  "$PWD/.data/d1510-static-c-snapshot-mcp-driver-v1/bin" \
  "$PWD/.data/d1510-frozen-safety-bundle-replay-v3" \
  "$PWD/.data/d1510-reader-whitespace-native-v2" \
  "$PWD" snapshot "$PWD/.data/d1391-runtime-object-source/build/bin/gsc"
```

Results: `PATCH-LOCK-OK patches=6 driver=True runtime=True evidence=True
gsc=True performance=True` and `STATIC-SNAPSHOT-PATCH-REPLAY-OK`.
Replay receipts contain relative identities, not personal absolute paths.
The first two local attempts selected incomplete source fixtures and failed;
they are not counted as successful replays. The v3 receipt above passes.

Unknown bundle selections and a snapshot selection without GSC fail before
creating output. Raw evidence or GSC drift also fails before creating output.
The focused lock and replay-preflight suite passes **71 checks**; Bash syntax
validation passes. The original five-patch lock still passes its retained
driver/runtime/raw-evidence/performance checks. It does not contain a GSC identity,
so requesting that additional check correctly rejects it rather than inventing
an identity or modifying the historical lock.
This is patch reconstruction and regression protection, not a new consumer
benchmark, full latest-staging rebuild or GitHub delivery claim.

## Receipt Polish

The existing `--performance` verification now prints each retained cold sample,
the complete test duration and inventory, and the three fixed ceilings after
successful validation. Output explicitly says `not-a-new-benchmark`; identity-only
verification does not print performance admission. No patch, runtime, helper,
historical evidence, or gate identity changes. The same reconstruction command
therefore shows the preserved results without requiring a second report script.

Current verification: the same command with fresh output
`.data/d1510-frozen-safety-bundle-replay-v4` passes the actual six-patch reverse /
forward reconstruction, exact source/helper parity, selected driver/runtime/GSC
identities, original raw report identities, and retained performance validation.
The lock, replay-preflight and summary tests pass **74 checks**. Bash syntax
validation also passes. This does not add a new build or full-test sample.

## Fail-Closed Inventory Polish

Complete-test admission now requires positive integer file, case and passing-run
counts. Boolean, fractional and non-finite counts are rejected. An explicit
`passed` field must be the boolean `true`, not a string, null or numeric value.
Historical receipts without this optional field retain their locked inventory
and evidence checks; their contents are not rewritten.

The focused lock, replay-preflight and summary suite passes **83 checks**,
including nine new malformed-receipt rejection controls. Actual six-patch
reverse / forward replay at `.data/d1510-frozen-safety-bundle-replay-v5` passes
with exact source/helper parity, selected driver/runtime/GSC identities and
original raw-evidence digests. All retained samples pass **4.5 / 42 / 97 seconds**.
No measured patch bytes, compiler flags, toolchain or timing receipts changed.
This is regression-protection polish, not new timing evidence or GitHub delivery.

## Frozen Admission Contract

`tests/test_frozen_safety_bundle.py` now pins the exact six-patch order,
the **4.5 / 42 / 97 second** ceilings, three cold samples, and the complete
**39-file / 965-case** test inventory. It also requires the explicit admission
boundary: MCP qualified, opt-in only, full ASCENT and general release still
unqualified. A new experimental patch, relaxed ceiling or inflated release
claim must not silently redefine this baseline.

Current focused validation passes **86 checks**. Actual reverse / forward replay
at `.data/d1510-frozen-safety-bundle-replay-v6` passes source and measured-helper
byte parity, selected runtime / driver / GSC identities and original report
digests. Bash syntax and scoped whitespace checks pass. The retained timings
above remain unchanged; this validation is not another cold build or full test.

To rerun the frozen contract from the repository root:

```sh
python3 -m pytest -q \
  patches/gerbil-v19-darwin/tests/test_patch_lock.py \
  patches/gerbil-v19-darwin/tests/test_mcp_v4_patch_lock.py \
  patches/gerbil-v19-darwin/tests/test_mcp_v4_replay_preflight.py \
  patches/gerbil-v19-darwin/tests/test_frozen_performance_summary.py \
  patches/gerbil-v19-darwin/tests/test_frozen_safety_bundle.py
```

Polish is kept in the admission checks and receipts, not folded into the
measured implementation patches. Behavioral changes require a separate series
and fresh whole-consumer correctness and performance evidence before promotion.

## Complete Receipt Identity

The frozen contract now pins the SHA256 of the entire six-patch identity receipt:
`a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2`.
This catches edits to retained timings, tool identities, evidence references or
admission scope even when the measured patches and performance ceilings remain
unchanged. A new qualification must use a separate receipt, not overwrite this
checkpoint. Expected runtime benefit from this packaging change is zero.

Current validation: **98 focused checks pass**. Actual reverse / forward replay
at `.data/d1510-frozen-safety-bundle-replay-v9` passes all six patches, exact
source/helper parity, selected driver/runtime/GSC identities, original raw
evidence identities and all retained per-sample performance gates. No measured
patch or lock bytes changed; no new build/test timing or GitHub delivery is
claimed. Experimental member-cache and tool-snapshot work remain excluded.

The real six-patch bundle is also copied into an isolated temporary fixture for
negative controls. Changed patch bytes, a missing safety patch, reordered
patches, an appended experimental patch, changed digest-helper source and
changed receipt bytes must all be rejected. The unchanged copy must pass. These
checks do not mutate the frozen originals or reinterpret component performance
as complete-package admission.

Four additional negative controls reject unqualified selected driver, runtime,
GSC and raw evidence bytes against the actual frozen lock. They do not manufacture
a new tool identity or copy large native images into test fixtures. The live v9
replay separately checks the unchanged real selected tools and evidence. No
measured implementation, lock, gate or timing was changed by this polish.

## Reconstruction Receipt Pin

The `snapshot` reconstruction entry point now checks the entire qualification
receipt against its frozen SHA256 **before parsing or creating a fixture**.
Previously the complete-receipt pin was enforced by the regression suite only;
direct reconstruction checked the identities declared inside the receipt.
Changing those declarations must not silently select a different baseline.
The generic verifier exposes `--lock-sha256` for this check. The historical
five-patch path is unchanged.

Review: this is the existing proven preservation path, not another performance
experiment. Expected extra runtime gain is zero. Implementation patch bytes,
compiler flags, tool identities, timings and admission limits remain unchanged.

Validation: **100 focused tests pass**. The added negative control changes the
receipt after pinning it and confirms rejection before any output directory is
created. An invalid JSON replacement is rejected by its digest before parsing.
Actual six-patch reverse / forward reconstruction at
`.data/d1510-frozen-safety-bundle-replay-receipt-pin-v1` passes with source/helper
byte parity, selected driver/runtime/GSC identities and original evidence bytes.
Bash syntax validation passes. Retained results remain **3.950-4.038 seconds
first log, 35.552-37.770 seconds complete cold build, and 86.924 seconds complete
test with 39/39 files and 965/965 cases**. Limits remain **4.5 / 42 / 97 seconds**.
These are not new timing samples, complete ASCENT admission or GitHub delivery.
