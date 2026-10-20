# D1510 Hash Cold-Tail Candidate: DENY

## Mechanism And Scope

This is an executed private RTS candidate, not another flag audit. The frozen
runtime's GC hash lookup at 0x1014858c0 saves/restores LR and a 32-byte C frame
on ordinary lookups, because its KEY_MOVED branch calls in-situ rehash.
The source prototype moves rehash into a separate noinline/cold helper and
uses GNU musttail transfers between the helper and original lookup/setter.
Original hashing, slot probes, weak values, flags, resize return values and
mutation instructions remain unchanged. Other platforms retain the original
rehash call through the conditional source branch.

The guard requires Darwin, AArch64, GNU GCC >=16 and no Clang. No result cache,
new table layout, SIMD scan, callback suppression, MCP specialization, std/make
or std/test change is made. Original RTS flags and all other objects remain.

[GNU's shrink-wrap documentation](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
describes moving prologues onto paths that need them. This source-level
hot/cold separation is not a claim that a missing compiler flag caused the
platform difference, and no compiler-option sweep is performed.

## Construction And Reached Controls

The shared runtime-member framework reuses the original mem.o compiler recipe.
The original control object matches the frozen archive member byte for byte:
`284504db424c05a2584759cf9f74abd1c576d79f95f6f3ad074514086710f553`.
The original control link also matches the retained binary byte for byte.
Candidate binary SHA256:
`c9ab2cb7a13a41a56425c8e799558fad9b6ce7db93e73ee2d83b54feaeaca807`.

Read-only inspection of candidate mem.o confirms lookup has no SP allocation
or LR spill and tail-branches on KEY_MOVED. This changes instructions, not
established elapsed cost. It does not prove that this optimization dominates
fresh-process imports or explains the Darwin/Linux difference.

Both original and candidate execute 14 exact GC-hash controls: misses, insertion
status, object identity, false values, forced ref/set rehash, live/raw mutation,
post-GC lookup, resize status, collision contents and rooted weak-key/value GC.
Both exit zero with the final success marker. These are interpreted primitive
contracts, not complete weak-table, compiled-emitter or full-suite qualification.
Their sequential invocation times are 0.288967 / 1.697569 s; no stable speedup
or attribution of that difference is claimed.

## Actual Standard-Library Cold Gate

The candidate runs original list/list and encoding/json source through real
std/make, with 12 hardware-derived workers and the selected original home/GSC.
Clean exits zero, with zero native artifacts remaining, in 8.385958 s.

| Required line | Candidate result | Gate |
| --- | --- | --- |
| First actual compile | Not reached; DENY observed at 5.016912 s | <=5 s |
| Complete build | null; killed before completion | <=50 s |
| Complete test | null; skipped after build DENY | <=112 s |

The process group is immediately killed and reaped, exit -9, cleanup errors
empty. No MCP cold campaign, later rounds, full tests or re-tuned copy runs.
This implementation is closed; do not repeat it or promote the instruction
reduction to a runtime improvement. No production patch, commit or push.

## Reflection

High lookup counts identified a reached operation but did not establish that
its two common-path stack instructions owned substantial import time. The
candidate confirms the source mechanism and focused semantics, then fails
the actual gate. It does not prove that the entire hot/cold architecture is
wrong or that this change causally delayed the first log. The concrete decision
is to reject this implementation, preserve the retained host and avoid another
micro-tuning extension without a larger exclusive execution budget.

Historical retained measurements, not this candidate's current acceptance:
first compile 4.850866 / 4.573628 / 4.592897 s; complete cold build 47.771713 /
47.824226 / 47.927094 s; complete test 105.750982 s, 39 files/965 passed.
Later strict test DENYs remain distinct and unresolved.

Private evidence:

- `.data/d1510-hash-cold-tail-runtime-v1/report.json`
- `.data/d1510-hash-cold-tail-native-v1/report.json`
- `.data/d1510-hash-cold-tail-semantics-v1/report.json`
- `.data/d1510-hash-cold-tail-stdlib-v1/report.json`

The initial sandboxed hardware discovery failed before compilation; the
authorized isolated GNU build completed afterward. That pre-launch failure
is not a runtime failure or performance measurement. All owned processes are
terminal; original binary, inputs and global installations remain unchanged.
