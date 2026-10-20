# Producer Mode Semantic Control

## Review

The fresh-object candidate must preserve the selected reference compiler's
semantics, not merely execute a trivial Scheme program. This control makes a
foreign function return 17 under `___DYNAMIC` and 29 otherwise. It executes the
same module / dependent-job / executable pipeline with the reference compiler
and the 0037 overlay, using the same Multiple-VM GSC and genuine GNU GCC.
Expected speed benefit of this control is zero; it tests the admissibility of
further producer-proof work. No optimization patch is changed.

## Actual Result

Receipt: `.data/d1510-producer-mode-parity-v4`, exit zero.
Both native executables return `PRODUCER-MODE=17`. Both compile the module object
once and retain exactly the object produced before executable preparation.
The candidate additionally reports 20 closed-link selected inputs. The script
asserts the expected native result, per-role object byte parity, single module
object compilation and the candidate branch marker; output equality alone is
not sufficient. This is one real control, not complete consumer admission.

Reference home: `.data/d1510-producer-mode-original-home-v1`, an owned clone of
the previous ASCENT reference. Candidate home:
`.data/d1510-fresh-produced-ascent-v1/toolchain`. Its compiler overlay is loaded
by the qualification launcher, not a released native AOT replacement. The
reference retains read-only compiler-image references; this is a selected
reference comparison, not a claim of pristine upstream compiler identity.
Both homes have identical header/archive bytes:

| Input | SHA256 |
| --- | --- |
| `gambit.h` | `8257ff05aadb634e2ef2532f7e1a21608a828c4adae35cf88276b78e7efff1e5` |
| `libgambit.a` | `ac280ecde9fb375cb8bfc22e78f494466f4bdd4d8463004223d957d02480c192` |
| Reference native Gerbil | `bedfdae04633b2e2862b6083e7ab7cd20e20ca4d2b0823482cb8aa4e10c597af` |
| Reference compiler image | `70ac1d3cfdac30dbb09c92863b1c064d7d561a7042fe94ed2c61d8f30d2e61af` |
| Candidate compiler image | `8b61c5f638cbeacfa45268d8aa09df75e77a5c2ce6aa016b6e8774145093dd8a` |

| Raw evidence relative to receipt | SHA256 |
| --- | --- |
| `identity.log` | `a2feb4a949dc169b2b5a4053f1c9445ad9ac6091c5c465c77d8d2cd77ab509cc` |
| `original/build.log` | `aec99138b684237756399b9127bae052e27e2f9151b5938a59d3b773d2a24b1f` |
| `candidate/build.log` | `ca44fe43cc50bf28e3ddf40a138602b92692f689c0e0abc4fe06328a6481ad17` |
| Either `native.stdout` | `e8dfb09af559d6ff2aefba522ce64e4f86006fd2c43a29f0ae4503bde50214fd` |

The original v1 setup failed final linking because inherited PATH selected Nix
`ld`. The runner now requires Darwin's `/usr/bin/ld`, matching the qualified GNU
GCC path. The v2 setup linked successfully but the fixture called a namespaced
identifier while its raw foreign definition was unnamespaced. `extern namespace:
#f` corrects that fixture binding without changing compiler behavior. The v3
control then passed; v4 adds and passes explicit assertions and relative digest
output. Setup failures are not timing samples or candidate regressions.

## Remaining Boundary

The fresh candidate's previous whole-test denials are not erased by this
control. Modes/options changed across separate compiler processes still require
full proof. Frozen six-patch source, helper, runtime and performance identities
remain unchanged; no new speedup or complete ASCENT admission is claimed.

## Consumer Options Change: Denied

The same runner now accepts an optional fourth argument, `options-change`.
Production remains unchanged; the dependent executable request adds
`gsc-options: ["-cc-options" "-U___DYNAMIC"]`. This demands static-mode
preprocessing for the consumer module object, yielding 29 in the fixture.
The default unchanged-options control still expects 17 and exact per-role
producer-object preservation.

Actual receipt: `.data/d1510-producer-options-change-v1`, exit 42. Both native
executables still return 17. Their module objects are retained despite changed
consumer CC options. The identity log is written before the expected-result
check; the first explicit denial is the reference result. Both native results
exist, so this is an executed invalidation control, not a setup failure.

| Raw file relative to receipt | SHA256 |
| --- | --- |
| `original/build.log` | `ffe1754e5852c32a1340f033c51058f259742fb4832d6aee700c5d3cf2329d5a` |
| `candidate/build.log` | `6bd60145e0074c3cea39441727ad09b2e6107a623e993860acb2336701980a60` |
| `identity.log` | `0aeaeb0e9648c5ac3338be9f0bbcd1c5609ca78585c00000d6a21d8945e34065` |

The reference also preserves the old object, so this is not proof of a newly
introduced 0037 regression. It is proof that matching reference timestamps is
insufficient for the requested explicit options-invalidation contract. Existing
backend controls cannot cover a fresh object bypassing that backend. Do not
promote 0037 as generally safe or describe its source check as a complete recipe
proof. The next design must bind the successful producer recipe and object,
including options/toolchain identity, and route mismatches through full proof
or ordinary compilation. Avoid repeating rejected all-producer capture without
a distinct bounded design and whole-consumer qualification.
