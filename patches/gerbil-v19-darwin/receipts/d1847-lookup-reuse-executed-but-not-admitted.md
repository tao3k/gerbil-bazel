# D1847: lookup reuse executes, major startup/full-build gate still fails

## Original Line And Source Scope

This turn advances D1837's real lookup-locality evidence into an executed
candidate, not another presumed cache gain. Input is immutable original
D1510/D1513 B carrier, original D1391 home and all original objects/GSC/RTS.
Canonical staging is freshly verified as
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
The development baseline is not overwritten or replaced. GNU GCC and twelve
physical cores remain; Linux and Clang paths are not enabled.

`gambit_lookup_result_cache.py` is an experimental carrier transformation,
not production compiler integration. Only original helpers 7 and 11 change.
Their class/interface/global/procedure checks and terminal handling remain
fresh and original. A 64-slot `(table,key)->value` cache per helper invalidates
on all 23 MR_ALL state definitions and known writes/EXPR statements.
Dirty writes coalesce; epochs advance lazily on lookup, clearing tags on wrap.
Old words are not roots. KEY_MOVED always calls the original RTS lookup and
marks the window dirty, preserving lazy rehash rather than returning a cache hit.
Opaque CFUN bodies and changed source envelopes are refused.

This is not complete general mutation, GC callback or foreign-code admission.
No installed runtime, std/make/std/test, consumer, package or HTTP source changes.

## Construction And Native Write Contracts

D1838 generates only from the original carrier with unchanged input hashes.
D1839 GNU compilation/link/framework imports pass. Candidate SHA256:
`d0c95fad3c9e2a6f9de4fb53bb7d810194fc6558b0d54d07b4cd38793476191f`.

D1840's test fixture uses nonexistent FIXOR and fails native compilation before
executing. Corrected bitwise FIX flag construction is run in new D1841; failed
evidence is retained. Fourteen exact CASE-OK records, final LOOKUP-CACHE-UNIT-OK
and exit zero pass within the original five-second load gate. Checks cover first
read, actual no-read reuse, setter, field/unchecked aliases, both raw word-store
macros, statement fence, forced KEY_MOVED original call, epoch wrap, negative
reuse/insertion, reload invalidation and coalesced writes with single evaluation.
The unit compiles the exact candidate cache C body and header hooks against real
Gambit tables. This is not proof of every host-level GC/FFI path. Five Python
source-shape/fail-closed tests pass.

## Real Complete MCP Build: Rejected

D1842 uses untouched MCP `9a5c35e275e5d6847ff421151bb224f2eae177c1`, official
clean/build, original home, twelve workers, unchanged ten-second genuine-output
and complete-build budgets. Clean exits zero with zero native images afterward.

| Boundary | Result |
| --- | ---: |
| Clean | 6.455394 s, exit 0 |
| First literal compile line | 6.941030 s |
| Complete build | 78.505889 s, exit 0 |
| Maximum genuine build output gap | 8.384157 s |
| Complete-build ceiling 55 s | failed |

Executable exists and consumer inputs remain unchanged. Driver exits one for
performance rejection. No ratio against historical or unmatched current full
builds is claimed; the best-line ceiling remains unchanged.

## Actual Bypass Coverage

D1844 compiles the same cache with counters and existing first-write observer;
SHA256 `b0294eb110a577b0aec354198beb83aa825b60defe47afd2bdaf79da7c82cae3`.
D1845 verifies actual MCP builder PID 97396, records the first real compile at
8.484465 seconds and deliberately stops with build exit 70. No completed build
or diagnostic speed claim is made.

| Helper | Queries | Cached returns | Actual RTS calls |
| --- | ---: | ---: | ---: |
| 7 | 383,476 | 148,224 | 235,252 |
| 11 | 30,369,686 | 9,281,110 | 21,088,576 |

Of 30,753,162 queries, 9,429,334 actually bypass RTS, approximately 30.7%.
Counters reconcile exactly: query = cached return + original call at both sites.
This is reduced lookup execution, not reduced total CPU or major acceleration.

## Real Concurrent make/test And MCP Tests

D1843 passes twelve native starts, twelve framework imports and unchanged
std/make/std/test cold/no-op/dependency-invalidation cases, final SUITE-OK and
D885-OK, exit zero. Cold/no-op/incremental phases:
13.392509/0.012697/2.385179 seconds. Make wall 17.571641 seconds; max genuine gap
3.184633 seconds, original five-second gate. Actual peak GCC frontends ten with
twelve configured workers. This candidate-only control is not a speed ratio.

D1846 runs actual unmodified MCP regex `gerbil test` with original D1510 and
candidate, twelve processes per role. All 24 exit zero with nineteen CASE-OK
records and final OK: 456 cases, unchanged inputs. Five-second output/90-second
wall gates remain. This is regex-only, not a complete MCP test suite.

| Wave | user CPU | system CPU | wall |
| --- | ---: | ---: | ---: |
| Original D1510 | 11.639844 s | 2.788151 s | 4.202081 s |
| Candidate | 11.906150 s | 2.907729 s | 3.536133 s |

Candidate user CPU is higher. A lower single-wave wall is not stable test gain.

## Decision

Do not admit or solidify this result cache into a production patch. Actual RTS
calls decrease substantially, but the required first-log and full-build result
does not follow. Do not equate lookup-count savings with macro-expansion CPU,
declare these contracts complete GC/FFI qualification, redefine success around
passing small tests, or replace the original 51.737/53.497-second reference line.
The major Darwin startup/build/test objective stays open. This evidence changes
the next action: look beyond caching this one operation to the repeated live
validation/execution surrounding it, with exclusive cost evidence before a new
candidate. Do not simply increase cache size or stack this candidate on baseline.

Evidence: `.data/d1838-lookup-cache-preflight/`, `.data/d1839-lookup-cache-native/`,
`.data/d1840-lookup-cache-unit/`, `.data/d1841-lookup-cache-unit/`,
`.data/d1842-lookup-cache-mcp/`, `.data/d1843-lookup-cache-concurrent/`,
`.data/d1844-lookup-cache-census/`, `.data/d1845-lookup-cache-prefix/`,
`.data/d1846-lookup-cache-mcp-test/`. All owned sessions are terminal.
No commit, push, baseline overwrite or system installation occurs.
