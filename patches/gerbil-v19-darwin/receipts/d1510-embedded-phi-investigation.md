# D1510 embedded providers and generated phi source investigation

Status: **not admitted**. The frozen 49-second baseline is unchanged.
All paths below are project-relative. These are real local macOS measurements,
not Linux A/B evidence, production qualification or an exact-head CI result.

## Mechanisms

- Embed 280 exact-provenance native objects in the executable. Rename only
  their Mach-O entry symbols; do not pre-register or initialize their modules.
  The original Gambit object setup/registration/evaluation runs at actual load.
  An exact path/linker/content-SHA guard falls back to the original backend.
- Compile ordinary non-foreign phi code as generated Scheme, retaining native
  fallback for foreign/compiler-only forms and explicit debug compilation.
  This removes actual phi GCC work, not just moves the first log.
- Both are experimental, Darwin/Mach/real-GNU/non-Clang guarded. No std/make,
  std/test, package HTTP or MCP business-source edits are part of this change.

## Results Retained

| Candidate | First real compile | Complete cold build | Complete test wave | Admission |
| --- | ---: | ---: | ---: | --- |
| Phi source alone v2 | no log by 5.526 s | killed | skipped | DENY |
| Embedded providers alone v1 | 5.360 s | incomplete at 52.050 s; killed | skipped | DENY |
| Embedded providers + phi v1 | 5.071 s | 47.162 s, exit 0 | 52.137 s; 20/39 files passed, 19 failed | DENY |

Combined binary SHA-256:
`5bfa53ddb6a9f4597320095724b9244ccc4ab42b46f68d5f6fcb73ad79e40a4c`.
Cold source identity was unchanged. Full-test correctness and performance did
not pass, so **47.162 seconds is a cold-build result only**, not a new baseline.

Raw evidence:

- `.data/d1510-phi-source-progressive-v2/`
- `.data/d1510-embedded-provider-progressive-v1/`
- `.data/d1510-embedded-phi-progressive-v1/`

## Correctness Root Cause

Some generated phi source files were handed to Gerbil's source expander by
ordinary file/module loading. Gambit's `(declare ...)` was then rejected as an
illegal Gerbil expression. The initial 28-case source/native control had manually
bound `__scheme-source`; it did not exercise this real loading boundary and was
insufficient. Its success must not be used as production semantic qualification.

The next control removes that shortcut and exercises ordinary `##load`, `load`
and actual `load-module`. The candidate tags generated artifacts explicitly;
Gambit's file loader bypasses the language expander only for that tag on Darwin
GNU builds while retaining the compilation context, source locations, demanded
modules, callback and CTE behavior. Unmarked Gerbil files keep their original path.
This repair has not yet passed real MCP acceptance.

## Corrected Source Protocol v3

The 32 real controls pass, including ordinary `load`, `load-module`, original
native execution, GC, exceptions and unmarked Gerbil source. The corrected binary
is `ef48fb8e1d4ec1ff92f36c0cb4e25918d8e5ff6a17274c869948cf95c36c4db4`.

- First cold run: first compile **5.218 s**, complete build **47.274 s**, exit 0.
- Full concurrent test wave: **47.036 s**, **23/39 files passed**, 16 failed;
  517 `CASE-OK` lines were recorded. Real-output gap gates reject the failing
  files. These are not 965 passed cases or complete-test acceptance.
- Two subsequent cold attempts used the stricter **50 s** complete-build gate.
  Both were stopped before any compile log: first-log deadlines at **5.536 s**
  and **5.503 s**. Both owned process groups were killed with SIGKILL and reaped.
  Their complete build times are **unknown**, not 50 s or 52 s.

Evidence: `.data/d1510-embedded-phi-progressive-v3-r1/` and
`.data/d1510-embedded-phi-progressive-v3-r2-r3/`.

Therefore the requested repeated sub-50-second admission is **not satisfied**.
No replacement baseline or production patch is frozen. The runner now supports
an explicit 50-second watchdog and cold-only repeated runs without claiming that
skipped tests passed; the original lock remains unchanged.

## New Mechanism Controls

Compiled interpreter code was serialized without running the module, then
restored in two separate fresh processes. All **19 controls** passed: global
bindings, initial mutable state, aliases, multiple values, exceptions and GC.
This supports investigating removal of repeated phi parsing/compilation, not
a measured end-to-end win. Evidence:
`.data/d1510-compiled-phi-blob-controls-v2/`.

A separate raw-native AST serialization attempt for parsed `std/make.ssi`
crashed its consumer (exit -11) during deserialization. That representation is
**rejected** and is not used by the compiled-phi candidate. Evidence:
`.data/d1510-parsed-ssi-blob-controls-v1/`. No timeout or assertion was relaxed.

## Unchanged Gates

First real compile <= 5.5 s; complete cold build <= 52 s, target <= 50 s.
All 39 real test files and their 965 expected cases must pass, with final `OK`,
valid exit status and no swallowed errors. Complete concurrent test wave <= 52 s;
real test-output silence <= 5 s. Over-budget runs are forcibly stopped and reaped.
No threshold widening or baseline overwrite is allowed.
