# D1674: returned container is executed, but does not meet the speed gate

## Scope

D1663 analyzes actual generated syntax-e returns and their consumers. Both
folds have completed before the region starts. Every original poll is an
unchanged stopping point. Both fields, callback effects and escaping identity
remain observable. This is not the earlier unused-second-field experiment.

Current isolated inputs are D1391, Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, GNU GCC 16, twelve physical
workers. No consumer SCM, std/make, std/test, package HTTP, installed runtime or
Linux behavior changes. Existing object reuse remains active.

## Native and semantic receipts

The source audit accepts 269 positions and 315 paths. D1665 initially builds
four poll-boundary cases; D1666 builds sixteen effect-boundary cases; D1667
builds 264 cases including at most two modeled pure calls. Unsupported or
nonunique original source fragments are omitted, not guessed. Construction
and imports succeed; construction is not performance qualification.

D1667 binary SHA256:
`eda21f8f4bb122cd81579cb894418b8b7edfe411327d704b6186f90b3eb27185`.
Dispatch uses each owning module's actual label base. All original binding,
layout and return guards remain. Misses roll back the private heap checkpoint
and resume original code. No call, effect or poll occurs before rollback.

D1668 compares actual compiled split/splice operations with literal expected
values under marks, improper lists and live-result GC. A rebinding control
checks that both folds still execute. Twelve concurrent baseline/candidate
processes pass 504 cases in total. This does not cover all 264 paths or the
complete Native/FFI suite.

D1670 passes twelve native starts, twelve imports and actual std/make
cold/no-op/invalidation plus std/test contracts. Cold/no-op/invalidation times
are 11.861818/0.008218/1.855994 seconds. Genuine maximum output gap is 3.218521
seconds under the unchanged five-second gate. This is a candidate-only
workflow control, not a test speed ratio.

## Actual performance rejection

D1669 runs a fresh actual MCP clone, unchanged sources and official clean.
Clean exits zero and leaves zero project native images. Uninstrumented first
compile is **5.424049 seconds**, complete build **61.683842 seconds**, exit zero.
The executable is produced, but the driver exits one because the required
**55-second complete-build gate fails**. No success patch is admitted.

The historical reference remains D1513's exact D1510 candidate: complete
51.737180 and 53.496910 seconds, mean 52.617045. Different batches cannot
establish a causal speed ratio or regression cause.

## First-write execution evidence

D1671 instruments this exact 264-case construction in a separate binary.
D1672 verifies the actual builder child and freezes counters at its first
successful literal compile write. D1673 validates all 264 numeric rows, binary
and snapshot identities, attempts = hits + misses, and three words per hit:

- Attempts: 3,292,380; hits: 3,292,168; misses: 212.
- Active sites: 73; removed logical constructor words: 9,876,504.
- Raw constructor bytes: 79,012,032, not physical GC/CPU savings.
- Largest consumer: syntax-split-splice->vector, 834,479 hits.

The diagnostic first log is 5.940788 seconds and the prefix deliberately exits
70. It is not a full build or an uninstrumented speed sample. No denominator
from another observer run or process-statistics field 7 is used for coverage.

The candidate demonstrably executes on the hot path, yet does not solve the
main startup cost or complete-build ceiling. Keep it separate from D1510's
positive outline evidence. The next extension returns to D1510's unchanged
guarded readonly carrier rather than treating this failed candidate as the
new performance baseline.

Private evidence: `.data/d1663-return-container-audit/`,
`.data/d1667-native-return-container/`, `.data/d1668-return-container-contract/`,
`.data/d1669-return-container-real-mcp/`,
`.data/d1670-return-container-concurrent-make/`,
`.data/d1671-container-census-native/`, `.data/d1672-container-first-census/`,
and `.data/d1673-container-first-census-summary/`. No commit or push performed.
