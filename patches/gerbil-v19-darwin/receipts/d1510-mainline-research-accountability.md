# D1510 Mainline Research Accountability

## Outcome, Not Activity

Recent protocol probes, source audits and framework checks have produced no
new admitted full-build or full-test acceleration. They must not be reported
as performance progress. The retained historical measurements remain:

| Measurement | Historical result | Current whole-task gate |
| --- | --- | --- |
| First compile log | 4.850866 / 4.573628 / 4.592897 s | <=5 s |
| Complete cold build | 47.771713 / 47.824226 / 47.927094 s | <=50 s |
| Complete test | 105.750982 s; 39 files, 965 cases passed | <=112 s |

These are not fresh measurements. Later strict test DENYs remain failures;
the historical pass does not establish stable current acceptance.

## Research Selection Errors

The multiple-VM segment-cache component accesses an operation absent from
the retained SINGLE_VM preprocessor branch. Its ideal-hit component ratio
cannot improve this baseline. Stop this direction for the mainline; retain
its private evidence without integrating a production patch.

The final executable-tail hypothesis was selected from the older 71.716029 s
diagnostic composition. That trace does not establish the current retained
47-second critical path. The source audit confirms that Gambit's linker reads
generated linker metadata and preserves ordered module/preload/resource and
link-option contracts; it does not establish a large current removable cost.
Do not launch a prelinked-closure experiment from this attribution alone.

## Next Admission Boundary

The existing independent standard-library profile reaches import binding,
identifier resolution and module-body expansion, but sparse source-location
samples are not exclusive costs. Continue source analysis there without
claiming a dominant function. Original expander code resolves exports at the
requested phase, constructs weak import bindings, resolves identifier marks
against contexts, and mutates bindings during block expansion. A permanent
resolved-result cache is not equivalent merely because a lookup repeats.
The already rejected whole-context memo route remains closed.

Before another candidate run, identify reached removable work, distinguish it
from existing admitted patches and rejected routes, and state its semantic
contract. Component results alone cannot admit a patch. Only a genuinely new
candidate warrants independent-library controls and heavy clean/build/full-test
validation, with unchanged gates, immediate DENY cleanup and no MCP-specific
production behavior. Do not repeatedly benchmark the unchanged MCP baseline.

No production source, frozen binary, deadline or test assertion changes here.
No new performance claim, commit, publication or goal completion is admitted.

## Four-Question Review Before Implementation

Review date: 2026-10-08. The retained binary SHA256 was checked again and is
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
This checks identity, not current timing. No new cold/test baseline was run.
The stationary-parameter candidate construction was interrupted and its
process query subsequently returned no matching process. No candidate binary
was linked or admitted. The earlier diagnostic compile exceeded 300 seconds;
the second construction was interrupted, not a product performance DENY.

Print the following review before editing candidate code or starting a build:

1. Is the mechanism correct? Identify the reached work, the active retained
   platform branch, removable operations, observable effects, and fallback.
   A plausible source transformation is not proof of correctness or Darwin
   relevance.
2. Has it been explored? Cite the existing positive/negative receipts and
   explain the actual mechanism difference. An absent search match does not
   prove novelty. Do not rename, retune, or compose a denied mechanism.
3. Is it worth optimizing? Tie the removable work to this composition's
   first-log/build/test critical path, not an older slow composition, a static
   instruction count, allocation bytes, or an inclusive sampled stack.
4. What is the expected benefit? Give an evidence-backed time range and its
   assumptions. For removable cost fraction f and acceleration r, an ideal
   total speedup is 1/(1-f+f/r); this is a sensitivity calculation, not measured
   benefit. Counts without a cost fraction cannot supply f. Account for added
   checks, misses, materialization, and construction cost.

Decision must be IMPLEMENT, ANALYZE ONLY, or NO. Unknown semantic obligations
or an unquantified benefit mean no implementation admission. A paper's reported
ratio cannot replace the retained workload's cost fraction. Once admitted to
implementation, independent stdlib correctness and real MCP clean/build/full
test still decide delivery under unchanged 5/50/112 gates.

## Reviewed Leads

