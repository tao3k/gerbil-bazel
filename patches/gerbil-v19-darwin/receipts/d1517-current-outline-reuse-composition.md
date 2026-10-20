# D1517: current object-reuse inputs plus guarded outline carrier

## Scope and prior evidence

This requalifies the existing D1083 guarded readonly outline carrier on current
D1391 object-reuse inputs. It is not a newly discovered optimization and not
a production Gambit patch. D1266 already measured uninstrumented official
first logs (9.35% lower); D1267 completed builds but recorded a slower candidate
and failed full-suite gates. Those negative records remain applicable history.

No std/make, std/test, consumer SCM, HTTP/package code, installed toolchain,
original static objects, GSC, headers or runtime archive is changed. Existing
0001, 0007/0008 and GCC macro-tracking settings remain selected. Linux is not
activated. C preprocessing gains are not counted as Scheme execution gains.

Canonical staging was checked live during this run and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit remains
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. The native construction uses
GNU GCC 16 and physical 12-core concurrency. All work stays in project .data.

## Native construction and contracts

D1508 regenerates the carrier from current input C and original static module
order. Its 14 trace shapes match the old carrier on module, removed calls,
conditions, frame delta, steps, polls, peak frame, outlined lookup, lowered
type-chain loops and terminal boundary. Original input hashes remain unchanged.
This is source-shape parity, not a proof of speed or general compiler validity.

D1510 compiles that 19,746,620-byte carrier at O1 with bounded native helpers,
then links unchanged current original objects and RTS. Compilation takes
46.228593 seconds; framework imports succeed. Generated fast paths retain
Darwin/GNU/non-Clang and host-mode guards. No result cache, relaxed mutation
policy, GC epoch shortcut or ABI change is introduced.

| Input | SHA256 |
| --- | --- |
| Current baseline gerbil | a398d0b2e3200019a1542a0fea8b101062a76118f82dcba30f580b481a608e5a |
| Current candidate gerbil | 446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3 |
| Common GSC | 9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00 |
| Carrier C | e4a2ffde9b4dc329bf44db818f8241a30ef0c8ecaa7fc220c3fe6521936277e1 |

D1511 passes the current native small-contract comparison and twelve concurrent
candidate processes, each with 200 explicit GCs and twelve Scheme threads.
Covered contracts include initialization order, cross-module rebinding,
continuation/wind/values, nonprocedure exceptions, rest freshness/order/arity,
parameter identity/environment, mutable/deep ancestor lookup and bounded
primitive behavior. The 53 focused trace/parameter/primitive unit tests pass.
These are not complete Native/FFI suite qualification.

## Actual MCP first logs and complete builds

MCP remains at `9a5c35e275e5d6847ff421151bb224f2eae177c1`.
Both roles use current D1391 libraries, GSC, RTS and settings. Each ABBA row
uses its own fresh project clone, official clean exiting zero and zero project
native images afterward. This is project-cold, not OS-page-cache-cold.

D1512 first-window ABBA means are 6.421643 versus 5.043441 seconds, 21.46% lower.
Those builds deliberately stop at the actual `... compile util/compat` line
(exit 70); they are not completed builds. Legacy-input repetitions D1505/D1506
are retained separately, not combined into current-input speed claims.

D1513 instead completes every build under unchanged ten-second real-output
and 180-second complete-build gates, configured for twelve workers:

| Order | Role | First compile seconds | Complete build seconds | Exit |
| --- | --- | ---: | ---: | ---: |
| A | Baseline | 6.072760 | 53.918332 | 0 |
| B | Candidate | 4.789153 | 51.737180 | 0 |
| B | Candidate | 4.933479 | 53.496910 | 0 |
| A | Baseline | 5.710633 | 53.425696 | 0 |

Means: first compile 5.891696 to 4.861316 seconds (17.49% lower), complete build
53.672014 to 52.617045 seconds (1.97% lower). Whole-build sample ranges overlap.
This local batch retains startup benefit alongside object reuse but supplies
no stable major whole-build speedup. Do not add this percentage to D1396's
22.8% or compare unmatched historical best times as a causal denominator.

## Real tests and output acceptance

D1514 uses this run's completed project artifacts and actual unmodified MCP
regex tests through `gerbil test -v 5`, four serial ABBA waves of twelve
processes. All 48 processes exit zero with exact 19 CASE-OK records and final
OK: 912 cases. Sources remain unchanged. Original five-second output and
90-second wall gates remain.

Mean first CASE is 1.805700 to 1.734531 seconds; mean complete process time is
2.198313 to 2.244666 seconds (2.11% higher). There is no current-input test
speedup. D1507's legacy-input 10.2% observation must not be transferred here.
This is the regex subset, not acceptance of the failing D1267/D1268 full suite.

D1515 passes twelve native starts and twelve make/test imports, followed by
actual std/make cold/noop/invalidation builds with std/test contracts and final
SUITE-OK/D885-OK. Cold/noop/incremental phases are 11.008677/0.018166/1.701805
seconds; wall time 14.293562 seconds. Maximum genuine output gap is 3.221050
seconds under the unchanged five-second gate; peak observed GCC frontends is
eleven with twelve configured workers. This candidate-only semantic control
does not establish a performance ratio.

D1516 validates all four completed MCP executables: initialize, tools/list
and gerbil_eval of (+ 1 2) returning Result: 3. Each passes the original RPC
gate. Applications still use common GSC/RTS; these smoke results do not imply
the carrier optimization was embedded into their application executables.

## Decision and retained evidence

Retain the carrier as a bounded experimental startup advantage compatible with
current object reuse. Do not promote it as the seven-to-eight-second solution,
a test acceleration, a complete toolchain build or a release-qualified patch.
Python post-codegen carrier construction is not production integration into
the Gambit C/link backend. The major startup and complete-test goals stay open.

Receipts and raw logs:

- `.data/d1505-outline-official-first/` and `.data/d1506-outline-official-first-repeat/`
- `.data/d1507-outline-mcp-tests/` and `.data/d1509-outline-concurrent-make/`
- `.data/d1508-outline-current-preflight/` and `.data/d1510-outline-current-native/`
- `.data/d1511-current-outline-native-contract/` and `.data/d1512-current-outline-first/`
- `.data/d1513-current-outline-full/` and `.data/d1514-current-outline-mcp-tests/`
- `.data/d1515-current-outline-concurrent-make/` and `.data/d1516-current-outline-mcp-protocol/`

All owned build/test/remote-check sessions in this batch are terminal. No commit,
push, consumer edit or system installation is performed.
