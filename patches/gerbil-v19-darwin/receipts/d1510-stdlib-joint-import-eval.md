# D1510 Joint Standard Library Import/Eval Attribution

Decision: pursue the remaining interface expansion and begin-form execution
boundaries, not symbol-reference acceleration or submodule request-count
reduction. No production optimization or end-to-end speedup is admitted.

## Actual Shared Entry Points

The observer uses current-expander-module-import, current-expander-module-eval,
current-expander-compile and current-expander-eval. These parameter callbacks
are actually reached, unlike earlier global reader rebinding with zero hits.
Their defaults in expander/init.ss are core-import-module, core-eval-module,
__compile-top and Gambit ##eval respectively. The compile category denotes
Gerbil lowering; it is not GNU C compilation and does not separately measure
Gambit's internal compilation during ##eval.

All boundaries share one nesting depth. Records are postorder and subtract
immediate children once, across categories, before aggregation. The observer
validates nonnegative finite durations and complete roots. It does not collect
allocation intervals already known to be unreliable for subtraction.

Four original standard libraries complete in fresh processes with an empty
package home, standard-library-only load path, unchanged frozen host, matching
cached context identity, exit zero and final OK. No MCP package is loaded.
This is protocol attribution, not full library correctness or build/test
qualification. Observer overhead and substantial wall variability remain;
these timings cannot be used as candidate/control speedup measurements.

## Request Count Is Not Executed Cost

The first joint trace sees 2,328 JSON submodule requests without an exact raw
registry-key hit; their summed observed own interval is only 0.003222 seconds.
The corresponding values are 585 requests/0.001683s for make, 509/0.000449s
for test and 354/0.000509s for list/list. An absent exact key does not establish
an interface cache miss: submodule resolution can use an already cached origin.
Do not mistake these requests for repeated interface parsing or native reloads.

## Gambit Evaluation Form Costs

The corrected observer unwraps Gambit source containers and the Gerbil
__noexpand: prefix for classification only. It always delegates the original
code to the original evaluator. No direct global read or evaluator fast path
is introduced. The helper checks ordinary and noexpand root classification.

The final trace groups observed own time over both first-import and explicit
eval phases:

| Library | begin calls / observed own time | Global-reference calls / observed own time |
| --- | ---: | ---: |
| std/make | 107 / 0.404402s | 581 / 0.002351s |
| std/test | 67 / 0.126807s | 469 / 0.001596s |
| std/encoding/json | 263 / 0.823771s | 1,852 / 0.006736s |
| std/list/list | 53 / 0.028539s | 329 / 0.008253s |

The first-import residual import category, after subtracting reached lowering,
evaluation and nested module calls, is 1.209263/0.342097/1.165717/0.226753 seconds
for make/test/json/list respectively in this observed run. It is not pure
reader or binding time: direct internal calls, observer work and other execution
remain inside it. Do not sum inclusive parent times to these exclusive totals.

The source explains why module-eval alone misses work. core-expand-import%
evaluates positive-phase dependencies; core-expand-begin-syntax% executes
compile-time bodies. Actual SSI files contain begin-syntax load-module calls.
eval-syntax* dispatches through the lowering/eval parameters, covering that
execution even when it does not call current-expander-module-eval.

Next: split begin-form preparation, actual native loading and initialization
at reached execution boundaries. These components are not yet separately
quantified. This evidence does not justify skipping begin forms, caching their
results, changing phase order or promoting previous serialization candidates.

## Closed Paths And Receipts

d1510-bound-symbol-native-rejected.md already records both a semantic failure
and no stable major build/startup gain. It remains DENY; high reference-call
coverage is not reason to reopen it. No symbol fast-path candidate was built.

Private reports: .data/d1510-stdlib-joint-import-eval-v1/report.json through v4.
v1 covers only module callbacks; v2 adds lowering/eval. v3 incorrectly labels
all noexpand-wrapped forms as applications, so its root classification is not
evidence. v4 uses the documented decoding rule. Earlier reports are preserved.
Parser and existing import-tree regression checks: 17 passed.

The frozen host remains SHA256
1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21.
No full cold build/test wave was rerun, no performance gate was widened, and
no runtime patch or GitHub publication follows from these diagnostics.
