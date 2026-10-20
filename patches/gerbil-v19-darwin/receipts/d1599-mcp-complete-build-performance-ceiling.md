# D1599: MCP complete-build ceiling is 55 seconds

The user explicitly sets a maximum 55-second performance gate against the
retained D1513 candidate complete-build mean of 52.617045 seconds. This is an
acceptance ceiling, not a new measured speedup or a replacement baseline.

| Recorded boundary | D1513 candidate mean | D1592 candidate run |
| --- | ---: | ---: |
| First compile | 4.861316 s | 4.641963 s |
| Complete build | 52.617045 s | 68.561755 s |
| After first compile | 47.755729 s | 63.919792 s |

D1592 fails the complete-build ceiling by 13.561755 seconds. Its improved first
line does not admit the candidate. These historical runs are not a newly matched
comparison, and the added tail time has not yet been attributed to a stage.

The private driver `.data/d1395-mcp-runtime-object-ab.py` now records
`buildPerformanceCeilingSeconds=55`, per-run `buildPerformanceGatePassed`, and
`performanceCeilingQualified`. Every required run must complete successfully
within 55 seconds to pass the ceiling; missing or failed runs cannot pass.
The existing 180-second diagnostic termination budget remains separate so a
diagnostic can finish collecting the tail without qualifying its performance.
No existing report is rewritten and no matched acceleration claim is generated.

Real clean, zero project native images, locked source/toolchain identity and
hardware-derived concurrency remain required. Build-output silence stays ten
seconds; test-output silence stays five seconds. First-log stability, complete
build performance and actual test correctness/progress are independent gates.
No product source, installation, commit or push changes occur in this turn.
