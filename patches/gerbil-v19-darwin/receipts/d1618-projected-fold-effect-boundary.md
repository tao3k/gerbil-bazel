# D1618: projected fold execution and the required effect boundary

## Existing opportunity, not repeated measurement

D1344-D1345 already counted 1,370,219 allocated syntax-e results consumed by
two immediately-CAR continuations. Reuse that observation; do not repeat its
counters or equate 32,885,256 pair bytes with a major startup improvement.
The execution opportunity is the second, CDR-side fold, not merely the final
pair allocation. No speed result or compiler transformation is admitted here.

## Current source findings

Canonical v0.19-staging was checked live during this turn and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

On the D1510 carrier, syntax-e continuation 6 loads the original pair's CDR
and calls the global foldl__0 a second time. Continuation 7 constructs the
result pair. Both calls use the same local callback at continuation 9.
That callback uses JUMPINT to stx-apply-mark; its allocating branch uses
JUMPINT to stx-source and then an inline four-field structure allocation.
Thus stx-wrap is already inlined at this boundary. Repeating wrapper inlining
does not remove the discarded fold execution.

The remaining fold call is JUMPGLONOTSAFE, not a fixed local call. The normal
foldl__0 checks procedure arity/type and enters the local fold loop, which
invokes its callback dynamically. The loop stops on a non-pair tail: it does
not require a proper list. Any eligibility proof must match that behavior,
not invent a proper-list exception absent from the actual source.

Relevant source locations under the private D1391 source/build tree:

- src/gerbil/expander/stx.ss:49, syntax-e and the two stx-wrap calls.
- src/gerbil/expander/stx.ss:159, stx-wrap and stx-apply-mark.
- src/gerbil/runtime/util.ss:268, foldl1 and foldl dispatch.
- src/gambit/gsc/_ptree2.scm:1465, side-effects-impossible?.
- D1508 carrier:274805, second global fold; 276087, fixed callback body.

Gambit's existing parse-tree effect predicate accepts specialized procedures
only when their proc-obj side-effects bit is false. It does not establish a
transitive, guarded purity summary for this user-defined fold/callback chain.
Changing that bit globally, or deleting an unused field's evaluation solely
because the caller takes CAR, is not a valid implementation.

## Actual native-producer contracts

D1617 runs twelve independent processes at the physical twelve-core
concurrency. Six execute the original D1391 binary and six the retained D1510
binary. The Scheme fixture is interpreted; syntax-e and its fold implementation
are the actual native runtime procedures, not copied test implementations.
The environment uses existing Bazel GNU GCC discovery and common D1391
libraries. No MCP, std/make, std/test, installed runtime or product source is
modified. The unchanged five-second genuine-output watchdog is enforced.

All twelve processes exit zero with six exact CASE-OK markers and final
PROJECTION-EFFECTS-OK 6: 72 passed checks. The contracts establish:

- Normal CAR projection returns the expected head.
- A rebound fold observes both head and discarded tail, in that order.
- An exception raised only in the discarded branch remains observable; its
  actual Gerbil Error message is checked.
- A continuation escape raised only in the discarded branch remains observable.
- A binding change during the first fold is used by the second fold.
- dynamic-wind restores the original binding.

Original binary SHA256:
`a398d0b2e3200019a1542a0fea8b101062a76118f82dcba30f580b481a608e5a`.
D1510 binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.

D1615's sandbox attempt stopped at physical-core discovery before any native
process. D1616 failed after two successful cases because the fixture used a
Gambit exception accessor on a Gerbil Error. Both failures are retained.
D1617 corrects the accessor and preserves exact exception-message checks;
it does not turn arbitrary exceptions into successful controls.

## Next implementation boundary

The next source transformation needs generic producer/consumer projection
facts plus a transitive effect/termination eligibility proof for the actual
fold and fixed callback, with runtime binding guards and an unchanged fallback.
Global calls must not be declared pure by Gerbil procedure name. A proof must
also handle mutable inputs, cyclic traversal, polling/interrupt boundaries,
non-pair producer returns, exceptions and continuations. A binding guard alone
is not that complete proof.

Retain D1513 as the historical complete-build reference and the fixed 55-second
acceptance ceiling. D1617 is a semantic boundary test, not a startup benchmark,
full std/test qualification or a complete toolchain build. The major startup,
full-build and complete-test acceptance requirements remain open.

Private evidence: .data/d1614-projection-effects.scm,
.data/d1615-projection-contract.py, .data/d1616-projection-contract/,
and .data/d1617-projection-contract/.
