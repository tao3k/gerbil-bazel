# V4 Actual GNU Tool Content Invalidation

Status: isolated native tool-content invalidation PASS. This closes a missing
V4 scenario, not full cold/default-enabled performance qualification.

## Review Before Execution

Correct direction: require the real native consumer to reject both its executable
entry and its static object proofs when the actual compiler file changes. Earlier
V4 controls changed real tools only in a small object fixture; the real ASCENT
scenario checked lookup-path alignment, not changed compiler contents. This
missing end-to-end safety check is worthwhile. Expected speed benefit is zero:
invalidation deliberately recompiles; no failed speed candidate is reopened.

Source review also confirms why MCP's 186 generated-C records were not a gain:
its executable closure already passes this build's produced C directly. Planned
library-only proofs cannot be promoted to an extra MCP Scheme-link consumer.
That prior DENY is retained, not recast as a missing mixed-build optimization.

## Isolated Native Execution

Fresh COW workspace `.data/d1510-ascent-v4-tool-upgrade-v2` copies the frozen
ASCENT workspace at `21e3638687d42ecfc36acebb28991987435ebc60`. Existing library
outputs are retained. Only its private GNU GCC executable and driver paths are
changed; original source, global GCC and shared dependencies remain untouched.
The original Multiple VM toolchain and V4 static-object helper are retained.

GCC needs its relative program and runtime-library layout after relocation. The
preparer exposes those original directories through read-only symlinks, then
checks real cc1 resolution, emutls archive resolution and an actual small link/run.
This is a test-tool relocation, not a changed compiler flag or optimization.

The direct Bash/just/Scheme runner selects the private executable consistently
for both the compiler driver and the consumer's `which gcc` identity. Hardware
core detection, original native heap and Cases deadlines remain unchanged. Each
complete scenario retains the existing 135-second cap. Python does not supervise
the native tests; its post-run use only verifies immutable file identities.

Receipt `.data/d1510-ascent-v4-tool-upgrade-receipt-v2` is terminal exit zero:

| Scenario | Whole Seconds | User / System Seconds | Entry | Object Cache | Cases |
| --- | --- | --- | --- | --- | --- |
| Establish private tool context | 68.38 | 105.08 / 34.91 | MISS | 72 MISS | 30/30 |
| Change actual private GCC bytes | 49.52 | 105.33 / 35.30 | MISS | 72 MISS, zero HIT | 30/30 |
| Same changed tool, unchanged inputs | 7.74 | 6.49 / 1.92 | HIT | no object reuse events | 30/30 |

All three logs contain the final `OK` and exit zero. The mutation appends only
non-executed bytes to the private real GCC copy at the same path. No entry
receipt is manually removed. The third scenario executes every Case; cached
test verdicts are not used. These are warmed-library AOT entry scenarios, not
package-cold builds, full ASCENT suites or repeated MCP tests. The cache-hit
duration is existing consumer entry reuse, not a new compiler speedup.

Raw output SHA256 values, in table order:

- `ee2f03c338b4ff2bd64c07bd6eacf8980c1fb43ce3d69c5e201fd978527d1c12`
- `68beb48978b7846c995aa32c76a3e8aa0d1616467a6d38ea04b4193e888954a0`
- `b3e62dd4558aad8649de6e12a470365ba160dca183565c4d4d96f9a0145c1545`

After execution, 1,992 toolchain and 2,809 dependency dynamic image identities
verify. The global GCC before/after hashes match, and the frozen original
consumer's tracked Git diff is empty. Frozen MCP patch/runtime identity remains
separately locked; no MCP measurements or optimization patch bytes are replaced.

## Retained Failure And Remaining Gates

v1 relocated cc1 through `GCC_EXEC_PREFIX` but omitted GCC's runtime-library
layout. It reached linking, failed on missing `emutls_w`, exited 70 after 73.88
seconds and executed no Cases. It is a fixture failure, not a performance result.
The global compiler hash still matches its pre-run hash. v2's relocation preflight
addresses that specific failure before launching the real consumer.

After v2, checker-only polish catches HIT tags even when concurrent stdout embeds
them within a long line. The launcher restricts an explicit private compiler to
the direct owned bin directory; defaults are unchanged. These tighter checks
are not a separately timed rerun of v2.

Whole-consumer source/options/failure/concurrency qualification, complete cold
performance and both consumers' complete test gates still require evidence.
The old snapshot candidate's 135-second cold timeout remains DENY. No new
default enablement, latest-staging rebuild, commit, push or goal completion is
claimed.
