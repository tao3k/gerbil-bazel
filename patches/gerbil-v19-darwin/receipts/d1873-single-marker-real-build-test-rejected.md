# D1873: actual no-copy entry candidate fails performance admission

D1867 implements one private caller-inline single-cell marker gate. Immediate
and permanent objects return without entering the allocation-capable marker;
forwarded cells use the exact original tag/forwarding expression; other cases
call the unchanged original marker. Function arguments are evaluated once.
Darwin/GNU/non-Clang, eight-byte, single-VM/thread/processor and non-debug guards
leave other configurations' original code untouched. Two generator tests pass;
hook removal reconstructs the original source and the forwarding expression is
checked against it. These tests are not full cross-platform compilation proof.

D1868 GNU preprocessing confirms activation, then mem compilation, native
linking and framework imports succeed using original D1510 carrier/static
objects and original D1391 home. Original inputs remain hash-checked unchanged.
Candidate binary SHA256:
`c7e280eb3174c9e9d786ed781849855c9640b839f25b3cd82b050ddaad921fb1`.
This qualifies native construction/import only, not acceleration.

## Real Semantic Checks

D1869 runs twelve concurrent processes, alternating original and candidate.
All pass the original five-second real-output gate, exit zero and emit explicit
final success. Tests cover repeated GC of shared/cyclic graphs, still-to-movable
edges, live hash keys, continuation roots, live weak keys/values and mutation.
They do not establish complete weak-expiry/finalizer/FFI conformance.

D1871 passes twelve native starts, twelve framework imports and the unchanged
real std/make/std/test cold/no-op/incremental fixture. The make phase takes
15.621519 seconds, with maximum real-output gap 4.285186 seconds. Actual GCC
frontend peak is eleven, although configured physical workers are twelve.
This is semantic/concurrency evidence, not a paired speed result.

## Complete MCP Build

D1870 executes successful official clean, zero remaining project native images,
then official build on unchanged MCP sources with twelve physical workers:

| Boundary | Seconds |
| --- | ---: |
| Clean, exit zero | 5.110180 |
| First literal compile log | 9.628876 |
| Complete build, exit zero | 77.030693 |

The ten-second genuine-output gate passes. The 55-second complete-build ceiling
fails and the performance controller exits one. No causal comparison against
an unmatched prior wall time is admitted. This does not restore the historical
52.617045-second line or solve startup.

## Actual All-Unit gerbil test

D1872 uses ABBA, all thirteen distinct MCP unit files per wave, at most twelve
concurrent CLI workers. Exact CASE counts, final OK, exit and five-second genuine
output gates are retained. No identical-file concurrent replicas are used.

| Wave | Role | Complete? | CASE-OK | User CPU | Wall |
| --- | --- | --- | ---: | ---: | ---: |
| A | original | no, twelve output-gate failures | 19 | 17.831632 | 7.997483 |
| B | candidate | no, nine output-gate failures | 35 | 19.622853 | 8.651720 |
| B | candidate | yes, all thirteen files | 177 | 22.504322 | 6.394084 |
| A | original | yes, all thirteen files | 177 | 23.565908 | 4.469628 |

The complete ABBA batch is unqualified. Truncated failed waves are not matched
CPU comparisons, and dropping them to compare only later waves is not stable
performance evidence. No full-test acceleration or overall unit-batch success
is claimed. Passed processes retain unchanged test-source hashes.

## Decision

The counted 62.2% no-copy opportunity translated into a real candidate, but
actual complete build and full test-batch gates reject admission. Keep this
negative result; do not expand its scope or promote bounded GC/fixture passes
to the requested full result. Original D1510 remains selected, with historical
52.617045-second mean and mandatory 55-second ceiling unchanged. No production
patch, installed toolchain replacement, commit or push occurs. All owned
processes are terminal. The requested optimization remains unachieved.

Private evidence: `.data/d1867-marker-single-fastpath.py`,
`.data/d1868-single-marker-native/`, `.data/d1869-marker-contract/`,
`.data/d1870-single-marker-real-mcp/`, `.data/d1871-single-marker-concurrent/`
and `.data/d1872-single-marker-all-unit-tests/`.
