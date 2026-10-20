# D1510 Import Binding Construction Contract

Original-only execution, no runtime optimization or performance admission.
Keep the historical 47-second cold-build anchor and 5/50/112-second whole-task
gates. No unchanged cold/full-test campaign was repeated.

## Actual Generated Path

The retained `expander/module.ss:541` calls `make-import-binding`, but its
generated `build/lib/static/gerbil__expander__module.scm:1870` directly allocates
the structure and calls `gx#import-binding:::init!`. The corresponding C path
uses `___BEGIN_ALLOC_STRUCTURE(8UL)` and the initializer's global entry. Thus,
bypassing the public generic `make-instance` constructor is already performed
and is not a new optimization opportunity at this call site.

`core-resolve-module-export` performs key substitution and phase-context
resolution. It does not recursively reconstruct an export chain. Do not turn
the earlier import-attempt count into a presumed expensive resolution chain.

## Executed Original Contracts

`tests/run_import_binding_contract.py` runs the frozen native binary with the
recorded host environment, the selected local toolchain home and an empty
isolated package home. It requires exact ordered case identities, exit zero,
the final `IMPORT-BINDING-OK` marker and unchanged binary identity.

The original native initializer global is replaced only within the diagnostic
process and restored with `dynamic-wind`. The wrapper delegates to the original
initializer; an explicit exception case tests the same live call boundary.

The first execution passed all 14 original contracts:

- Initialization happens eagerly and independently for each target context.
- Binding objects and mutable properties are isolated across contexts.
- Both imports retain the same original resolved source binding.
- A same-ID import keeps the prior binding but still calls the initializer.
- Strong conflicts raise after initialization and preserve the prior binding.
- A forced weak import cannot replace the existing strong binding.
- An initializer exception propagates before insertion into the target table.
- The original initializer global is restored before final success.

Evidence: `.data/d1510-import-binding-contract-v1/report.json` and
`original.log`. Native binary SHA256:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
The 0.356-second fixture wall time is not an import benchmark or a speedup.
The exact ordered-case checker was then executed in
`.data/d1510-import-binding-contract-v2/`: all 14 cases passed again with exit
zero and unchanged native binary. Its 0.174-second wall time likewise carries
no performance claim.
This small contract fixture does not qualify all standard libraries or the
complete test suite.

## Live Dependency And Initializer Effects

The existing fixture/runner now includes five further original-native checks;
the original fourteen assertions remain. The first attempted run stops during
sandbox-restricted Darwin memory discovery, before Scheme starts. A fresh
output using the existing host-environment permissions completes all nineteen
ordered cases, final `IMPORT-BINDING-OK` and exit zero, with frozen binary
identity unchanged. Evidence: `.data/d1510-interface-live-effects-contract-v2/`.
The 0.852718-second fixture wall is not product timing or acceleration.

Replacing the source context's exported binding before a later import changes
the new import's resolved binding. The earlier import retains its prior source
binding. Thus an interface program must perform current export resolution,
not capture one initialized export binding in a native constant.

A live initializer that installs a conflicting binding in the target context
causes the later normal binding step to raise, preserving the injected binding.
An implementation must not precompute the conflict decision before the live
initializer, or overwrite its effects with a prepared target-table image.
The final assertion requires restoration of both source binding and initializer.

This is a correctness/admission investigation, not an optimization candidate:
the mechanism is reached and relevant to generic interface construction; these
specific effects were not covered by the earlier fourteen cases; the checks
are worth executing to rule out invalid preparation boundaries; expected
performance benefit from the checks is none. A factory's savings remain unknown.

## Decision

A deferred/shared binding implementation or skipped initialization on
same-ID imports would change observed original behavior. They are not eligible
shortcuts. Likewise, compiled interface construction must retain the live
initializer call, error timing and fresh mutable binding state.

This removes a false generic-constructor opportunity and narrows immutable
material research to preparation outside those required instance operations.
It does not prove that such material owns a substantial remaining budget.

## Generic Context-Key Contract

The extended original fixture passes twenty-five exact cases in twelve
hardware-concurrent processes: 300/300, all final markers and exit zero,
frozen runtime identity unchanged. New assertions cover non-symbol pair keys,
eq identity, live rebinding callback, mark-to-gensym substitution, resolution,
and the existing symbolic hash after explicit GC. The last assertion does not
claim movement of the particular gensym. The initial nineteen cases remain.

Evidence: `.data/d1510-context-key-contract-v1/`. Its 1.371907-second diagnostic
wave is not full tests or a speedup. See the stable-symbol review in
`d1510-interface-architecture-transfer.md` for the distinct semantic rejection
and the existing 1.196893-percent rehash cycle evidence. A symbol-only table is
not a direct replacement for the generic public context-key protocol.
