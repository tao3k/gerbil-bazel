# D1740: selective whole-producer source lowering, not a speedup

Continue from the selected D1513 B / D1510 baseline. No baseline binary,
compiler, runtime, consumer or std/make/std/test file is changed, and no later
twenty-second discrepancy investigation is resumed.

The experimental Python GVM lowering helper now distinguishes normally retained
constructors from snapshot-only constructors. Its normal-return roots come from
the existing Program materializer, not a hand-selected projected result. Returned
objects and their dependency graphs keep their original constructors. Only owned
objects excluded by normal-return liveness can move into original poll exits.
The existing original full heap reservation remains mandatory. Unknown effects,
transfers, raw field reads, constructor mismatches and early snapshot guard reads
remain refusals. No production Gambit SCM/backend integration is implied.

D1739 applies this lowering to the actual whole syntax-e producer states on the
selected line. The unchanged bounded model completes 198 states; 122 ordinary
return states with original poll snapshots reach this check. All 122 lower to
source fragments that remove one three-word pair from the normal path, keep the
original poll exits and preserve byte-identical normal-return export strings.
This crosses D1661's earlier source boundary, where those same containers could
not simply be deleted because poll snapshots observed their addresses.

All 122 fragments remove only three heap words each. This is a static path count,
not executed frequency or allocated-byte savings. The bounded source model is
not exhaustive. No substantial startup benefit is established, and this narrow
producer alone is not promoted to a native candidate or performance patch.
Broader eligible allocation ownership must be established before a complete
native/toolchain build is justified.

Validation: 28 discarded-container, 10 fresh-escape and 23 trace-tree unit tests
pass. The initial test-edit placement error produced seven fixture errors and
was corrected without dropping tests. Native ABI, GC/continuation execution and
actual MCP build/test performance are not qualified by these unit tests.

Private evidence: `.data/d1739-selective-whole-producer.py`,
`.data/d1739-selective-whole-producer/report.json` and `lowering.json`.
Helper SHA256 at this source check:
`e96ad79323261eb9cefa70cd1dacec5b32e9c7e491204b39502cd872dffa22ba`.
The historical mean remains 52.617045 seconds and complete-build ceiling 55.
The first-log/build/test acceleration goal remains unachieved.
