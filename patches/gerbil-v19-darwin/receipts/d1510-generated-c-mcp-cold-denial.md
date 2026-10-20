# Generated C Dispatch: MCP Cold Gate Denial

## Candidate And Gate

One real isolated MCP cold attempt used the frozen runtime
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`,
the existing native static-object driver and isolated generated-C dispatcher v4.
The progressive framework explicitly binds original GSC plus dispatcher/journal/
cache/adapter identities before execution and rechecks them afterward. This does
not replace the underlying compiler-byte check with a wrapper-byte check.

Raw receipt: `.data/d1510-generated-c-mcp-cold-v1`.

| Metric | Observed Result |
| --- | --- |
| Clean | 2.873347 s, exit 0, zero native images afterward |
| First compile | Not observed by 5.041113 s |
| First-log hard ceiling | 5.000000 s |
| Build attempt including termination | 5.050198 s |
| Complete build | Unknown; forcibly interrupted |
| Complete tests | Not run because cold admission failed |
| Source identity | Unchanged |
| Cleanup | All children reaped, no cleanup errors, terminal exit -9 |
| Admission | DENY |

The 0.041113-second overrun is watchdog observation granularity, not permission
to exceed the five-second ceiling. The complete-build ceiling remains 50 seconds.
No performance threshold was widened and this unchanged candidate was not rerun
to select a more favorable wall time.

## Evidence Boundary And Next Action

The build log is zero bytes; no generated-C proof was found in the owned output.
This attempt does not establish that the adapter actually ran before the first
log deadline, and provides no complete-build or C-reuse timing evidence. Do not
attribute the early denial to C generation, nor promote component HIT timings as
consumer speedups. Direct evidence of the pre-log GSC call boundary is needed
before selecting a startup change. Prior accepted frozen measurements are not
overwritten by this rejected candidate.

The framework now has an explicit `--generated-c-reuse` option for cold and full
test phases, binds all five generated-C tools, and requires the full-test setting
and tool bytes to match the cold report. Existing focused cold-admission and
driver tests pass (9 tests). This wiring is not whole-consumer qualification.

## Raw Receipt Identity

- Cold report: `ddb99a8263e755964a15d188f630e441287e37ca9a99e907f570dc624bc3aa68`
- Progressive admission: `3fbad9d73e6ede45af7b5684f66c9f18450fac5bb099f5b825d5c0b1ef2649d7`

Candidate remains default-off, unpromoted and not pushed. Both consumer
performance/correctness gates in the active goal remain open.
