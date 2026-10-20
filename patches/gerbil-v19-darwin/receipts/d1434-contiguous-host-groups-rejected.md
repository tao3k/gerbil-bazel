# D1434: contiguous host groups regress the actual MCP first log

## Scope

Gerbil v0.19-staging remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`;
Gambit remains `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
The common baseline is D1391 with the existing object-reuse candidate retained.
Only isolated generated C copies of expander core and stx change. Genuine GNU
GCC 16, original O1, original headers, GSC, library home and consumer sources
remain unchanged. Physical concurrency is 12, not a fixed two-worker setting.

This implements a private prototype of the intermediate host arrangement
described in D880/D888. It is not the rejected D912 per-procedure-host mode,
nor a new SCM emitter patch. Production patches and manifests are unchanged.

## Ownership Contract

- Procedures remain in original contiguous public-label order.
- Groups target 256 label rows, including introduction rows; an indivisible
  larger procedure occupies its own group rather than being split incorrectly.
- Module-wide register/resource declarations are conservatively retained for
  each host. This is not a per-group resource-union optimization.
- Each group receives its own host-label array and original first label origin.
- Procedure/return label metadata changes host ownership only; public indices,
  frame metadata, module descriptor and initialization remain unchanged.
- Same-group internal calls retain direct gotos. Cross-group internal calls
  set the original argument count and use the existing host-transfer machinery.
- The changed branch requires Darwin, genuine GNU GCC, single-host mode and
  label values. The inactive branch retains original generated code.

Core has 163 procedures in six groups with row counts
`609, 231, 231, 250, 253, 254`; 65 static internal jumps stay local and 78 cross
groups. Stx has 80 procedures in three groups with counts `254, 255, 73`;
29 static internal jumps stay local and 53 cross groups. These are static site
counts, not measured dynamic transfers or CPU attribution.

## Executed Gates And Results

D1430 catches an introduced outer preprocessor-boundary error. D1431 catches
an incomplete internal-jump parser before compiling core. Both failed receipts
remain retained. D1432 fixes those prototype errors without weakening checks;
both units compile, the isolated binary links, and original std/make, std/test
and std/build-script imports return `IMPORT-OK`, exit zero. Original generated
inputs remain byte-identical. Import success alone does not qualify all Scheme
semantics or a full toolchain.

D1433 runs fresh independent official MCP clean/build fixtures in ABBA order:

| Role | Actual first `... compile util/compat`, seconds |
| --- | ---: |
| Baseline | 6.071805 |
| Group candidate | 8.091421 |
| Group candidate | 7.392711 |
| Baseline | 6.265091 |

Means are 6.168448 versus 7.742066 seconds: the candidate is about 25.51%
slower, not an acceleration. Each clean exits zero with zero native `.o1`
images afterward. The unchanged ten-second real-output gate passes. Each build
is deliberately stopped after the first genuine compile line, terminal exit
70; no completed build, test suite, or final executable claim follows.

Evidence: `.data/d1430-bounded-host-runtime/report.json`,
`.data/d1431-bounded-host-runtime-fixed/report.json`,
`.data/d1432-bounded-host-runtime-fixed/report.json`, and
`.data/d1433-bounded-host-first/report.json`. The implementation is
`.data/d1430-bounded-host-runtime.py`; the existing D1407 measurement harness
is reused without relaxing budgets.

## Admission

Do not activate or freeze this arrangement as a performance patch. Existing
0001, object reuse and preprocessing benefits remain intact. This rejects
unweighted contiguous grouping with conservative resource unions for the
measured startup workload; it does not prove every profile-guided grouping
policy fails, and it does not establish a Darwin/Linux root cause.

The startup objective remains active and unresolved. The next candidate must
reduce measured execution work without introducing this extra host-transfer
cost. A smaller C function or passing framework import is insufficient.
