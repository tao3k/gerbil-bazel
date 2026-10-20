# D1855: broad type-loop lowering lacks major-cost evidence

D1854 joins readonly exact type-loop recognition to the retained D1612
sampled-PC source-line map. It verifies the original D1508 carrier SHA256,
mapping qualification, zero unmapped weights, and every mapped source line's
current text before aggregation. No source is transformed, profiler attached,
native binary built or MCP workload rerun.

The original eleven-module carrier contains 78 recognized control-flow loop
shapes; ten have sampled lines in this retained capture. Their disjoint
recognized instruction-line sets sum to 68,695,800 weights out of the host's
3,376,001,668, or 2.034827% of host line weights. The highest two attributed
loop labels are stx-source and stx-e, at 1.015667% and 0.385858% of host weights.
The prior D1852 count of 158 covered all 42 inputs, not just these eleven
carrier modules. These are distinct scope counts, not conflicting results.

This does not prove an exclusive type-loop CPU fraction or an upper bound on
its total cost: compiler-merged DWARF lines can share attribution and the
recognizer's expression stubs do not establish production eligibility. The
profile is the D1590 composition with the same carrier text, not a new exact
D1510 timing replay. Setup frames outside recognized loop lines are not
included. None of these quantities is a predicted removable-cost percentage.

Nevertheless, existing evidence does not support broad loop lowering as the
requested major startup optimization. D946's separate primitive jump lowering
was already slower. Do not build another whole toolchain based on 158 source
sites alone, or turn this line-attribution result into a claimed speedup.

The broader retained capture identifies host execution and GC marking as the
large distributions. Existing D999 traversal reordering has no CPU gain;
D1004 strong-table batching has only 2.48% and remains rejected. Those tests
are not newly rerun or promoted. Any next candidate must identify a materially
different eliminated-work mechanism before construction, preserving native
roots, polling, mutation and rebound bindings.

Original D1510 stays selected. Historical full-build mean remains 52.617045
seconds with a mandatory 55-second ceiling; performance restoration, major
first-log improvement, full build and concurrent test delivery remain open.

Private evidence: `.data/d1854-type-loop-sampled-line-audit.py` and
`.data/d1854-type-loop-sampled-line-audit/report.json`. The owned audit process
is terminal, no toolchain or product source changed, and no commit/push occurs.
