# Planned Producer V11

## Reviewed Direction

The prior V9 MCP experiment generated 186 producer records without an observed
new Scheme-link consumer before its build deadline. The new contract requests a
proof only for library-only build specifications that will expose a Scheme static
closure. Existing executable specifications keep direct C/object reuse. This is
generic compiler-consumer routing, not a package-name exception or log reordering.

Expected gain is removal of irrelevant proof work, not a claimed numerical MCP
speedup. This route has a new implementation and controls; it does not reopen the
unchanged V9 configuration or the rejected external dispatcher.

## Separate Candidate Artifacts

`0023-gerbil-darwin-planned-library-producer.patch` replaces experimental 0022
at the same original std/make base; **do not apply both**. SHA256:
`c1f0c0d5aaff6f627e9cfd357d7118db7f804c83eacffeed9cfee7672d65dbe2`.

The patch carries a boolean explicitly through build workers and nested specs to
the GSC option list. Darwin and the existing opt-in flag are required. Ordinary,
static and optimized executable specifications do not request proofs; the original
static-capture policy for exe/static-exe is preserved. Linux uses the original
capture policy with no new GSC option. No parent-process environment is mutated.

`gambit-generated-c-planned-producer.scm` adds a CLI-local request contract. The
preparer adds the boolean `-generated-c-proof` option and strips it before compiler
transformations or context construction. Requests select the existing validated
producer; absent requests take the original compiler. Source/options/tool/env,
alias, pin, failure and concurrency validation are not weakened.

Native GSC profile: `d1510-native-generated-c-profile-v11.json`.
GSC SHA256:
`d9120bda14708071e1870d504eb06ba86d65f1eeff09854bc3c608b04879dccd`.
Both in-process digests and planned producers require explicit controller options.
Compiled std/make overlays are content-bound across cold build and tests, including
interfaces, images, Scheme source and optimizer metadata; mismatches deny admission.
All old V8/V9 profiles and frozen MCP patch hashes remain unchanged.

## Executed Controls

`.data/d1510-native-generated-c-planned-controls-v1` passes no-request parity,
requested MISS/HIT, whole-link C parity, changed source/debug/index fallback,
backend invalidation, failed compilation preservation and work cleanup.

`.data/d1510-std-make-planned-producer-v4` passes real std/make library production,
native link adoption, whole-link byte parity and fresh dynamic-library import.
It also builds and runs a standalone executable with **zero producer records**.
Output is `PLANNED-EXECUTABLE-OK`; its log SHA256:
`22ef6050604675c7e26e89afa33aac5871be25a36f5fd8b200c314c254f9d841`.
Native/original link C SHA256:
`572e4a62c8562a48091545be329ea45d40d7b5c6d2c457f4f5a2d483af8d3435`.
Focused profile, overlay, progressive and three-time-gate unit checks: 46 passed.

Failed preparation v10 placed an expression before Gambit's internal definitions;
v11 moves selection after definitions and builds with genuine GNU GCC. Fixture
v1 lacks a helper in the original runtime; v2 lacks the executable library load
path; v3 encounters the retained runtime's outdated OpenSSL link directory.
v4 uses the isolated selected driver, explicit output load path, current SDK and
Homebrew dependency discovery. None of v1/v2/v3 is a successful performance sample.

## Whole MCP Gate: DENY

Receipt `.data/d1510-native-generated-c-mcp-v11-planned-v1` is terminal:
official clean 3.174136 seconds, exit zero and no remaining project native images.
Build stops at **4.545961 seconds** because no actual compile log arrived within
the **4.5-second** first-log ceiling. Owned process group is reaped, terminal -9.
Complete build and tests are unknown; they are not passing samples.

Raw report SHA256:
`95d610fd31ff0f58d43cc4395944d420ab7077c5b87dc564d1382cd884500495`.
Admission SHA256:
`cdfd5da354ed5b42b7a6aec5e8e8a661a3f13ddde353ecbc8b45f5fae126688f`.

The build log is empty, so this failure does not measure proof creation or reuse.
The owned overlay has a different build recipe from the retained std library
(notably original std/build.ss requests debug metadata). A loading/recipe audit
is needed before attributing the first-window failure to the new compiler route.
Do not repeat the unchanged whole task or widen the gate. This candidate is not
added to the frozen MCP series; full dual-consumer qualification remains open.

## Matched Recipe Correction Still Denied

`.data/d1510-std-make-planned-producer-v5` now builds the overlay with the original
standard-library `debug: #t` recipe. All library and executable mechanism controls
still pass. Debug symbol `.dSYM` directories are not loadable modules and are
excluded from runtime overlay identity; symlinked symbol bundles and every
loadable-module symlink remain denied. Focused combined checks: 52 passed.

