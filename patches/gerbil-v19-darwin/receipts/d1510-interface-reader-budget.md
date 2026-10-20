# D1510 Reached Interface Reader Budget

Diagnostic only. No new candidate, toolchain rebuild, cold build, full-suite
qualification, speedup or publication follows. Retain the historical
47.771713 / 47.824226 / 47.927094-second cold anchor and 5 / 50 / 112-second
whole-task gates. Strict complete-test DENY remains unresolved.

## Source And Executed Entry

`expander/module.ss:227` reads syntax before expanding a module interface.
`runtime/syntax.ss:268` delegates that read to Gambit's
`##read-all-as-a-begin-expr-from-path` with the current readtable and original
syntax wrapper/unwrapper. Retained generated `gerbil__runtime__syntax.c:4208`
uses `___JUMPGLONOTSAFE` through global slot 93 for this actual call. This is
not a guessed global hook that native code bypasses.

The diagnostic replaces only that live slot in its own process, delegates
all original arguments to the captured original function and records reached
calls. It restores the original slot before emitting results and verifies
both installed-wrapper and restored-original identity. It does not change
reader handlers, module interfaces, source positions, consumer code, evaluator
implementation or the installed runtime. Joint callback accounting subtracts
children once; reader CPU/allocation records also carry independent read depth.

Earlier source review finds no new location-cache opportunity:
`_eval.scm:398` already caches the container in the read environment, and
`##filepos->position` is an identity function. `_io.scm:10318` packs file
positions with fixnum operations. Do not claim these paths repeatedly allocate
filename metadata or convert positions with arbitrary-precision arithmetic.
Neither a native AST cache nor another rejected span/fusion candidate is built.

## Completed Original Standard-Library Imports

V2 runs make, test, encoding/json and list/list with the frozen host, selected
runtime home and an empty package home. No consumer packages participate.

| Root library | Reached reads | Observed reader user CPU | Observed reader system CPU | Observed reader own wall |
| --- | ---: | ---: | ---: | ---: |
| make | 60 | 0.020716 s | 0.003216 s | 0.024055 s |
| test | 40 | 0.019345 s | 0.002288 s | 0.022395 s |
| encoding/json | 139 | 0.051498 s | 0.006765 s | 0.059050 s |
| list/list | 32 | 0.017906 s | 0.002639 s | 0.040119 s |

All 271 read budgets have read depth zero, so there are no nested reader
intervals to double-count in these sums. Statistics and joint observer work
have overhead; CPU is not a wall-speedup forecast. Reader GC intervals are
included in reader CPU and must not be added as another disjoint budget.
The observations do not cover every other port, string or source-reading API.
They do not prove an exact whole-build fraction or a macOS/Linux causal gap.

Each process completes import/eval/cached-import/cached-eval with original
cached-context identity, final OK and exit zero. Export/native-module inventories
match the corresponding original Gambit-split control. The frozen binary SHA
is unchanged. Selected parser/loader regression tests: 40 passed. All children
are terminal. This is import-contract validation, not every library assertion
or the complete 39-file test wave.

## Separate Failed Allocation Measurement

One JSON reader observation reports an allocation delta of -1,245,216 bytes
across a GC. The cause is not established here. V1 consequently fails its
nonnegative-allocation diagnostic check after make/test, despite completed
original execution; its failure record remains unchanged.

V2 retains the signed raw delta and marks
`readerAllocationBudgetQualified=false` for JSON. Finite CPU/GC intervals,
matched reached calls, restoration and functional checks remain required.
This separates valid CPU observation from failed allocation observation; it
does not clamp the value, admit an allocation saving or relax a performance/
correctness gate. Do not sum the JSON allocation deltas into a claimed reader
allocation budget. Other nonnegative samples alone do not prove exact
application-only allocation accounting.

## Next Decision

These measured reader intervals do not support a several-fold startup win
from replacing this interface parser. This narrows the next investigation
to the remaining shared in-process expansion/construction/evaluation work,
rather than reviving reader span/fusion, disabling source metadata or adding
a parsed-interface cache from source plausibility alone. The successful
token/whitespace patches remain retained; this finding does not reject them.
No new production candidate or cold/full-test campaign is admitted here.

Evidence: `.data/d1510-stdlib-interface-reader-v2/report.json`, SHA256
`aa2eef898c7bf56685d481f672797cfa374d17ac844241a273c34f38a22692f3`.
Original comparison: `.data/d1510-stdlib-gambit-eval-split-control-v1/report.json`.
Unqualified allocation attempt: `.data/d1510-stdlib-interface-reader-v1/report.json`.
