# Object Request Context Candidate

**Performance promotion DENIED:** the subsequent
[matched actual GSC request-cost control](d1510-object-request-cost.md) is slower
in both candidate waves. Correctness qualification is not a speedup. Do not
integrate the unchanged preparation-plus-coordinator route.

## Admission Review

Direction: retain the exact configured GSC/GNU GCC recipe while coordinating
independent object requests. Already explored: 0044 alone is unsafe because the
declared environment was not executed; 0045 repairs that defect. Repeated whole
MCP runs of the unchanged 0043 configuration are denied, not a new experiment.
Worth fixing: real GSC changes into the source directory and uses relative source
spelling. Losing either breaks producer proof identity and relative includes.
Expected gain from this polish alone is **zero**. Any scheduling gain remains
unmeasured until Gerbil consumer integration and whole-package qualification.

## Frozen Checkpoint

The admitted six-patch MCP checkpoint is **not changed**:

| Metric | Retained actual samples | Hard limit per sample |
| --- | --- | --- |
| First compilation log | 4.038430 / 3.980393 / 3.950160 s | 4.5 s |
| Complete cold build | 36.414237 / 35.551924 / 37.770491 s | 42 s |
| Complete tests | 86.924285 s, 39/39 files, 965/965 cases | 97 s |

These are historical receipts revalidated against the exact driver, runtime,
GSC, raw evidence and patch lock, **not fresh benchmark results**. There is only
one complete test timing. Lock SHA-256 remains
`a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2`.
The new candidate does not enter `static-c-snapshot-candidate.series`, default
builds or release builds. Whole ASCENT qualification remains incomplete.

## Reviewable Candidate Patches

`native-object-request-candidate.series` applies after 0043. All four patches
must remain together; unpaired 0044 is denied.

- **0046** adds v3 requests: canonical source identity plus original source
  spelling and per-job working directory. Child working directory, environment
  and display spelling are thread-local and reset after execution. Proof/source
  hashing stays on the canonical file; GCC source markers keep the original
  spelling. Tool discovery sharing also includes working directory. Relative
  PATH lookup is not qualified. Older incomplete protocols return 77.
- **0047** adds an opt-in preparation branch to the existing configured object
  driver. It uses existing option extraction and object-command substitution,
  preserves compiler prefix flags during GNU/platform/tool probes, and emits
  exact environment and request records without compiling or publishing objects.
  Unset preparation controls leave the existing dispatcher unchanged. This is
  a preparation candidate, **not an installed toolchain feature**: helper install
  rules and Gerbil consumer scheduling still require integration.

No package name, MCP source path or test inventory is hardcoded in either patch.
Personal absolute paths remain in local `.data` only.

## Actual Configured Driver Check

`.data/d1510-object-request-driver-controls-v4` exits 0 using the actual configured
Single-VM GSC and real MCP generated C. An ordinary dynamic/PIC object compilation
first creates the producer object/proof. Preparation leaves both byte-identical.
The subsequent native v3 request reports HIT and COMMIT; both object and proof
still match the original byte for byte. This validates producer handoff identity,
not complete package speed.

V2 passed before the final polish. V3 failed because the test build accidentally
compiled the standalone digest CLI instead of the native capture entry point;
it is excluded. V4 uses the correct native entry point. No frozen binary changed.

**34 focused checks pass**: candidate byte pins and separation from the frozen
series; 0044/0045/0046 apply and reverse, coordinator source
parity, 0047 apply/reverse and shell syntax, protocol/environment rejections,
compiler-prefix controls, and frozen checkpoint contamination/identity checks.
Native concurrent controls are recorded separately; passing preflight checks
alone does not admit object execution or a consumer performance claim.

`.data/d1510-object-request-native-controls-v2` exits 0 with 12 physical workers:
ordinary object byte parity, genuine GCC failure with no target publication,
two reverse-order concurrent HIT requests, tool-content change MISS, external
mid-request tool mutation DENY, option retry parity, environment MISS and bound
source mutation DENY. V1 could not read the core count in the sandbox and is
excluded; v2 reads the real count under approval.

`.data/d1510-object-request-native-environment-v1` also exits 0: declared failing
GCC environments reject, parent poison does not leak into normal jobs, mixed
per-job environments execute independently with normal-object reference parity,
changed GCC tool selection rejects, and no failed request publishes targets.

## Identities

- 0046: `c98665e2b56e942624e0be7a4ea48ba1d46f4a54af632d0e40ccf4f0f2cfb23e`
- 0047: `73088ff011836b7eaf2191db3a95002615a670679217c8c990c7f9a6a3c3dbd9`
- Coordinator prototype: `9d12d928ce8f36f6ffbaaad93827c0a5f6c5cf71e35d8b8cc4cb6b4b0234600b`
- Actual native binary: `ea0e5566a57bc7527035d7f552970fe7f87accc305fd03c104cd16662adae01a`

Remaining gates: exact per-job relative-include semantics,
installation/consumer integration, then all three MCP
metrics and independent ASCENT correctness. Until then these candidates cannot
replace the frozen performance checkpoint.
