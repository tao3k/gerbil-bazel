# ASCENT PR 1 Latest Revision Measurement

Accepted by the user as a stage measurement. This acceptance does not relabel
the semantic timeout as a passing full test or change the frozen MCP baseline.

## Identity and Scope

This round fetched and detached the isolated consumer to ASCENT PR 1 HEAD
`86ad9ae3469565bea6229b71ef1d9197c6a82d63`, verified through GitHub immediately
before execution. It is the revision measured here, not a claim about future
moving PR heads. The consumer's tracked source remained clean after all targets.

Workspace: `.data/d1510-ascent-pr1-latest-v1`. Commands and raw transcripts are
under `results/<target>/`. `run-upstream.sh` invokes unchanged upstream Just
targets directly; it does not discover, shard or schedule Gerbil tests.

Toolchain: `.data/d1510-static-c-snapshot-ascent-v1/toolchain`, Multiple VMs,
GNU GCC 16, existing static object reuse enabled. No retained-entry overlay or
later closed-link candidate was enabled. Hardware capacity and build setting
were 12 cores, confirmed by `BUILD-TEST-LIBRARY modules=336 cores=12`.
Selected executable digests and commands are captured separately per target.

The private writable dependency prefix was APFS-cloned with symlinks preserved.
Its 2809 read-only dynamic references passed verification after execution.
Declared dependency source identities were checked before execution:

- POO Flow Core: `e85fd45303b208b23e5957fd316e7004994109a4`.
- ASP v0.1.2.2 peeled commit: `f5b7c009d2cab61144a8af18008a0bfba3056584`.
- Gerbil POO: `099b381588360a8a49fd772f666a1a00351366f5`.

## Actual Results

| Target | Wall seconds | Verdict |
| --- | ---: | --- |
| `just build` | 44.18 | Exit 0; 86 production module compilation markers |
| First production compilation log | 15.085507 | Slow; no startup improvement admitted |
| `just prepare-test-library` | 126.41 | Exit 0; 250 additional module compilation markers |
| `just test-compiled` | 137.13 | DENY: upstream GxTest 120-second timeout, recipe exit 124 |
| `just test-performance-contracts` | 83.25 | Exit 0; 7/7 modules, 10/10 Cases, HARNESS-OK and final OK |

Times include each target's upstream prerequisites and environment selection.
The semantic and performance targets each recheck library currentness; these
costs were not subtracted from reported wall time. The semantic timeout target
was not a completed full test run: zero MODULE-OK/CASE-OK markers were produced.
No complete semantic-test duration can therefore be reported as a passing score.
No repeated-cold-build stability claim is made from this single build.

Initial library preparation phases:

- Inventory before: 0.122440 seconds.
- Upstream make: 123.041059 seconds.
- Inventory after: 0.144557 seconds.
- Production modules rebuilt: zero.

Semantic-target currentness recheck: 11.616248 seconds in make; performance-target
recheck: 11.508788 seconds. Neither recompiled production modules.

## Failure Evidence and Admission

A one-second live sample of the semantic GxTest process recorded 885/887 main
thread samples under Gambit `___dynamic_load` / dyld `dlopen`; 868/887 were under
Mach-O `mapSegments` / `fcntl`. Only three ASCENT qualification dynamic images
appeared in that sample. This local sample identifies a blocked loading stage;
it does not prove the duration or cause of all loading, a Scheme macro bottleneck,
or a general compiler defect. Raw evidence: `results/test-compiled/wait-sample.txt`.

An earlier receipt, `d1510-static-reuse-identity-controls.md`, already recorded
the same stack family in a rejected copied-image profile. This round preserved
dependency image symlinks and compiled the consumer images from the latest
source; nevertheless this loading boundary is still not admitted. Do not rerun
unchanged full semantic attempts, increase the timeout, or promote these scores
as full consumer qualification without resolving that boundary.

The historical 434-second run used consumer commit `21e3638` and a different
per-Suite native coordinator. It is not a latest-PR result and is not a matched
control for the 44.18-second production-only build or the 83.25-second performance
group. This receipt supersedes its use as current ASCENT performance evidence.

The frozen MCP lock was independently reverified, without a new MCP benchmark:
first logs 4.038430/3.980393/3.950160 seconds; cold builds
36.414237/35.551924/37.770491 seconds; full test 86.924285 seconds,
39 files and 965 passing Cases. Its 4.5/42/97-second gates are unchanged.
