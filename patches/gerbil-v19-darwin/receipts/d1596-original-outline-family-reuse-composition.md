# D1596: combine retained outline and family reuse, not a startup release

## Source And Construction

The preceding goal turn made progress: D1589 proves executed child reuse and a
remaining post-load interval. This turn checks composition instead of repeating
failed broad O2/O3, wrapper/fold inlining, directory caching or return outlining.
Canonical v0.19-staging is freshly checked and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0; its Gambit input remains
ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f.

D1579's 317-object prototype used the original carrier, not D1510's retained
guarded-outline carrier. D1590 now combines those verified 317 objects with the
original D1510 carrier. Its fourteen readonly traces retain only the original
two outlined reentry paths; the failed D1569 return-outline expansion is not
selected. The builder rejects that expansion and locks the original carrier
receipt, SCM/C inputs, GSC and RTS identities. No carrier recompilation occurs.

Only the existing guarded Gambit loader/registry prototype and selected link
carrier differ. Original static objects, native objects and consumer compiler
remain. GNU GCC comes from the existing Bazel host environment. Linux and Clang
product paths are not activated. Compile-loader, compile-registry, link and both
disabled/enabled import smokes pass. Candidate SHA256 is
019d8cbab671fbf2425571aa5b5fa83ec7a035999a56144e27b66d27f1dd85c2.

## Real First Compilation And Complete Build

D1591 uses actual fresh MCP clean/build ABBA, current 0007 baseline, common
library/GSC home and twelve workers. Each role locks its parent and shebang
child binary. All cleans exit zero and leave zero project native images. Both
baseline builds fail the unchanged ten-second real-output gate. Candidate first
compilation appears at 8.122371 and 5.064355 seconds; builds deliberately stop
at that line. The ABBA is unqualified: no mean ratio or baseline speedup claim.

D1592 separately completes actual project-cold MCP construction with lookup
enabled, unchanged source and the original output/180-second complete gate:

| Boundary | Observed time/status |
| --- | ---: |
| Clean | 1.226201 s, exit 0 |
| Native artifacts after clean | 0 |
| First literal compile line | 4.641963 s |
| Complete build | 68.561755 s, exit 0 |
| Maximum build output gap | 4.641963 s |

The executable exists and is retained with SHA256
3ed70bc52cf598055d43f61d9cfe273cc500cd99bcdb11dbe36833de0db2bd6d.
This is candidate-only construction, not a matched acceleration relative to
historical 53/56/69-second lines. The legacy private driver's means divided by
two even in candidate-only mode; this run's raw row is authoritative. The
driver is corrected for future runs to divide by actual role count and omit
absent roles. Old report means are not silently relabeled.

## Actual Native Contract And Wider Unit Coverage

D1593 executes the actual preloaded native stx-wrap in twelve baseline and
twelve candidate processes, not a copied toy implementation. All 24 exit zero,
return eight CASE-OK markers and final OK: 192 cases and 236,184 mark streams.
Checks retain source-token and input identity, mutation aliasing, quoted and
cancelled identity, fresh wrappers, improper tails, exhaustive three-mark
streams through depth eight and explicit GC with live results. Original five-
second output and ninety-second total gates remain. This is a focused contract,
not lifetime/reinitialization or complete toolchain qualification.

D1594 broadens real gerbil-test coverage to all thirteen original MCP unit files,
177 declared cases per wave. Twelve workers run distinct files, each once per
wave. The JSON-store test has fixed global temporary filenames, so duplicating
the whole suite in twelve simultaneous processes would create test collisions.
Inputs are not rewritten; each invocation retains exact case/exit/final-OK and
source-hash checks and its own TMPDIR. Four ABBA waves produce:

| Wave | Role | Passing file processes | Completed cases | All passed |
| --- | --- | ---: | ---: | --- |
| 0 | baseline | 1/13 | 19 | no |
| 1 | candidate | 5/13 | 56 | no |
| 2 | candidate | 13/13 | 177 | yes |
| 3 | baseline | 13/13 | 177 | yes |

Overall 32/52 file processes pass and 429 cases complete. Twenty processes fail
the unchanged five-second real-output gate. The two later complete waves do not
erase earlier failures, prove their cause, qualify cold tests or justify an
overall speed ratio. No regex-only result is presented as the entire unit suite.

## std/make And Decision

D1595 uses the exact candidate with twelve workers. Twelve starts and twelve
make/test imports pass. The macro-heavy cold std/make phase emits its genuine
CASE/PHASE-START, then fails the unchanged five-second product-output gate before
any observed GCC frontend. No no-op/invalidation or complete make pass follows.

Preserve the constructed composition, successful complete MCP build and native
contracts, but do not promote the prototype or claim the seven/eight seconds
are solved. First-log stability, cold/wider test progress and real std/make
construction still fail. Module lifetime/reinitialization, installation and
replacement semantics also remain unqualified. Existing 0001/0007/preprocessing
patches stay unchanged. No Gerbil/std/make/std/test/package/HTTP product source,
Homebrew installation, security policy, output deadline, commit or push changes.
All owned sessions are terminal. The full toolchain goal remains active.

Private evidence: `.data/d1590-outline-and-family-reuse/` through
`.data/d1595-composed-std-make-test/`.
