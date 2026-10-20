# V4 HIT Cost And Multiple VM Safety Qualification

## Review

The preceding source-change diagnosis proved 70 real object HITs and two
appropriate MISSes. This slice measures required HIT work before changing the
optimization. Native CommonCrypto digesting was already implemented in V4;
rediscovering it is not a new route. Expected optimization gain remains unknown.

The safety harness also needs explicit selected-toolchain support: its previous
default is the MCP Single VM header tree. Testing ASCENT's GSC with that default
would not qualify its actual Multiple VM ABI. Correcting this test boundary is
worthwhile, but has zero expected application speed benefit.

## Actual HIT Component Measurements

`tests/check_static_reuse_hit_cost.sh` uses the uninstrumented measured V4 helper,
selected ASCENT GSC/header pair, and a copied real dependency-graph C module.
It compiles a control object, populates a proof, then requires four genuine HITs
with exact control-object parity. Four independent preprocessing operations
have identical output; all native eight-file tool snapshots are identical
before, during and after the test.

Receipt: `.data/d1510-static-hit-cost-ascent-v1`.

| Operation | Four real times | User CPU | System CPU |
|---|---|---|---|
| Complete GSC object HIT | 0.38 / 0.35 / 0.36 / 0.35 s | 0.22 / 0.21 / 0.21 / 0.21 s | 0.13 / 0.11 / 0.12 / 0.12 s |
| One matching preprocessing operation | 0.07 / 0.07 / 0.07 / 0.07 s | 0.04 / 0.05 / 0.05 / 0.04 s | 0.02 each |
| One native eight-file tool snapshot | 0.03 each | 0.02 each | 0.00 at recorded resolution |

The source is 104,398 bytes; preprocessing produces 325,048 bytes. GSC is
16,952,320 bytes and GNU cc1 is 49,295,392 bytes. The whole HIT includes three
tool snapshots plus preprocessing, source/object/context checks and process
startup. These independently timed components are not a precise additive
profile of one HIT and must not be extrapolated into package wall-clock savings.
One real module does not establish the distribution for all closure members.

Result: `STATIC-HIT-COST-OK four-HITs byte-parity stable-tools stable-cpp`.
There is no evidence here for a new order-of-magnitude gain from another hash
implementation. No optimization code or performance gate is changed.

## Actual Multiple VM Controls

Four existing native controls now accept a third argument selecting the actual
toolchain home. Their old MCP default is preserved for existing callers. The
eight-case object control also accepts a fourth argument for actual generated
C from the selected consumer. Each receipt binds selected GSC/header hashes.

Selected fixture: `.data/d1510-static-reuse-ascent-v1/toolchain`.
Its header defines `___MULTIPLE_VMS`; the historical MCP header defines
`___SINGLE_VM`. The actual ASCENT identities are:

- `include/gambit.h` SHA256:
  `8257ff05aadb634e2ef2532f7e1a21608a828c4adae35cf88276b78e7efff1e5`.
- `bin/gsc` SHA256:
  `dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`.

| Direct native control | Private receipt | Result |
|---|---|---|
| C parity, options, header, object tamper, concurrency, failure | `.data/d1510-ascent-multiple-vm-static-controls-v1` | `STATIC-OBJECT-REUSE-OK 8`, exit 0 |
| Source/helper/driver byte invalidation | `.data/d1510-ascent-multiple-vm-identity-controls-v1` | `STATIC-OBJECT-IDENTITY-OK 3`, exit 0 |
| Proof directory/symlink, diagnostics, mid-flight mutations | `.data/d1510-ascent-multiple-vm-safety-controls-v1` | `STATIC-OBJECT-SAFETY-OK 6`, exit 0 |
| Actual GNU GCC/assembler/digest mutations, unavailable digest, platform fallback | `.data/d1510-ascent-multiple-vm-toolchain-controls-v1` | `STATIC-OBJECT-TOOLCHAIN-OK 5`, exit 0 |

These are 22 native component contracts, not 22 Scheme suites or full consumer
test qualification. Tests use fresh owned outputs and compiler copies; no
global compiler, selected source toolchain or shared dependency is changed.
The non-Darwin fallback control is mocked and is not native Linux CI evidence.

## Fail-Closed Harness Polish

Eight preflight tests require missing/symlinked selected headers to be rejected
before receipt creation or any native launch. The first run correctly exposed
four missing-header failures: Bash `set -e` does not terminate on the left side
of an AND list. Explicit `if missing-or-symlink; then exit 2; fi` fixes the
guard without changing successful native commands. Symlink guards passed in
the initial run. The cost probe and generated-C input checks use the same
explicit form.

After correction, selected-home preflight, trace and patch-identity tests pass
55 checks. These Python tests exercise shell rejection only; they do not launch
or supervise Scheme/native semantic tests. Bash syntax checks pass for all five
modified/new shell controls.
The broader selected-home/trace/identity/three-gate/progressive-controller suite
passes 102 checks.

Frozen MCP patch/driver/runtime/raw-report identity still passes. No recorded
MCP samples, five optimization patch bytes or active 4.5 / 42 / 97-second
ceilings change. Full consumer correctness/performance admission and integrated
ASCENT performance remain incomplete; no goal completion is claimed.
