# D1544: current image experiments targeted inactive native versions

## Scope and evidence change

D1527 completed original-code parity for the old D935 image closure and retained
a scoped Native CPU gain. It did not prove that those images are selected by
the current D1391 profile. This turn discovers that missing execution boundary.
No product source, std/make, std/test, consumer source, signing or security
policy is changed. No candidate is promoted. Existing optimization patches remain.

The source remains canonical staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0` and Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, GNU GCC 16, twelve workers.

## Bounded old-profile grouping

The diagnostic repacking helper now supports a zero/default unchanged limit
or an explicit module cap of at least two. Four partition tests verify default
greedy shape, bounded size, unique linker basenames, retained input/order and
invalid-limit rejection; fourteen focused partition/Mach-O/manifest tests pass.

D1528 reuses the parity-validated objects with a 32-module cap, making thirteen
images (twelve groups of 32 and one of seven). D1529 confirms no duplicate
definitions, newly internal cross-image bindings, export changes, architecture/
flag/rpath changes or new initialization hooks. Original outer FFI exclusions
remain byte-exact. D1530 is a construction envelope, not performance admission.

D1531's original-profile actual MCP clean/build ABBA has all four builds fail
the unchanged first-output gate. All cleans exit zero and leave zero project
native images. No first-compile ratio or complete-build result is admitted.

D1532 nevertheless passes actual unchanged MCP regex tests: four ABBA waves of
twelve processes, 19 CASE-OK records and final OK per process, 912 cases total.
Original five-second output and 90-second wall gates remain. Per-process means
are 3.269456 to 1.458375 seconds, approximately 2.24x. First-CASE means are
2.630368 to 1.443744 seconds. These are this old matched profile's measurements,
not current-profile or full-suite claims.

Each serial twelve-process wave now also records aggregate RUSAGE_CHILDREN
CPU around the complete pool; it is not invalid per-thread subtraction:

| Wave | Role | User CPU seconds | System CPU seconds | Wave wall seconds |
| --- | --- | ---: | ---: | ---: |
| A | Original | 12.612146 | 3.596176 | 3.104610 |
| B | Bounded images | 6.026345 | 2.290799 | 1.607567 |
| B | Bounded images | 6.133159 | 2.277106 | 1.502818 |
| A | Original | 13.481618 | 3.761690 | 3.691416 |

All waves execute the same 228 cases. This retains a major local test advantage
worth pursuing, without implying fresh-cold cache behavior or a CI-wide ratio.

## Current-profile composition fails

All 391 selected old `.o1` images equal the current profile's corresponding
`.o1` files byte for byte. GSC, headers and RTS also match. However, 242 selected
SCM hashes differ. D1533 therefore copies the current home, retaining its current
binary and all SCM/metadata, and changes only those matching image paths. Source
metadata is not replaced. This is image-level construction, not source provenance
for regenerating current code from old SCM.

D1534's current-profile test ABBA fails: both original waves pass all 228 cases;
both candidate waves fail before any CASE output. D1535 uses the exact original
executable rather than the copied one and still fails candidate waves. D1537/D1538
share the old validated immutable aggregate image vnodes via hardlinks and still
fail. No signature, permission, system-policy or kernel-validation bypass occurs.
These controls do not prove a vnode-sharing acceleration.

The earlier lanes used role-specific completed fixtures. D1539 removes that
confound by using the same original executable and the same current-built MCP
fixture for all four waves. Originals again pass 228 cases per wave; candidates
again have zero cases and fail the original five-second gate. Thus the current
failure cannot be dismissed as merely different consumer build artifacts or
copied-executable bytes. Failed-wave CPU and premature elapsed times are not gains.

## Actual failed path and loader selection

D1536/D1540 sample only owned reproduced failed processes. Their quiet windows
are predominantly `dynamic_load -> dlopen -> dyld mapSegments -> fcntl`, not
Scheme macro execution. These are one-second diagnostic stack observations,
not whole-run attribution or proof of a specific fcntl command/security cause.

D1540's descriptor snapshot identifies the open native file as
`lib/gerbil/core/contract~3.o2`. Other already mapped core images also use `.o2`.
They are not the aggregated `.o1` files whose hashes were compared.

Gerbil runtime loader `__find-library-module/find-compiled-file` starts at `.o1`
and walks consecutive existing versions until the first gap, returning the last
path. Gambit's load-without-extension loop follows the same contiguous-version
rule. Neither rule selects an old `.o1` merely because that file exists or matches
another profile. No change to either rule is proposed; Linux behavior is retained.

D1541's initial recursive inventory also included dSYM debug companions whose
DWARF basenames end in `.o1`. Its totals are withdrawn as a native-image inventory.
D1543 explicitly excludes `.dSYM` directory components and retains unsupported
formats conservatively. The corrected actual library inventory has 1,100 module
bases: 1,033 select `.o2`, 67 select `.o1`, with generated SCM present for each.
Of the old closure's 391 targets, 354 currently select a higher native version.

D1542 independently records actual dyld loading during a successful original
current-profile `gerbil test` of the unchanged regex owner. The original process
exits zero with 19 CASE-OK records and final OK. Its observed library closure is
185 native images: 164 `.o2` and 21 `.o1`. Loader diagnostic output is not counted
as product-progress or timing acceptance. Consumer/third-party images are outside
the reported toolchain-native closure.

## Decision

The current composition's construction checks proved equality for the wrong
native-version targets. That is an implementation/inference error in this
experiment, not an optimization of the actual current execution path. Newly
copied, unaggregated higher-version files remain on that path; the failed stack
and descriptor observations are consistent with mapping those files.

Do not transfer D1532's twofold advantage to current 0007, promote old image
aliases, report failed current tests as acceleration, or claim the original
seven-to-eight-second macro cost is solved. Next construction must capture and
verify the actual active-version objects from current inputs, preserving all
source/ABI/init/binding/invalidation boundaries and testing the real selected
paths. This is now a concrete source-input correction, not another blind packing
ratio or timeout change. The full requested goal remains active.

Evidence: `.data/d1528-parity-bounded-images/` through
`.data/d1543-current-active-native-images/`, especially D1532, D1534/D1535,
D1538/D1539, D1540's raw sample/descriptors, and D1542's actual load trace.
All owned sessions are terminal; no commit, push or system install is performed.
