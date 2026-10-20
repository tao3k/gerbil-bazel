# D1772: actual table mutation boundary on the best line

The active baseline is the original D1513 B / D1510 native binary, not the
D1764 producer experiment. No product source, installed toolchain, original
carrier or original RTS archive changes in this investigation. The startup
goal and the <=55-second complete-build gate remain unmet by new evidence.

## Source boundary

Retained Gambit source under `.data/d1391-runtime-object-source/src/gambit`:

- `lib/_system.scm:1452` implements raw GC-table field mutation using
  unchecked structure mutation. The table implode path also writes raw slots.
- `gsc/_t-c-2.scm:3801` emits `GCHASHTABLEFIELDSET` independently of the
  `gc_hash_table_set` runtime call. Line 4090 emits unchecked structure stores.
- `include/gambit.h:6086` writes raw weak-table slots directly; line 5838
  permits unchecked structure stores through `STORE_WORD_FX`.
- `lib/mem.c:5781` covers normal table mutation, but not those generated stores.
  In-situ rehash, collector processing and union/find compression write slots
  as well. A nominal find operation is not necessarily read-only.

Therefore a cross-call table-result cache invalidated only by the C setter
is unsound. Comparing flags/count/min-count/free is insufficient even without
GC. A full context-result cache must additionally cover parent/type/global
binding mutation; this receipt does not establish that coverage. No cache
implementation or mutation-epoch ABI change is admitted.

## Actual primitive checks

D1770 runs twelve processes on the exact selected original binary. Its first
five cases verify setter lookup, raw field value replacement, unchanged table
metadata, unchecked structure replacement and unchanged metadata again. The
sixth case fails because the fixture incorrectly allocates a heap-key table
without MEM_ALLOC_KEYS. Retain all twelve failures; this is a fixture error,
not an admitted collector regression or a passed GC contract.

D1771 uses a distinct fixture with the required MEM_ALLOC_KEYS flag (16),
retaining D1770 unchanged. Twelve concurrent processes each return all six
exact CASE-OK records, final MUTATION-CONTRACT-OK 6 and exit zero: 72 cases.
The post-GC lookup returns the updated value. The unchanged five-second
actual-output gate passes in all processes. These are actual interpreted
primitive checks, not newly compiled-emitter or complete weak-table coverage.

Fixture SHA256:
`58a3c63bd91bd1cf3f6cc89817e2e43fbb6d33c9a340bf44da32d30f5a08e786`.
Selected binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.

Both mutation paths change the actual returned value without changing table
metadata. This rules out setter-only and metadata-only result-cache proposals.
It does not prove a startup speedup, a cache hit rate or a Darwin/Linux cause.
Do not spend a native performance build on either unsound proposal.

Private evidence: `.data/d1770-hash-mutation-contract/`,
`.data/d1771-hash-mutation-contract/`, `.data/best-line.py`.
