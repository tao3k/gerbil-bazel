# D1866: real single-cell no-copy coverage, not acceleration

The original D1510 carrier, 42 static objects and D1391 library home remain
selected. D1863 privately replaces only the RTS mem object with a counting
version and links a first-output hook. Original files remain hash-checked and
unchanged. GNU preprocessing confirms the counter guard is active; mem/counter
compilation, native linking and std/make/std/test/build-script imports pass.
This is observer construction, not collector performance qualification.

D1860's initial attempt fails at sandboxed sysctl environment discovery before
compilation. D1861 builds an exit-only counter; D1862 adds separate PID files
and existing output hooks. Neither is used as first-window coverage evidence.
D1863 explicitly freezes marker counters on the real first compile write;
exit totals have separate files and are not substituted for the first snapshot.
The three generator/parser tests pass after the snapshot changes.

## Actual Builder Snapshot

D1864 clones unchanged MCP head 9a5c35e275e5d6847ff421151bb224f2eae177c1,
performs successful official clean and verifies zero remaining native images.
The actual build child PID 37539 is verified against observer binary SHA256
`c148e63e2e8011dc50182c0a0dba60acdf9ba6622f35d8d9dff09e4a2b9d16f0`.
Physical concurrency is twelve. The unchanged ten-second genuine-output gate
passes. Literal first compile appears at 5.248306 seconds; the build then stops
deliberately with exit 70. This is a counter observation, not a speed result
or completed build, and does not restore the historical performance baseline.

D1865 admits only `marker.first.37539.json` after checking that PID, native
identity, successful clean, strict output gate and first-line stop. Counts:

| First-entry classification | Count |
| --- | ---: |
| All marker calls | 86,119,232 |
| Single-cell calls | 60,199,810 |
| Single-cell immediate values | 27,594,045 |
| Single-cell movable objects | 22,744,075 |
| Single-cell forwarded objects | 3,170,055 |
| Single-cell still objects | 356 |
| Single-cell permanent objects | 6,691,279 |

Immediate values plus all eight header-kind counts equal single-cell calls
exactly. Immediate/permanent/forwarded entries total 37,455,379, or 62.218434%
of single-cell calls. This closes the missing entry/class intersection; tail
visits are not counted as independent entry opportunities. It establishes
potential no-copy gate coverage, not eliminated CPU time or an expected ratio.

## Next Qualification

A Darwin/GNU-only caller-inline gate can now be evaluated for those actual
entries. It must retain the original forwarded-cell expression, argument
evaluation count, debug/multiprocessor fallback and original movable/still
collector paths. Native GC graph/continuation/weak-table contracts and a real
unobserved performance comparison are still required. No optimizer is yet
implemented or admitted. Collector-only changes are not presumed sufficient
for the complete startup objective.

Historical complete-build mean remains 52.617045 seconds and the mandatory
ceiling remains 55 seconds. Current historical performance restoration,
substantial first-log acceleration and complete concurrent test delivery remain
open. All owned build and observation processes are terminal; no product
source edit, commit or push occurs.

Private evidence: `.data/d1860-build-marker-entry-observer.py`,
`.data/d1863-marker-entry-frozen-observer/`, `.data/d1864-observe-marker-entry.py`,
`.data/d1864-marker-entry-prefix/`, `.data/d1865-validate-marker-prefix.py` and
`.data/d1865-marker-entry-prefix-admission/`.
