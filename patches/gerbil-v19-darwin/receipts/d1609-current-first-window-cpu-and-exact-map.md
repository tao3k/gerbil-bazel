# D1609: current first-window CPU burst and exact carrier map

The preceding turn made progress with a complete adjacent ABBA; all four builds
failed the user's 55-second ceiling. This turn returns to remaining first-log
execution, not repeated complete-build timing or previously rejected strings,
hash scan, generic optimization or GC-only variants. The goal remains open.

## Actual Builder And Hardware Capture

The existing first-window diagnostic now accepts a qualified flat native
binary and explicit embedded lookup. Required-builder mode waits for the
actual build.ss child rather than silently sampling its outer parent. libproc
resolves that child's executable and checks path and SHA before attachment.
No Gambit/Gerbil product source, consumer source or installed binary changes.

D1607 uses the unchanged D1590 composition with D1391 libraries/GSC/RTS,
original MCP head and twelve workers. Official clean succeeds with zero project
native images. Attachment is requested at +1.331629 seconds to the verified
builder child. First literal compilation appears at +4.818600 seconds, with
the unchanged ten-second output gate passing. The build is deliberately stopped
and reaped with exit 70; this is not a complete build or performance comparison.
The sampler exits zero and exports actual hardware records.

907 Running rows contain 779,601,046 active-core-cycle weights, with 775,217,867
cycles validated against actual native function starts, UUID and SHA. One
zero-weight row is kept separately. Crucially, the actual exported rows span
only 0.401846 seconds of trace time. The sampler-launch-to-first-line interval
does not equal the recorded CPU window. Attachment startup and the polling
termination boundary prevent treating this burst as the whole pre-first prefix.

| Function in this short burst | Self-cycle share |
| --- | ---: |
| coalesced Scheme host | 29.45% |
| mark_array | 23.03% |
| mark_array constprop clone | 19.11% |
| garbage_collect_pstate | 5.79% |
| movable-object scanner | 3.73% |
| GC hash lookup | 2.61% |

This GC-heavy burst does not replace D1009/D1105's wider execution accounting or
justify a GC-only speedup claim. Old 187-module preparation proportions likewise
cannot simply be assigned to this current actual child. Wider coverage of the
same real first-window execution remains needed before selecting a major route.

The initial summarization correctly refuses the flat binary: its legacy binary
home points to common D1391 rather than D1590. A new explicit native-binary
argument requires actual child verification, matching reported child/GXI SHA,
isolated .data location, plus the existing recorded-image UUID/SHA checks.
Summarization then succeeds without rewriting the original recording receipt.
Four new refusal/acceptance tests and fourteen existing first-window/native CPU
tests pass. Future sampler receipts additionally record the actual native ref,
flat overrides as partial runtime profiles and physical rather than logical
worker discovery; D1607's original report is preserved.

## Exact Current Source Mapping

The retained D1108 debug carrier cannot be reused unchanged: its relocation
records match, but 44 bytes of current __text differ. Both text extents are
1,126,540 bytes; matching sizes, function starts and relocations alone are not
enough for exact source attribution.

D1608 compiles only a debug object from the locked current D1508 carrier source,
using the existing GNU GCC recipe and unchanged generated helpers. No product
binary is relinked. Entire __text and symbolic text relocations then match the
executed D1510 carrier object exactly, with text SHA256
087382cb4239ed3bb462a1669d8ce6850b6f26205fb122a74d5f030e00038f7e.
Twenty actual coalesced-host PCs map successfully through DWARF.

Mapped instructions include the shared host entry, syntax-e arity/structure
checks, stx-source ancestor-type test and returns, import-binding alias traversal,
and the already-selected context-resolve helper setup. These are real C lines,
not exclusive procedure costs or a newly dominant single optimization. Keep
prior guarded-outline/type-chain/return-outline negative evidence; this short
burst does not admit another broad return expansion or a speculative cache.

Evidence: `.data/d1607-real-composed-first-cpu/`,
`.data/d1608-current-carrier-debug/`, and their isolated original source scripts.
No real test suite is rerun or claimed qualified in this turn. First-log stability,
complete build <=55 seconds and actual concurrent make/test acceptance are still
required. All owned sessions are terminal. No release patch, full-toolchain
rebuild, commit, push or goal completion is admitted.
