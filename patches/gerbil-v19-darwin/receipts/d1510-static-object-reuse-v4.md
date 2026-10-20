# Native Digest Static Reuse v4

## Admission Review

- Direction: reduce new digest costs within the demonstrated generic object
  reuse path. No package-name checks or package-specific product behavior.
- Prior evidence: v3 achieved 71 real ASCENT hits but 43.40 seconds did not
  beat the 43.08-second control. Repeating unchanged v3 was denied.
- Worth investigating: each eligible object rereads complete tool content
  across preprocessing and hit/compile admission. The native SHA component
  preserved exact digest output while reducing its measured cost.
- Expected benefit: lower verification cost without weakening content checks;
  true-cold acceleration is not assumed.

## Implemented Candidate

0021-gambit-darwin-native-static-reuse-digests.patch applies after 0020 on
Darwin/GNU only. It adds the public CommonCrypto SHA-256 file backend and
source/build/install wiring, binds the backend executable into tool snapshots,
and leaves all source/options/tool/object checks intact. Explicit non-Darwin
opt-in takes the original compiler command before touching a cache lock or proof.
The patch is experimental, default-off and not in the production release list.

The isolated composition fixture applied 0014, 0015, 0019, 0020 and 0021.
Its helper matches the exact tested v4 helper byte-for-byte. Its native C source
matches the tested source. The existing retained config.status generated its
makefile, and the new make target successfully built with the configured GNU
compiler/flags. That binary returns the canonical SHA-256 of abc. It is a
separate build from the earlier component-test binary, not a claimed identical
Mach-O executable.

## Actual Consumer Results

| MCP Metric | v4 | Frozen Gate |
| --- | --- | --- |
| First compile | 4.049 / 4.044 / 4.004 s | 5 s |
| Complete cold build | 37.365 / 37.406 / 36.467 s | 50 s |
| Complete tests | 87.409 s, 39/39 files, 965/965 cases | 112 s |

MCP tests use the first cold-built artifact, selected-toolchain fixture, and
whole-task gates. Test first output: 1.663563 seconds. All final OK markers,
inventories, exit codes and gates pass. The other two cold artifacts have
build/source gates, not independent complete test runs. The frozen runtime
binary remains unchanged. All three cold logs have zero object-reuse events;
do not attribute their wall-clock improvement over history to this cache.
Raw receipt: .data/d1510-static-reuse-mcp-v4, including tests/report.json.

| ASCENT Scenario | Whole Time | User CPU | Cases | Real Object Events |
| --- | --- | --- | --- | --- |
| Original command, entry miss | 43.08 s | 81.36 s | 30/30 | no reuse |
| v3 repeated entry miss | 43.40 s | 98.47 s | 30/30 | 71 hits / 1 miss |
| v4 proof population | 47.25 s | 98.13 s | 30/30 | 72 misses |
| v4 repeated entry miss | 38.42 s | 51.17 s | 30/30 | 71 hits / 1 miss |

Every admitted ASCENT scenario exits zero, contains final OK and has 74 GSC
object invocations. Entry receipts were deliberately removed in the isolated
workspace; each log confirms an entry-cache MISS. This is real static-object
reuse, not skipping the Cases or relying on an existing test executable.
v4 reduces this observed complete repeated-entry scenario by 10.8% versus
control, and user CPU by 37.1%. These are single scenario observations, not
repeated statistical or complete from-zero ASCENT qualification. Population
remains 9.7% slower than the original-command control and must not be hidden.
Native qualification remains direct just/Scheme, with original heap/deadlines.
The source libraries remain warm in all compared entry scenarios.
Raw summary: .data/d1510-static-reuse-ascent-native-v4-summary.json.

## Native Safety Controls

- Eight original byte-parity/options/header/tamper/concurrency/failure contracts.
- Six proof target, diagnostic parity and mid-flight source/compiler controls.
- Five expanded tool/platform controls: changed private real GNU GCC executable,
  changed actual assembler entry, changed digest executable, unavailable digest
  executable, and mocked non-Darwin original-command fallback.
