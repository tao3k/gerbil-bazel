# D1510 Test Execution Boundaries

## Unchanged Official CLI

Original D1510 binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Original runtime home, retained 0015 driver, thirteen distinct MCP unit files,
twelve physical workers, five-second real-output gate and ninety-second wall
gate remain selected. No debugger is attached. Per-child wait4 accounting is
collected only when the supervised process is reaped.

Regex passes all nineteen cases, final OK and exit zero: first output
2.862792 seconds, invocation 3.175061 seconds, user CPU 1.005931 seconds,
system CPU 0.360114 seconds. The other twelve invocations exceed the unchanged
silence gate and are terminated/reaped. Wave wall time is 8.861668 seconds,
including cancellation and the queued thirteenth file. All thirteen input
hashes match after execution. All thirteen children have CPU receipts.

This is not completed suite timing or evidence of acceleration. Root-process
reap accounting does not split Scheme, loader and waited-child work; subtracting
CPU from wall time cannot identify the cause of the remaining interval.

Private evidence: `.data/d1510-test-reap-cpu/report.json`.

## Source Execution Path

`src/tools/gxtest.ss` calls prepare-harness before test-run!. prepare-module
uses import-module with evaluation enabled. In `src/gerbil/expander/module.ss`,
source import reads and expands the module, then delays eval-syntax* until
evaluation. `src/gerbil/expander/core.ss` implements eval-syntax* by calling
current-expander-compile followed by current-expander-eval.

Thus the first test-body output includes tool preparation, module expansion
and evaluation, not just test assertions. These callbacks are Scheme-level
operations, not external GCC compilation.

## Private Callback Diagnostic

A separate private wrapper starts the original gxi, wraps module-import,
expander-compile and expander-eval parameters with dynamic-wind, then invokes
the unchanged upstream gxtest main with the same arguments. It preserves
return values and exceptions. Callback records go to a separate file and
never satisfy the real-output watchdog. No toolchain or test source is edited.

All thirteen processes complete the tool import with the same nested counts:
2,767 module-import entries, 1,858 expander-compile entries and 1,858 eval
entries. Import entries include cache hits and are not distinct loaded modules.
For parse-test, the subsequent completed test-file import adds 796 import,
759 compile and 759 eval entries. Regex adds 7 import, 135 compile and 135 eval
entries. Only regex completes the test gate; the diagnostic exits one.

The common callback workload is a concrete source-level investigation target,
not proof that it explains the macOS/Linux ratio. Per-callback logging adds
allocation, file IO and timing overhead. Interpreter initialization before
the wrappers is excluded; unfinished intervals are omitted. The altered
dispatch is not official CLI timing, and no recorded interval is admitted as
an uninstrumented phase cost or speedup. Nested intervals are summarized with
exclusive accounting rather than summed inclusively.

Private helpers: `.data/d1510-test-phase-diagnostic.py` and
`.data/d1510-summarize-test-phases.py`. Raw records and structured summaries:
`.data/d1510-test-phase-diagnostic/`. The summarizer uses the installed
sexpdata parser; unreadable printed syntax-object labels are retained as
token sequences rather than evaluated.

## Admission

No new performance patch is selected. The next source target is the common
Scheme preparation/evaluation workload, not GCC preprocessing, reordered
logging, a test cache or the rejected lookup-result cache. Actual official
gerbil test success and complete cold build at or below 55 seconds are still
required. Diagnostic success cannot substitute for either gate. All owned
workload and summary processes have exited; supervised children are reaped.
