# D1390: frozen object-reuse profile on current staging

The user explicitly requested retaining and pursuing D851's object-reuse
direction. This permits investigating its existing Gerbil compiler/build-graph
changes; it does not authorize unrelated package or HTTP changes.

## Git and source identities

Patches 0007 and 0008 were already tracked in commit `d255435`. They were not
lost, but are absent from the default release workflow. There are nine tracked
patch files in this directory, not nine admitted performance optimizations.

Canonical `v0.19-staging` was checked live against
`https://git.cons.io/mighty-gerbils/gerbil.git`: it is still
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, with Gambit gitlink
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
`runtime-object-reuse.json` freezes that source and the SHA256 identities of
0002, 0003, 0007 and mandatory pure-module safeguard 0008. It is a source
profile, not a complete toolchain configuration or release admission.

## Actual replay and syntax checks

`tests/replay_runtime_object_reuse.py` cloned the local source cache without
copying dirty changes, checked out the frozen revision in
`.data/d1390-runtime-object-reuse-replay/source`, verified the Gambit gitlink,
and applied the four checked patches in order. Every step exits zero.
Only `src/gerbil/compiler/base.ss`, `src/gerbil/compiler/driver.ss`, and
`src/std/make.ss` change. `git diff --check` passes. The structured report
is `.data/d1390-runtime-object-reuse-replay/report.json`.

An output outside project `.data` is rejected with exit 2 before cloning.
Python compilation passes. These checks do not execute the output dependency
contract or compile a new binary.

The first checkout-local `gxc -S` attempt fails because a clean checkout has
no generated `src/gerbil/runtime/version.ss`. The repository's official
`src/build/build-version.scm`, run by the existing cache GSI with the replay
source directory and revision, generates that file. The subsequent `gxc -S`
checks of all three changed Scheme files pass with exit zero, each bounded
by 30 seconds. Syntax outputs are isolated under the replay's `syntax/`.
This is expansion qualification using the existing compiler, not correctness
or performance qualification of a newly built candidate compiler.

## Gain and expansion boundary

D851's two complete MCP pairs show 72.130 to 60.690 seconds and 74.727 to
59.555 seconds. D862 reproduces an executable-closure interval reduction
from approximately 17.6 seconds to 0.061 seconds. These locate a real reuse
opportunity: compiling the module's PIC C object once and using it for both
the dynamic bundle and executable closure, with dependency/failure ordering.
They do not establish an improvement of the pre-first-compile expansion.

Current 0007 includes D874's output-dependency correction; the older timing
receipts predate it. Do not assign the historical gain to the current profile
without a new complete-build check. The pure-module path, toolchain static
closure, canonical linker identities and failure propagation must stay intact.
Broader reuse must establish compatible C definitions, PIC/optimization flags,
module identity and freshness; it cannot reuse an object just because its
source filename matches. Existing 0004/0012 GCC macro-tracking savings must
remain in the toolchain used for that verification.

No default release switch, Homebrew overwrite, consumer modification or
speedup admission is made here. Next build the isolated current candidate,
run the output-dependency contract, then actual order-balanced clean/build
and concurrent std/make/std/test gates. Keep first-log and whole-build results
separate and retain the user's approximately 56-second historical reference.
