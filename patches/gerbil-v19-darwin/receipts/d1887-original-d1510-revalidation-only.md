# D1887: unchanged original D1510 revalidation

Only original D1510 is executed. No 0013, marker, substituted GSC, copied
library home or later native carrier is selected. The retained binary remains
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
The original GSC, build driver, RTS and 42 retained input hashes pass identity
checks. Worker count is the machine's 12 physical cores.

The historical B2 project path is used after backup and isolation of generated
outputs. Official clean exits zero with zero native images remaining. Actual
complete build exits zero and source checks pass:

| Original-line run | First compile seconds | Complete build seconds |
| --- | ---: | ---: |
| D1878 | 5.053081 | 56.255963 |
| D1884 | 5.271922 | 58.442762 |

D1884 fails both the additional original-line replay reference (first <=5.2,
full <=56.256) and the unchanged official 55-second complete-performance gate.
The controller exits one. It is not a restored best line or a new baseline.
Historical 51.737180/53.496910-second references remain mandatory history.

## Configuration and freshness

D1884's recorded configuration file is byte-identical to D1878's, SHA256
`a9d7986de75c3dcd2190e55f0d46705804c0b5b84d378111e33e88073f33f5aa`.
This covers the captured flags, compiler/SDK paths and selected artifact hashes;
it is not a snapshot of every possible environmental or kernel state.

D1885 checks all 42 retained static C hashes, their adjacent objects and
Scheme inputs. All C hashes match, all objects exist, and no C or Scheme input
is newer than its object. Current freshness predicates show no stale retained
object. Historical timestamps and actual invocation counts are not inferred.

## Narrowed execution boundary

| Actual output boundary | D1878 seconds | D1884 seconds |
| --- | ---: | ---: |
| First compile | 5.053081 | 5.271922 |
| Prepare-executable-link | 51.606115 | 53.818633 |
| Link-executable | 55.341088 | 57.523001 |
| Complete exit | 56.255963 | 58.442762 |

The observed increase is before executable preparation, not a larger final
object/link interval. These are output-observation boundaries, not exclusive
CPU attribution or per-job completion timings.

D1886 ranks preserved native output modification times for historical B1 and
both replays. Each has 550 package images. Late outputs consistently include
lib, resolve-imports, repl-session and explain-error. The last image precedes
executable modification by approximately 4.6-4.8 seconds. File timestamps
approximate production order, not exact job completion or latency causes.

Original generated outputs are restored after the run; new artifacts remain
separate and the historical tracked project diff is empty. No product source,
original binary, release profile or GitHub PR is changed. Further investigation
must stay on original D1510 and its pre-executable compilation boundary.

Private evidence: `.data/d1884-second-best-line-replay/`,
`.data/d1884-historical-project-backup/`,
`.data/d1885-original-line-freshness/`, and
`.data/d1886-original-line-tail-artifacts/`.