- Native digest component: exact shasum parity for empty/binary/escaped names
  and tool files; missing/directory/read errors reject; GNU warning-clean build.
- Focused framework tests: 42 passed.

The first real-GCC mutation attempt could not write the copied executable
because its installed read-only mode was preserved. Only the fresh isolated
compiler copy was made owner-writable for the complete control; the installed
compiler was never changed. GCC_EXEC_PREFIX selects its original cc1 after
relocation. Appending private non-executed bytes changes the real GCC file
digest and forces a MISS, with identical correct object output. The assembler
entry test verifies actual GNU compiler calls via its invocation log; a cache
HIT makes no new assembler call. Missing digest tooling leaves object/proof intact.
The mocked platform control does not substitute for native Linux CI.

Post-run checks verified all 1,992 shared toolchain and 2,809 dependency dynamic
image digests. The original consumer's relevant tracked files remain unchanged.
Only independent static outputs and owned candidate files were modified.

## Remaining Scope

The isolated ASCENT package-cold pair passes correctness but regresses from
98.66 to 101.90 seconds; general cold/default-enabled performance admission is
denied. See d1510-ascent-static-reuse-package-cold.md. The full toolchain/consumer
invalidation/failure/concurrency scenario set is not finished. The isolated
launcher now aligns the upper entry-cache gcc
lookup with the actual selected GNU compiler. A real unchanged-entry case
passes; actual upper-cache tool-upgrade invalidation is not yet qualified.
Repeated integrated ASCENT performance and a full source-toolchain rebuild
remain open. No default enablement, GitHub delivery or goal completion is claimed.

## Follow-Up Native Qualification

Before compiler alias alignment, an independent forced entry-miss repetition
completed in 40.67 seconds (user CPU 51.43 seconds), with 30/30 Cases, final OK,
exit zero, 74 GSC object invocations and 71 hits / 1 miss. The previous repetition
was 38.42 seconds. Both beat the recorded 43.08-second control, but no repeated
matched control or statistical claim is made.

The isolated launcher creates a gcc symlink only inside its owned toolchain bin,
pointing to the selected GNU compiler. An existing nonmatching entry is rejected.
This aligns the consumer's which-gcc entry proof with GERBIL_GCC; no product
source, global executable or active ASCENT checkout is changed. The dependency
bin directory is empty, so the consumer's additional PATH prefix cannot shadow
this entry in the observed runs.

| Aligned Native Scenario | Whole Time | User CPU | Cases | GSC Objects | Cache |
| --- | --- | --- | --- | --- | --- |
| Changed compiler entry identity | 38.62 s | 51.65 s | 30/30 | 74 | entry MISS; 71 object hits / 1 miss |
| Subsequent unchanged entry | 7.65 s | 6.47 s | 30/30 | 0 | entry HIT |

The first run invalidates the older proof that recorded the system gcc lookup.
The second run retains the new receipt, does no compilation, and still executes
every Case with final OK and exit zero. The 7.65-second result is existing upper
entry-cache reuse, not a new static-object or cold-build speedup. Actual changed
compiler contents and upper-cache failure/concurrency remain separate checks.

Raw runs: .data/d1510-static-reuse-ascent-readonly-v4-hit-v2,
.data/d1510-static-reuse-ascent-readonly-v4-aligned-v1 and
.data/d1510-static-reuse-ascent-readonly-v4-unchanged-v1. Offline summaries:
.data/d1510-static-reuse-ascent-native-v4-repeat-summary.json and
.data/d1510-static-reuse-ascent-native-v4-entry-summary.json. Both summaries bind
raw output SHA-256 values. The post-run dynamic reference verification passed
1,992 toolchain and 2,809 dependency images. An initial dependency verification
used the wrong root (prefix rather than its parent); the recorded relative paths
start with prefix/, and the correctly rooted verification passed without repairs.
