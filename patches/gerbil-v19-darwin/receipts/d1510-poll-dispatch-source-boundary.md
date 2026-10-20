# D1510 Poll Dispatch Source Boundary

No runtime candidate, AOT edit or speedup is admitted. This source audit rules
out the premise that every poll duplicates the complete host-exit protocol.

## Existing Shared Exit

In the retained Gambit header, `POLL(n)` tests the configured poll trigger,
stores the original resume descriptor in `ps->temp1`, and invokes
`JUMPEXTPRM(NOTHING, ps->handler_stack_limit)`. `JUMPEXTPRM` delegates to
`JUMPEXT`, which sets the target PC and jumps to `___jumpext`. Both the inline
and non-inline label-value branches define that shared exit in `END_SW`.
The debug branch additionally preserves the original file/line annotation.

Authoritative source: `.data/d1391-runtime-object-source/src/gambit/include/`
`gambit.h.in`, lines 6917-6940, 8100-8108 and 8518-8536. This is a source
control-flow proof, not a count of executed exit instructions. The existing
[host-exit audit](d1510-host-exit-branch-boundary.md) separately verifies the
retained GNU proper-tail-call branch and its native exit block. Do not rebuild
that already-established mechanism as a new optimization.

The wider D1612 line map has source SHA256
`e4a2ffde9b4dc329bf44db818f8241a30ef0c8ecaa7fc220c3fe6521936277e1`.
Its line numbers must not be applied directly to the different frozen D1510
carrier. Aggregated IF/arity/poll cycle categories span many procedures and
are not evidence of one removable instruction sequence.

## Literature Applicability

[Ertl and Gregg's interpreter study](https://jilp.org/vol5/v5paper12.pdf)
establishes that indirect dispatch can matter greatly for interpreters. It
does not identify a Darwin-specific defect in this compiled Gambit host.
Distributed computed-goto exits were already rejected in D916; the general
paper does not authorize reopening that candidate.

The new [hardware/software co-design paper](https://arxiv.org/abs/2609.34263)
requires a hardware lookahead engine and evaluates CPython workloads. Its
reported predictor and IPC improvements are not a deployable Mach-O/GNU-GCC
software patch, a Gambit result or evidence of the macOS/Linux disparity here.

## Acceptance Remains Unchanged

Historical cold builds: 47.771713 / 47.824226 / 47.927094 seconds.
Historical complete test: 105.750982 seconds, 39 files and 965 passed cases.
Current whole-task gates: first real compile <=5 seconds, cold build <=50
seconds, complete tests <=112 seconds. No new timing follows from this audit.
Continue looking for substantial eliminated execution in reached macro/import
work, without omitting polls, roots, rebinding or escaping object identity.
