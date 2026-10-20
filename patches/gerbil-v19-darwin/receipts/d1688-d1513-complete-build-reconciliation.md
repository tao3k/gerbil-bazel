# D1688: historical full-build reference is not currently reproduced

## Correct comparison

D1513 records four complete builds, not embedded-object completion times:

| Historical role | First compile seconds | Complete build seconds |
| --- | ---: | ---: |
| A, original baseline | 6.072760 | 53.918332 |
| B, D1510 candidate | 4.789153 | 51.737180 |
| B, D1510 candidate | 4.933479 | 53.496910 |
| A, original baseline | 5.710633 | 53.425696 |

All four builds exit zero after successful separate official clean. B mean
is 52.617045 seconds. The 55-second complete-build gate remains mandatory.

D1678 uses the exact historical **B binary as its new A control**, not the
historical A binary. That binary's SHA256 remains
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
The new control completes in 71.946552 and 74.649196 seconds. In particular,
the 51.737180-to-71.946552 difference is 20.209372 seconds. This is not a
successful reproduction of the historical complete-build performance.

## Retained artifacts, without another performance run

D1686/D1687 compare the retained D1513 first B clone and D1678 first A clone:

- Same exact binary, MCP head, all 266 Git-tracked source files and 12 workers.
- Same job counts: 549 compile-file, 189 compile-executable-object, one
  prepare-executable-link and one link-executable; 740 recorded jobs each.
- Job names are not a byte-identical multiset: one compile-file name differs.
  Equal counts alone do not prove the complete execution schedule is equal.
- Each clone retains 1,112 generated C/SCM files. All generated C hashes match
  after replacing only that clone's project path and explicitly recognized
  module timestamp literals. No arbitrary instruction or identifier masking.
- 229 generated SCM files still differ after that normalization. Inspected
  mark-deserialization lists show ordering differences; no blanket semantic
  equivalence is asserted for those remaining files.
- Current GSC and runtime archive hashes match D1510 construction. All 42
  original native C input hashes match that construction as well.
- Embedded generated C is 11,425,281 bytes in both clones. Three selected
  native objects have equal text lengths and identical text relocations, but
  text bytes differ; do not claim exact object identity. Timestamp constants
  do differ in their generated source.

The old full driver/environment snapshot and per-job timing are not available
from these reports. Current script contents must not be treated as the saved
historical configuration. These checks narrow the mismatch; they do not prove
its cause, equal complete environments, a resource explanation, or a new speed
ratio. No extra-build-work or candidate-caused-regression claim is admitted.

## Expansion boundary

D1675 deepens readonly discovery and adds one source-qualified trace. D1676
allows all unique-provider roots under unchanged trace execution budgets and
preserves the original 14 shapes, adding 12 more. D1677 builds and imports this
26-shape candidate using the original compiler/runtime inputs.

D1678's successful candidate row has first compile 5.302059 seconds and
complete build 74.584774 seconds; the other candidate row fails the original
ten-second output gate before its first compile. The ABBA batch is not
performance-qualified. D1683 passes 72 actual module-context binding, identity
and live-GC cases across twelve original/expanded native processes. Initial
D1679 failed because the private fixture used an illegal top-level declare;
that fixture error is retained, not called a product regression.

D1680 constructs a separate 26-site counter observer and passes fragmented
write controls. D1681 verifies the actual builder PID but fails the original
ten-second gate. It has no frozen first-write snapshot. Its truncated child's
exit counters show zero successful hits at the twelve added sites; these are
not complete first-window counts. D1682's parser explicitly refuses this
failed observation rather than using exit counters as first-write evidence.

D1684 passes twelve native starts and twelve framework imports but its actual
std/make phase fails the original five-second genuine-output gate. No overall
std/make/std/test success, startup solution or frozen performance patch follows.

Keep D1513's 52.617045-second historical reference and the 55-second gate.
Neither the later slow control nor the unsuccessful expanded candidate replaces
that reference. The main Darwin startup/build/test goal remains open.

Private evidence: `.data/d1513-current-outline-full/`,
`.data/d1678-outline-discovery-real-mcp-abba/`,
`.data/d1681-outline-first-census/`, `.data/d1683-outline-discovery-contract/`,
`.data/d1684-outline-discovery-concurrent-make/`,
`.data/d1686-d1513-input-reconciliation/` and
`.data/d1687-d1513-timestamp-and-native-reconciliation/`.
