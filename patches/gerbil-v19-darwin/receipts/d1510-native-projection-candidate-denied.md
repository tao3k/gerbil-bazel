# D1510 native projection prototype: DENY

## Unchanged Anchor

The frozen source-loader candidate remains unchanged and hash-verified:
49.742614 / 49.938471 seconds complete cold build, target 50 seconds,
hard ceiling 52 seconds. These are retained measurements, not measurements
of this prototype. Full MCP test qualification remains false.

No release patch, default build configuration, runtime archive, retained
0015 driver, original 42 C inputs, or frozen binary is replaced.

## Isolated Construction And Semantics

This prototype specializes exactly core-expand1 and core-expand-head.
It retains both field computations in order, omitting only the final result
pair. Helpers are enabled only for Darwin with GNU GCC, not Clang.

- First construction failed its import smoke check: a generic Python
  S-expression serializer corrupted a Gambit character literal. The caller
  generator now refuses such input; the actual core rewrite uses native
  Gambit read/write. No performance result was taken from that binary.
- Second construction imported successfully, but native rebinding controls
  failed: a direct fallback reference had been inlined by the compiler.
- Third construction explicitly reads cached Gambit global-variable handles
  for identity guards and producer fallback. It imports successfully and
  passes all 18 native semantic controls, final OK, exit zero. The bounded
  control run took 0.299086 seconds; this is not gerbil test timing.
- Eight Python generator/caller tests pass. The 18 native controls do not
  establish full consumer-suite or interrupt/continuation conformance.

Native candidate SHA256:
`f3227fa487c8fc665e6f8b98e1226d8f27882c9fc1d62620a73c97ae78055d76`.
Raw construction and control records are in
`.data/d1510-projection-native-v3/` and
`.data/d1510-projection-native-controls-report.json`.

## Real Cold Build: Not Admitted

The matched campaign selected the frozen 49-second binary as A and the
prototype as B, with the same 0015 driver, original single-VM recipe,
GNU GCC, 12 physical cores, no embedded candidate mode, and clean native
image count zero. Actual policy is 10-second real-output gap, 180-second
build budget, and 52-second complete-build ceiling.

| Role | Clean Seconds | Clean Exit | Build Result | First Compile | Complete Build |
| --- | ---: | ---: | --- | --- | --- |
| A, frozen binary | 10.938874 | 0 | output watchdog, terminal 70 | absent | incomplete |
| B, prototype | 12.887230 | 0 | output watchdog, terminal 70 | absent | incomplete |

The campaign stopped on the first failed B. No B2/A2 retry, speedup claim,
or interpretation of the watchdog as a complete-build duration is allowed.
The private adapter records an actual 52-second ceiling; only a copy of
report metadata is adapted for the immutable historical 55-second checker.
The candidate-specific checker still enforces 52 seconds and reports DENY.
Raw records: `.data/d1510-projection-cold-abba/`.

## MCP Test Attempt: Incomplete

The strict CLI test attempt used the prototype binary and retained cold-built
MCP artifacts, explicit source HOME, selected binary aliases, and the existing
5-second real-output / 90-second wall gates. The inventory is 39 files, but
the controller failed during process cleanup with PermissionError after a
wait timeout. Only 23 test logs exist; only one ends in OK, with 19 CASE-OK
lines. These log observations are not exit-qualified passes. No completed
wave, total gerbil test duration, or all-39 result is recorded.

The controller exit is 1; its report has zero admitted rows. A subsequent
exact-path process check found no surviving prototype processes. Do not
present this attempt as a completed suite or a test-speed improvement.
Raw records: `.data/d1510-projection-selected-tests/`.

## Next Source Boundary

Pair-only elimination leaves both mark folds and wrapper allocations intact.
It has no demonstrated end-to-end benefit and is not promoted to a patch.
A larger field-sensitive specialization must establish the canonical
stx-wrap, stx-apply-mark, stx-source and fold implementation identities,
their actual native inlining boundaries, and conservative fallback on
rebindings before removing unused tail computation. Allocation counts alone
are insufficient. Previously rejected cache/grouping/compiler-tuning routes
are not reopened by this result.
