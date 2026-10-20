# Member Tool Snapshot Experiment

## Review Before Promotion

Correct direction: avoid regenerating unchanged Scheme members in the common
Darwin closed-link consumer. Existing independent-generation evidence established
exact C and flat-link parity for 55 real ASCENT modules. Directory-wide proofs
still invalidate all members on one change. This is not a package-specific hook.

Already explored: naive per-member proofs repeatedly hash the same 17 MB GSC.
That configuration is DENIED: cold population 3.914 -> 5.319 seconds and stable
HIT 0.078 -> 1.490 seconds. Do not repeat it unchanged.

Worth testing: one request-local full tool-content snapshot, revalidated after
the complete batch. No timestamp cache or cross-request memo is introduced.
0040 only enables this explicit experimental coordinator; ordinary seven-argument
closure calls retain their original tool checks. The default dispatcher does not
select the member coordinator. Expected benefit is selective invalidation, not
cold-generation acceleration or a proven whole-package win.

## Real 55-Member Measurement

Receipt: `.data/d1510-member-tools-real-v1`, exit 0. Durations are native API-body
wall time in separate fresh GSC processes, not complete build/test durations.

| Phase | Existing group proof (s) | Member snapshot (s) |
| --- | --- | --- |
| Cold population | 3.661444 | 3.666485 |
| Stable HIT | 0.073285 | 0.174391 |
| One changed source | 3.671269 | 0.189643 |

One-change generation is approximately 19.36x faster in this component; stable
HIT is approximately 0.101 seconds slower. Only one matched six-phase sample was
collected. The changed member produces one MISS; the other 54 produce HITs.
All 55 C outputs and the complete flat-link output match ordinary full Scheme
generation. Original source inputs remain unchanged. No cold-build, full-test,
MCP or complete ASCENT speedup is inferred from these component timings.

## Safety Evidence And Remaining Work

`.data/d1510-member-tools-controls-v1` passes 13 controls with the interpreted
coordinator over compiled native closure primitives, plus two real concurrent
processes requesting reverse member order. Source/include, option, tool-content,
environment, failure, corrupt pin, duplicate target, disabled flag and macro
context controls pass. Two injected mid-batch changes are rejected.

`.data/d1510-member-tools-default-controls-v1` passes those same controls without
the shared-tool mode, preserving the original per-member tool-check path.

The first compiled-coordinator attempt at
`.data/d1510-member-tools-compiled-controls-v1` fails after seven controls:
rebinding the closure procedure does not intercept its compiled direct call.
The intended mid-batch mutation never happens. This is a fixture limitation,
not a passed mutation control and not proof of a runtime safety failure.

The corrected explicit compiled scope at
`.data/d1510-member-tools-compiled-controls-v2` passes **11 controls** and both
concurrent processes, with exact ordinary C parity. It excludes the two rebinding
injections, rather than falsely reporting 13 compiled controls. External-process
mid-batch mutation controls are required before promotion.

Publication remains member-local: earlier successful members may publish before
a later member or final batch validation fails. Failed members preserve their
prior C/proof and release locks; no successful batch result is returned on error.
This does not prove atomic whole-batch publication. Failure/retry behavior and
complete ordered CLI binding must be qualified before consumer integration.

No whole-consumer routing or complete ASCENT qualification is claimed. 0040 and
the member coordinator remain outside the frozen six-patch MCP series. Its
4.5 / 42 / 97 second gates and measured implementation bytes remain unchanged.

## Exact Identities

- GSC: `8d273f3b0063033d3cb477cc4117e7be6f53920e1315d6bd1f08918f361bb7f8`
- 0040: `0fb295ac80667c247c0bed86222b7c4e2745b6a4232af3e2d18baced1ee57b5b`
- Coordinator: `a4a0f2f9a97278aa762aa3ed87c9c71832cd039804e1c11eaf79f4de3ffefeda`
- Benchmark: `99d476c90c5ab2b6470aa11b3f0156d9619b2348473875935eaed0b0031677a7`
- Real output identity log: `24e47e5f56c4d8da1bf084e005f013a858e2a471d822a9ea73591edd18ef0227`
- Complete ordinary/member link C: `c63ba70603e2afcd4b05da8eaccfc17252dbda32566d4d49970e6c8c3a0fc962`
- Compiled-controls v2 identity log: `5d6dcf2ec13573945111cbcc4930f7fab83cb26dd6feaa7a3b85123d0d31b36c`

Native controls run GSC directly with the matched Multiple-VM runtime and GNU
GCC-built compiler. Python is used for compiler-source preparation only, not to
supervise these native tests. Personal absolute paths are not included here.
