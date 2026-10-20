# Three Independent Time Gates

The current policy has three separate ceilings:

| Metric | Ceiling |
| --- | ---: |
| First real workload log | 5 s |
| Each complete cold build, three required | 50 s |
| Complete real test wave | 52 s |

A candidate's timings must never be mixed with another candidate. Full test
correctness is an additional requirement, not another timing ceiling. A wave
that stops test processes can meet its wall-time ceiling without providing a
successful complete-test duration. Existing five-second real-output-gap
watchdogs remain active; no assertion or progress gate is removed.

## Corrected Previous Results

| Candidate | First compile seconds | Complete cold seconds | Test wave |
| --- | --- | --- | --- |
| Whitespace reader v2 | 4.851 / 4.574 / 4.593 | 47.772 / 47.824 / 47.927 | 49.983 s, 22/39 files passed |
| Frozen host + private FD archive v1 | 4.792 | No completed build | SKIP |

The whitespace candidate passes all three cold repeats and both cold timing
gates. Its test-wave duration is below 52 seconds, but complete correctness is
not qualified. Preserve the cold result; do not report it as a build failure.

The **other** private-archive candidate is interrupted at 50.013553334 seconds.
That number is the watchdog's observed deadline violation, not a completed
build duration. The additional 0.014 seconds is polling/detection granularity,
not an admitted extension of the 50-second ceiling. This result does not
invalidate or override the whitespace candidate's three successful builds.

`summarize_three_time_gates.py` validates binary identity, emits per-round times,
and separates test duration from correctness. Its tests cover a 51-second test
passing while a 51-second build fails, mixed-candidate rejection, interrupted
builds, incomplete repeat campaigns, invalid times, and failed test waves that
still meet the duration gate. `run_selected_mcp_wave.py` now emits both test
gate fields and uses a 52-second test target and five-second first-output limit.
Historical raw reports are not rewritten.

## Next Composition

The next isolated candidate combines the whitespace reader with the C-only
fork FD cleanup object. This extends the three-cold-pass reader configuration
and targets host test subprocess work. It does not retry the private consumer
archive route: original HOME, original archive, source identities and compiler
flags remain selected. Its carrier remains the retained original program.
The whitespace runtime linker object is retained exactly so added Scheme
globals remain correctly linked.

Before real cold testing, the combination passes all 45 reader controls and
matches frozen process-control output/status for explicit environment,
ENOEXEC, changed child PATH and missing command. Construction and control
qualification do not substitute for the new three-round 5/50 campaign and
52-second complete test gate.

Private evidence:

- `.data/d1510-three-time-gates/`
- `.data/d1510-reader-whitespace-fd-runtime-v1/report.json`
- `.data/d1510-reader-whitespace-fd-native-v1/report.json`
- `.data/d1510-reader-whitespace-fd-controls-v1/report.json`
- `.data/d1510-reader-whitespace-fd-process-controls-v1/report.json`
- `.data/d1510-reader-whitespace-fd-progressive-v1/`

The externally repaired repository-provider issue is not reopened here.

## Composition Result: Separate DENY

Candidate binary SHA256:
`a15b848398e81101c0e2294e7c9789c710b530102ec3299ea9f1dad0906e0e9e`.

The first clean exits zero with zero native images. The new combination has
no first compile log when the watchdog observes 5.028988667 seconds; it is
killed and reaped with exit -9. Sources remain unchanged. There is no completed
cold-build time, no later cold round and no complete-test wave for this binary.
Do not report 5.029 seconds as a measured first log: the log never arrived.

This result is DENY for the composition only. It does not override the original
whitespace candidate's three cold passes. The combination is not promoted and
this composition route is not retuned or rerun. The FD discovery remains a
separate component result, not a qualified build/test optimization.

The updated gate/reader/FD checks pass: 47 Python tests. Original raw evidence
remains unchanged; the corrected three-gate summaries are separate artifacts.
