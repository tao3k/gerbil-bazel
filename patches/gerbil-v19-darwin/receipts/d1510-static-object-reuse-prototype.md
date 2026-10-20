# Darwin Static Object Reuse Prototype

## Review Before Implementation

- Alignment: real static-object compilation after repeated identical C generation.
- Prior work: 0007 covers current-process runtime C producers; this opt-in
  prototype covers an object requested again after C regeneration. It does
  not revive metadata-empty driver probes or interpreter memoization.
- Worth investigating: ASCENT's existing entry cache-miss log has 74 actual
  object calls. That count alone does not prove redundant compilation.
- Expected benefit: incremental/new-entry object calls may avoid native
  compilation. No large true-cold or test-body improvement is assumed.

## Actual Candidate

The isolated v2 driver is based on the retained 0015 shell-substitution driver.
Only the obj branch is opt-in through GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1.
The exact tested helper is frozen in experimental patch 0019. It remains
default-off and is not admitted to the production release patch list.

Candidate driver SHA256:
`d9d537df086e1e40fcd78f0f0713cdd16df71b4101f459bf6b6625c9c2e67779`.
Candidate helper SHA256:
`3d1bb8a18485910711042871d5cf2d78bffef8ff98df66f263091603e075db18`.

Without an existing eligible object, the original object command executes.
With an existing object, the actual GNU compiler preprocesses the source.
The prototype binds preprocessor bytes, original effective object command,
working directory, conservative environment and the content of GCC, cc1,
assembler, Apple assembler, GSC, driver and helper. An object-content digest
must also match the published proof. A miss compiles the private preprocessed
snapshot, checks source content again, then publishes the object and proof.
No source timestamps are manufactured. Unsupported auxiliary-output options
fall back to the original command. Same-output helper writers serialize via
a bounded owned lock; failed preprocessing/compilation leaves old object and
proof intact. This is not a complete arbitrary-wrapper/specs/plugin contract.

The first implementation contract incorrectly required both concurrent
requests to hit; one conservatively missed and the other hit. Both produced
the correct object. That incomplete v1 receipt remains. The corrected v2
requires both successful valid HIT/MISS outcomes, at least one hit, and
byte-identical final object, without changing the lock bound or workload.

## Completed Local Controls

check_static_object_reuse.sh runs the original native Scheme compiler directly,
not a Python-supervised ASCENT runner. Its native contracts include:

1. Real ASCENT generated C: private preprocessed compile is byte-identical to
   the retained original native object.
2. Repeated original input: actual object reuse hit.
3. Changed -O2 option: miss and byte parity with the original -O2 command.
4. Tampered output object: miss and correct original-object reconstruction.
5. Concurrent same-target calls: both succeed; correct final native object.
6. Local header initially matches and hits, then a changed header causes miss.
7. Changed-header output matches the original compiler's output.
8. Invalid C compilation fails without changing old object/proof; lock cleaned.

Final control marker: STATIC-OBJECT-REUSE-OK 8.
Output: .data/d1510-static-reuse-contract-v2.
Focused Python/framework tests: 32 passed. These tests are not either
consumer's complete semantic or performance admission.

## Real MCP Cold Gate

The initial cold-v1 attempt failed hardware discovery under sandbox restrictions
before any workload. cold-v2 used the permitted Darwin discovery boundary and
completed the actual cold MCP clone/clean/build with 12 hardware-derived workers.

| Metric | Historical Frozen Baseline | Candidate Cold-v2 |
| --- | --- | --- |
| First compile | 4.851 / 4.574 / 4.593 s | 4.269718 s |
| Complete build | 47.772 / 47.824 / 47.927 s | 40.042297 s |
| Complete tests | Historical 105.751 s, 39 files / 965 cases | 91.039574 s, 39 files / 965 cases, all passed |

Cold-v2 passed the existing first-5/build-50 gates, exit zero and source identity
checks. The frozen runtime binary hash is unchanged. The cold build logged no
static-object cache HIT or MISS. Therefore the 40.042-second cold result is a
passing non-regression observation, not proof of a candidate speedup versus
the historical baseline. No matched unchanged control was run in this turn.
Raw cold-v2 predates the explicit opt-in field added to future framework
reports and has not been rewritten or backfilled.

Full tests use the exact cold-built MCP artifact, selected-toolchain fixture
patch, v2 driver and enabled opt-in, under whole-task first-5/test-112 gates.
No per-file silence gate or diagnostic extension is used. The complete run
exited zero, qualified all 39 files and 965 cases, and verified each file's
final OK and expected inventory. Test first output was 2.281771 seconds.
Raw receipt: .data/d1510-static-reuse-mcp-tests-v1/report.json.

## Frozen Checkpoint

0019-gambit-darwin-static-object-reuse-candidate.patch contains the exact
tested v2 helper, opt-in driver branch, and source/build/install wiring.
The adjacent d1510-static-object-reuse-40-checkpoint.json records all three
gates, observed timings, source hashes and raw receipt hashes without personal
absolute paths. Patch application is checked against the retained Gambit
source, including sequential application after 0014 and 0015 in an isolated
fixture. The installed helper bytes match the tested v2 helper, and shell
syntax validation passes. The local observation improves on the three historical build samples
by approximately 16.2%; that comparison is not causal attribution.

Repeated cold qualification, hardening of the experimental helper, and the
six isolated ASCENT scenarios remain required before production admission.
