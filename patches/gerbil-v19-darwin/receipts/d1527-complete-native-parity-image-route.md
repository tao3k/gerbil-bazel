# D1527: complete native-code parity for the existing image route

## Decision boundary

This finishes a previously incomplete construction/identity gate, not a new
image-packing discovery. D1215/D1219 already recorded approximately twofold
Native user-CPU reductions, alongside cold-output failures and weak full-cycle
results. D1255-D1257 failed to finish complete installed-native-code parity.
Those receipts are retained, not retroactively promoted.

The original D935 baseline remains canonical Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, and GNU GCC 16.
This is the original matched profile, not the D1391 object-reuse profile;
no composition with current 0007 or D1510 runtime is claimed.
All work is isolated in project .data. No consumer Scheme, std/make, std/test,
package/HTTP code, original objects or Homebrew installation is modified.

## Complete original-code reconstruction

D1518 retries only the retained missing `std/io/interface/socket~1` unit,
using unchanged original C and `-D___DYNAMIC -g` settings. Object compilation
finishes in 51.353349 seconds and linkage in 0.429536 seconds. The rebuilt
image's machine-code text equals the original byte for byte. Original 900-second
native-construction admission remains; no product progress gate is changed.
This does not establish why the older 900-second observation failed.

D1519 independently checks original/source/C/object/text hashes and actual
generation logs before combining 242 prior verified objects with the two
successful retained-unit retries. Its 244-unit evidence manifest deliberately
remains incomplete and non-performance-qualified. Missing generation logs in
the descendant tree are resolved from the hash-locked D1253 ancestor, with
matching generated C; no empty replacement log is manufactured.

D1520 reuses those objects and finishes the complete 391-unit ordinary native
closure with twelve GNU workers. Every rebuilt individual image's machine-code
text matches its original installed image, with original debug/macro settings.
The same original gxi/GSC binaries are retained. Five aggregate images are then
constructed and framework/Native preload imports succeed. This is a prototype
image construction, not a full fresh source/toolchain build or general FFI gate.

D1521 reapplies conservative system-only/weak-binding/initializer exclusion,
reusing all newly validated objects. Group sizes are 298, 60, 22, 9 and 2.
The three original exclusions (libcrypto, zlib and libssl native FFI images)
were outside this 391-unit closure; direct current hash and non-symlink checks
confirm they remain byte-exact in original, reconstructed and conservative homes.
The new report's empty preserved-input array describes its selected ordinary
closure, not evidence that the three outer exclusions disappeared.

D1526 checks each complete group's Mach-O semantics. All five have zero duplicate
definitions, zero potential newly internal cross-image bindings, zero added or
removed definitions, matching architecture/flags/literal rpaths, and no original
or new native initialization hooks. The three outer FFI images also pass unchanged
hash checks. This static binding audit does not prove arbitrary unload,
replacement, invalidation, reinitialization or all FFI behavior.

## Real MCP first output: not admitted

D1522 binds the validated image inventory to the unchanged original executable.
D1523 uses four fresh MCP fixtures at
`9a5c35e275e5d6847ff421151bb224f2eae177c1`, official clean and actual build,
twelve configured workers, ten-second real-output and thirty-second prefix gates.
Both roles have identical executable bytes; library images alone differ.

| Order | Role | Clean seconds | First compile seconds | Gate |
| --- | --- | ---: | ---: | --- |
| A | Original | 3.636303 | 6.606005 | Pass |
| B | Packed | 1.854895 | Not observed | Fail |
| B | Packed | 1.453716 | 6.484673 | Pass |
| A | Original | 3.196989 | Not observed | Fail |

All cleans exit zero and leave zero project native images. Failed build logs
are empty; failures are retained. Observed builds stop at the literal first
compile and are not complete builds. There is no valid ABBA startup ratio,
no accepted large MCP first-log improvement, and no resource-only explanation.

## Actual Native execution and concurrency

D1524 executes the same byte-exact five-case parser Native owner through its
original harness, ABBA with unchanged five-second real-output and 90-second
wall gates. All four processes exit zero, produce all five CASE-OK records,
propagate HARNESS-RETURN status zero, and finish final GC/final Native OK.

| Role | User CPU seconds | Wall seconds | First CASE seconds |
| --- | ---: | ---: | ---: |
| Original | 1.380289 | 37.702459 | 37.556088 |
| Packed | 0.681474 | 1.493713 | 1.404288 |
| Packed | 0.674323 | 0.981506 | 0.887686 |
| Original | 1.234613 | 1.636600 | 1.512181 |

User-CPU means are 1.307451 versus 0.677899 seconds, 48.15% lower / 1.93x.
This retains the previously observed major CPU advantage with stronger original
machine-code identity evidence. The first original wall sample is much larger
than the last; do not present its wall ratio as stable latency improvement.
Its genuine import output stays within the original gate (maximum gap 2.454752
seconds), not synthetic heartbeats. No full parser CI or MCP-suite claim follows.

D1525 expands the candidate to twelve concurrent copies of that unchanged owner.
All twelve pass: 60 cases, all zero exits, final GC and Native OK. Maximum real
output gap is 0.611451 seconds; longest individual wall time is 2.467066 seconds.
This is semantic/concurrency acceptance without a paired concurrency speed ratio.

## Remaining work

The image route now has complete original machine-code text parity and a scoped
major Native CPU result; its prior identity blocker no longer applies. MCP first
output still fails the unchanged batch gate. Production Darwin-only Gambit
integration, arbitrary replacement/unload/FFI contracts, a fresh complete
toolchain and the requested major MCP build/test delivery remain unproven.
No patch is promoted, and existing 0001/0007/preprocessing advantages are untouched.

Evidence:

- `.data/d1518-original-socket-parity/` and `.data/d1519-merged-original-parity/`
- `.data/d1520-original-parity-image-closure/` and `.data/d1521-parity-system-only-packing/`
- `.data/d1522-image-first-envelope/` and `.data/d1523-parity-image-real-first/`
- `.data/d1524-parity-image-native-abba/` and `.data/d1525-parity-image-native-concurrent/`
- `.data/d1526-parity-packing-binding-audit/`

All owned native build/test sessions in this batch are terminal. No commit,
push or system install is performed. The full goal remains active.
