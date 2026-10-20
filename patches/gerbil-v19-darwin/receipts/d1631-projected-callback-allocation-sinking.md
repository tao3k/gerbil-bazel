# D1631: guarded callback composition and allocation sinking

## Concrete transformation

The existing GVM trace prototype now accepts an optional copied initial State.
The default path is unchanged. This permits a returned fresh structure to stay
virtual across a subsequent callback analysis rather than starting each analysis
with an unknown heap object. Effects, stack state, predicate facts, visits and
analysis budgets are carried, not cleared to obtain acceptance.

The new discarded-structure lowering sinks recorded fresh constructors into
existing poll deoptimization exits. It removes normal-path construction only
when the result is explicitly discarded, the transfer is completed with its
frame restored, and the symbolic executor recorded no external effects.
It requires the caller to retain the full original heap reservation for
deoptimization; the helper does not independently verify a native reservation.
This is not a heap-size or GC-epoch change. Nested dependencies materialize in order
inside the original handler branch before stack/register snapshot export.

The pass refuses incomplete/mismatched constructors, unknown allocation kinds,
fresh addresses observed outside a poll exit, non-discarded returns, effects,
unrestored frames, cyclic/forward constructor dependencies and insufficient
reserved heap. It does not declare an entire user procedure pure. This helper
is experimental code generation and is not connected to product code. Future
integration must retain the existing Darwin/GNU/non-Clang and single-VM guards.

## Current generated-source execution

D1623 structurally identifies fresh pair producers that repeatedly pass the
same local callback to a three-argument global fold. No procedure name is an
eligibility allowlist. On the current stx module the two matching producers are
syntax-e and stx-unwrap__%; this naming is diagnostic attribution only.

For each callback, the source-symbolic executor derives eleven completed,
guarded one-step transfers. Allocating paths return a five-word fresh structure;
none of these completed paths has an external effect or an unrestored frame.
Longer type-ancestor traversals exceed the existing visit bound and are refused.
These are bounded guarded paths, not exhaustive termination/purity proofs.

D1630 carries the result into a second callback with a distinct next-mark input
and an explicitly installed abstract caller return address:

| Source-symbolic paths across both producers | Count |
| --- | ---: |
| Completed two-step transfers | 108 |
| Transfers with normal-path structure allocation removed | 102 |
| Transfers removing two nested allocations (ten heap words) | 48 |

The retained poll exits still materialize the required virtual dependency graph.
The generated normal path is not allowed to expose a fresh address. Source and
analysis-helper hashes are recorded. This is an actual source transformation on
current callback traces, not a native execution, removed-work timing or proof
that all observed MCP folds qualify.

## Controls and retained failures

Four seed controls cover default parity, using a copied seed without mutating
the input, preserving seeded effects, and refusing unknown seed types. Seven
lowering controls cover nested poll-only materialization, non-discarded results,
heap reservation, address escape, cyclic dependencies, corrupted construction,
and effect/frame refusals. All 140 test_gambit*.py tests pass after the edits.
Whitespace/diff checks on the touched files pass.

D1624 yielded no transfers because entering a callback directly did not install
its arity. D1625 supplies a synthetic call with the actual two-argument ABI.
D1626's first composition carried an inner R0 left by the preceding callback;
that is not the caller's new return installation and its results are not valid
two-step transfer evidence. D1627 corrects that boundary. D1629 exercises the
first sinking implementation; D1630 records the final stricter dependency
validation and helper hashes. Earlier reports remain unchanged.

## Remaining production boundary

Do not promote this as a Gambit patch or measured startup improvement. It still
needs the actual fold frame/return protocol, global-fold binding guards, producer
projection guards, correct materialization at every unsupported boundary,
native ABI/GC/continuation tests and integration into Gambit's backend rather
than a standalone Python carrier transformer. D1617's rebound-fold exception and
continuation contracts must keep passing. Unbounded/cyclic type chains require
the original behavior, not widened analysis limits or a totality assumption.

No installed toolchain, MCP, std/make, std/test or Linux behavior changed. No
new MCP cold-build measurement was performed. D1513 and the fixed 55-second
full-build ceiling remain the performance reference; the major first-log and
complete build/test goals remain unachieved.

Private source evidence: .data/d1623-projected-callback-summary.py and the
.data/d1624 through d1630 projected-callback directories.
