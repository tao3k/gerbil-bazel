# D1510: projection-sensitive execution boundary

## New investigation, unchanged candidate

Retain the 49.743/49.938-second source-loader candidate, original 0015,
single-VM configuration, 50-second target and 52-second hard gate. No native
object, binary, driver, core Scheme source or runtime archive is changed by
this investigation. No complete-build or test speedup is claimed.

Existing D1344/D1345 evidence in `d970-guarded-trace-progress.md` records
1,370,219 allocated syntax-e result pairs consumed by CAR immediately in
core-expand1 and core-expand-head. That is executed allocation evidence from
the historical preparation profile, not a new timing measurement or a claim
that all wrapper work is removable. Unlike the rejected lookup caches, the
candidate opportunity is avoiding unused fresh intermediate results.

## Retained native caller scan

`audit_syntax_e_projections.py` checks all 42 retained C-input hashes and scans
the existing generated procedure/continuation structure. It admits only an
explicit one-argument global syntax-e call whose selected return continuation
starts immediately by replacing R1 with CAR(R1) or CDR(R1). Intervening
operations, other callees and missing labels are excluded; duplicate labels
are rejected. Four analyzer regression tests pass.

It finds 97 opportunities: 18 CAR and 79 CDR sites. The historical core sites
are confirmed at core.c lines 14797/14854, with return continuations
core-expand1 L15 and core-expand-head L5. Four CAR and six CDR sites occur in
core.c overall. The scan does not count static internal syntax-e calls; it is
not complete producer coverage. Every site explicitly has
`producerSideEffectsProvenRemovable=false`.

Raw opportunity report:
`.data/d1510-source-loader-projection-opportunities.json`.

## Actual native semantic controls

The generated syntax-e pair branch calls the global foldl__0 twice, once for
each field, then allocates the result pair. stx-wrap is inlined here: replacing
its global binding does not intercept those native calls. An initial control
that assumed interception therefore fails and remains a failed diagnostic;
it does not establish that the tail is effect-free.

`tests/syntax-e-projection-effects.scm` exercises the actual fold boundary on
both the original D1510 binary and the unchanged source-loader candidate.
Explicit original HOME/load paths are used; no global installation fallback
is selected. Both runs exit zero, print five exact CASE-OK lines and final OK:

- Original projection invokes both field computations.
- Naive head-only projection invokes just one, dropping an observable call.
- Original projection retains an exception introduced in the tail fold.
- Naive head-only projection incorrectly suppresses that exception.
- Mutated fold binding is restored through dynamic-wind.

These five assertions are boundary proofs, not a production optimization or
full std/test/consumer-suite qualification. They demonstrate a required
fallback condition: unknown/rebound fold execution cannot be deleted simply
because a caller immediately projects one field.

## Transformation boundary

The next admissible transformation must establish the actual canonical
producer/consumer identities, preserve rebindings, errors, interrupts,
continuations and non-pair behavior, and either prove unused-field computation
effect-free or retain it. Removing only the final result-pair allocation is
less ambitious than removing the unused wrapper/fold work; allocation counts
alone do not establish a major speedup for either.

Implement this as a Darwin/GNU compiler-owned guarded specialization with
ordinary Scheme return/GC/frame/debug metadata, not an ad hoc register marker
or an unboxed value passed through the old pair-return ABI. All unsupported
contexts retain the original implementation. No such production transformation
is admitted or enabled by the current source scan and controls.
