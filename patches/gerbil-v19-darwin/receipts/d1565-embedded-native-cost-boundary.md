# D1565: embedded original objects remove native loads, not the first-log cost

Correction: D1585 supersedes the family-wide load-removal and first-window
control conclusions below. DYLD tracing omitted the shebang child, and the
custom baseline child PATH was not locked. These historical measurements remain
recorded, but are not whole-family same-binary causal evidence. See
`d1585-family-native-reuse-and-first-log-gate.md`.

## Scope and source change

This turn is progress beyond D1555: a native Gambit prototype, real same-binary
controls, actual load-path evidence, complete build and concurrent contracts.
The original canonical staging, GNU GCC 16, current 0007 baseline and hardware
sized twelve workers are retained. Everything new lives in isolated `.data`.
No Gerbil, std/make/std/test, consumer, package or HTTP product code changes.
Existing optimization patches remain unchanged; no production patch is promoted.

D1556 copies only Gambit's os_dyn.c and adds an explicit opt-in compile guard
requiring Darwin, Mach and GNU GCC, excluding Clang. Before allocating a dynamic
load entry, the guarded path asks an executable-local native linker lookup;
a miss continues through unchanged ordinary dynamic loading. Successful hits
use the original setup_modules path; Scheme modules are not eagerly initialized.

The first build fails for a missing configured config.h include directory. That
receipt remains. D1557 supplies the original configured source include path and
successfully compiles the loader, registry, original unmodified Gerbil link
carrier, and executable with the original static modules/runtime archive.

All 280 D1548 verified native objects are reused. A bounded thin-Mach-O object
transform changes only an external linker symbol name and its string-table
reference, preventing basename collisions; native text remains byte-exact for
every object. No object code recompilation, new macro optimization or replacement
SCM is involved. A generated private registry maps original path and linker name
to unique embedded exports, gated by GAMBIT_EMBEDDED_NATIVE=1.

Lookup requires the recorded device, inode, size, mtime and ctime including
nanoseconds, and a regular file. Unknown paths/names or changed identity fall
back. Registry paths are private experiment data, not a relocatable install
mechanism or a production content/security proof. Ordinary executable linking
and system validation remain; no signature or security policy bypass is used.
Both enabled and disabled standard-library import smoke runs pass.

## Actual load-path evidence

D1558 executes unchanged real MCP regex tests: exit zero, 19 CASE-OK records and
final OK, with zero toolchain native images in genuine dyld output. All 185 paths
in the successful original D1542 trace are present in the embedded input set.
The older diagnostic's boolean remains false because it requires a nonempty
image list; this is retained, not silently rewritten into a qualified receipt.
The raw successful test and zero-load result are the evidence used here.

D1560 runs fresh official MCP clean, verifies zero project native images, and
observes actual first compilation. Only three toolchain native images remain:
libcrypto, zlib and libssl; none is embedded or modified. Instrumented first
compilation is 5.904718 seconds. This is load-path diagnosis, not timing admission.

## Same executable and library home controls

D1559 real clean/build first-log ABBA uses exactly the same embedded executable
and original library home, changing only the lookup environment switch. All
cleans exit zero with no native artifacts, all first-log gates pass, and inputs
remain unchanged. Successful builds deliberately stop at first compilation.

| Role/order | First compile seconds |
| --- | ---: |
| A disabled | 6.394399 |
| B enabled | 6.704633 |
| B enabled | 5.808738 |
| A disabled | 6.514907 |

Means are 6.454653 versus 6.256685 seconds, only about 3.1% difference with
overlapping ranges. This route does not resolve the first-log objective. The
eliminated native calls cannot be equated to eliminated Scheme execution cost.

D1561 same-binary/same-home actual MCP test ABBA runs twelve processes per wave.
All 48 pass exit zero, 19 CASE-OK and final OK: 912 cases. Five-second real-output
and 90-second wall gates remain. Process means are 2.422920 versus 1.626157
seconds, about 1.49x; wave user-CPU means are 12.618521 versus 6.163820 seconds,
about 51.2% lower. First-CASE means are 1.971575 versus 1.617101 seconds.
These are observed current regex-test benefits, not fresh executable first
launch, every MCP test, or CI-wide performance qualification.

## Construction and contract gates

D1562 links the actual registry object into a diagnostic guard driver. Controlled
stat substitution checks a valid hit, disabled switch, wrong name/path, failure,
device/inode/size changes, both timestamp components, and nonregular file mode:
13 predicate checks pass. Original files are unchanged. This is a unit boundary,
not real runtime reinitialization, replacement-race or universal FFI proof.

D1563 completes a fresh actual MCP clean/build with lookup enabled: clean exit
zero, zero residual native files, first compile 5.711648 seconds, full build
61.544324 seconds, build exit zero and executable produced. Source is unchanged.
It is candidate-only construction evidence, not a matched full-build speedup.

D1564 passes twelve starts, twelve make/test imports, and actual macro-heavy
std/make cold/no-op/invalidation plus std/test contracts with lookup enabled.
Worker setting is twelve; ten simultaneous GCC frontends are observed. Maximum
real-output gap is 3.846670 seconds. Candidate-only phase times are 11.480710,
0.008364 and 1.629190 seconds, not performance comparisons.

## Decision and remaining gate

Retain the verified object inputs and test execution advantage as research
artifacts. Do not ship the embedding prototype: install relocation, initialized
module lifetime, cleanup/reinitialization and runtime replacement semantics are
not qualified. In particular, permanently linked dynamic-module state is not
automatically equivalent to unloading and freshly loading an image.

For the major first-log objective, pursue the remaining Gambit Scheme execution
path rather than extending native-load caches or claiming native-load removal
solves macro execution. Full toolchain/source integration and the seven-to-eight
second objective remain incomplete. All owned processes are terminal.

Evidence: `.data/d1556-embedded-native-source/`, `.data/d1556-embedded-native/`,
and `.data/d1557-embedded-native/` through `.data/d1564-embedded-std-make/`.
