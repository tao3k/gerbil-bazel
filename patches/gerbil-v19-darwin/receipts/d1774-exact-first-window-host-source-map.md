# D1774: executable-identical first-window source attribution

The selected baseline remains D1513 B / D1510. This diagnostic only maps the
already retained D1769 sample of the rejected D1764 producer experiment; it
does not install that experiment, replace the baseline, repeat a performance
comparison, or explain the historical twenty-second difference.

D1773 compiles the same D1763 carrier with the same GNU GCC O1 recipe plus g1.
The original and debug object executable text is byte-identical and their
symbolic text relocation records match exactly. The original native binary
and carrier hashes match their retained native receipt. Compilation completes
in 61.405387 seconds; this is diagnostic construction, not product timing.

Original/debug text SHA256:
`27dfe4148674c6499804492cb02eb2c21ddeaf3d6e0f54ef2dcaa9da796e8a8c`.
Sampled binary SHA256:
`313769585f8cf57ea2d948c04938aad2d2792a90a1be958d5da1f28de4f07495`.
Carrier SHA256:
`e987f9c71dfba16f97124e4c5a0b9bdbfaf47e6aa70415e6415179538e8ae408`.

Twelve distinct nonaggregated host offsets have unique DWARF line mappings.
Offsets belong to the sampled binary, not to the original D1510 binary.
Selected carrier locations:

| Host offset | Carrier line | Actual operation |
| --- | --- | --- |
| 652568 | 349881 | Status check immediately after original native trace 11 |
| 523688 | 317604 | Status check after experimental producer helper 3 |
| 523520 | 317544 | Status check after experimental producer helper 0 |
| 523576 | 317564 | Status check after experimental producer helper 1 |
| 523632 | 317584 | Status check after experimental producer helper 2 |
| 604904 | 347109 | Current expander phi parameter fast path |
| 643304 | 347114 | Current expander context parameter fast path |
| 616000 | 351894 | Bounded reverse before syntax-quote construction |
| 682360 | 351948 | Current context parameter in quote-syntax |
| 502744 | 318631 | Bounded reverse before identifier-wrap construction |

The original native trace 11 continues to perform one checked context/table
lookup and export the parent continuation, not an unchecked cached answer.
Its caller status-check PC follows a native call in actual ARM64 code. Several
other mapped offsets likewise follow helper calls. Inclusive stack-node
counts at these return addresses must not be assigned to those caller
instructions or added to callee top-of-stack counts. Mapping establishes
source identity, not exclusive cycles, helper misses, dynamic call frequency
or a performance percentage. Aggregated comma-separated PCs are not silently
expanded into fabricated individual observations.

This evidence does not justify widening the four experimental producer trees
or paying for another native build of that small-allocation route. The
existing bounded reverse and parameter fast paths are already present in the
selected original carrier; rediscovering their call sites is not a new win.
Context/result reuse remains conditional on complete mutation/GC coherence,
as D1772 demonstrates. A further candidate must remove measured repeated
execution while preserving these existing guards and transfers; no new
candidate or complete-toolchain acceleration is admitted here.

Private evidence: `.data/d1773-first-window-host-map/report.json`, its twelve
lookup logs and `.data/d1769-outlined-producer-prefix/first-window.sample.txt`.
No live diagnostic process remains. The major startup/build/test goal is
still active and incomplete; the original <=55-second build gate is intact.
