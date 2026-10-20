# Native Capture Transport Cost

## Review

Correct path: investigate the common GNU GCC object-proof backend that failed
the complete MCP build gate, without changing the frozen six-patch bundle.
Already explored: simple producer-process fusion and unchanged eager-proof
configurations are rejected in earlier receipts. This control does not repeat
either configuration's package benchmark. Worth measuring: separate the saved
intermediate transport from the complete capture/validation path before choosing
a new implementation. Expected package benefit is unknown, not a promised gain.

The existing `check_native_object_capture_cost.sh` gains an optional `transport`
control; its default shell/native comparison remains available. The new control
uses the machine's physical core count and runs ordinary/saved/native/native/
saved/ordinary waves. Each job owns a distinct object path. Saved transport
removes the incompatible `-pipe`; the ordinary path retains it. No diagnostics
are suppressed. Every successful job must match the ordinary object bytes.

## Actual Native Evidence

Receipt: `.data/d1510-native-capture-transport-cost-v1`, exit 0, **12 physical
workers**, **72 concurrent-wave object compilations**, all exact byte parity.
Input is real MCP registry generated C, not a synthetic instruction loop.
All runs use the same source path and matching Single-VM GSC/GNU GCC 16 recipe.
The candidate includes the 0043 compiler-prefix correctness fix.

| Phase | Wave wall seconds |
| --- | ---: |
| Ordinary A | 2.76 |
| Saved intermediate A | 2.92 |
| Native capture A | 3.20 |
| Native capture B | 3.12 |
| Saved intermediate B | 2.88 |
| Ordinary B | 2.64 |

At the timer's two-decimal precision, pair means are 2.70 / 2.90 / 3.16 seconds.
Native capture adds approximately 0.46 seconds (17.0%) over ordinary compilation
in this workload; saved transport accounts for approximately 0.20 seconds.
The remaining 0.26 seconds includes the whole additional binding, tool/source/
object hashing, proof publication and process path, not tool hashing alone.
These are component observations, not a causal allocation of package wall time.
Saving `.s` is therefore not the entire regression, and eliminating it cannot
be assumed to admit the rejected package configuration.

Input: 1,092,831 bytes; one saved `.i`: 1,729,395 bytes; one saved `.s`: 762,058
bytes. Native phases require fresh CAPTURE/MISS markers. This is not a cache-HIT,
complete build, complete test, first-log, or Linux comparison measurement.

## Next Implementation Boundary

Investigate a request-local tool-validation coordinator with deferred proof
publication, not timestamp memoization or fewer checks on an individual published
proof. Existing 0040 shares a snapshot only for generated-C members; its earlier
member-local publication limitation cannot be transplanted into object capture.
An object coordinator must stage outputs/proofs privately, validate the complete
request before exposing them, preserve failure/lock cleanup, and reject external
tool changes before allowing a consumer binding. Mid-request failure, real
external mutation, concurrent requests and retry parity are prerequisite controls.
No such object coordinator is implemented or admitted by this receipt.

The unchanged 0043 whole-MCP configuration remains DENIED at 42.008 seconds;
74 object HITs do not change that decision. The frozen checkpoint remains
35.552 / 36.414 / 37.770 second cold builds and 86.924 second full tests,
39 files / 965 cases, with 4.5 / 42 / 97 second per-sample ceilings. No later
patch is promoted. Complete ASCENT and generic release admission remain open.

## Identities

- Input C: `9c9628e3f8285c41b7515d634acfc3d4962ac057a6857fe50adba3fbc16881fd`
- Ordinary and all 72 objects: `b966b90bfb59167d64b630eb7fa5ef613f425a6852b80baac6213a9d1f783727`
- Harness: `db898fae971ed0ea64872670b4f7cccbc87923c7daecd0db7e65f25f5a3f3f50`
- Raw receipt manifest: `b7b43e68d37f2c711841e988ab5273e10cf8f708e5d9c310543de6c786bf86e2`

The raw manifest binds the selected tool/input identity log, all six timer
reports and terminal status. Native execution is Bash/GSC/GCC, without Python
supervision. No active consumer checkout or shared dependencies were modified.
