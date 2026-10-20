# D1510 Original GNU Source Map

## Correction: Existing Evidence Takes Precedence

The later audit finds that this mapping repeats the exact-code standard-library
analysis already recorded in `d1510-host-exit-branch-boundary.md`, which also
points to D1612's much wider actual MCP first-window map. The new sidecar is
not a newly discovered hotspot or evidence beyond those earlier mappings.
The redundant per-PC subprocess mapping implementation and CLI options have
been removed; reuse the established `native_dwarf_lines` implementation and
existing qualified exports instead. Private duplicate artifacts remain for
audit, not another profiling campaign or performance claim.

No new performance patch is admitted. The historical anchor remains first
compile 4.850866 / 4.573628 / 4.592897 seconds, complete cold build
47.771713 / 47.824226 / 47.927094 seconds and complete tests 105.750982
seconds, 39 files / 965 cases passed. Current gates remain 5 / 50 / 112.
This diagnostic does not run another cold build or complete test wave.

## Existing Parameter Coverage

The frozen carrier already contains three-slot parameter lookup, guarded
environment-tree lookup, default-value lookup and identity-getter return.
Do not treat environment misses or identity getters as a newly missing
optimization. Existing D1038 evidence records 16,159,871 shortcuts, including
2,128,423 environment-tree hits and 75,715 defaults. Those diagnostic counts
are not an exclusive CPU budget or a new performance result. No cache,
VM guard, thread policy or parameter representation is changed here.

## Actual Debug Sidecar

The unified compiler-frame workflow compiles the unchanged original carrier
with the original GNU GCC driver plus opt-in `-g1` debug information.
The original source, reference object and driver hashes remain unchanged.
Compilation exits zero; the sidecar never replaces the frozen runtime.

The native object text is byte-identical: 1,126,540 bytes, SHA256
`b8c7a61e5e7243590c2c4790426322f860418ec6df99bff01a1f315080652848`.
Raw relocation bytes differ, so the initial strict raw comparison rejects
the sidecar. That failed receipt is retained. Subsequent structured Mach-O
analysis resolves external symbol indices into names, section identities,
symbol kinds/descriptors and section-relative values; local relocations
retain section identity, and ARM64 addends retain their encoded value.
Relocation address, kind, PC relativity and width remain part of comparison.
All 79,635 semantic relocations match. Canonical relocation SHA256:
`7480e7d483bd7f487fb741be28543e296f1f080a18e86ecbbdbba79a2c3252e6`.
Tests distinguish harmless symbol-index renumbering from actual target
substitution, text changes, relocation changes and truncated object data.
This is source-attribution evidence, not whole-executable equivalence or a
runtime optimization. Different debug sections are expected.

## Native PC Lookup

The existing completed standard-library CPU-counter/time-sample recording
is reused without rerunning its workload. Frozen binary SHA/UUID and precise
sample buckets remain checked. An initial native-site export is empty due
to an export condition error; it is retained and not used. The corrected
export preserves the original 513 matched running samples and all existing
leaf statistics while exposing validated native PCs.

Mapping uses the exact common-host symbol in both reference/debug objects,
the actual frozen function start and DWARF line lookup. Linked and object
common-host extents match at 1,059,016 bytes. All 71 distinct common-host PCs
map to original C source lines, totaling 81 one-millisecond sample weights.
This does not assign nearby GVM labels as PC owners or infer exclusive Scheme
procedure, instruction-cycle, allocation or removable wall-time costs.

Two mapped source locations are VM boundaries: carrier line 156590
(`___END_M_HLBL`, entry state/PC preparation) has three sites with nine sample
weights; line 381240 (`___END_M_SW`, dispatch/exit boundary) has three sites
with six weights. Another is line 276245 inside `gx#stx-e`, with two weights.
The remaining sites are dispersed. These sparse old standard-library samples
do not establish dominant current MCP startup cost, authorize another
host-splitting/dispatch candidate or reopen any denied route. They enable
source-grounded inspection instead of treating the large host as a black box.

## Evidence And Verification

Private artifacts remain beneath:

- `.data/d1510-original-gnu-debug-sidecar-v1/`: actual GNU object, original
  failed raw-identity receipt and corrected native-site export.
- `.data/d1510-original-gnu-source-map-v2/report.json`: source/object/image
  identities, actual extent and all 71 mapped sites.
- `.data/d1510-stdlib-counter-profile-v1/`: unchanged original recording and
  retained empty first native-site export.

Forty-seven focused compiler/resource/counter/framework checks pass. No AOT,
CI, Linux behavior, consumer source, installed binary or performance ceiling
is modified. No fresh first-log/full-build/full-test pass, speedup or GitHub
publication is claimed.
