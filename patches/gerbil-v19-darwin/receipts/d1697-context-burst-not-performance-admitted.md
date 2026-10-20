# D1697: D1510 bounded context burst remains unqualified

## Source change

D1689 starts from the exact retained D1508/D1510 carrier, not the unsuccessful
26-site discovery extension. The fourteen original entry sites remain. Only
the native helper for core-context-resolve site 11 changes. Original GNU GCC
O1 carrier compilation and O3 helper compilation remain selected; original
Darwin/GNU/non-Clang guards remain. No Linux activation, consumer SCM,
std/make/std/test product edit, package HTTP, installed toolchain or ABI change.

Within one native invocation the helper advances through at most 32 context
lookup misses. Binding/interface reads are kept only for that invocation,
never cached across calls. Each iteration retains entry and post-lookup
stack-trip checks and the original type-chain helper. No handled poll, Scheme
callback, heap allocation or live-frame write occurs inside the burst.

Moved-key tables return to original code before hash lookup, preserving lazy
rehash rather than pretending the original hash read is always side-effect
free. The original mem.c hash reference only reads when KEY_MOVED is clear.
Any binding change between invocations still takes the original path. Mutable
context parents and each new context's table remain live reads.

The private helper result grows from eight to nine words. The ninth is the
current logical cursor before the most recent lookup, which is exported to
the original negative frame slot on effect fallback. This preserves the
fallback continuation after multiple local iterations. Completed iteration
frame delta stays zero. No heap object identity is replaced or eliminated.
This is source reasoning plus limited native testing, not a general compiler,
interrupt/FFI or complete toolchain proof.

## Actual native tests

D1690 builds, links and imports successfully. Binary SHA256:
`9843e6532037ee7822eebd5e1af3e163e036a8584e35f6ce827543a066dec3c0`.

D1691 compares the actual original D1510 and candidate native operations in
twelve concurrent processes. All 432 cases pass: depths 0, 1, 31, 32, 33 and
160; absent, inherited, live-GC, nearest and removed bindings; rebindings with
callbacks, exceptions and continuation escape; restored function binding and
mutable/restored context parents. These are explicit semantic controls, not
a cold-start speed result or forced-interrupt qualification.

All 152 focused test_gambit unit tests also pass. Their scope does not override
the real workflow failures below.

## Complete build and workflow rejection

D1692 fresh MCP official clean exits zero, leaving zero project native images.
First literal compilation is **5.525691 seconds**; the complete build exits
zero in **70.949493 seconds** and produces the executable with unchanged
checked source hashes. The 55-second complete-build gate fails, so the driver
exits one. No matched speed ratio or major startup benefit is established.
Keep the historical D1513 candidate mean of 52.617045 seconds as the reference,
not the later 70-second result.

D1693 passes twelve native starts and twelve framework imports, but actual
std/make subsequently fails the unchanged five-second genuine-output gate
before compile progress. No overall std/make/std/test success is admitted.
Do not infer that the limited semantic tests close this workflow failure, and
do not attribute it to resources without cause-specific evidence.

## Configuration and counter boundary

The private full-build driver now supports --capture-configuration. D1692
retains its selected flags, compiler/version, GSC, build script, headers,
runtime archive and exact driver digest in configuration.json. The snapshot
is taken before the timed build starts. This is selected current configuration,
not every nested compiler argv or the missing historical full environment.
It narrows future drift but does not explain the historical 20-second gap.

The older counter wrapper enabled GAMBIT_EMBEDDED_NATIVE=1 while this actual
full-build driver used zero. D1695 therefore explicitly matches zero; this
alignment is not a loader optimization or an explanation of the gap. Prior
diagnostics retain their own recorded environment and evidence boundaries.

D1694 separately builds and controls the native-call/logical-iteration observer.
D1695 verifies the actual builder PID but fails the original ten-second output
gate without a frozen first-write snapshot. D1696 is executed and refuses this
failed observation. Exit totals are not substituted for first-write counts.
No actual first-window call reduction or CPU saving is admitted from it.

Canonical v0.19-staging input remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, twelve physical workers. This
candidate is private research, not a frozen success patch or completed goal.

Evidence: `.data/d1689-outline-context-burst-preflight/`,
`.data/d1690-outline-context-burst-native/`,
`.data/d1691-context-burst-contract/`, `.data/d1692-context-burst-real-mcp/`,
`.data/d1693-context-burst-concurrent-make/`,
`.data/d1694-context-burst-census-native/` and
`.data/d1695-context-burst-first-census/`. No commit or push performed.
