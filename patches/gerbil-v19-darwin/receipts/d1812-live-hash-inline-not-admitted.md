# D1812: live hash probing inline, correctness passes but performance fails

The selected best line remains D1513 B / original D1510. Historical full
builds remain 51.737180 and 53.496910 seconds, with a 55-second acceptance
ceiling. This turn does not investigate or redefine the later discrepancy.

## Source candidate

The original trace-11 context helper calls `___GCHASHTABLEREF`, which calls
Gambit's generic `___gc_hash_table_ref` in mem.c. D1806 derives a single
candidate from the exact retained D1508 carrier: inline the original live
probe algorithm in this helper only. It uses the same hash/step macro,
wraparound, equality and UNUSED termination as the original implementation.
KEY_MOVED falls back to the original runtime function, including its lazy
rehash behavior. There is no lookup-result cache, epoch, mutation barrier or
ABI change. Existing caller guards, type checks, transfers and polls remain.

The helper stays inside the original Darwin/GNU/non-Clang single-VM guard.
The injection utility rejects unsupported guards, duplicate injection and
unexpected call shape. Four focused unit tests pass. This is experimental
carrier tooling, not an admitted product patch or automatic compiler mode.

D1807 compiles with the original GNU GCC/O1 carrier recipe and O3 helper
attributes, links the original objects/runtime and passes real framework
imports. Original inputs remain unchanged. Candidate binary SHA-256:
`2dddcc36f86373515bc1ff342be8693941199d788b3c816509d8bd96d5e96bcb`.
ARM64 object disassembly shows the hash rotate/multiply instructions inside
trace 11 and a separate branch on the tagged KEY_MOVED bit. This establishes
code generation, not an execution-cost percentage or startup gain.

## Native primitive contract

D1808's initial load uses the wrong module entry name and fails before the
contract executes. The actual native entry is `____LNK_module_2e_o1`.
D1809 uses the correct loader identity and passes all ten exact CASE-OK lines,
final INLINE-HASH-CONTRACT-OK 10 and exit zero under the unchanged D1510
runtime. Cases cover setter/live value, raw field mutation, unchanged metadata,
unchecked structure mutation, absence, KEY_MOVED fallback, post-GC lookup,
collision parity and deleted-entry parity against the original primitive.

## Real build and concurrent framework gates

D1810 uses a fresh MCP clone at unchanged head
`9a5c35e275e5d6847ff421151bb224f2eae177c1`, the original runtime home, GNU GCC
and 12 discovered physical cores. Official clean exits zero in 3.527144
seconds and leaves zero project native images. Literal first compile:
`... compile util/compat` at 5.559945 seconds. The complete build exits zero
in 100.020032 seconds, with maximum real-output gap 7.934431 seconds and
unchanged consumer inputs. Correctness is qualified; the 55-second
performance ceiling is false. This is not a matched speedup measurement or
proof that this change alone caused the later wall time.

D1811 subsequently runs the unchanged hardware-concurrent std/make/std/test
controller, without overlapping the MCP build. All 12 runtime and all 12
framework imports pass. Parallel make/test completes in 20.531010 seconds,
maximum real-output gap 4.376813 seconds, and observes 12 concurrent GCC
frontends. All three CASE-OK lines, SUITE-OK, D885-OK and controller exit zero
are verified. This qualifies the tested framework semantics/concurrency, not
a build/test speedup against the best line.

Decision: do not admit or merge this candidate. Keep original D1510 selected.
The major startup/build/test goal remains incomplete. Eliminating this one
generic call is not sufficient evidence of a major execution-cost reduction;
do not claim acceleration from static emission or correctness alone.

Evidence: `.data/d1806-inline-hash-preflight/report.json`,
`.data/d1807-inline-hash-native/report.json`,
`.data/d1808-inline-hash-contract/report.json` (failed load),
`.data/d1809-inline-hash-contract/report.json`,
`.data/d1810-inline-hash-mcp/report.json` and
`.data/d1811-inline-hash-concurrent/report.json` / `parallel-make.log`.
