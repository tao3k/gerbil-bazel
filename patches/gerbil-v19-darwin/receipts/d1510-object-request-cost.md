# Configured Object Request Cost: DENIED

## Admission Review

The previous goal turn made progress: replayable 0046/0047 candidates, real GSC
proof handoff, native concurrency and environment regression passed. It did not
prove a package acceleration. Before changing Gerbil, inspect its real scheduler:
`schedule-darwin-objects-and-link` already submits every static object job before
the link barrier. A new coordinator does not create previously absent parallelism.

The next hypothesis was that sharing validation would offset preparation cost.
Expected benefit was unknown. A matched real GSC experiment now contradicts
that hypothesis for the proposed preparation route. Do **not** integrate the
unchanged preparation-plus-coordinator route or repeat its package benchmark.

## Actual ABBA Evidence

`.data/d1510-object-request-cost-v3` exits 0. The direct Bash/GSC/GNU GCC harness
uses 12 physical workers, real MCP generated C, independent source directories,
dynamic/PIC compiler options and the same owned configured driver in both arms.
It first creates 12 genuine producer proofs, then runs ordinary/batch/batch/
ordinary requests. Each timed member must HIT. All four waves preserve the exact
original object **and** proof bytes, not just program output or an exit marker.

| Request wave | Complete request wall time |
| --- | ---: |
| Existing configured GSC check A | 0.83 s |
| GSC preparation plus native coordinator B | 1.52 s |
| GSC preparation plus native coordinator B | 1.66 s |
| Existing configured GSC check A | 0.93 s |

Both candidate waves are slower. Pair means are 0.88 versus 1.59 seconds,
approximately **81% higher request cost** at the timer's two-decimal precision.
This is a component regression, not a measured package regression, cold build,
first-log result or test timing. No aggregate package gain is extrapolated.

The current candidate repeats configured-driver GNU/tool preparation, then the
coordinator separately verifies tool selection before/after execution. It also
retains the per-object before/after content checks. The experiment establishes
net cost, not a causal time allocation among those steps. Reducing checks without
an equally strong correctness argument is not an admitted optimization.

## Excluded Attempts

V1 exported changing phase labels into the GCC environment; proof identity
changed and byte comparison rejected it. V2 removed those labels but exported
the harness variable `output`; ordinary and preparation helpers assigned it
different spellings, again changing the exact environment and rejecting proof
parity. These are invalid timing controls, not evidence of an acceleration.
V3 passes harness controls as shell positional arguments, without exporting
diagnostic variables into the compiler context. It passes all identity checks.
Arbitrary exported helper-local variable collisions remain an integration concern;
this matched experiment does not qualify that broader environment surface.

## Decision and Next Boundary

**DENY performance promotion.** 0044/0045/0046 correctness evidence remains valid
for its qualified contexts, but 0047 is not a performance feature. No patch is
added to the frozen six-patch series. No Gerbil scheduling edit, full MCP retry,
ASCENT admission or release promotion follows from this measurement.

Return to the faster frozen implementation rather than treating more coordination
as an optimization. Any future producer reuse route must first account for the
cost of proof acquisition at every dynamic library compilation, not only the
static consumer HIT count. The unchanged eager all-producer 0043 configuration
was already denied at the 42-second whole-build ceiling. A valid replacement
must eliminate demonstrated duplicate work while preserving execution context,
source/options/tools binding and whole-request mutation rejection; it cannot
reuse these failed results as admission.

Frozen retained MCP numbers remain: first logs 4.038430 / 3.980393 / 3.950160 s;
cold builds 36.414237 / 35.551924 / 37.770491 s; complete tests 86.924285 s,
39 files / 965 cases. Per-sample limits stay 4.5 / 42 / 97 s. No new whole-package
timings were measured in this turn; full ASCENT and general release stay open.

Harness SHA-256:
`26c475e790027a8049c5dd6549855b01a2708abb09602aa156f0e0e11cb37bed`.
Raw `.data` binds four timer files, individual HIT logs, reference objects/proofs,
batch records/logs, tool/input identities and terminal status. Native semantic
execution is direct Bash/GSC/GCC; Python does not supervise Scheme tests.
