# D966: large string constants in the actual Gambit emitter

Status: source candidate saved as `0013-gambit-darwin-packed-large-strings.patch`.
Not in the admitted release stack. MCP first-compile latency remains unsolved.

## Timing boundaries

D857 measured one real MCP embedded module, not a whole MCP build:
mean C-to-object time was 12.04 s with STR macros and 3.93 s with packed words,
about 3.1x faster. Four objects were byte-identical. The separate 18.04 s
preprocessing observation used another diagnostic invocation; do not add it
to the 3.93 s or subtract it from an unrelated package total.

No D966 whole-package elapsed time or first-compile improvement is established.
The 7-8 s real first-compile delay is a separate acceptance target, preceding
the embedded module's native compilation. This patch must not be presented as
solving that delay or delivering a 3.1x whole-build speedup.

## Scope

Base: Gerbil staging `1cfb032c7a1612637da6205f5f8a15683eba3ba0`,
Gambit `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
Only `gsc/_t-c-1.scm` changes. Darwin-hosted compilers emit a packed branch
for ordinary strings of at least 4096 characters. This cutoff bounds the
candidate to large payloads; it is not a measured optimal threshold.
Generated C enables the branch only on Apple GNU/non-Clang, WS=8, CS=4,
little-endian targets. Other targets retain the original STR body. Small
strings and all NSTR output retain their original path. Padding and the
zero high half of odd tails are preserved. No consumer source or flags change.

## Validation

- Patch replay check passes against the isolated immutable staging source.
- Native MCP balance passes, 227 top-level forms after editing.
- MCP syntax cannot resolve the Gambit include/macro context; this is a checker
  environment failure, not a passing source check.
- An initial fallback incorrectly compiled the read API's entire result vector.
  Those apparent successes are invalid and discarded. The API returns
  `[script-line, source, port-name]`; real validation compiles element 1.
- Gerbil gxi's active readtable is incompatible with this Gambit namespace
  context. The checkout's native GSC, with `~~lib` pointing to its source macro
  library, passes actual full-file expansion for both original and candidate.
- `check_packed_string_emitter.py` reads the two changed definitions from the
  actual source and executes them in the native GSC macro context. It does not
  transform generated C or substitute an independently implemented emitter.
- Fifteen lengths cover 0, 1, 7, 8, 9, 4095, and 4096 through 4104. Values cover
  NUL, ASCII, 255, 256, 65535, 65536, and 1114111. GNU GCC 16 O1 objects from
  portable and packed output have the same SHA-256:
  `d8277cf5abcac3c85e9a1282d4d8b429fc46217361f0ab2ac9278fabd2faa1ab`.

## Rebuilt binary and real module

The native GSC rebuild completed with the baseline configured GNU GCC 16 flags
and `make -j12 gsc`. The candidate binary, not an interpreted hook, then emitted
the unchanged real MCP embedded module from one shared Gerbil-generated Scheme
input. Original C is 11,423,503 bytes; candidate C is 47,077,507 bytes including
the inactive portable fallback. Both GNU objects have the same SHA-256:
`acd11ac8db847cb9e45d8e0c398e522fedeea4835d14d536845bba6922bd5413`.
The packed branch was checked in the rebuilt compiler's actual output.

Under a loaded host, sequential emission/object wall times were 2.442/78.131 s
for original and 14.483/22.819 s for candidate. These are functional-run wall
observations, not a controlled performance admission. In particular, new emission
does additional work to preserve the portable fallback; its total cost must be
included, not hidden behind the earlier isolated 3.1x C-to-object result.

The local runtime and Gerbil SDK remain the unchanged D935 qualified artifacts;
only GSC was rebuilt. This is not a fresh whole-toolchain rebuild.

## Official clean/build attempt

The first lifecycle attempt failed the 10-second product-output gate in the
runner's unnecessary default `deps --install`; it never reached clean/build.
The runner now supports a narrow dependency-free MCP scenario: native Scheme
reading verifies that the manifest contains only package/version/description
fields before skipping dependency installation. No GXPkg source changed.

The next official lifecycle attempt passed that manifest check, but `gerbil clean`
exceeded the 10-second product-output gate and was terminated. Host load was
approximately 60. It never entered `gerbil build`: no new MCP total elapsed time,
first-compile time, or full test pass exists. This failure remains recorded and
the output gate was not relaxed.

Durable raw evidence is under project `.data/d966-*`, including
`d966-emitter-contract-qualified-context`, `d966-real-mcp-emitter`, and
`d966-mcp-clean-build-no-deps`. Whole clean build/test and first-compile acceptance
remain required. Functional object equivalence is not performance admission.
