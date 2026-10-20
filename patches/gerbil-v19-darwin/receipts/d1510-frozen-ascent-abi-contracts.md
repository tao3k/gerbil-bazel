# Frozen ASCENT ABI Contracts and Cold Fallback Boundary

## Review

The preceding turn made progress by denying the genuinely slower configured
preparation route. This turn reviews existing ASCENT evidence before execution:
the six-patch snapshot helper already passed 30 positive-plan Cases in 77.73 s
and an upper entry-cache hit in 7.70 s. Repeating those unchanged runs is not an
optimization. Historical full 94-Suite results use the five-patch helper, and
the old 22 Multiple-VM backend controls also predate 0026. Neither can qualify
the final six-patch source-race boundary automatically.

Worth doing: qualify the actual six-patch helper against the selected ASCENT
Multiple-VM GSC/header pair. Expected speed benefit is zero; this closes an ABI
correctness evidence gap without claiming full consumer acceleration.

## Actual Native Evidence

Raw root: `.data/d1510-frozen-ascent-abi-contracts-v1`.
The direct Bash/GSC/GNU GCC controls pass:

| Control | Executed result |
| --- | --- |
| Real generated C, options, header, object tamper, concurrency, failure | 8 passed |
| Source, helper and driver content invalidation | 3 passed |
| Compiler, proof directory/symlink, warning and mid-flight mutation | 6 passed |
| Real GCC/assembler/digest mutation, missing digest, platform fallback | 5 passed |
| Existing-object source ABA during preprocessing | Protected, native status 0, exact object parity |
| Existing-object source ABA during compilation | Protected, native status 0, exact object parity |

The selected 104,398-byte generated module is ASCENT dependency-graph C.
Both existing-object ABA controls compare original/candidate object bytes and
execute the linked native predicate; success is not just a log marker.
The original driver, helper, digest executable, GSC, header and installed GNU
GCC hashes remain byte-identical in `original-before.sha256` and
`original-after.sha256`. Only a fresh owned driver copy normalizes the private
GNU executable spelling for the existing mutation fixtures; ABI/options are
retained. No active checkout, original toolchain or shared dependency is edited.

**The initial aggregate harness exits 1**, not zero: after the above 24 passing
contracts it incorrectly applied the reuse-MISS assertion to a missing-object
ordinary fallback. Its empty candidate log is consistent with ordinary dispatch;
the failed assertion is retained and is not presented as a passing full run.
The corrected harness explicitly covers the 22 contracts plus two existing-object
ABA controls only. It pins actual header/GSC/helper/digest bytes before receipt
creation. It has not been re-run merely to obtain another green aggregate marker.

## Missing-Object Source Race: Reproduced, Not Admitted

The existing ABA fixture gains an explicit `ordinary` dispatch expectation; its
default reuse assertion remains unchanged. This allows measuring the actual
fallback rather than failing early because it emits no reuse marker.

`.data/d1510-frozen-ascent-cold-aba-v1` exits 0 **as a defect reproducer**:
missing object, mutation during actual GNU compilation, no object reuse marker,
no proof publication. The source is restored to A, but the compiler read B.
The linked native predicate exits **71** rather than 0, and the produced object
differs from the ordinary A reference. This is not successful test correctness.

| Artifact | SHA-256 |
| --- | --- |
| Restored source A | `78a5330cc923a5f6ee044bc60b7e043675c7b21eceda68c1ccdcf903fe248275` |
| Reference object A | `63bdabdf011323e437e0e25485d3406aef3b5de4b0e73159a3bfae76bf3e3d0b` |
| Produced object B | `f955b391cddf6f63485440010e69bf74356750eec56ce6d383bc1b301a8eec34` |

0026 protects the existing-object reuse path; it does not claim to snapshot the
original missing-object fallback. This is a stronger new qualification boundary,
not proof that frozen MCP timings are invalid or a new regression relative to
ordinary GCC compilation. Cold source protection must be explicitly integrated
and tested before a broader generic source-race guarantee can be granted.
0032 already explores a bound cold snapshot; that implementation and its prior
performance denials must be reviewed before proposing another cold capture path.
No unchanged eager-proof or preparation-plus-coordinator retry is authorized by
this evidence.

## Identity and Remaining Gates

- Helper: `3b6b040aebcc87fcb4b3ab39907f82214c7ea55c6602ac1316128b3d06f38a4b`
- Digest: `e0124f9b69561d6fc34b148aa57e1573aebb7f3adc0ef4470b657f895156f2df`
- Multiple-VM GSC: `dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`
- Header: `8257ff05aadb634e2ef2532f7e1a21608a828c4adae35cf88276b78e7efff1e5`

29 focused preflight/frozen/selected-home checks pass. Python only tests rejection
before native launch; all semantic compilation and execution is Bash/GSC/GCC.
No new package performance measurement, complete six-patch ASCENT suite, general
release admission or goal completion is claimed. The frozen MCP lock and gates
remain unchanged: retained first logs 3.950–4.038 s, cold builds 35.552–37.770 s,
complete tests 86.924 s / 965 cases; ceilings 4.5 / 42 / 97 s.
