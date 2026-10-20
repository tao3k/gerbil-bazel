# D1830: original best-line identity, performance not restored

Human direction: develop from original D1510 / D1513 B, not a later slower
candidate; do not investigate the historical/current twenty-second discrepancy.

## Selected Development Input

The existing `.data/best-line.py --identity` validates original binary,
carrier, GSC, runtime archive and all 42 native inputs. All checks pass.
Binary SHA256 remains
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Physical workers remain twelve. No later candidate is selected or layered in.

D1513 B complete builds remain 51.737180 and 53.496910 seconds, mean
52.617045; first compile lines remain 4.789153 and 4.933479 seconds.
The complete-build ceiling remains 55 seconds. Artifact identity alone does
not prove these historical timings have been reproduced.

## Original Binary, One Current Complete Build

D1829 uses that exact original binary and original D1391 library/GSC/runtime
home, existing Bazel GNU GCC configuration, twelve workers, unchanged MCP
head and official clean/build. No new carrier is compiled for this run.

| Boundary | Current result |
| --- | ---: |
| Clean | 5.707417 s, exit 0 |
| Native images after clean | 0 |
| First literal compile line | 6.532353 s |
| Complete build | 82.293993 s, exit 0 |
| Complete-build ceiling | failed |

Sources remain unchanged; the executable exists. This failed timing is not
admitted, does not redefine the best line and does not establish a cause for
the historical/current difference. No discrepancy investigation is performed.
The driver exits one for the performance failure, not a compiler failure.

## Extension Boundary

Source inspection confirms original fourteen traces with only native helpers
7 and 11 outlined. Keep those, object reuse and existing preprocessing policy.
Do not select failed larger outlining, binding-fact or nargs candidates.
Existing D983/D984 evidence of zero real prefix-cache hits across 32,979,564
attempts excludes repeating that cache as an assumed major gain.

The pending binding-fact concurrent build is not launched. Its three Python
shape/invalidation unit tests pass, but its existing full-build failure still
excludes admission. No new performance optimization is delivered in this turn.
The next extension must demonstrate real-workload coverage, preserve native
mutation/GC contracts and pass the original full-build ceiling before admission.

All owned sessions are terminal. No product source, installed toolchain,
consumer, std/make, std/test or HTTP code is changed; no commit or push occurs.
Evidence stays in project-relative `.data/d1829-original-best-line-restored/`.
