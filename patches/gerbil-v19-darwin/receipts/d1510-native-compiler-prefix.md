# Native Compiler Prefix Preservation

## Review And Root Cause

Correct path: preserve the actual GNU GCC recipe before considering any timing
claim. The native 0035/0036 argument builder used the executable component of
`C_COMPILER` but omitted its remaining arguments. Frozen MCP's
`-ftrack-macro-expansion=0` therefore disappeared. More generally, an explicit
compiler-prefix `-D` option could change generated code while the native backend
still recorded the declared shell recipe. This is a correctness defect, not a
new general hashing optimization. CommonCrypto digesting is already implemented;
producer fusion and unchanged denied capture routes are not reopened.

The real control `.data/d1510-native-compiler-prefix-denied-v1` declares
`-DCOMPILER_PREFIX_VALUE=29` and compares ordinary GNU GCC with native capture.
It rejects with exit **42** because the objects differ. The ordinary object SHA
is `95d496216adf6cfcb0a5784713aeebd0f5950bf7deb1580da69d5cf20f3e9dea`;
the incorrect native object is
`123a9c38ce986b23df57d42131eacaa72ee59a533b70c11924422e6eea0ff95a`.
This proves the argument loss; it does not prove its share of total build time.

## Independent Experimental Patch

0043 follows 0036/0038. The shell helper transmits the compiler-prefix arguments;
the native backend inserts them before the existing optimization/object flags
for capture, preprocessing and rebuilding. The context key explicitly includes
them using a v3 domain. Tool/source/environment/CPP/object content validation is
retained. Complex prefixes return the existing validated fallback; the old
24-argument protocol also returns fallback 77 rather than silently dropping flags.
Unsupported compiler-prefix flags now receive the same conservative checks as
other compiler options. Existing non-Darwin/default-off dispatch is unchanged.

`.data/d1510-native-compiler-prefix-controls-v3` passes population/HIT for value
29, option-change MISS and repeat HIT for value 31, all with exact ordinary GCC
object parity. `.data/d1510-native-compiler-prefix-modes-v1` passes dynamic/static
mode changes and matching-mode HITs. Patch reverse/forward source parity,
unsupported-protocol controls and the focused controller/frozen suite pass
**54 checks**. The helper is compiled with genuine GNU GCC, the macOS SDK and
the Darwin linker; a first inherited-linker attempt failed and is not admitted.

| Artifact | SHA256 |
| --- | --- |
| 0043 | `c87fcc0458642eb8cf7d12a68daabff135fae5dac7aed9ae8f959e3ccd0d01e5` |
| Native helper executable | `6aa7801f3b88a4b189572622c40b740da2ef8a034f67cd9a174eb6ac2463eb2b` |
| Shell helper | `36d663b110d0579d88758927dfb24d82ada2c34b10cfa8df25dd00310c1b541f` |

## Whole MCP Admission: Both Configurations Denied

| Configuration | First log | Build stop | Completed backend events |
| --- | --- | --- | --- |
| Frozen AOT recipe, old native backend | 4.228276 s | DENY at 42.043020 s | 166 capture MISS, 0 HIT, no closed link |
| Same AOT recipe plus 0043 | 3.939208 s | DENY at 42.007643 s | 186 capture MISS, 74 check HIT, one closed link |

Both were real clean builds with zero remaining native images after clean.
Both exceeded the unchanged **42-second** build ceiling, were killed/reaped,
and skipped full tests. These stop times are **not complete build durations**.
First-log variation is not attributed to this backend change. 74 real HITs
prove object handoff happened, not whole-package correctness or performance.
Neither unchanged configuration should be repeated to seek a passing sample.

Receipts are `.data/d1510-recipe-frozen-aot-mcp-qualification-v2` and
`.data/d1510-recipe-prefix-mcp-qualification-v1`. Report SHA256s are respectively
`29eb5123604918766dc6add585ee2e52efed293d61c8c75cd4a982a838dee103` and
`6770e6713fb2588bdc689cf253def3ee419d0f916f9bab7a36611c0c377aa47e`.
The first sandboxed launch failed sysctl discovery before a benchmark; it is
not a timing sample. The old and new private compiler homes are separate.

The required next improvement must reduce real capture/HIT verification work,
not omit tool or CPP validation. Eight tool files total 68,563,495 bytes per
snapshot for this exact private compiler pairing. Two snapshots per capture
would hash 22,763,080,340 bytes across the old 166 captures; this is a source/size
cost calculation, not measured CPU attribution or a promised wall-time gain.
Existing HIT-cost measurements already constrain simplistic hash/fusion claims.

Frozen six-patch MCP remains unchanged and verified: first logs
4.038/3.980/3.950 seconds, cold builds 36.414/35.552/37.770 seconds, and complete
tests 86.924 seconds with 39 files/965 cases, under **4.5 / 42 / 97 seconds**.
0043 remains an independently proven correctness building block, outside that
series. Complete new MCP/ASCENT qualification and release admission are pending.
