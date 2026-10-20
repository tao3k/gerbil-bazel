# Native Object Proof Backend: DENY

## Review And Mechanism

Correct path to investigate: previous eager producer capture was expensive before
the intended link reuse occurred. Existing records did not contain this native
proof-acquisition implementation. Worthwhile hypothesis: collapse per-object
snapshot, digest, normalization and publication subprocesses into one Darwin GNU
C helper. Expected benefit was lower acquisition overhead, not a promised whole
package improvement. No tool timestamp cache, tool-content memoization, package
special cases or weakened validation was introduced.

0035 adds first-object capture using CommonCrypto and `posix_spawn`; the legacy
digest CLI stays available. 0036 extends it to full existing-proof validation and
MISS compilation. Both remain explicit opt-ins, after experimental 0033/0034;
neither is in the measured frozen series. Linux and flag-off dispatch retain
their existing path. Complex shell recipes fall back to the existing implementation.

The native path still binds actual compiler input to the expected source digest,
preserves relative includes and timestamps, fingerprints compiler/backend content
before and after work, hashes actual expanded input and object bytes, and builds
the same full `gambit-static-proof-v2` key. It does not accept C equality alone.
Publication remains under the existing per-output lock; failed compilation or
tool mutation does not replace the old object or publish a new proof.

## Component Evidence

`.data/d1510-native-object-cost-v1` compiles one real generated C sample with the
same binary/toolchain and dynamic options. Each shell/native/native/shell phase
forces three fresh captures. Wall times: **1.73 / 1.34 / 1.35 / 1.77 s**; user times:
1.17 / 0.98 / 0.98 / 1.18 s. All twelve objects exactly match ordinary compilation.
Approximately 23% acquisition improvement is a component observation only.

Actual mechanism controls pass:

- `d1510-native-object-modes-v2` and `d1510-native-check-modes-v1`: identical C,
  different dynamic/static objects; recipe changes MISS, matching recipes HIT.
- `d1510-native-object-bound-controls-v1` and `d1510-native-check-bound-v1`: cold
  capture, source rejection, invalid digest, unsupported options, recovery and
  two concurrent writers with exactly one MISS and one HIT.
- `d1510-native-object-aba-v1` and `d1510-native-check-aba-v1`: real compile-phase
  source A/B/A mutation; exact ordinary-object and native-execution parity.
- `d1510-native-object-semantics-v1` and `d1510-native-check-semantics-v1`: relative
  headers, filename macros, timestamp/line semantics and debug/prefix-map fallback.
- `d1510-native-object-failure-v2` and `d1510-native-check-failure-v1`: actual GCC
  error and private tool mutation during compilation; old object retained, proof
  not published, recovery HIT and no lock/snapshot leftovers.
- `d1510-native-check-toolchain-v1`: real compiler, assembler and digest changes
  invalidate proofs; missing digest fails closed; mocked Linux path stays original.
- `d1510-native-object-handoff-v1`: real Gerbil producer and native executable
  handoff preserve exact object/proof bytes and execute successfully.

The initial failure-control v1 stopped on an erroneous literal in its leftover
inventory assertion; its corrected v2 passes. The first modes v1 had a marker
assertion mismatch, not object/recipe parity failure; v2 passes. Do not count
those failed fixtures as passes. Source patch reconstruction for 0035 then 0036
matches the actual native source and helper byte for byte in the independent Git
root `.data/d1510-native-object-patch-replay-v1`.

## Whole MCP Evidence

| Candidate | First log | Complete build | Complete tests |
| --- | --- | --- | --- |
| Native capture only | 3.824904 s | Unknown; DENY at 42.043926 s | Skipped |
| Native capture and validation | 4.015630 s | Unknown; DENY at 42.000390 s | Skipped |

Both terminal runs force-stopped and reaped the child process group with no
cleanup errors. Both skipped the remaining cold repetitions and complete tests.
They are not completed 42-second builds. Native capture-only additionally fails
patch identity: replay context was corrected in 0035 while the run was live.
That is an invalid qualification attempt, even independently of its time failure.
The capture-and-validation profile was finalized before launch; all identities
pass both before and after its terminal DENY. No identical configuration was
rerun to select a passing sample.

Capture-only reached 186 captures, 88 object HITs and 320 selected link inputs.
Full native validation reached 186 captures, 67 native checks/HITs and 320 selected
inputs. These counts establish actual execution and change the next investigation;
they are not comparable work-normalized timings or whole-package speedups.

The focused policy/profile/controller/producer suite passes **51 tests**. The
existing six-patch lock still passes actual driver, runtime, GSC, raw evidence and
all retained performance samples. Its three cold builds stay **36.414 / 35.552 /
37.770 s**, first logs **4.038 / 3.980 / 3.950 s**, and one complete test **86.924 s,
39 files / 965 cases**. No patch in that frozen bundle changed.

## Next Decision

Close these whole-consumer configurations unchanged. Native proof machinery is
correct in the tested scope and cheaper at acquisition, but did not overcome
whole-closure admission overhead. Re-examine the actual work avoided: the original
Darwin flow already produces and reuses dynamic objects in the same executor;
the experimental `selected` branch unconditionally validates them again. A next
design must distinguish unnecessary new proof work from genuinely repeated
generation/compilation while preserving explicit source/options/toolchain safety.
Do not remove those checks, broaden the performance ceilings or claim the
component result as a finished optimization.

See [exact evidence hashes](d1510-native-object-backend-denied.json). No additional
ASCENT consumer run, full latest-staging toolchain build, production admission,
commit or GitHub delivery is claimed. The dual-consumer goal remains incomplete.
