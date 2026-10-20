# D1728: six retained builds narrow, but do not explain, the gap

The reference remains D1513's four complete project-cold builds. Its two
D1510 candidate builds take 51.737180 and 53.496910 seconds (mean 52.617045).
The mandatory complete-build ceiling remains 55 seconds. Neither later slow
controls nor the new emitter candidate replace this reference.

## New retained-evidence check

D1727 reads all four D1513 logs and both successful D1678 controls; it runs no
product build. Each log contains 740 emitted compile jobs. Against the first
D1513 B log, the other historical logs have 536, 559 or 592 jobs matched in
order; the later slow controls have 600 or 611. Historical fast builds already
have task-order changes and, in two cases, one compile-file name substitution.
These observations do not prove equal scheduling, but they rule out treating
the mere existence of such differences as a demonstrated regression cause.

The embedded Scheme job positions are 6 and 7, and its executable-object job
position is 553 in all six logs (zero-based). This is emission order, not
actual process start or completion time.

| Retained build | Complete seconds | Last SCM write after first C | Last object write after first C |
| --- | ---: | ---: | ---: |
| D1513 A1 | 53.918332 | 18.516708 | 41.993128 |
| D1513 B1 | 51.737180 | 18.433282 | 41.676922 |
| D1513 B2 | 53.496910 | 20.955064 | 43.166579 |
| D1513 A2 | 53.425696 | 18.371745 | 42.148330 |
| D1678 control 1 | 71.946552 | 29.148262 | 58.749882 |
| D1678 control 2 | 74.649196 | 33.216693 | 62.350903 |

All six retain 739 SCM, 373 C and 187 object files. Artifact write windows
include overlapping work, queueing and possible rewrites. They are not CPU
durations. The two slow controls have longer SCM-generation windows too;
attributing the entire discrepancy solely to embedded C compilation is not
established. Historical complete environment and per-job CPU records remain
missing. No resource, scheduler or compiler root cause is claimed.

Private reproduction: `python3 .data/d1727-retained-sequence-check.py`.
The output directory is exclusive; the retained report includes input log
SHA256 values and complete normalized job sequences. No retained input is
modified. No personal absolute paths are needed in this Git receipt.

## Actual native grouped-emitter result

D1723 rebuilds the actual native GSC from the D1714 emitter source, using
the configured GNU GCC 16 toolchain and unchanged original compiler inputs.
It verifies those inputs unchanged. GSC SHA256:
`815b0fb8ea1df2b9389083484e1e60b27883eedc280d1a589208b2b0d1b8f2a9`.
D1724 provides a private home with the original runtime/library and this GSC.

D1725 uses that home and the exact historical D1510 Gerbil binary for real
MCP clean/build with 12 workers. Clean exits zero and leaves zero native
images. First actual compile is 6.638822 seconds; complete build is
72.089178 seconds, exit zero. The controller exits one because the 55-second
performance ceiling fails. Source inputs are unchanged. No speedup is admitted.

The actual embedded C contains the new grouped packed initializer. It is
36,642,389 bytes versus the retained original's 11,425,281 bytes. Neither
file contains a line beginning `#line`; source line directives therefore do
not explain this particular enlargement. The backend emits packed numeric
initializers and also emits the complete portable fallback. Source layout
reduction alone did not qualify complete-build performance.

D1726 passes twelve native starts, twelve framework imports and the actual
concurrent std/make/std/test fixture with strict genuine-output checks.
The fixture wall time is 16.492 seconds; the observed GCC-frontend peak is
11, so full 12-frontend concurrency is not claimed. This is correctness
evidence, not matched test-speed evidence or a full MCP test-suite result.

The startup/build/test objective remains open. No emitter candidate is promoted
to an admitted performance patch, and no std/make product source is changed.

Private evidence: `.data/d1723-grouped-gsc-native/`,
`.data/d1724-grouped-gsc-home/`, `.data/d1725-grouped-gsc-real-mcp/`,
`.data/d1726-grouped-gsc-concurrent/`, `.data/d1727-retained-sequence-check/`.
