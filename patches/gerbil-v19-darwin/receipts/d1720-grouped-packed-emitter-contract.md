# D1720: grouped packed emitter is correct, performance remains unqualified

The major first-log goal and complete-build ceiling remain open. D1513's
52.617045-second historical candidate mean and <=55-second complete-build gate
are not replaced by the slower later controls or this source experiment.

## Source-frontier corrections

Current gambit.h selects GCHASHTABLE_HASH_STEP_MULT, not its MOD alternative.
It uses rotations, mixing and multiplication, not the hypothesized repeated
division. No prehash candidate is built on that incorrect cost hypothesis.
D1064-D1066 already bound the empty-table opportunity, so it is not repeated.

The wider D1613 profile's mark_array functions are C GC markers, not Scheme
syntax-mark application. D999/D1004 traversal/stride experiments are retained
negative results. The source stx-e used by stx-pair?/identifier? strips wrappers
without the allocations performed by the separate syntax-e function. Therefore
those predicates do not justify claiming elimination of syntax-e constructors.
These facts prevent three misdirected optimization experiments.

## Concrete emitter change

The isolated D1714 source starts from the current original _t-c-1.scm and the
existing candidate 0013, without changing the latter's Git file. That old
candidate prints one Unicode pair per packed line, whereas the portable writer
prints eight characters per line. targ-display performs source-line handling
at line starts; excessive packed rows cause extra printer/line-tracking work.
D966's native packed compiler previously records 14.483359-second emission,
versus 2.441585 seconds for the original compiler on that retained module.
Those historical timings are not a new candidate speed result.

D1714 groups four packed words per line, matching the portable eight-character
granularity, and computes the character-list length once for the header and
threshold. Numeric packing, tail zero padding, 4096-character scope, original
fallback and the Apple/GNU/non-Clang/64-bit/little-endian/4-byte-character guard
are unchanged. NSTR's separate definition is byte-identical to the original.
The small/non-Darwin path still emits the original portable representation.

Candidate source SHA256:
`3ca0743a5d0a3607f884ac7b00857170ba6a5a5f5b7b57fb04c97c94bce1fba4`.

## Actual source execution and native objects

D1715 initially fails full-source expansion because the isolated copy lacks
_envadt.scm. Original include files are added without replacing the candidate;
that setup failure is retained. D1716 then passes full actual-file macro
expansion and executes the actual changed emitter forms in the existing GSC.
Its fifteen lengths cover zero, small chunks, the 4095/4096 boundary, odd/even
tails through 4104, NUL, byte/16-bit boundaries and supplementary Unicode.
Portable and packed GNU native objects are byte-identical, SHA256:
`d8277cf5abcac3c85e9a1282d4d8b429fc46217361f0ab2ac9278fabd2faa1ab`.

D1718 repeats the semantic contract with actual source tracking enabled and
verifies identical GNU objects again. It is a tracking/correctness check, not
another atomic speed benchmark. D1719 verifies emitted packed rows directly:
36,900 large-string characters need 18,452 per-pair rows under the old format,
but the actual candidate uses 4,616 grouped rows. This is a row/call reduction,
not a fourfold execution-time or complete-build improvement.

No native compiler containing the revised emitter has been constructed yet.
The actual source-form execution does not qualify native GSC emission cost,
toolchain construction, MCP first-log time, <=55-second complete build or real
concurrent test speed. This route affects work after the first compile line;
it does not solve the remaining pre-first-line Scheme execution cost. No
production patch, upper Gerbil, std/make, std/test, consumer or GCC-flag change
is admitted. All owned sessions are terminal.

Evidence: `.data/d1714-packed-emitter-source/`,
`.data/d1715-grouped-packed-emitter-contract/`,
`.data/d1716-grouped-packed-emitter-contract/`,
`.data/d1718-grouped-emitter-tracked-contract/`,
`.data/d1719-grouped-emitter-summary/`.
