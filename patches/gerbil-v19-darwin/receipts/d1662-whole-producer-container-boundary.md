# D1662: whole-producer temporary-list boundary, not an acceleration

The preceding goal turn made progress: D1657 proves that the selected two
consumers already have approximately 99.19% observed fast-path coverage, while
D1654's actual complete build fails the unchanged 55-second gate at 63.367271
seconds. Expanding only their remaining branches is not admitted as the major
startup solution. D1513's 52.617045-second historical mean remains retained.

## Reuse Existing Evidence

D1613's wider hardware capture attributes 33.55% of active cycles to the
coalesced host, 28.66% to mark_array and its clone, and 5.24% to GC hash lookup.
This is a perturbed diagnostic capture, not a fresh uninstrumented time split.
Its source categories do not identify one removable opcode. Existing heap,
strided-marker, hash, arity, entry and callback experiments are not repeated.

D1290/D1296's existing constructor census records 5,355,054 initial mark-list
cells in syntax-e (128,521,296 bytes), 1,762,913 additional list cells
(42,309,912 bytes), and 12,855,681 fresh stx-apply-mark wrappers
(514,227,240 bytes). These historical preparation-workload counts are not
new first-write measurements, and cannot be multiplied by current path counts
or turned into a wall-time reduction. The wrapper site remains the larger
individual recorded allocation site.

D1154-D1169 already reject adjacent-mark cancellation as the canonical
syntax-e opportunity. D1503 already tests callback/loop specialization.
The new audit asks a different question: whether the temporary list container
can disappear while its escaping contents and result objects remain intact.

## Current Source Audit

The current D1391 generated C for stx, util and mop is parsed into the existing
GVM model. The audit starts at the actual original syntax-e entry, rather than
after the first fold or in a selected caller. Providers, branch predicates,
allocation fields, frame changes and original poll snapshots are retained.
No Scheme source or product behavior is changed.

D1660 initially supplies no entry arity and obtains zero states: the model
refuses the original one-argument entry test. This is an analysis setup failure,
not evidence that the source contains no eligible work. D1661 supplies nargs=1
with an explicit runtime eligibility guard; wrong arities are not assumed valid.
The existing bounded path option requests 1024 paths, keeping all other work,
statement, frame, call, allocation and poll bounds unchanged.

| Audit measurement | Count |
| --- | ---: |
| Completed bounded states | 198 |
| Completed ordinary-return inventories | 122 |
| Paths with a three-word pair unobserved by normal return | 122 |
| Paths where original poll snapshots still observe that pair | 122 |
| Paths allowing deletion with snapshots unchanged | 0 |

The normal-return-only inventory excludes poll snapshots solely to identify
the container. It does not emit transformed code or authorize skipping polls.
All reported candidates are pairs; result structures remain retained. Thus
this whole-producer audit does not justify eliminating the larger wrapper site.
It is not exhaustive: unsupported box operations, bounded ancestor visits,
unsupported return/frame cases and infeasible paths are recorded separately.

## Decision And Required Proof

Do not blindly delete the list, declare its enclosing wrappers dead, or turn
the hypothetical inventory into an emitted native optimization. Any container
elision must materialize the original list at each relevant poll exit, reserve
enough original heap space, preserve retained allocations and dependencies,
and roll back private allocations on a failed guard. Identity, rebinding,
exceptions, continuations, live roots and original resume points remain gates.

This source audit expands ownership coverage beyond two consumers, but finds
only a three-word container on its completed paths. It supplies no proof of a
major execution-cost reduction. Before investing in a full candidate/toolchain
rebuild, the next source hypothesis must cover substantially more executed
work than this container alone, rather than merely having more static paths.
The 55-second full-build ceiling, real first-log and concurrent make/test
requirements remain unchanged and unachieved.

Private evidence: `.data/d1660-syntax-e-spine-audit/` (arity setup failure),
`.data/d1661-syntax-e-spine-arity-audit/`, and
`.data/d1660-syntax-e-spine-audit.py`. Reports lock the actual input C and
analysis-helper hashes. Python syntax validation passes. No runtime benchmark
is repeated, no candidate is promoted, and no consumer/stdlib/package code is
edited. No installation, commit or push occurs. The original goal stays active.