| Mechanism | Correct/reached? | Prior work | Worth optimizing now? | Expected benefit and decision |
| --- | --- | --- | --- | --- |
| Stop parameter cache-slot promotion on read hits | Existing helper is reached; preserving values does not prove an unchanged miss rate or a Darwin bottleneck | D1038 counts are historical; shared-result storage is already denied, and must not be reused | Current critical-path cost and miss-rate consequences are unknown | No defensible seconds/factor estimate; NO to further candidate construction from this evidence |
| Broaden rest-list elimination | Some structural entries are proven; polling, debug and argument contracts constrain others | D1316 removed 3,004,279 pairs; D1323 complete build was 69.833692s. D1439 later matched composition only had overlapping full-build ranges and the stdlib candidate was slower | Counts do not support a major current gain; broader poll coverage was already reviewed in D1449 | No current 47s estimate; NO to replay/expansion on these counts |
| Remove syntax-e result fields/wrappers | Fresh allocation is real; unused field evaluation can still have observable effects | Two-module/89-site field elimination and canonical mark-fold are explicitly denied in the progressive-gates receipt | The historical allocation census is not permission to repeat these prototypes | NO; no new benefit estimate is admitted |
| Accelerate fresh-process dependency import execution | Reached in independent stdlib callbacks and original recipe batches; not MCP-only | Joint import/eval, preparation/initialization, and import-binding contracts already constrain it | Retain as an analysis target, not a selected accelerator: native setup is ms-scale, global-reference cost is small, and fresh mutable binding initialization is required | Current removable fraction and concrete algorithm are missing; ANALYZE ONLY, no code/build admission |

Evidence reused rather than rerun:

- [Rest forwarding composition](d1443-rest-forward-reuse-composition.md) and
  [poll coverage boundary](d1449-rest-poll-coverage-boundary.md).
- [Executed allocation and rest-entry records](d970-guarded-trace-progress.md),
  sections D1288-D1345; they are not current exclusive CPU budgets.
- [Closed projection candidates](d1510-progressive-runtime-gates.md) and
  [observable projection effects](d1510-projection-execution-boundary.md).
- [Joint stdlib import/eval](d1510-stdlib-joint-import-eval.md),
  [required binding construction](d1510-import-binding-construction-contract.md),
  and [original recipe import attribution](d1510-125-atomic-investigation.md).

Next safe action is to inspect which immutable preparation, if any, remains
outside required live initialization on the reached import path. Do not launch
another observer campaign, pool MCP's verifier, skip begin forms, or reuse
mutable binding results. If existing sources/receipts cannot identify a
substantial removable cost, reject the proposed mechanism before coding.

## Rejected Candidate Entry Cleanup

After the review, the newly added stationary-hit transformer, CLI switch,
private-carrier test and Scheme control fixture were removed from the active
test source. The retained parameter helper, its existing guards and other
tests were not removed. The Scheme fixture is preserved under
`.data/d1510-stationary-parameter-control-v1/fixture.scm` beside its raw log.
Its original-runtime execution exited 70 after two named checks: the nested
phase-resolution check raised Bad context. It is not an 18-case semantic pass,
candidate failure, or evidence of a regression in the frozen binary.

Parameter/helper and common-framework checks after cleanup: 20 passed.
These checks validate the remaining test code, not full Gerbil correctness or
performance. No candidate artifact is selected, no full test wave is claimed,
and neither the frozen binary nor a production patch was changed.

## Object-Reuse Extension Review

The [compile-job closure](d1510-original-compile-job-closure.md) and
[reuse audit](d1510-reuse-audit-grouped-native.md) were consulted before any
new object experiment. The active patch's executable job checks freshness
after emitting its job log. Existing receipts classify 186 runtime producers
and three different executable/linker inputs. They do not establish another
186 avoidable GCC compilations.

| Question | Answer |
| --- | --- |
| Is more runtime-object reuse the right mechanism? | Existing 0007 reuse is reached and retained; uncovered second compilation is not demonstrated. |
| Has it been explored? | Yes: producer classification and runtime/static C equality are already audited. |
| Is expansion worth implementing? | Not from job counts. NO to removing freshness/dependency checks or merging loader/runtime/phi contracts. |
| Expected benefit? | No supported additional seconds estimate; zero new compiler invocations have been proved avoidable. This is not proof that every possible extension has zero benefit. |

No baseline rebuild, object capture or grouped-emitter retry follows this
review. The previously denied grouped emitter's component improvement is not
an exception to its complete-build denial.
