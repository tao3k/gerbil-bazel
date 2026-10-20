# D1510 Symbol Hash Filter Rejected

Branch only from the original D1510 carrier, static objects and runtime
archive. The retained 56.255963-second baseline is not replaced.

## Source Hypothesis

Gambit mem.c's UTF-8 and Scheme-string intern-table lookups compute the query
hash but compare bucket neighbors' names without first rejecting a different
stored hash. A private candidate inserts that rejection before name decoding
and comparison. Same-hash collisions still use the full original comparison.
No cache, roots, ABI, table resize, poll or object identity changes are introduced.
The change is guarded by Darwin plus GNU/non-Clang preprocessor conditions.
Non-Darwin source paths remain unchanged; no SCM or consumer source is modified.

Compile the isolated mem.o with the original RTS GNU flags and link the
original D1510 objects/carrier/archive. Compile, link and make/test import/GC
smoke all exit zero. Candidate SHA256:
`dbc00fd43ea639c4917e3ba97f227867e608c22af844837ea20823bd3e865966`.
The original GSC remains in use; this does not claim compiler-process gains.

## Semantic Contracts

Twelve concurrent processes, six original and six candidate, pass twelve cases
each: 144 CASE-OK records. Cases cover symbol/keyword repeated identity,
round trips, empty/Unicode names, mutable input, embedded NUL, full-hash
collisions, 20,000 additional symbols and keywords, rehash and live GC.
The two distinct collision names `gb-collision-38224` and
`gb-collision-79740` both have the compiler-compatible 29-bit hash 494181053.
Real five-second output and ninety-second wall gates are unchanged.
These are focused contracts, not exhaustive unsafe-internal mutation or full
toolchain qualification and not a speed measurement.

Private evidence: `.data/d1510-symkey-contract/report.json`.

## Real Cold Build And Tests

Official MCP clean/build uses an independent clone and twelve physical workers.
Clean exits zero and leaves zero native images. First compile is 5.311764 s;
complete build is 62.443346 s, exit zero, source unchanged. The 55-second
controller exits one. A readonly original-baseline inventory verification was
performed during this build; this is not an independently isolated matched
performance comparison. No subtraction or regression/speedup ratio is admitted.

On that built fixture, official `gerbil test -v 5` runs thirteen distinct
unchanged unit files per twelve-worker wave. Original passes 1/13 files and
19 cases; candidate passes 5/13 files and 75 cases. Both waves fail the existing
five-second real-output gate and the controller exits one. These are sequential
unqualified waves, not cold matched throughput improvement. Failed processes
are terminated/reaped rather than admitted with relaxed deadlines.

Private evidence: `.data/d1510-symkey-filter-mcp-cold/report.json` and
`.data/d1510-symkey-filter-mcp-unit-wave/report.json`.

## Decision

Reject this candidate from baseline selection and release patches. Do not
extend it into GSC or a complete toolchain based on source plausibility or
passing narrow contracts alone. Final original-baseline verification still
matches all 50 locked files and all 1,100 runtime-home modules. No public
optimization patch, selected binary replacement, commit, push or PR follows.
The 51/52-second restoration and test acceleration goals remain unachieved.
