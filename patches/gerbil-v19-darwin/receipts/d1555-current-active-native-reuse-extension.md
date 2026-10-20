# D1555: active native object reuse doubles established MCP test throughput

## Scope

Canonical staging was verified live as
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit remains `ea114fc3`.
All native reconstruction uses Darwin, real GNU GCC 16 and twelve physical
workers in isolated project `.data`. Existing patches are retained. No product
SCM, std/make, std/test, HTTP, consumer source or security policy is changed.
This candidate is not a production patch or complete fresh toolchain build.

## Actual execution inputs and original object parity

D1545 failed generation because GSC used its obsolete compiled install prefix.
D1546 supplies the current isolated GAMBOPT directories; two active `.o2`
modules reconstruct with byte-exact native text, identical direct dependencies,
and unchanged original images and SCM. No old installation directory is created.

D1547 clones the recorded MCP head, runs official clean successfully and checks
zero project native images. Genuine first compilation occurs at 7.117571 seconds
under dyld tracing; this is diagnostic, not uninstrumented performance evidence.
It records 277 toolchain native images. Union with the successful D1542 actual
test trace contains 283 active images, all matched to the corrected inventory.

D1548 reconstructs all 280 ordinary system-only active images from current SCM,
original macro inputs and debug/C flags, with actual native-version linker names.
All 280 pass native text byte parity, dependency equality and unchanged inputs.
Two already verified current objects are reused with locked hashes. These checks
do not imply byte equality of all data sections or universal FFI semantics.

D1549 links nine groups, capped at 32 modules, targeting actual `.o2` paths rather
than inactive `.o1` aliases. All groups pass the conservative static audit: no
duplicate definitions, new internal cross-image bindings, export changes, new
initialization hooks, or architecture/flag/rpath changes. The three active
libcrypto/zlib/libssl images remain ordinary, byte-exact original files. Current
binary, GSC, headers, runtime archive and source metadata remain unchanged.

## Real tests: substantial established-load gain, initial-launch failure retained

D1550 uses the same original current executable and same current-built MCP
fixture for all twelve-process ABBA waves. Both original waves pass; the first
candidate wave has zero cases and fails the unchanged five-second output gate.
The second candidate wave passes. The whole experiment is unqualified; failed
wave CPU and elapsed times are not acceleration evidence.

D1553 separately repeats ABBA after initial loading and complete builds, without
concurrent timing harnesses. All 48 actual `gerbil test` processes pass exit zero,
19 CASE-OK records and final OK: 912 cases. Original five-second silence and
90-second wall gates remain. Source and consumer fixture are unchanged.

| Established-load result | Original | Active grouped images |
| --- | ---: | ---: |
| Mean process completion seconds | 2.529845 | 1.275530 |
| Mean first CASE seconds | 1.896165 | 1.267082 |
| Mean twelve-process wave user CPU seconds | 12.455829 | 5.971068 |
| Mean twelve-process wave wall seconds | 2.624359 | 1.407927 |

Completion is approximately 1.98x faster; user CPU falls about 52.1%. This is
current-profile, established-load regex-test evidence, not cold first launch,
full MCP suite, Scheme-only attribution, or the Linux/macOS CI-wide ratio.

## Cold build and contract gates

D1551's first-log-only experiment has candidate values 9.635524/9.647529 seconds
and a final original output-gate failure. It deliberately terminates successful
runs at first compilation. It overlaps the first D1552 baseline complete build;
therefore it does not admit a performance ratio, and that complete-build row is
also not a clean independent timing control. Neither overlap is hidden.

D1552 nevertheless completes all four fresh official MCP clean/build runs with
zero native images after clean, original inputs unchanged, exit zero and an
executable produced. Raw complete times are A 70.286384, B 66.127542,
B 74.524971, A 70.893094 seconds. First compile is respectively 6.250208,
5.718411, 5.357531, 7.040532 seconds. There is no substantial complete-build
gain and the initial test failure precludes cold-start admission.

D1554 uses the current original binary plus the active library overlay to pass
twelve starts, twelve make/test imports, and actual macro-heavy std/make cold,
no-op and invalidation/std/test contracts. Twelve GCC frontends are observed.
This candidate-only semantic check is not a matched speed claim.

## Decision

Keep the established-load test advantage and current original object inputs for
further Darwin/GNU-only Gambit work. Do not promote grouped-image construction
as a cold-start fix. The next gate is removal of the initial native-load failure
without warming as a prerequisite, weakening deadlines, or bypassing security.
Seven-to-eight-second first-log execution cost remains unresolved.

The diagnostic GSC recipe helper now accepts an explicit positive native version
and retains `.o1` as its backward-compatible default. Regression tests verify
`.o2` linker identity, unchanged module reference and invalid version rejection.
Nineteen focused recipe/partition/Mach-O/manifest tests pass. No changes committed.

Raw evidence: `.data/d1545-current-active-source-probe/` through
`.data/d1554-current-active-std-make/`, with terminal processes and retained failures.
