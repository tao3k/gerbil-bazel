# Fork FD Cleanup: Compiled Consumer Gain, MCP Admission Denied

This experiment follows the retained FD component result, not the rejected
same-PATH spawn eligibility extension. It never changes executable search,
resource limits, MCP business code, std/make, std/test, or the original HOME.
The host-FD candidate's failed first-log repeat remains DENY.

## Archive Boundary

`build_darwin_fork_fd_archive.py` makes a private copy of `libgambit.a`, replaces
only `os_io.o`, and compares every non-index archive member by SHA256. No member
is added or removed. The Scheme reader, Scheme globals and RTS linker object
remain original in this consumer archive. Frozen artifacts are verified before
and after construction.

Private archive SHA256:
`29ce53bfe87ba4cb30db9dac4f9d1a78bff18740d31634197e0c88b4bc51062c`.

Evidence: `.data/d1510-fork-fd-consumer-prefix-v1/report.json`.

## Actual Compiled Consumers

The original unchanged GSC and GNU GCC compile identical Scheme into two
executables, differing in selected RTS archive. Actual link logs select the
respective archives. `nm` confirms `proc_pidinfo` in the candidate executable
and not the frozen executable. This is deployment evidence beyond host CLI
interpretation; it is not yet MCP deployment evidence.

The four controls retain exact output and exit status for explicit-environment
shell execution, no-shebang execution, changed child PATH, and missing command.
An initial single-consumer ABBA has variable startup timings; no ratio is
admitted from it. The next campaign repeats all four controls eight times per
consumer with 12 concurrent workers per wave:

| ABBA role | Wave seconds | Consumers passed |
| --- | ---: | ---: |
| Original A | 9.145776708 | 12/12 |
| Candidate B | 0.932322042 | 12/12 |
| Candidate B | 0.351461583 | 12/12 |
| Original A | 8.454456459 | 12/12 |

All 48 compiled consumers pass, with **1536 exact process outcomes** checked.
The component campaign retains 5-second first-output/silence and 50-second
complete watchdogs. The roughly 13.7x ratio of aggregate wave times is scoped
to this repeated four-process workload, not macro expansion, cold builds,
Gerbil startup generally, or the MCP suite.

Evidence: `.data/d1510-fork-fd-consumer-controls-v1/report.json` and
`.data/d1510-fork-fd-consumer-controls-v2/report.json`.

## Real MCP Consumer Route: DENY

`run_d1510_consumer_archive_progressive.py` leaves the frozen reader CLI and
the original runtime HOME unchanged. A scoped wrapper injects the existing
`GERBIL_BUILD_PREFIX` into the retained cold environment so the executable
link can select the private archive. The original progressive harness file
and its 5/50 gates are not edited. This experiment contains neither the
string-span nor whitespace-reader candidate, nor the denied host-FD binary.

The first real MCP cold attempt records:

- Clean: exit zero, zero native images remaining.
- First actual compile: **4.791511000 seconds**.
- Full-build deadline: **DENY at 50.013553334 seconds**.
- Killed and reaped: terminal exit -9.
- Sources and frozen inputs unchanged.
- Later cold rounds and full test wave: SKIP.
- Completed/deployed MCP executable: none; no complete build time exists.

Evidence: `.data/d1510-fork-fd-consumer-progressive-v1/report.json`,
`progressive-admission.json` and `consumer-deployment.json` in that directory.

The component advantage is retained as a bounded discovery. This consumer
prefix route is not an admitted optimization and must not replace the mainline
anchor. No claim is made that FD cleanup caused the cold deadline failure.
Do not repeat this route by widening gates or averaging away the failure.

## Published Anchor CI Boundary

For published commit `0e4330af5300548415f3062b5b4dba8de571c9e1`, Ubuntu
source-host CI succeeds, but macOS source-host CI exits 70 in the repository
provider validation. The typed failure is a missing materialized `gambuild-C`,
not a local performance-gate pass or a diagnosed reader regression. This CI
failure remains unresolved in this investigation; no unrelated provider code
is modified to claim performance qualification.
