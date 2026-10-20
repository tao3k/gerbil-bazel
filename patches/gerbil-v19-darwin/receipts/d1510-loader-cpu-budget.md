# D1510 Loader CPU Budget

Observation only. Preserve the frozen reader-whitespace host, historical
47.771713 / 47.824226 / 47.927094-second cold builds and current whole-task
5 / 50 / 112-second gates. No optimization, full-test pass or publication
is admitted. This follows `d1510-stdlib-process-budget.md`, not a new Linux
comparison or consumer-specific experiment.

## Actual Native Boundaries

The private GNU-linked observer samples `getrusage(RUSAGE_SELF)` around the
original content digest, dlopen, dynamic setup_modules and linker conversion
calls. Original arguments, return values, content/path checks, callbacks and
error/fallback paths remain unchanged. No symbol hash filter, cache, native
image substitution rule or omitted assertion is introduced.

Each CPU observation records process user/system microseconds and minor/major
fault deltas. Samples include observation overhead and any concurrent work
in the same process; these are not exclusive thread hardware counters.
Microsecond resolution and first-touch effects limit small intervals. The
original wall observer remains separate, with matching completed-call counts.
GC and native setup intervals may overlap: do not sum them as disjoint costs.

After the original fixture load, a diagnostic environment marker enables
count reset at the first target provider call. This excludes earlier native
boot/fixture loading, while retaining original standard-library import/eval
execution. It does not measure work before that provider call. Report paths
are copied before the marker mutation; exit-time environment lookup is not
used for this mode's output paths. The observer does not change Gambit's
environment-variable implementation or claim to fix it.

V1 captures process-lifetime native calls: its native counters are not aligned
with root Scheme phase statistics and must not be directly subtracted from
them. V2 runs the first control/probe pair but fails to emit the required
loader receipt after the environment mutation; it is unqualified. V3 copies
report paths early and completes all three alternating control/probe rounds
for make, test, encoding/json and list/list. Both earlier directories remain.

## JSON Results

System CPU milliseconds in the V3 observation:

| Boundary | Round 0 | Round 1 | Round 2 |
| --- | ---: | ---: | ---: |
| Original digest | 9.496 | 14.700 | 9.125 |
| Original dlopen fallback | 3.983 | 5.148 | 3.533 |
| Gambit dynamic module setup | 28.710 | 17.082 | 12.638 |
| Linker conversion | 2.658 | 1.753 | 1.253 |
| Whole four Scheme phases | 142.848 | 224.773 | 126.886 |

Each target observation has 219 provider/setup/linker calls, 196 digest calls
and 23 dlopen calls. Startup excluded by the reset accounts for 35 additional
native calls seen in V1. The four observed boundary system-CPU totals are
44.847 / 38.683 / 26.549 milliseconds. Most phase system CPU is not explained
by these four intervals. Provider table search is outside these CPU samples;
its earlier wall observations are not CPU coverage measurements.

The root phases report 1,895 major faults in each JSON observation. Native
setup reports 1,783 and linker conversion 112, with digest and dlopen at zero.
Their sums match these phase fault counters after the reset. This localizes
reported faults in the observation; it does not establish physical disk reads,
fault latency, removable relocation work or equivalence on a different binary
layout. Do not mistake Gambit registration for dyld fixups or a fault count
for seconds of startup cost.

Digest user CPU is 22.481-24.069 milliseconds; setup user CPU is
54.436-65.908 milliseconds. CPU and wall intervals differ substantially in
some runs. No wall acceleration or scheduling cause follows from this data.
The CommonCrypto digest implementation is already present; neither removing
its identity check nor switching to that same library is an eligible win.

## Correctness And Decision

All 24 imports complete with final OK, cached-context identity, matching
original export/native-module inventories and unchanged frozen objects/source.
Parser/instrumentation regression tests: 39 passed.

Four concurrent original list/JSON test processes use the selected hardware
worker count. Control and probe each pass 32 list plus 33 JSON cases, final OK,
exit zero and identical case identities. Source and selected binary identities
are unchanged. Control list/JSON walls are 1.236750 / 2.120875 seconds; probe
walls are 2.574137 / 3.236460 seconds. This is a slower diagnostic, not an
optimization or full-suite result. All owned child processes are terminal.

The next target remains the substantial non-GC execution and system CPU
outside these native-loader intervals. A new I/O or allocation mechanism
needs reached operation coverage and a distinct semantic contract. No digest,
dlopen, relative-label, GOT or marker micro-tuning candidate follows from
these observations; the existing rejection records still apply.

Evidence: `.data/d1510-loader-cpu-budget-v3/report.json`, SHA256
`247aba7fe5395401eb82c65d4a2cb586be8829b9aaee4ce76e50a49e45fbfc1f`;
diagnostic binary SHA256
`3d6d34f346c8b25671580467983dff46068ea0a932834b86ff7dba54ef104042`.
Original tests: `.data/d1510-loader-cpu-stdlib-controls-v1/report.json`, SHA256
`8de672477b88e801d4353490b305c40ba41ceefd2fcc65dc59d6f7abdd441333`.
No cold build or full-test wave is rerun without a production candidate.
