# D1510 Standard Library Filesystem Budget

Original-only diagnostic; no production patch, speedup admission, or unchanged
cold/full-test campaign. Keep historical cold times 47.771713 / 47.824226 /
47.927094 seconds and the 5/50/112-second whole-task gates.

## Reached Calls

The retained generated `_nonstd.c` calls the live global entries for
`##os-file-info` and `##os-path-normalize-directory` (GLO 346 and 353).
The optional `--filesystem-budget` observer wraps those actual globals,
delegates original arguments/results and restores both globals before output.
It does not change filesystem policy or cache directory answers.

Process user/system CPU and minor/major fault deltas accompany each observed
call. Every observed filesystem call has independent depth zero, so their
budgets do not overlap each other. The parser rejects nesting, missing either
operation, malformed/negative/nonfinite counters, unmatched postorder trace
entries and missing restoration. Measurements include observer overhead and
do not constitute pure syscall timings or candidate/control gains.

## Original Outcomes

| Library | File-info calls / CPU ms | Directory-normalization calls / CPU ms | Directory-normalization system CPU ms |
| --- | ---: | ---: | ---: |
| make | 503 / 9.010 | 1,014 / 57.594 | 53.528 |
| test | 306 / 3.099 | 648 / 19.783 | 18.016 |
| encoding/json | 1,450 / 21.608 | 2,626 / 130.544 | 120.895 |
| list/list | 258 / 2.636 | 548 / 18.548 | 17.012 |

All four fresh original processes finish with exit zero, original cached-context
identity and final OK. Export/native-module inventories exactly match the
earlier interface-reader control. No consumer package is imported. Both native
globals are restored and the frozen binary SHA256 remains
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
All sampled filesystem intervals report zero major faults. This does not
explain the phase's other major faults or establish disk/cache behavior.

Evidence: `.data/d1510-stdlib-filesystem-budget-v1/report.json`, SHA256
`19746db9dc8a5ce842636028914971ff25ffaf7fd8497803c044cd9face5588b`.
The reached-parser and retained-native-loader regression tests report
41 passed. These are diagnostics and focused regressions, not complete
stdlib/MCP correctness or performance admission.

## Do Not Reopen The Old Filesystem Route

The source uses a mutex-protected save-cwd/chdir/getcwd/restore sequence in
`os_files.c:1451`. This is not newly discovered: D1088 and D1246 already
quantified/rejected a filesystem rewrite as the dominant startup remedy.
D1250 also records Apple's existing getcwd F_GETPATH/identity-check path.
Those entries were not in the compact exclusions index; they are now indexed.

The new observation narrows some previously unclassified standard-library
system CPU, but does not justify repeating directory caching, a realpath
rewrite, replacing getcwd with F_GETPATH, or omitting identity/permission checks.
Directory-normalization savings alone have no demonstrated seconds-scale
startup budget here. No such candidate was built.

The existing provider observations likewise show only 0.211-0.343 ms
provider-own wall time for make and 0.582-1.127 ms for JSON in the CPU-loader
report. Rewriting the provider table search is not a major-gain target from
those observations. Its digest and setup components were measured separately;
they cannot be relabeled as lookup cost.
