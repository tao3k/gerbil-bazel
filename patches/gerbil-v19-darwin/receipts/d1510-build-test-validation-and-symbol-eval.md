# D1510 Build/Test Validation and Symbol Eval

## Selected Inputs

Retain original D1510, original runtime home, admitted 0015 driver, GNU GCC
and twelve hardware physical workers. No new VM profile, side patch 0017,
rejected cache, driver extension or consumer modification is selected.
Private projects and evidence remain under repository-local `.data/`.

Binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Driver SHA256:
`65aba56445c2b165b667922603873aec9e58ad3edb733c6d040651eecf6d8d15`.

## Complete Cold Build

An independent clone at MCP head
`9a5c35e275e5d6847ff421151bb224f2eae177c1` runs official clean then build.

| Measurement | Actual | Unchanged gate | Result |
| --- | ---: | ---: | --- |
| Clean | 3.435719 s | 30 s watchdog | exit 0 |
| Native images after clean | 0 | 0 | PASS |
| First actual compile | 5.575722 s | 10 s build silence watchdog | PASS |
| Complete build | 52.723776 s | 55 s performance ceiling | ALLOW |
| Maximum build output gap | 5.575722 s | 10 s | PASS |
| Build terminal status | 0 | 0 | PASS |
| Clean plus complete build | 56.159495 s | separately reported, not the historical build-only ceiling | recorded |

The 180-second build wall watchdog remains separate from the 55-second
performance ceiling. Source hashes are unchanged and the executable exists.
The fail-closed admission controller returns zero with ALLOW; its five focused
regression tests pass. This is a fresh validation of the retained line, not
proof of a new acceleration or stable gain across repeated runs.

Evidence: `.data/d1510-test-mainline-cold-check/report.json`, configuration
snapshot, build log and `admission.json` beneath the same directory.

## Actual Test Gates

The unchanged gates require at most five seconds without actual output,
at most ninety seconds per invocation, exit zero, exact CASE-OK count,
final standalone OK and unchanged input. No synthetic heartbeat or debugger.

The first thirteen-file unit wave passes only regex; twelve files hit the
silence gate. Keep this negative observation. Private evidence:
`.data/d1510-test-mainline-official-wave/report.json`.

The expanded test-file runner also selects all chunk files and protocol tests.
Its initial attempt lacks the upstream script's source-package loadpath for
`test/mcp-client.ss`; integration imports fail. It is invalid as complete
integration qualification and is retained at
`.data/d1510-test-mainline-all-files/`. This is a harness setup error, not
evidence of an interpreter optimization or regression.

The corrected runner adds that project loadpath without editing any module.
The compiled library path and original runtime home remain selected. Child
gxi/gxc/gxpkg entrypoints resolve to the original D1510 binary. MCP server
uses the just-built executable and the upstream full mode.

| Measurement | Corrected actual test-file wave |
| --- | ---: |
| Distinct original files attempted | 39 |
| Files passing all gates | 29 |
| Failed files | 10 |
| Unit files passing | 13 / 13 |
| Successful unit CASE-OK | 177 |
| CASE-OK in successful files | 541 |
| Observed CASE-OK including failed/partial files | 713 |
| First actual output range | 1.411785-3.138595 s |
| Output-silence failures during execution | 4 |
| Terminal result failures | 6 |
| Scheduling/observation wall | 52.195490 s |
| Controller exit | 1 |

Silence failures: chunks 03, 07, 15 and 23. Terminal result failures:
chunks 05, 06, 10, 12, 18 and 21. Examples include chunk 05 expecting stdlib
source paths containing `/src/`, chunk 12 expecting `Binary` output, and
chunk 21 expecting `not found`. Their logs are retained; no consumer fix or
relaxed gate is used to turn them into passes. Some product failures exit
zero, so terminal exit alone is not sufficient.

All thirty-nine test input hashes are independently verified unchanged after
execution. This invokes each file separately, not the upstream twenty-seven
batch script (which groups unit files). The 52.195490-second observation
includes failed/terminated work and is NOT a successful complete-suite time.
It cannot establish a test speedup, nor erase the preceding failed unit wave.

Evidence: `.data/d1510-test-mainline-all-files-v2/report.json`, per-file logs,
and `.data/d1510-test-mainline-cold-check/validation-summary.json` containing
every file's timing, status, expected/observed cases, source check and failure.

## New Source-Level Target

The root census must unwrap both Gambit source objects and Gerbil's
`__noexpand:` prefix. Without the second step, roots incorrectly appear as
compound-headed applications. These invalid classifications are retained,
not used as optimization evidence.

In the corrected diagnostic, tool import records 1,924 eval callbacks:
1,672 symbol references, 186 begin forms and 66 make-type-env calls. These are
diagnostic-dispatch counts, not a measured percentage of official CLI CPU.
There are no root quote callbacks in this census; a quote-only shortcut is
not justified as the main optimization.

Source path: Gambit `_eval.scm` ##eval -> ##eval-top -> ##compile-top ->
##compile-in-new-compilation-ctx -> ##comp-ref -> ##gen-glo-ref. Even a symbol
reference goes through a new compilation scope/table, context parameterization,
code-object generation and source-location conversion. ##var-lookup resolves
CTE namespace aliases and rejects macro-as-variable; ##cprc-glo-ref checks
unbound values and invokes reference stepping. None of these contracts may
be silently removed.

A private shadow experiment always performs ordinary eval first. For symbol
roots whose fresh ##cte-lookup reports not-found, it then reads the resolved
global and compares results by identity. All thirteen tool imports report
1,672 eligible reads and 1,672 identical results, with no mismatch. Regex
test preparation additionally verifies 24 / 24. No original eval is skipped,
no lookup result is cached and no native toolchain source is modified.

This supports investigating a guarded global-reference execution path. It is
different from the rejected runtime hash-filter/result-cache routes: it would
remove per-evaluation compilation work rather than reuse an old lookup.
However, these normal-input shadows do NOT prove namespace/macro mutation,
unbound exception, custom expander hook, stepping or declaration semantics.
They do not establish wall-time benefit or warrant a production fast path.

Private evidence: `.data/d1510-test-eval-census-noexpand-decoded/` and
`.data/d1510-test-symbol-shadow/`. Both diagnostic controllers remain failed
when any test hits its original gate; passing shadow comparisons do not
override that result.

## Decision

Cold-build-only admission: ALLOW at 52.723776 seconds. Joint build/test
delivery: DENY because ten real test files fail. No new acceleration is
claimed, no patch is promoted, and no PR push follows from this receipt.
The next fast-path candidate must be Darwin/GNU-only and pass semantic
controls plus real official tests and the complete 55-second cold-build gate.
All owned workloads are terminal and supervised children have been reaped.
