# D1510 Link Resource Source Audit

## Scope

Investigate previously unaudited final-link metadata work on the retained
D1510 plus 0015 line. No candidate compiler is built or selected. No production
source, GNU options, runtime image or consumer is changed. Existing rejected
driver, emitter, batching and cache routes are not rerun.

## Source Mechanism

Gambit's `gsc/_t-c-1.scm` calls `targ-union-list-of-rsrc` for the final
symbol, keyword and global resource lists. Its implementation folds modules
one at a time with `targ-union-rsrc`, repeatedly traversing the accumulated
sorted resources. The binary union also appends demanders and suppliers in
operand order; changing grouping must preserve that order, not merely the set
of resource names.

An isolated semantic probe reads the leading Scheme linker metadata from 187
actual MCP static C inputs retained by the admitted 0015 build. It uses the
original resource constructors/accessors and binary union directly extracted
from the original compiler source. It constructs the global resources using
the original three-category union. It compares the original module fold with
a balanced union over reversed module order, preserving the fold's effective
precedence. The original input lists are not mutated.

| Global-resource check | Result |
| --- | --- |
| Actual input modules | 187 |
| Final global resources | 3,386 |
| Original string comparisons | 697,001 |
| Balanced string comparisons | 63,610 |
| Exact Scheme result equality, including demanders/suppliers | True |
| Probe exit | 0 |

This is about 10.96 times fewer comparisons in this one metadata operation.
It is not an execution-time ratio, native GSC proof, byte-identical generated
link C, complete-build result or first-log/test improvement. The interpreted
probe does not establish the native compiler's CPU share.

## Admission Boundary

The existing [task-identity record](d1604-task-identity-and-tail-boundary.md)
already distinguishes link generation from the later final closure C-object
compilation. Resource merging occurs in link generation, not the GNU backend
compilation of that closure. Reducing metadata comparisons cannot be credited
with removing the closure's C compilation or the early Scheme import cost.

Do not build or publish a full toolchain solely from these counts. This is a
source hypothesis with one real global-resource contract, not an admitted
optimization. Further eligibility requires actual native attribution and
symbol/keyword/global output and warning-order contracts, then an isolated
Darwin/GNU-only implementation. Any complete candidate build above 55 seconds
is DENY. The selected D1510, original GSC and 0015 driver remain unchanged.

Private persistent evidence:

- `.data/d1510-link-resource-audit.py`
- `.data/d1510-link-resource-audit/audit.scm`
- `.data/d1510-link-resource-audit/stdout.log`
- `.data/d1510-link-resource-audit/stderr.log`

No new speedup is admitted by this investigation.
