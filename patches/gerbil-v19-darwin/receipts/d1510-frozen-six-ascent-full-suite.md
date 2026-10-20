# Frozen Six-Patch ASCENT Full Suite

## Superseded Consumer Revision

**Historical-only: not current ASCENT PR performance admission.** After the
user requested an exact latest-PR audit, GitHub PR 1 was observed at
`78e1e7a35b6e65891a6c40d04b9c7ea445dce873` and a fresh isolated checkout
confirmed that same HEAD. This receipt instead uses private snapshot
`21e3638687d42ecfc36acebb28991987435ebc60`. The latest PR has removed
`t/native/qualification.ss` and its per-Suite preparation/actor-pool protocol.
It now uses one upstream make invocation in `tools/build-test-library.ss`
and one GxTest per compiled semantic/performance group. No result below is a
latest-PR baseline. The old launcher is closed for new consumer admission.
Preserve its original evidence without rerunning it or rewriting its pin.

Old-protocol ordinary source-change control
`.data/d1510-frozen-six-ascent-all-source-control-v1` also completed:
574.57 s wall / 796.64 s user / 111.45 s system, exit zero, 94/94 modules,
852 CASE-OK, upper entry MISS, zero helper events and 298 recognized GSC
object calls. Its output SHA256 is
`abda4e5b1a9db2dcb68dca2b23f9cef63473bc83f10aa5f9172dd3356c994f0b`.
Both old source-change fixtures have been removed. The 434.10/574.57-second
pair does not qualify the replacement latest-PR test architecture or justify
relaxing any current gate. The next admission must use the fresh exact-HEAD
checkout at `.data/d1510-ascent-pr1-latest-v1/project`, with matching isolated
dependencies and the upstream test commands.

## Admission Boundary

The actual frozen six-patch helper now has a complete independent ASCENT native
correctness run. This does not qualify full-suite performance, repeated cold
builds, or the retained-entry cleanup experiment. No experimental compiler
overlay is loaded, and retention is unset. Do not substitute this result for
MCP's separate 39-file/965-Case evidence.

## Actual Complete Run

Owned raw receipt: `.data/d1510-frozen-six-ascent-all-v2`.
Project head: `21e3638687d42ecfc36acebb28991987435ebc60`.
The direct Bash launcher invokes the unchanged project command
`just test-native-suite auto`. Scheme owns discovery, compilation, scheduling,
Cases and result admission. No Python launches or supervises native tests.

| Requirement | Actual evidence |
| --- | --- |
| Complete whole task | 479.20 s wall / 813.59 s user / 164.65 s system |
| Whole command exit | 0 |
| Native plan | 75 parallel + 19 exclusive modules, 12 workers |
| Module coverage | 94 expected / 94 unique PASS |
| Case records | 852 CASE-OK |
| Terminal success | 94 final OK lines, module admission passes |
| Executable entry | MISS, real AOT rebuild |
| Object reuse | 0 HIT / 296 MISS |

The preparation log contains the 85-module production layer, 149-module support
layer, and all 94 one-Suite compilation layers. The measured whole time includes
preparation, AOT entry compilation/linking and every test, including the final
Steensgaard application measurements. It is not an execution-only timing.
The original 1-GiB per-process heap and 120-second module execution deadline
are unchanged. No extra single-file silence timeout is introduced.

Expected module paths were independently derived with the selected GSC by
reading `qualification-files` as Scheme data and inspecting the qualification
source directory. They agree exactly, after sorting, with the generated native
registry inventory. The offline suite parser checks unique PASS coverage,
plan coverage, zero exit, per-module final OK and absence of failure markers.
The expected inventory has 94 paths, not a number inferred from PASS records.

All 296 backend events are MISS. This is a full-pool configuration population
run, not demonstrated whole-pool reuse or stable acceleration. Missing-object
ordinary fallback can emit no event, so 295 recognized verbose GSC object calls
and 296 backend events are not a reliable complete GCC invocation census.
Historical five-patch timings are not a matched six-patch performance control.
Do not claim that 479.20 s is an improvement over them.

## Native Identities And Isolation

Multiple-VM GSC SHA256:
`dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`.
Frozen helper SHA256:
`3b6b040aebcc87fcb4b3ab39907f82214c7ea55c6602ac1316128b3d06f38a4b`.
Native digest SHA256:
`e0124f9b69561d6fc34b148aa57e1573aebb7f3adc0ef4470b657f895156f2df`.
Executed runner SHA256, archived in the receipt as `runner.sh`:
`0fead42e71b01f96d1ef73abdfa8b89b789679b845e703c7e3d1ee10d63b699e`.
Raw output SHA256:
`a070275d8ab4193b5dc6b305a16f8958379af1fd7195001b57f0eb62686f974b`.
Time receipt SHA256:
`fd7be19f51c89af702d859ffd4b2171276a0477828a0067e2b6722433bb3ce53`.
Expected inventory SHA256:
`daf682c498376ea1d129675f265da62c44af34a4280ee14c11f50a268cca6d10`.
Generated inventory SHA256 (original order):
`65eb1b294f7a157d2cec47f54b48a2191f41e4117ac1537335c4e70fcb980f86`.
Toolchain identity log SHA256:
`b7a29d7f00a240ba745db125970da7b58bf994a18e9743fab265979bf7506542`.

