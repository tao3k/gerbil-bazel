# D1738: pair snapshot support, no admitted performance candidate

The selected baseline remains D1513 B / D1510, verified by D1734. No historical
twenty-second discrepancy investigation or new timing workload is performed.

The experimental Gambit lowering helper now supports discarded pair/structure
graphs with materialization at original poll exits. Original constructor fields,
dependency order and shared references are preserved. Original full heap
reservation, effect-free completion and projected-caller ABI proof remain
required. Poll guards may not read an object before materialization. Visible
normal-path references, escaping results, cyclic/forward dependencies, unknown
constructors and missing fields are refused. Pair support is explicit opt-in;
the existing structure-only and projected modes retain their default behavior.

Validation: 23 discarded-container, 10 fresh-escape and 23 trace-tree unit tests
pass. These are lowering tests, not native Scheme or performance qualification.

D1737 uses the actual original generated core/stx/util inputs from the selected
line. Both lowerings receive the identical Program and State for each comparison.
Four current consumers yield 512 bounded states: old accepted 512, new accepted
512, additional accepted 0, lost accepted 0. Each consumer reaches the configured
128-state cap; this is not exhaustive source coverage. The final comparison locks
the changed helper SHA256. D1736's preceding result is retained separately.

Decision: these four consumers do not establish expanded optimization coverage.
Do not rebuild their existing native candidate or promote pair snapshots as an
acceleration. Find genuinely newly eligible source paths before paying for a
native carrier and real MCP/std/make/std/test performance run. No layout/ABI,
Gerbil, consumer, Linux or selected baseline binary changes are made.

Private evidence: `.data/d1736-pair-snapshot-real-source.py`,
`.data/d1737-pair-snapshot-real-source/report.json` and `comparison.json`.
The complete-build mean reference remains 52.617045 seconds and ceiling 55.
The requested first-log/build/test optimization remains unachieved.
