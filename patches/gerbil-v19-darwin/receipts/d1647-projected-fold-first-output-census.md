# D1647: real first-output trace coverage and selection flaw

This records diagnostic coverage, not an acceleration. D1639's uninstrumented
complete build remains 63.229195 seconds and fails the unchanged 55-second gate.
The retained D1513 candidate complete-build mean remains 52.617045 seconds.

## Boundary And Controls

D1644 instruments only isolated native carrier clauses and an isolated copy of
the RTS write object. The original source, archive, installed binaries and MCP
source remain unchanged. A fragmented-line/interleaved-fd control verifies that
the first snapshot is frozen immediately after the actual successful write of
the first literal compile line; exit counts are recorded separately.

D1646 uses the existing real MCP controller with the original ten-second
output gate, not its extended diagnostic grace. Actual builder child PID 43405
is verified against diagnostic binary SHA256
`c0d01b7b8278a344933c98ff3883bbe859419d3b7407be9ee74853f5007537d6`.
Clean succeeds with zero remaining native images. The genuine first compile
is observed at 6.028199 seconds; the build is deliberately stopped afterward
(exit 70), so this is neither a completed build nor a performance result.

## First-Write Counts

| Consumer | Single-wrapper hits | Two-wrapper hits |
| --- | ---: | ---: |
| core-expand-top | 0 | 0 |
| core-expand-expression | 0 | 0 |
| core-expand1 | 678174 | 0 |
| core-expand-head | 680441 | 0 |

The single-wrapper paths succeed 1,358,615 times before the actual first compile
write. Their omitted pair-plus-wrapper constructors account for 10,868,920
logical heap words (86,951,360 bytes with eight-byte words). This is not a
measured malloc, GC, CPU or wall-time reduction. Exit counts are excluded.

## Source Finding And Next Action

D1635 chooses the shortest lowered code for each extent. Its selected
two-wrapper state 35 requires the fresh record's constructor descriptor TYPEID
to differ from the wrapping tag. Under the ordinary wrapping descriptor this
path cannot succeed. State 41 instead retains a positive descriptor/tag guard
and a distinct-mark guard. All runtime guards and original fallbacks must stay.

The next experiment ranks multiple-constructor traces that recognize their own
constructor descriptor before shorter rebound-descriptor traces, without a
procedure-name whitelist or changing single-constructor selection. This ranking
is a coverage heuristic, not a compiler correctness proof or a speed claim.

Evidence: `.data/d1644-projected-fold-census-native/`,
`.data/d1646-projected-fold-first-census/`,
`.data/d1634-real-fold-region-sinking/report.json`, and
`.data/d1636-native-projected-fold/report.json`.

No std/make, std/test, package/HTTP or consumer SCM change is made. Native
construction, coverage, semantic contracts, whole-build timing and production
backend integration remain distinct gates. The optimization goal stays open.
