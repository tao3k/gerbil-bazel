# D1744: reject normalized-mark dead-wrapper paths

The selected starting point remains D1513 B / D1510, not a later candidate.
D1742 rechecks its binary, GSC, runtime archive, carrier and 42 native inputs.
Historical complete builds remain 51.737180 and 53.496910 seconds. Identity
verification is not current performance reproduction; the 55-second gate is
unchanged. No historical/current timing discrepancy is investigated.

D1741 examines the original generated stx/util/mop inputs with the existing
bounded ownership model. Its five-word-removing paths number 37 for stx-wrap
and 18 for stx-rewrap. D1743 follows the actual emitted CAR/CDR expressions
from the mark-list input and checks the normal-path equality guards, excluding
poll snapshot blocks. All 55 paths require equality of adjacent input marks.
This is an explicit guard prerequisite, not a dynamic hit-rate measurement.

In the original Scheme source, syntax-e initializes a singleton mark list and
extends it through apply-mark, which cancels adjacent equal marks. stx-unwrap
preserves this invariant when its initial marks are normalized. The ordinary
core-apply-user-macro parameterization prepends a freshly allocated expander
mark, rather than reusing the immediately preceding mark. These internal
inputs cannot satisfy the observed adjacent-equality prerequisites.

Arbitrary public stx-wrap/stx-unwrap inputs and externally parameterized marks
are not proved normalized. The bounded path inventory is not exhaustive.
Nevertheless, these 55 paths do not establish a significant allocation
opportunity for the normal macro-expansion path and will not be built as a
performance candidate. Historical wrapper-allocation counts must not be
attributed to them. The retained three-word selective syntax-e fragments are
also not promoted as a major win without real native evidence.

No product Scheme source, original carrier, runtime, GSC, std/make, std/test
or consumer is modified. No new speedup or completed goal is claimed.

Evidence: `.data/d1741-whole-producer-ownership/report.json`,
`.data/d1742-best-line-revalidation/report.json`,
`.data/d1743-mark-path-eligibility/report.json`.
