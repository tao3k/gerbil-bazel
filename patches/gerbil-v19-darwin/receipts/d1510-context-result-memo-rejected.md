# D1510 Context Result Memo Rejected

The selected entry remains the original D1510 / D1513 B binary. The recorded
fallback is D1878: first compile 5.053081 seconds, complete build 56.255963
seconds. New candidates must pass the unchanged 55-second complete-build gate.
Neither the fallback timing nor the historical 51/53-second timings are newly
reproduced by this investigation. No installed toolchain or consumer source is
changed. All experiments live under the project's private `.data` directory.

## Completed Original Work

A readonly diagnostic copy derives directly from the retained D1508 carrier,
the original ordered objects and RTS. Every original lookup executes. At the
first actual MCP compile log, the verified build child reports:

| Event | Count |
| --- | ---: |
| Whole resolver entries and returns | 4,574,995 |
| Unmatched returns or overwritten pending slots | 0 |
| Returns crossing an observed invalidation boundary | 896 |
| Completed repeated context/key calls | 1,768,289 |
| Different returned words in those repetitions | 0 |
| Original helper iterations | 30,369,684 |
| Helper iterations inside completed repetitions | 12,520,492 |
| Observed KEY_MOVED lookup boundaries | 1,796 |

The repeated calls account for about 41.23% of observed helper iterations.
This is work locality, not CPU savings, cache eligibility or end-to-end gain.
Saved words are never dereferenced or returned by the observer. Known stores,
global writes, all 23 register reload definitions and EXPR boundaries invalidate
observations. The readonly census does not fence STRUCTURETYPESET; source audit
found that direct type store and the candidate adds it and header-store fences.
Consequently the census is not a complete mutation or cache-safety proof.

The diagnostic first log is 5.844941 seconds; instrumentation makes it unsuitable
as a performance comparison. It deliberately stops there and reaps the build
child, exit 70. It is not a successful complete build.

Private evidence: `.data/d1510-context-result-census-v2/report.json` and
`.data/d1510-context-result-prefix/count.first.179.tsv`.

## Independent Candidate

The private candidate memoizes a completed whole resolver result rather than
individual table lookups. It preserves the original entry poll, is guarded for
Darwin/GNU/single-host/single-VM/single-thread operation, and clears eligibility
at known writes, global/type/header changes, reloads and KEY_MOVED lookups.
It never modifies the original carrier or selected executable.

Twelve concurrent real Scheme contract processes pass all 432 case records,
including absence, inheritance, GC, nearest binding, removal, rebound callback,
exception, continuation and parent mutation. These checks are not exhaustive
cache-hit or mutation-ABI qualification.

Actual MCP official clean/build, twelve workers, original GNU GCC environment:

| First compile | Complete build | Build exit | Native images after clean |
| ---: | ---: | ---: | ---: |
| 5.245279 s | 72.213895 s | 0 | 0 |

Source hashes remain unchanged. The 55-second performance gate fails; the
controller exits 1. This single candidate run is not a matched estimate of the
cache's slowdown relative to D1878. It is sufficient to reject admission.

The same build's unmodified thirteen MCP unit files also run through official
`gerbil test` with twelve concurrent workers and the unchanged five-second
genuine-output gate. Original: 1/13 passes; candidate: 3/13 passes. Both waves
are unqualified. Do not infer a test speedup from those partial passes or wave
times. All failing rows and logs are retained; no watchdog is relaxed.

Private evidence: `.data/d1510-context-memo-contract/report.json`,
`.data/d1510-context-memo-mcp-cold/report.json` and
`.data/d1510-context-memo-mcp-unit-wave/report.json`.

## Decision

Reject this candidate. Repeated-work counts have not translated into first-log,
complete-build or test qualification. No production cache patch, selection
change, commit or PR follows from these results. Do not widen this implementation
or promote its 72-second result to a new baseline. The original D1510 fallback
and 55-second upgrade gate remain locked; performance restoration remains open.
