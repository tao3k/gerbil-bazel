# Batched Native Digests For The Producer Consumer

This default-off experiment extends the existing GNU/Darwin CommonCrypto
digest implementation through a separate C entrypoint. The frozen digest C
and MCP five-patch series remain byte-identical. Explicit environment switch
`GAMBIT_GENERATED_C_BATCH_DIGESTS=1` selects ordered digest-only lines for a
batch of argv paths; the entire environment and helper bytes remain bound in
generation proofs. Unsupported or malformed transport fails closed.

No digest check is removed. Batch-end source/proof/pin/tool/environment checks
remain. Final source and pin groups can use one native digest process each
instead of one process per file. The Scheme decoder verifies line count,
lowercase SHA-256 syntax, process exit status and argv order.

## Qualification

- `.data/d1510-generated-c-batch-hash-controls-v2`: ordered and duplicate
  paths, newline/backslash/space names, missing file, directory and empty argv;
  Scheme/native digest parity and malformed/failed output rejection.
- `.data/d1510-generated-c-closure-contract-v20`: 15 original generation
  contracts and two concurrent native writers pass with batched digests.
- `.data/d1510-produced-generated-c-contract-v7`: all producer consumer
  controls pass, including post-leaf mutation denial and original-link parity.
- `.data/d1510-produced-generated-c-contract-v8`: same controls pass using
  the original single-file digest helper and no batch switch.
- Frozen patch-lock/preparation focused checks: 10 pass.

Preparation v1 failed at linking with GCC's default SDK. Preparation v2 uses
the SDK explicitly selected by xcrun and GNU GCC 16.2.0; it does not switch to
Clang. The frozen GSC bytes match the owned runtime exactly.

## Real 55 Module Measurement

`.data/d1510-real-produced-generated-c-v4` uses the isolated ASCENT paired
source fixture and directly launches native GSC with the matching runtime.

| Component | Seconds |
| --- | ---: |
| Separate cold proof population | 7.719672 |
| Existing producer lookup | 0.744068 |
| Original Scheme metadata link | 3.76 |
| Proven C metadata link | 0.18 |
| Lookup plus proven C link | 0.924068 |

Whole link C byte parity holds for all 55 modules. This is not a complete
package cold-build/test result, nor a matched A/B attribution for native
transport alone. Earlier v3 timings are retained, not overwritten. Cold proof
population must not be ignored or amortized away to claim a cold-build win.

## Identities

| Artifact | SHA-256 |
| --- | --- |
| Generated-C implementation | `18dd5a45a3026646f83412f36cc51f039f1046c7d507a3412828c93c9a05e8a4` |
| Batch native source | `aebedf267740d10f8c91b28a72dacb7531ccbb327547706cb65cef74f0542710` |
| Frozen digest source | `eaef399ff95eaf180ca2f1956ca2e7b66373bf8d63111c2635fedc396ce74a4a` |
| Native batch helper | `1f81c3639b332dfa0cd5301b6487b4156c569357fbf4e8371c87d4ce9f0b95f8` |
| GSC | `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00` |
| Real run output log | `845cb3584fa50aad90182b804b2b1624d0cd4d2311e2abbf55890736644686da` |
| Both link C files | `f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b` |
| Original link time receipt | `73280468404ad6cb0c3097bae556b38a972e02631bac70e3260f9f05d36f7994` |
| Proven C link time receipt | `101a7be27a4ca71fd35a056a6aa7616798c3f09fb24bc38e27a508a218c0d2c4` |
| Generation contract output log | `9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5` |
| Consumer contract output logs | `2bb6fc856b5359fd1856da301634a670653462eca14949f9abc567008873f826` |

Gerbil driver inspection confirms its Darwin producer already creates runtime
C and copies it to static C before object compilation. Same-process readiness
already selects runtime C during linking; cross-process fallback selects
Scheme. Remaining integration must capture proof at that existing producer,
not introduce another generation pass. Full MCP and ASCENT consumer gates
remain unproven; this experiment is not added to the measured patch series.
