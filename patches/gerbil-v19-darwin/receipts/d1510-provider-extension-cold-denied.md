# D1510 Three-Provider Extension: Cold DENY

Decision: do not promote or widen this candidate. The retained 47-second host
is not replaced. First-log/build/complete-test gates remain 5/50/112 seconds.

## Constructed And Executed Candidate

`tests/build_provider_extension.py` links the three verified ordinary objects
from `d1510-provider-extension-construction.md` into a separate host. It retains
all original static objects, reader runtime objects and 280 provider objects.
The original Darwin/GNU guard, exact pathname/linker/image-digest admission and
ordinary fallback remain. Only extra declarations, rows and objects are added;
the optional hit trace is a diagnostic, not performance admission.

The generated host SHA256 is
`7b6c66816a5ada54b150e1473039d9705bda3ae19b8c489faf922ea44893ff43`.
All eight original fresh-process standard-library imports/evaluations complete
with exit zero, original context identity and final OK. Control/candidate
export and native-module inventories match. Every added provider is reached
in the make import; none is reached by the control. The retained binary and
locked original inputs remain unchanged.

The initial candidate make process takes 3.166707 seconds versus the control's
0.456983 seconds. These single hit-traced observations are not a matched
performance campaign or attribution of cause. They are preserved, not removed
as warmup. No speedup follows from other single pairs that happen to be lower.

## Unmodified Focused Standard Tests

Control and candidate run original list/list and encoding/json tests
concurrently. Each host passes all 32 list and 33 JSON cases, with every CASE
matched to CASE-OK, exit zero and final OK. This is 65 cases per host, not the
complete stdlib or MCP test suite. These two owners do not exercise the added
make providers; their outcomes verify only the stated scope.

| Owner | Original wall seconds | Candidate wall seconds |
| --- | ---: | ---: |
| list/list-test.ss | 0.892935 | 0.835915 |
| encoding/json/json-test.ss | 2.406984 | 2.210389 |

These one-wave focused test timings are not stable gains.

## Real Clean/Cold Build Gate

`run_d1510_progressive.py --build-ceiling 50 --cold-only` runs the retained
heavy real consumer with the separate candidate, recorded GNU driver and
configuration capture. Clean exits zero in 2.512337 seconds and leaves zero
project native images.

No first real compilation log appears within 5 seconds. The watcher observes
the deadline at 5.041631 seconds, returns DENY, kills the owned build process
group and reaps the parent at exit -9. Cleanup reports no errors. This value
is watcher detection latency, not a first-log time or complete-build duration.
Build attempt including cleanup is 5.049857 seconds; actual complete build
time is unknown because the task was stopped. No gate was widened.

Full testing is SKIP after cold DENY. Do not run further cold rounds, claim
50-second compliance, or promote the candidate because focused tests passed.
The three-object pilot also lacks release-wide provider coverage and multiple-VM
qualification. Existing native-reuse successes remain retained; this rejection
applies to this extension/composition, not every future distinct mechanism.

## Evidence

- `.data/d1510-provider-extension-host-v1/report.json`: SHA256
  `76b563f703da1395eb84f14f8f437304914034fc1015f79a317da5821ba92844`.
- `.data/d1510-provider-extension-stdlib-tests-v1/report.json`: SHA256
  `4e7c8553ee91d6107dab30759e8e04e48fd07673e64eac90c6bdcd24e23675cc`.
- `.data/d1510-provider-extension-cold-v1/report.json`: SHA256
  `e62fad1170702723e1484a1870519c9116fa53de38497bb710473495655fb26f`.
- Raw generated source/object files, command/import/test logs, cold configuration
  and `progressive-admission.json` remain beside the reports.

The progressive watcher/controller and retained loader regression tests report
43 passed. No new runtime patch, commit, GitHub push or full-suite qualification
is made from these outcomes.
