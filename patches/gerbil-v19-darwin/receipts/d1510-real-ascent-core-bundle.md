# Real ASCENT Core Multi-Entry Bundle

Status: real native-module mechanism PASS; speedup and complete AOT consumer
qualification NOT PROVEN. The frozen five-patch series is unchanged.

## Review And Actual Integration

The prior default-loader fixture establishes that one image can expose two
independent module entries. Real emitted Gerbil objects additionally export
both a static module entry and a filename-derived alias. A combined image must
preserve both original symbols. This requires neither modified C nor different
initialization order, loader guards, RTLD flags or platform security behavior.

This small real-module check is worthwhile because alias handling and expander
metadata were not covered by the simple fixture. Expected benefit is fewer
mapped images, not a promised time reduction. Consumer wall time must decide
whether expansion is worthwhile.

Inputs are the isolated ASCENT snapshot workspace's existing emitted
`dependency-graph~0.c` and `expression-plan~0.c`, paired with their native objects.
This reuses artifacts, not that workspace's rejected compiler configuration.
The original Multiple VM toolchain links unchanged C with its GNU GCC flags.
Each alias must exist at its static entry's address in the original object and
the output bundle. Original C/object hashes are checked before and after testing.

`prepare_real_module_bundle.sh` is generic: library directory plus TSV manifest
of relative C paths and existing entry/alias pairs. The ASCENT manifest and
function assertions are consumer fixtures, not package branches in a patch.
Fresh control/grouped overlays share unchanged metadata and wrapper objects
read-only. No active checkout or shared package dependency is modified.

## Native Results

`.data/d1510-real-ascent-core-bundle-v1` and `...-v2` are terminal preparation
and execution passes. Four fresh real `gxi` processes run in ABBA order:
control, grouped, grouped, control. Ordinary Gerbil imports call compiled exports,
not replacement implementations. Assertions cover graph closure, unchanged
adjacency, ordered components, non-eager callback preparation and subsequent
reads of mutable frames in the original order. Image deltas are 2/1/1/2 in both
runs; original inputs remain unchanged.

These are native library-body calls through `gxi`, not a complete ASCENT AOT
Cases executable or full test-suite qualification.

| Run | Control A | Grouped B | Grouped B | Control A |
| --- | --- | --- | --- | --- |
| v1 wall seconds | 1.60 | 0.58 | 0.13 | 0.12 |
| v2 wall seconds | 0.18 | 0.39 | 0.14 | 0.13 |

The first sequence includes visible cache warming; the second has no consistent
advantage. Neither admits a speedup or replaces MCP's 4.5/42/97-second policy.
CPU times are nearly unchanged. BSD `time -p` measures complete diagnostic
processes with a 42-second cap; there is no Python native-test supervisor.
Both bundles have SHA256
`04e49bf147a71de3b5409d2e8e5e2c44b2be759e37c6a1dc23e6a6dba2012cc1`.

## Fail-Closed Group Constraint

Default aliases derive from basenames and may collide across directories. The
preparer rejects duplicate entries/aliases rather than selecting by link order.
`.data/d1510-real-ascent-core-bundle-duplicate-v1` is an expected exit-2 negative:
duplicate symbol rejected, no `link.log` and no `combined.o1`. This does not
establish simultaneous publication or all invalidation requirements.

Final preparer SHA256:
`c9c4fe8041a3190ae80eafe12056745ff801f5a64f0da0eb338ee28e71465a04`.
The checker now requires completed successful preparation before starting,
SHA256 `be5a34d1246fd94d2cd175ca3dda6ad1c681dd92fbf92e90f6966d486848135c`.
That precondition was added after v2, not separately exercised by the v2 run.
Its rejection side is exercised against the failed duplicate fixture: exit 1,
no native test launch and no `run-exit-status.txt` created.

## Remaining Decision

Expand only if an admitted consumer configuration has a material budget in newly
mapped images. Image reduction alone does not establish that budget. Group
invalidation, snapshot identity, immutable atomic publication, concurrency,
failure safety and both consumers' complete gates remain required before any
bundle patch enters the frozen series. The old snapshot positive-plan timeout
remains DENY; this does not reopen its unchanged configuration. No new complete
build/test time, latest-staging rebuild, commit or GitHub delivery is claimed.
