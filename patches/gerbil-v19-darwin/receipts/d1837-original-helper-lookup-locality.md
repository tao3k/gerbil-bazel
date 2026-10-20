# D1837: actual original-helper lookup locality, no acceleration admission

## Starting Line

Only original D1510/D1513 B carrier and original D1391 objects, library home,
GSC and RTS are used. The immutable development baseline is not replaced.
Canonical staging is checked live: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
GNU GCC and current twelve physical workers remain selected. No Linux path,
Gerbil product source, std/make/std/test, consumer or installed toolchain changes.

The preceding turn provided current original-binary timing evidence, not restored
best performance. This turn makes new progress by identifying actual lookup
locality inside original native helpers 7 and 11 rather than running another
unsubstantiated cache candidate or investigating the twenty-second discrepancy.

## Observation Is Not A Cache

Every original `___GCHASHTABLEREF(table,key)` still executes. A 64-slot direct
observation table per helper compares the current pair/result to the last
observation in the current window. Old words are compared only, never dereferenced,
returned or treated as GC roots. All 23 `___MR_ALL` definitions clear the window
through an epoch, including overflow clearing. Counters use the existing first
real write observer; the actual builder child and binary are verified.

D1831 and D1833 fail before native compilation on the source-shape assertion:
the shared lookup spelling occurs three times, not two. Generation is corrected
to select the exact helper function bodies; the unrelated third site is retained.
Failed directories are not overwritten.

D1834 compiles/links/imports successfully with unchanged original inputs.
Binary SHA256:
`1f09cb9de3920716d004070c0b7e5469244b9f6fcb17dacbae601445db3f5f5e`.
D1832 observes actual MCP builder PID 79843 through the first literal compile
line at 6.300530 seconds, then deliberately stops. Build exit 70 is expected;
there is no completed-build, performance or test qualification.

## Add Known-Write Fences Before Interpreting Reuse

D1835 additionally resets around `___EXPR` and after the original
`STORE_WORD`, `STORE_WORD_FX`, `GCHASHTABLEFIELDSET`, `GCHASHTABLESET`,
`GCHASHTABLEUNION`, `GCHASHTABLEFIND`, and `GCHASHTABLEREHASH` operations.
Original expressions are evaluated once and their values are preserved.
These are conservative observed fences, not a completed generic mutation audit.
The original lookup still executes on every repeated pair.

This binary compiles/links/imports with unchanged original inputs; SHA256:
`164dbcb0ff0bc2c12b394cf5b8bf40cfe248eb7faeed2563f55f6aa9dd2d0bcf`.
D1836 verifies actual builder PID 25301; first literal compile is 9.993238
seconds, just within the unchanged ten-second gate, then deliberately stops.
The diagnostic time is not a speed comparison or an admitted candidate.

| Original helper | Lookups | Repeated pair, reload-only | Repeated pair, known-write fences | Changed observed result |
| --- | ---: | ---: | ---: | ---: |
| 7 | 383,476 | 148,388 | 148,357 | 0 |
| 11 | 30,369,684 | 9,361,701 | 9,167,041 | 0 |

Total: 30,753,160 actual lookups; 9,315,398 repeated pairs remain with the
known-write fences, approximately 30.3%. This is lookup-count coverage, not
CPU coverage, a speed ratio, a general purity proof or a license to skip reads.
It differs from old D983 prefix-word caching, whose real-workload hits were zero.

## Source Boundary And Next Action

The original Gambit `lib/mem.c` lookup lazily rehashes when KEY_MOVED is set.
Suppressing a lookup can suppress this side effect, so a result-reuse candidate
must preserve that protocol. Original `lib/_system.scm` implements table field
writes through unchecked structure writes; listening only to the C table setter
is insufficient. The existing D1772 mutation evidence remains binding.

Next, assess the cost and full mutation/GC boundary of this genuinely executed
lookup family before implementing reuse. Small C-call savings alone must not be
called the major seven/eight-second solution. Any implementation must derive
directly from original D1510, demonstrate reduced actual execution, pass native
mutation/GC contracts and real concurrent make/test, and retain the 55-second
complete MCP build ceiling. No new cache is selected or admitted by this receipt.

Private source/receipts: `.data/d1831-build-lookup-locality.py`,
`.data/d1834-lookup-locality-native/`, `.data/d1832-lookup-locality-prefix/`,
`.data/d1835-build-fenced-lookup-locality.py`,
`.data/d1835-fenced-lookup-locality-native/`,
`.data/d1836-fenced-lookup-locality-prefix/`.
All owned sessions are terminal. No commit, push or baseline overwrite occurs.