After completion, the isolated tracked project is clean. All 1,992 toolchain
and 2,809 dependency dynamic-image references verify against their original
read-only targets. The active ASCENT checkout and shared dependencies remain
untouched. Consumer runtime and compiler are the isolated Multiple-VM profile,
not the frozen Single-VM MCP binary.

## Launcher Failure And Correction

V1 never starts native compilation or Cases. macOS Bash 3 with `set -u` rejects
the empty optional deadline array as an unbound variable. Preserve that failed
receipt; do not count it as a native test failure or performance sample.

The runner now uses Bash-compatible conditional array expansion for both scopes.
Two shell-argv controls verify no deadline creates no empty command argument and
an explicit 135-second deadline preserves the complete timeout argv. These are
utility-only tests, not Python native-test supervision. Combined wrapper,
selected-home and offline receipt tests pass 25 tests. No configured time limit
was widened to admit a failed native run.

## Remaining Gates

An unchanged full-pool repeat at
`.data/d1510-frozen-six-ascent-all-reuse-v1` completes in **351.46 s**
(375.29 s user / 47.17 s system), exits zero and again passes all 94 modules
with 852 CASE-OK records. It reports **NATIVE-ENTRY-CACHE-HIT**, zero GSC object
calls and zero Gambit object events. All 94 Suite preparation processes still
run. This is an upper ASCENT entry-cache result, not six-patch object-reuse
performance; never attribute the 127.74-second difference to Gambit HITs.
Its output SHA256 is
`3f3e51cc9d4138cbb4664fdfaeca01bcd28e34db600f3aa88eaf52104f52c57a`.
Do not repeat the unchanged full-pool scenario seeking backend HIT evidence.

## Real Source-Change Full-Pool Rebuild

`.data/d1510-frozen-six-ascent-all-source-change-v1` adds one comment to the
isolated positive-plan Suite, with no assertion or dependency changes. Its
`source-fixture.diff` SHA256 is
`29a12010e7eca34979851b0a1c82628f1dc888007e162ba0e3d2fa42eb4a9738`.
The comment is removed after completion and the tracked isolated project is
clean again. The 94-module inventory, helper, toolchain, heap and worker count
are unchanged. This is not the retained-entry overlay.

| Requirement | Actual source-change result |
| --- | --- |
| Complete whole task | 434.10 s wall / 546.91 s user / 143.54 s system |
| Whole command exit | 0 |
| Exact inventory / case count | 94/94 PASS / 852 CASE-OK |
| Upper executable entry cache | MISS, no HIT |
| Gambit static objects | 294 HIT / 2 MISS |
| Verbose recognized GSC object calls | 295; not a complete invocation census |

The independent expected inventory matches the generated native registry exactly.
Offline admission additionally requires 852 Cases, zero exit, complete module
coverage, entry MISS/no HIT and the actual 294/2 event counts. Afterward, all
1,992 toolchain and 2,809 dependency image references verify unchanged.

Raw output SHA256:
`6e628c5fdb66408fafe85fe0ab1169a976fa66213920f71567c42f4a1712ccc9`.
Time receipt SHA256:
`70fb35bbb7b263fc5bca9a860e3642ff89807897818298fe5163b65695f95476`.
Toolchain identity log retains
`b7a29d7f00a240ba745db125970da7b58bf994a18e9743fab265979bf7506542`.

This closes actual full-pool backend-HIT correctness, not a stable performance
gate. Against the earlier configuration population, the raw difference is
45.10 s wall and 266.68 s user CPU; preparation currentness and proof population
are different, so this is not a matched ordinary-versus-reuse speedup.
The next gate is an ordinary full-pool rebuild with the same isolated profile,
equivalent comment-only invalidation and all 94 modules, followed by matched
repeated admission. Do not use the upper-entry HIT or five-patch history as its
control. The unchanged upper-cache scenario is now closed for backend testing.

Component-only HIT evidence cannot replace that complete performance gate.
The retained-entry 57.07/59.65-second single-Suite experiment remains separate
and outside the frozen bundle.

Frozen MCP retained admission remains first 3.950-4.038 s, complete cold build
35.552-37.770 s and complete tests 86.924 s / 965 passing Cases. Its ceilings
remain 4.5/42/97 s. General qualification remains incomplete.
