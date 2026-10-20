# D1606: original D1513 candidate versus later composition

The preceding goal turn obtained new task identity evidence. The user's latest
correction requires returning to the recorded D1513 full-build configuration,
not treating a single module's 53.17-second completion as a full-build baseline.
D1513's 52.617045-second candidate mean remains valid recorded history.

The private complete-build driver now supports an explicit baseline binary,
checks its qualified receipt/SHA and gxi symlink, and prepends its directory to
PATH for the actual build.ss shebang child. This makes A the original D1510
candidate, not the original unoptimized Gerbil executable. B is D1590's same
outline plus 317-object embedded-native composition with reuse enabled.

A SHA256: 446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3.
B SHA256: 019d8cbab671fbf2425571aa5b5fa83ec7a035999a56144e27b66d27f1dd85c2.
Both use the same D1391 library/compiler/runtime home. The checked GSC SHA is
9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00 and RTS archive
SHA is fd3725c9cc68525efbd8c0385f242f72334de37d5c56a96fd7db8666bb873501,
matching the retained inputs. Canonical staging is freshly confirmed as
1cfb032c7a1612637da6205f5f8a15683eba3ba0. Bazel host discovery supplies GNU GCC
and twelve physical workers. No process observer or stack sampler is inserted.

## Real Adjacent Cold Builds

Each role receives a separate fresh MCP clone at
9a5c35e275e5d6847ff421151bb224f2eae177c1, official clean with exit zero and zero
project native images, then a complete build. Sources retain their checked
hashes. The executable exists after each build. Ten-second real-output and
180-second diagnostic termination budgets stay unchanged; the independent
complete-build performance ceiling is 55 seconds.

| Order | Configuration | First compile | Complete build | Exit | 55-second gate |
| --- | --- | ---: | ---: | ---: | --- |
| A | Original D1510 outline | 6.296346 s | 83.238059 s | 0 | fail |
| B | D1590 composition | 5.851100 s | 74.531504 s | 0 | fail |
| B | D1590 composition | 5.795456 s | 74.694105 s | 0 | fail |
| A | Original D1510 outline | 6.339959 s | 77.340697 s | 0 | fail |

Both original-candidate repeats are slower than both composition repeats in
this batch. Thus the unmatched historical 52.62-versus-68.56 comparison does
not establish that adding the 317 objects caused a full-build regression.
Neither arm reproduces the recorded D1513 performance or meets today's fixed
ceiling. Do not promote a relative batch improvement as satisfying the goal,
attribute the historical time change to machine resources or redefine the
baseline/ceiling upward. Its cause remains unresolved.

Private report: `.data/d1605-outline-vs-composition-complete-abba/report.json`.
All four construction rows pass, but performanceCeilingQualified is false and
performanceQualified remains false. Subsequent acceptance invocations can use
the driver's new --require-performance-ceiling option to return a nonzero exit
on ceiling failure; diagnostics may finish without admitting their performance.
Candidate receipt/SHA/gxi checks are also hardened for future invocations.
This run's original report is not rewritten.

## Decision

Keep D1513 as the historical performance reference and keep its original
candidate available. Do not remove the composition based on an unpaired timing,
nor release it based on this batch's relative benefit. Existing wrapper/test
contracts and D1515/D1598 std/make results retain their original limited scopes;
this turn runs no new test suite and does not erase D1594/D1595 failures.
Stable first-log reduction, full build at or below 55 seconds, and actual
concurrent test acceptance remain required. All owned sessions are terminal.
No product source, installed toolchain, release patch, commit or push changes.
The goal stays active and unachieved.