The first V2 request fails preflight on the debug symbol directory before creating
its output or running a workload. After correcting that classification, real
`.data/d1510-native-generated-c-mcp-v11-planned-v2` is terminal DENY: clean
3.431726 seconds, exit zero, no native images; build interrupted at 4.523109
seconds before any compile log. Child reaping is confirmed, terminal -9. It has
no complete build/test duration. No performance ceiling was changed.

Raw V2 report SHA256:
`8bb9c65de69cba089b015b9b7318c3fc50a07b128b91583ae10e9e3ca3e52d21`.
Admission SHA256 remains:
`cdfd5da354ed5b42b7a6aec5e8e8a661a3f13ddde353ecbc8b45f5fae126688f`.

A targeted direct import of `:std/build-script`, using the same frozen gxi,
runtime, project and GAMBOPT, passes with both old and new module paths. The
single diagnostic control/import observations are 0.45 / 0.29 seconds
(`.data/d1510-planned-overlay-import-v1`). They do not establish a stable speedup,
but provide no evidence that simple overlay import explains the first-window
failure. Do not claim the recipe mismatch was its root cause: correcting it did
not restore the MCP gate. Compared recorded environment values outside the
intentional GAMBOPT/GSC/load-path changes match the frozen MCP receipt.

The routing mechanism is implemented and independently correct, but remains
unqualified for release. Preserve this negative result and investigate the
remaining package-initialization path before another whole-task candidate.

## Frozen Interpreter And ASCENT ABI Verification

`.data/d1510-std-make-planned-frozen-interpreter-v1` repeats the full mechanism
fixture with MCP's exact frozen interpreter, not the ordinary runtime binary.
Library proof, actual link adoption, whole-link C parity, fresh dynamic import
and executable execution with zero proof records all pass. This verifies that
the overlay executes correctly despite the interpreter's embedded providers;
file fingerprint checks alone would not prove that boundary.

The independent ASCENT-ABI GSC is
`.data/d1510-native-generated-c-ascent-gsc-v3`, SHA256:
`eb43f94804f04d15224906aee1323f267fa325f9f6f63f69ad95273cc2dc538c`.
Its header matches the frozen multiple-VM runtime, not MCP's single-VM header.
Native contracts and the real std/make library/executable fixture both pass:
`.data/d1510-native-generated-c-planned-ascent-controls-v1` and
`.data/d1510-std-make-planned-ascent-v1`.

Real isolated cold positive-plan task:
`.data/d1510-native-generated-c-ascent-planned-positive-v1`.
The 135-second whole-task ceiling is the earlier 122.05-second candidate duration
plus ten percent, rounded upward. GNU timeout enforces it; native compilation and
tests run directly under Bash/just, with no Python supervision. No per-file silence
rule is added.

Result **DENY**: layers 85 and 87 finish; the Suite starts compilation but no
Case pass or native-link adoption is reached before timeout. The wrapper is
terminal with status 1. Raw BSD time records 136.02 seconds, including termination
grace, and reports an abnormal signal with zero CPU fields. Those CPU fields are
not a valid CPU measurement, and 136.02 is not a completed-test duration. No
correctness or performance pass is claimed; old 122.05-second evidence does not
qualify this different binary/overlay.

Output SHA256:
`5bc47d88fff0e8406d0e5813bbc47ffd3eaf743dfcc91d921ab092a06fc80196`.
Raw time SHA256:
`e3659a6236cfa7f03abf3f1f123be950dfa431ee5abc4cb0dab9b56a50347a92`.
Host process inspection finds no remaining command from this workspace or its
timeout group. The 1,989 remaining read-only toolchain images, nine owned overlay
files and 2,809 dependency images verify after the task; project Git diff is empty.

## Reviewable Gambit Source Patch

`0024-gambit-darwin-planned-generated-c-reuse.patch` contains the actual prepared
GSC/main changes and seven helper sources, not only a fixture-generation recipe.
It is experimental, Darwin-only in application scope, default-off, and outside
the frozen series and release workflows. Its CommonCrypto backend is not a
portable Linux patch; no Linux application/build qualification is claimed.
Apply 0023 at the Gerbil root and 0024 at the Gambit root. Do not stack 0022 with
0023. Full upstream-staging toolchain rebuild remains unqualified.

Patch SHA256:
`21a8d8654bdf2d1c855f96decae56b90598cf376717cf19f0c509caf1cb249c0`.
The reusable `check_native_generated_c_patch_replay.sh` derives it from the
original and compiled source fixtures, then actually reverses and reapplies it
inside a separate Git root. All seven newly created helpers disappear on reversal;
both original entry files and all reconstructed prepared files match byte-for-byte.
`.data/d1510-native-generated-c-patch-replay-v1` passes. The generated patch has
no personal absolute paths or package-specific MCP/ASCENT identifiers.

These artifacts improve reviewability and prove mechanism compatibility; they
do not override either consumer's DENY. Both consumer performance gates remain
open, and the frozen best MCP stack is unchanged.
