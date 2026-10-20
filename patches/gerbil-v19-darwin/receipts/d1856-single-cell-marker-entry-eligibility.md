# D1856: single-cell marker entry is a distinct mechanism, not a speed claim

Original D1510 remains selected; the historical complete-build ceiling is
55 seconds. The latest original replay did not restore that performance.
No new candidate is compiled or installed in this investigation.

## Existing Execution Evidence

D1008's complete 187-module preparation counted 75,524,454 marker calls,
52,633,995 single-cell calls, 197,833,368 visits, 50,984,834 forwarded-pointer
repairs and 31,914,212 permanent-object visits. These are aggregate counts:
they do not identify which object classes occur in single-cell calls. Visits
include tail marking and must not be treated as independent function calls.
D1009 measured GC user CPU at roughly 20.5% of that preparation's user CPU;
collector-only work cannot establish a several-fold startup solution.

## Source And Native Mechanism

The retained original mem.c marker loads allocation pointer and limit before
visiting its first cell. For immediate values it performs no object handling.
For permanent objects it performs no mutation. For forwarded objects it only
repairs the cell with the existing forwarding/tag expression. Movable and
still objects require the original allocation/queue paths. Debug validation
is an additional effect and cannot be bypassed.

The verified D1729 disassembly of the D1611 capture's RTS includes
`mark_array.constprop.4` at `0x101547564`. Before its first memory-allocated
tag test at `0x101547594`, it allocates a 144-byte native frame, saves the
link register and x19 through x28, and loads allocation pointer and limit.
Its immediate-value exit also stores allocation pointer and restores the
saved registers. Thus the retained GNU binary did not turn this entry into
a frameless no-copy fast path. The clone's argument-count interpretation
must be checked against actual callers before claiming single-cell coverage.

A possible distinct mechanism is a caller-inline single-cell gate: immediate
and permanent cells return without entering the full marker; forwarded cells
use the exact original repair; movable/still/unknown cases enter the unchanged
marker. It must evaluate pointer/count arguments once, preserve original
ordering, and stay Darwin/GNU, non-debug, single-VM/single-threaded/one-processor
only. This is not traversal reordering (D999) or strong-table batching (D1004).
No platform causal claim follows: the same algorithm can exist elsewhere.

## Admission Gate

First verify actual native callers and obtain the missing single-cell/object
class intersection, not another aggregate marker census. Preserve tail-mark
semantics and state/weak-table/continuation contracts. The old counts and
prologue establish a mechanism to investigate, not removable CPU cost or a
reason to launch a whole toolchain build. No fast-path source is implemented,
no performance patch is admitted, and no first-log/full-build/test improvement
is claimed. The broader requested optimization remains open.

Evidence reused without another workload: `.data/d1008-gc-mark-counts/report.json`,
`.data/d1729-native-instruction-audit/instructions.txt`, and original
`.data/d1391-runtime-object-source/src/gambit/lib/mem.c`.
All owned sessions are terminal. No product edit, commit or push occurs.
