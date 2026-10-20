# D1883: close the existing packed-emitter full-build evidence gap

## Retained line and scope

The original D1510 line remains selected. The D1878 original-line observation
is first compile 5.053081 seconds and complete build 56.255963 seconds; it
still fails the 55-second gate and does not replace historical B1/B2 complete
times of 51.737180/53.496910 seconds. No PR or release is admitted here.

Canonical staging was checked live and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; the candidate Gambit checkout is
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.

Existing D966 establishes the packed-string emitter's object equivalence,
but its old lifecycle attempt stopped in clean before a whole MCP build.
This missing whole-build result justified one bounded completion attempt,
not repeating the already measured atomic string benchmark. No new emitter
algorithm, Gerbil consumer source or std/make/std/test change was introduced.

Both roles retain D1510, original D1391 home/libraries/runtime, GNU GCC,
macro-tracking disabled and 12 physical-core workers. Only the candidate
GERBIL_GSC differs. D966's preserved candidate hash is
`f7c4b00779d491b7455f858264f09ec89900bdb8a37bf939fa2cc9139ccd07c1`;
its recorded original GSC hash equals the retained original compiler hash.

## Corrected entry and retained failure

D1881 incorrectly points GERBIL_GSC at the compiler source directory. The
existing 0007 driver resolves gambuild-C beside GERBIL_GSC, not through GAMBOPT.
The first candidate therefore fails with a missing gambuild-C path. This is
a harness/configuration error, not a packed-emitter performance measurement.
That invalid batch was stopped; its control happened to complete in 57.221367
seconds, but it is not combined with later candidates into a speedup ratio.

D1882 uses an isolated coherent entry directory containing the byte-identical
candidate GSC and a symlink to the unchanged original gambuild-C. Both hashes
are checked before launching. The original source, binaries and library home
are not overwritten. The actual emitted embedded C selects the intended guard
and has 47,079,285 bytes. No compiler-path shim modifies source or output.

## Complete results

Each row has an independent local MCP clone at revision
`9a5c35e275e5d6847ff421151bb224f2eae177c1`, official clean exiting zero and
zero project native images afterward. Gates remain 10-second real build output,
180-second diagnostic termination and 55-second complete performance.

| D1882 order | First compile seconds | Complete build seconds | Admission |
| --- | ---: | ---: | --- |
| A original | none | incomplete | real-output gate failed |
| B packed | 7.883464 | 68.080142 | build exit 0, 55-second gate failed |
| B packed | 4.979575 | 70.253448 | build exit 0, 55-second gate failed |
| A original | none | incomplete | real-output gate failed |

All checked candidate consumer inputs remain unchanged. The complete batch is
unqualified and its controller exits one. Both candidates fail the absolute
complete-build gate. The failed controls prohibit a matched speedup or causal
regression ratio. No resource cause, historical configuration loss, startup
fix or stable performance restoration is inferred.

The second candidate's real prepare-executable-link output is at 59.770481
seconds; link-executable output is at 68.864674 seconds. These observed
boundaries include all emitter work and are not exclusive per-job timings.
Gambit's targ-link-info reads only the first line and leading Scheme metadata
expression before closing its input. Consequently, the larger C file alone
does not justify an unmeasured claim that linking scans its entire body.

## Decision

Do not add 0013 to the retained best-line profile or submit it as the missing
51-second optimization. Its large isolated C-to-object advantage has not
qualified end-to-end. No candidate package-suite run or new whole-toolchain
build is started after this failed performance admission. Existing semantic
object-equivalence evidence remains valid within its original scope.

The first-log and complete-build targets remain independent. Original D1510
and the historical 51/52-second references are preserved; the 55-second gate
is not widened. GitHub PR submission remains conditional on actual performance
and applicable build/test closure, not on expectation that the last seconds
will return.

Private evidence: `.data/d1881-packed-gsc-original-line-abba/`,
`.data/d1882-packed-gsc-entry/`, and
`.data/d1882-packed-gsc-original-line-abba/`.
