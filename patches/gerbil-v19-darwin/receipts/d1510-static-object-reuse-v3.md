# Static Object Reuse v3

## Admission Review

- Alignment: qualify generic static-closure object reuse, not package-specific logic.
- Prior work: v2 freezes the observed 40-second MCP run; v3 adds previously
  unverified digest, publication, diagnostics and mid-flight identity contracts.
- Worth doing: an accepted object cache must preserve compiler diagnostics and
  reject changed inputs even when compilation itself succeeds.
- Expected benefit: avoiding repeated native compilation remains the intended
  gain. These correctness changes do not promise a true-cold speedup.

## Candidate

0020-gambit-darwin-static-object-reuse-hardening.patch applies after 0019.
It remains opt-in and absent from the production release patch list.
Candidate output: .data/d1510-static-reuse-driver-v3/bin.
Frozen v2 helper/driver and the 40-second checkpoint were not modified.

Digest command failures propagate before reuse/publication. Source and tool
snapshots are checked across preprocessing and compilation. Existing proof
directories or symlinks are refused. Calls that produce compiler diagnostics
use the original compiler command rather than caching a warning-producing
object. Unsupported specs/plugins/auxiliary-output options also use the
original command. All temporary staging remains under the owned output lock.

## Native Controls

- Eight original native contracts passed, including byte-identical output,
  changed options/headers, tampered output, same-target concurrency and invalid
  C preserving the old object/proof.
- Three source/helper/driver identity controls passed.
- Six safety controls passed: compiler-entry content change, proof directory,
  proof symlink, repeated warning diagnostic parity, compiler-entry change
  during compilation and source change during compilation.
- Focused framework tests: 32 passed. Shell syntax checks passed.

The first v3 contract expected a MISS for an -O2 invocation that actually emits
a GNU GCC disabled-optimization warning. The corrected contract requires exact
original diagnostic parity and object-byte parity, without permitting a HIT.
Its independent no-warning concurrency case still requires at least one HIT.
The initial -Wall probe was disabled by the driver's explicit -Wno-unused;
the final probe explicitly enables -Wunused-variable and checks a real warning.
Both incomplete attempts remain separate receipts rather than being rewritten.

Raw controls:
.data/d1510-static-reuse-contract-v3-diagnostics,
.data/d1510-static-reuse-identity-v3,
.data/d1510-static-reuse-safety-v3-midflight.

## Real MCP Qualification

| Metric | Frozen Historical Baseline | v3 | Gate |
| --- | --- | --- | --- |
| First compile | 4.851 / 4.574 / 4.593 s | 4.123 / 4.033 / 4.025 s | 5 s |
| Complete cold build | 47.772 / 47.824 / 47.927 s | 37.296 / 36.987 / 36.370 s | 50 s |
| Complete tests | 105.751 s, 39 files / 965 cases | 86.686 s, 39 files / 965 cases, all passed | 112 s |

The complete test first output was 1.632 seconds. All 39 files exited zero,
matched their expected inventory and final OK; all 965 cases passed. The
frozen runtime binary identity remains unchanged. Cold runs were sequential;
the two confirmation builds started after the complete tests had ended.
No per-file silence gate or diagnostic timeout extension was used.

No static reuse HIT/MISS occurred in these cold builds. Thus these are actual
passing retained observations, not causal proof that static reuse explains
the historical-to-current wall-clock difference. Complete tests exercise the
exact first cold-built artifact, not the two later confirmation artifacts.
Those later artifacts have build/source gates but not separate full-suite runs.

Raw receipts: .data/d1510-static-reuse-mcp-cold-v3/report.json,
.data/d1510-static-reuse-mcp-cold-v3-confirm/report.json,
.data/d1510-static-reuse-mcp-tests-v3/report.json.
The adjacent v3 checkpoint JSON stores exact metrics and hashes without
personal absolute paths. Patch application after 0019 and equality to the
tested helper are verified in the isolated composition fixture.

## Open Boundaries

The real ASCENT scenarios remain unqualified. Its isolated copied-library
control was terminated before any compile marker, with a dyld mapping wait;
that control is not rerun here and is not a candidate regression result.
Direct real GCC/assembler replacement (rather than compiler-entry wrapper
content mutation), arbitrary wrappers and an uncoordinated writer's filesystem
race are not claimed as qualified. GNU/Darwin eligibility guards cache entry,
but explicit cross-platform opt-in fallback side effects require their own
control before production admission. No GitHub delivery or goal completion
is claimed.
