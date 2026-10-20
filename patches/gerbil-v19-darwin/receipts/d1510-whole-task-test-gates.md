# Whole-task test acceptance

The user confirmed whole-task first-log 5s, cold-build 50s, complete-test 52s
acceptance. No per-file or per-case silence deadline is imposed. This replaces
the extra per-file 5s silence rule for new campaigns, not historical receipts.

The frozen 47s candidate and its matching cold-built MCP executable were used.
All 39 files and 965 case names remained required, with 12 physical-core workers,
selected-toolchain identity checks, unchanged assertions, exit-code checks and
final OK required. No MCP business source or std/test source was edited.

| Run | Scheduling | First real output | Test wave | Passed files | Verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | Original file order | 2.650681s | 52.101241s | 36/39 | DENY |
| v2 | Integration-first | 2.549699s | 52.136884s | 37/39 | DENY |

Both waves were forcibly stopped at the whole-task 52s deadline; reported wave
durations include process termination/reaping overhead. They are not successful
complete-test times. The v2 completed files account for 857 passing cases;
additional passing cases in unfinished files do not qualify those files.

Remaining v2 cases at termination:

- `chunk-07-test.ss`: `gerbil_howto_verify checks built-in recipes`.
- `chunk-12-test.ss`: `scans a real binary (gxi)`.

Both files started at the front of the v2 queue and still exceeded the global
deadline. Scheduling alone does not resolve these two bottlenecks. Chunk 18,
previously queued until about 21s, completed in 43.056364s when scheduled first.
Do not promote integration-first ordering as a Gambit runtime speedup.

Source boundaries identified without changing them: cookbook syntax verification
uses sequential batches of five recipes through selected gxi subprocesses;
binary audit captures `strings` output and classifies strings with Scheme regexes.
These are investigation targets, not yet proven root causes or qualified fixes.
The frozen CLI replaces runtime objects but preserves the original static
archive, so CLI and compiled MCP-server runtime coverage must remain distinct.

Private evidence:

- `.data/d1510-whitespace-complete-wave-v1/report.json`
- `.data/d1510-whitespace-complete-wave-v2/report.json`

The published cold baseline remains 47.771713s, 47.824226s, 47.927094s.
At v2, complete-test correctness remained unqualified. Neither strict wave
widened a timeout or marked an unfinished file passed.

## Authorized complete diagnostic

The user separately authorized one complete timing run without terminating at
the 52s performance ceiling. Formal acceptance limits remain 5s/50s/52s. The
diagnostic marks performance DENY at 52s and continues solely to observe final
correctness; it has a separate 900s execution safety limit. Internal MCP request
and subprocess timeouts and all assertions are unchanged.

Result: **39/39 files and 965/965 cases passed**, every invocation exited zero,
every file had final OK, exact case inventories matched, and all test file
hashes were unchanged. First real output was **3.489507s**. Full concurrent
test-wave wall time was **120.498387s**, including job scheduling, per-job
toolchain validation, test execution and process reaping. It excludes prior
cold builds and the runner's pre-wave identity/inventory preparation.

The performance ceiling was recorded as DENY at 52.018774s. Correctness passed;
performance did not. This run does not qualify a faster release.

Longest complete invocations, overlapping rather than additive:

| File | Cases passed | Complete invocation |
| --- | --- | --- |
| `chunk-07-test.ss` | 83 | 120.496085s |
| `chunk-12-test.ss` | 25 | 68.240751s |
| `chunk-18-test.ss` | 137 | 53.073309s |

The recipe-verification case loads both built-in and repository recipes.
The retained checkout has 25 built-in records, 765 repository records, and
789 distinct combined IDs. This is larger than the case title alone suggests;
no recipe data was removed or changed for the diagnostic. These counts do not
provide individual-case timing attribution.

Evidence: `.data/d1510-whitespace-complete-diagnostic-v4/report.json`, SHA256
`ca9aa5dd68299418774098f0656d16f5d4ae06cc0f0eec201391cf426e6bbd6e`.
See the portable summary `d1510-complete-test-diagnostic-v4.json`.
