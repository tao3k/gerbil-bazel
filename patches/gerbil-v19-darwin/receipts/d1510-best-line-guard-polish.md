# Best-Line Guard Polish

## Review

Correct path: preserve the whole-consumer measured stack and its safety fix,
not a faster component's timing. Existing research is not repeated. Worthwhile:
identity-only verification previously left the selected GSC and numerical gates
unchecked. Expected new speed gain is zero; this change prevents false admission.

## Frozen Bundles

| Bundle | First compile (s) | Three cold builds (s) | Complete tests |
| --- | --- | --- | --- |
| Original five-patch reference | 4.049 / 4.044 / 4.004 | 37.365 / 37.406 / 36.467 | 87.409 s, 39 files, 965 cases |
| Six-patch safety candidate, including 0026 | 4.038 / 3.980 / 3.950 | 36.414 / 35.552 / 37.770 | 86.924 s, 39 files, 965 cases |

These are retained real measurements, not new timings from this polish.
The five-patch helper has a reproduced C-input race; it remains a reference,
not a safe general release. Keep the six-patch candidate separate. Its MCP
qualification is three cold builds plus one complete test pass, not repeated
full-test stability or complete ASCENT qualification. Neither bundle includes
experimental 0027/0028/0029 or package-specific business changes.

All measured patch, runtime and evidence hashes remain unchanged. The active
whole-task limits stay **4.5 s first compile / 42 s build / 97 s test**.
Never average a failing run into a passing result or widen these gates.

## Verification

The shared checker now optionally verifies the actual regular GSC binary and
each retained cold sample against the content-locked policy. It rejects a
missing policy, changed ceilings, non-finite or boolean timings, fewer than
three cold runs, an over-limit individual run and incomplete file/case inventory.
Replay requires the performance preflight before creating its fresh fixture.
This offline Python check does not supervise native build/test execution.

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/patch_lock.py \
  patches/gerbil-v19-darwin/receipts/d1510-static-c-snapshot-patch-lock.json \
  --driver .data/d1510-static-c-snapshot-mcp-driver-v1/bin \
  --runtime .data/d1510-reader-whitespace-native-v2 \
  --gsc .data/d1391-runtime-object-source/build/bin/gsc \
  --evidence-root . --performance
```

Result: `PATCH-LOCK-OK patches=6 driver=True runtime=True evidence=True gsc=True performance=True`.
The original five-patch identity/evidence/performance check also passes.
Focused patch-lock and measured-stack regression checks: **57 passed**.
New negative controls include changed/symlinked GSC, first-log/build/test
regression, invalid timings, partial tests and widened policy.
The broader lock, source-preparation and native-receipt suite passes **71 checks**.
`.data/d1510-best-line-guard-replay-v1` passes actual five-patch reversal,
deletion, reapplication and exact source/helper parity. Applying 0026 in the
fresh `.data/d1510-best-line-guard-snapshot-replay-v1` then reproduces the
qualified six-patch helper byte for byte. These are reconstruction checks,
not newly timed whole-package runs.

## Experimental Boundary

The latest isolated entry-role ASCENT cold preparation completed at
119.35 s (310.89 user / 94.38 system), exit 0, with 30 positive-plan Cases and
final `OK`. Its private receipt is
`.data/d1510-closed-entry-role-ascent-receipt-v1`. This is not all 94 Suites,
not a matched package speedup, and not permission to change either frozen bundle.
No latest-staging release rebuild or GitHub delivery is claimed here.
