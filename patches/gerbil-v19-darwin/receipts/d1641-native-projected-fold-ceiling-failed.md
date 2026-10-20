# D1641: native projected-fold experiment fails performance acceptance

## Source and actual frame integration

D1633 audits the original second syntax-e fold with current core/stx/util GVM
bodies. The actual saved caller return is a runtime guard, not an assumed
constant. A nonexecuting CFG marker after the original CAR identifies the
projected caller boundary. Each of four structural CAR consumers reaches the
existing 64-path analysis cap; this is bounded coverage, not an exhaustive proof.
The completed states restore frame delta -8 and include three, eight or thirteen
heap words: a result pair and zero, one or two new wrappers.

D1634 lowers those bounded states through the new projected-boundary pass.
The pass checks the actual caller instructions up to its next one-argument
global call: no unknown read, branch, safepoint or observation of the ignored
registers is permitted. It rejects fresh references in the projected result or
live caller stack. The pair must have no address use outside its recorded
constructor. Registers 0/2/3/4 are explicitly cleared before the original caller
overwrites/clobbers them; the actual frame delta and live stack are retained.
Poll exits still materialize required fresh dependencies. The full original
heap reservation remains mandatory. All 145 test_gambit*.py controls pass.

This extends D1631 into the actual producer/fold/callback/caller source frames.
It remains experimental post-codegen lowering, not Gambit backend integration.

## Native construction

D1636 adds eight guarded paths at the original second-fold continuation to the
retained D1510 carrier: one eight-word and one thirteen-word path for each of
the four structural CAR consumers. The original code is retained on every
miss. Original readonly outlines, object reuse, GSC, RTS, module objects,
GCC macro-tracking settings and generated-C O1 remain unchanged. No Gerbil
consumer Scheme, std/make, std/test, HTTP/package code or installed binary is
edited. Non-Darwin/non-GNU configurations keep the original execution path.

GNU GCC construction completes: carrier compile 50.031005 seconds, native link
0.133478 seconds, real make/test/build-script import 2.415856 seconds. These are
construction clocks, not application build gains. The import finishes below
the five-second silence limit, although the construction helper itself used
its 180-second diagnostic limit; strict admission comes from the runs below.

Candidate SHA256:
`be019dafd26940245107ba8e0c0ec1174b19e37b8d454def6d8d2a9ac99a2bb1`.
Canonical staging checked live remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

## Real native contracts and MCP clean/build

D1638 reuses the unchanged native effect-contract controller with six original
and six candidate processes at physical twelve-core concurrency. All twelve
exit zero with six exact cases and final success: 72 checks. Rebinding,
discarded-branch errors and continuation escapes remain observable. This fixture
does not prove that the new guarded core-caller paths were taken; it is a real
native producer fallback/effect contract, not fast-path coverage or full Native
suite qualification.

D1639 runs a fresh real MCP project clone, original clean and complete build
using the actual candidate image through the root and shebang-selected builder
PATH. MCP head remains `9a5c35e275e5d6847ff421151bb224f2eae177c1`; physical twelve
workers, original ten-second genuine-output gate, and fixed 55-second performance
ceiling remain selected. Clean exits zero and leaves zero project native images.

| Actual candidate result | Seconds |
| --- | ---: |
| Clean | 4.167162 |
| First literal compile util/compat | 5.586510 |
| Complete build | 63.229195 |

Build exits zero, genuine maximum output gap is 5.586510 seconds, inputs remain
unchanged, and an executable is produced. The controller exits one specifically
because complete-build performance exceeds 55 seconds. Construction success is
not performance acceptance. This candidate-only run establishes no causal ratio
against the unmatched historical D1513 52.617045-second mean or later candidates.
It does not eliminate the main startup delay. No resource explanation is claimed.

## Concurrent std/make and std/test

D1640 executes this exact image with common original GSC/libraries. Twelve
native starts and twelve make/test imports pass, followed by the actual std/make
cold/noop/invalidation fixture with std/test assertions and final
SUITE-OK/D885-OK. Physical concurrency is twelve; peak observed GCC frontends
is eleven. The unchanged five-second genuine-output gate passes, with maximum
gap 3.181942 seconds.

Cold/noop/invalidation phases: 12.519992 / 0.008190 / 1.747216 seconds.
Fixture process wall: 15.862924 seconds. These candidate-only semantic/workflow
receipts establish no test acceleration and are not the full MCP unit suite.

## Decision

Do not promote this image or solidify it as a successful optimization patch.
Native construction and focused workflow semantics pass, but performance fails.
Retain the source transformation and its negative result. Before extending this
route, establish actual guarded-path use and removed allocation/CPU costs; source
eligibility counts alone are insufficient. Native deoptimization/GC stress,
full tests and Gambit backend integration remain open. The full goal is active
and unachieved; D1513 and the fixed 55-second ceiling remain unchanged.

Private evidence: .data/d1632-real-fold-region.py,
.data/d1633-real-fold-region/, .data/d1634-real-fold-region-sinking/,
.data/d1635-native-projected-fold.py, .data/d1636-native-projected-fold/,
.data/d1637-projection-native-contract.py,
.data/d1638-projection-native-contract/,
.data/d1639-projected-fold-real-mcp/, and
.data/d1640-projected-fold-concurrent-make/.
