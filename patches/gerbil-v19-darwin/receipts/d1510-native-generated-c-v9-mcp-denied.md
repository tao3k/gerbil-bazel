# Native V9 Whole MCP Admission

## Identity And Execution

The compiled in-process digest candidate has its own content lock:
`d1510-native-generated-c-profile-v9.json`. V8 remains the default profile;
V9 requires explicit `--native-in-process-digests` together with native GSC.
The cold controller records that choice and complete testing rejects a different
backend or binary identity. Inherited digest flags are cleared before selection.
All five driver files and compiled/tracked sources pass the V9 identity check.
Focused profile, progressive and three-time-gate checks: 39 passed.

Real isolated MCP receipt:
`.data/d1510-native-generated-c-mcp-v9-in-process-v1`.

| Metric | Result | Hard Ceiling |
| --- | --- | --- |
| Official clean | 2.494 s, exit 0, zero remaining native images | existing clean safety bound |
| First compile log | 4.356642 s | 4.5 s |
| Complete cold build | unfinished; stopped at 42.042186 s | 42 s |
| Complete tests | not run | 97 s |

Decision **DENY**. The controller confirms child reaping and terminal exit -9;
the observation timeout is not a successful build duration. No completion time,
test performance or complete correctness is claimed. Frozen MCP patches and
4.5 / 42 / 97-second ceilings are unchanged.

Raw cold report SHA256:
`d34acfd56438b950f36ae8495ebf4221e4aaf88d07cfd4749f2c439ce539087c`.
Admission report SHA256:
`288334ecd1c0ba1ead3ba2cc66c55a548583717bb0fc659f0aba7655d2ace559`.

## Direction Review Before Another Change

1. This version is not a whole-consumer win. The positive serial component and
   isolated ASCENT pair do not override the failed MCP gate.
2. The unchanged V9 MCP configuration is closed; do not rerun it to select a
   faster sample, relax the cap or resurrect the external dispatcher.
3. The producer index contains 186 records, but the observed build log has no
   native produced-C link adoption. Its terminal progress is executable-object
   work consuming existing static C. This is evidence of producer work without
   an observed new consumer, not proof that all time is hashing or that a later
   link could never adopt a proof.
4. The next architecture question is whether producer admission should follow
   the actual compiler consumer contract. Existing direct-C/object reuse should
   not pay for a second Scheme-link proof it does not consume. Library-only
   Scheme-link callers still require content proofs and full invalidation.

Any proposed change must use generic compiler state, not package names, directory
heuristics, workload exclusions or changed assertions. It must preserve thread-
local job parameterization, unchanged non-Darwin behavior and source/options/
tool/environment invalidation. Avoiding unrelated proof work can at most recover
the observed overhead; no numerical package speedup is predicted without a
matched passing run. No such routing change is implemented or admitted here.
