# Frozen Six-Patch ASCENT Source Invalidation

## Admission Review

The preceding goal turn made progress through actual Multiple-VM backend
contracts. Review of 0032 confirms its cold branch executed zero times in real
MCP; the unchanged configuration is denied, not rerun. No cold-snapshot
implementation is added here.

The historical 70-HIT/2-MISS source-change control used the five-patch helper.
The six-patch helper's 30 Cases and upper entry-cache HIT did not prove the same
backend behavior. Worth qualifying: keep the exact helper/ABI/options and change
only a Scheme comment, requiring a fresh native entry and actual object HITs.
Expected whole-time benefit was unknown, not a promised speedup.

## Actual Native Results

The consumer's own `just test-native t/qualification/ascent-positive-plan-test.ss`
owns compilation and Cases, launched directly by the existing Bash runner.
Hardware-derived build cores remain 12, heap protection is 1 GiB, and the
component whole-task deadline stays 135 seconds. No Python native supervision.

| Condition | Whole time | User / system CPU | Object events | Correctness |
| --- | ---: | ---: | --- | --- |
| First comment variant | 71.32 s | 114.33 / 35.87 s | 0 HIT / 72 MISS | 30/30, final OK, exit 0 |
| Second comment variant | 70.03 s | 74.23 / 32.80 s | 70 HIT / 2 MISS | 30/30, final OK, exit 0 |

Both runs have entry MISS, 73 actual GSC object calls and no generated-C cache
HIT markers. Assertions remain unchanged, including all 512 directed three-node
graphs, independent reachability, ordering, budgets and concurrent-engine cases.
This is not a complete 94-Suite run or a package-cold sample.

The first run repopulates every proof and fails backend reuse admission. The
second passes 70 required HITs, exact 72-event cardinality, entry MISS/no entry
HIT, enough object calls, all Cases and final exit admission. Why the older
proofs missed in run 1 is unproven without component fingerprints; no source or
environment cause is inferred from MISS counts alone.

User CPU falls by 40.10 seconds, but whole time changes by only 1.29 seconds.
Distinct source variants, population and warming prohibit a causal speedup
claim from this pair. Actual reuse is proven; a new end-to-end acceleration is
**not**. Remaining time is not causally allocated without phase instrumentation.

## Identity and Isolation

Owned workspace: `.data/d1510-static-c-snapshot-ascent-v1`, consumer HEAD
`21e3638687d42ecfc36acebb28991987435ebc60`. Only one comment changes between
variants. Both diffs are bound before/after native execution, then removed by
the exact inverse edit. The isolated tracked checkout is clean afterward.
No active consumer, original toolchain or shared dependency is edited.

Raw roots: `.data/d1510-frozen-ascent-source-change-v1` and `v2` (same prefix).

| Artifact | SHA-256 |
| --- | --- |
| Variant 1 diff | `d8bff8c427528b2df78a60de8692a83ad5d3cc468778bdf07bb3f99670f401d8` |
| Variant 2 diff | `663ef18fe87e49702fc220d80caab29f0fd998de000a52c9c115055ea39e1dd9` |
| Either toolchain log | `b7a29d7f00a240ba745db125970da7b58bf994a18e9743fab265979bf7506542` |
| Variant 1 native output | `335862598b7cc5ba2429b64c5e93147cf732b24adb9748cb689ad78d1520cdd6` |
| Variant 2 native output | `1025679bef3cc1d38ce8baedbe5f687b3fb4c1b3e929d73997dbae9616c06370` |

Post-run verification passes all 1,992 toolchain and 2,809 dependency read-only
dynamic image references; logs remain under the second receipt. No patch enters
the frozen series. Personal absolute paths remain in local raw evidence only.

## Framework Qualification

The existing offline `experiment_framework/native_receipt.py` optionally requires
exact backend event count, minimum actual HITs, enough object calls, complete
correctness and entry MISS/no HIT. Existing CLI behavior stays unchanged unless
explicit reuse arguments are provided. A failed policy writes the negative
receipt and exits 2. This is event admission, not a deduplicated Suite inventory.

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/native_receipt.py \
  --run .data/d1510-frozen-ascent-source-change-v2 --expected-cases 30 \
  --reuse-events 72 --minimum-object-hits 70 --output FRESH_SUMMARY.json
```

39 focused offline receipt/reuse-policy/frozen checks pass, including incomplete
correctness, entry HIT, zero/insufficient HITs, missing/extra events and too few
object calls. These are not 39 Scheme Suites.

## Remaining Gates

Retained MCP numbers remain first 3.950-4.038 s; cold builds
36.414237 / 35.551924 / 37.770491 s; complete tests 86.924285 s,
39 files / 965 Cases. Per-sample ceilings remain 4.5 / 42 / 97 s. No new MCP
timing is measured here.

Next separate native entry preparation, GSC link generation, object validation
and final linking under the now-qualified source-change condition. Existing
compiler jobs expose these boundaries, but the completed runs cannot supply
retroactive monotonic phase timings. Do not retry the denied coordinator or
all-producer capture unchanged. Full six-patch ASCENT correctness/performance,
general release and goal completion remain open.
