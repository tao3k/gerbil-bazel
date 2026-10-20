# D932 Gambit Execution Cost Progress

## Scope

This is not a delivered cold-start fix. The unchanged real MCP first-compile
gate still fails. No std/make, package HTTP, consumer flags or Linux source
behavior is changed. Experiments use durable project-local `.data`, the staging
source identified in D879, GNU GCC 16 and hardware-derived parallel capacity.

## Completed Evidence

- D925 corrected nine-unit runtime bundle: complete 187-module preparation CPU
  6.089/6.071 seconds versus baseline 6.942/6.880. Real MCP first-output gate
  still fails. Evidence: `.data/d925-mcp-preparation-cpu/`.
- D926 counts 115,153,945 inherited structure predicate primitive calls, followed
  by reverse 4,111,840 and apply 2,356,890. Counts are diagnostic, not timings.
  Evidence: `.data/d926-primitive-counts/`.
- D927 resolves all 527,837,218 measured exits from eleven selected caller hosts.
  Kernel receives 121,842,212; STD 23,259,787; thread 2,359,370; evaluator 113,261.
  Core to STD accounts for 20,577,580. Internal STD/thread round trips are not
  counted, so these data do not establish their complete call counts.
  Evidence: `.data/d927-host-summary.json`.
- D928 direct private-register peer bridge has only a small directional CPU
  change (6.624/6.731 versus 6.799/6.914). It is not promoted to production.
- D929 two bounded bundles plus the predicate C helper: preparation CPU
  5.731/5.579 versus 6.882/6.918. Twelve runtime probes, twelve framework imports
  and the cold/no-op/incremental make/test fixture pass, with twelve GNU
  frontends observed. Real MCP first compile is still 10.820 seconds and fails
  the unchanged ten-second gate. Neither earlier diagnostic output nor the
  CPU measurements count as solving the first-log delay.
- D930 uses the actual Gambit primitive expansion API, not a C dispatcher
  override or consumer rewrite. Four descriptor steps precede the unchanged
  deep-chain fallback. Original first-class reference and twelve native VMs
  each pass 6607 assertions including GC, inheritance and wrong arity. Actual
  187-module preparation CPU is 6.135/6.052 versus 7.292/7.159, under external
  load. Real MCP clean/build still fails before its first compile line.
  Evidence: `.data/d930-primitive-expansion-contract/`,
  `.data/d930-mcp-preparation-cpu/`, `.data/d930-mcp-cold/`.

These CPU results are directional execution-cost evidence, not controlled
wall-time performance admission or complete toolchain qualification.

## Rejected Parameter Shortcut

D931 cannot identify parameter closures from the immutable current-handler
primitive cell: the original VM reports that the cell is not a closure. Its
fixture fails before candidate qualification. Substituting a mutable global
cell would not prove safe recognition; directly returning a cached value would
also skip custom getter effects. This C shortcut is rejected, not an optimization.
Evidence: `.data/d931-parameter-cache-contract-dynamic/`.

## Source Candidate D932

The isolated Gambit parameter implementation adds a Darwin-only compile-time
macro. It reads the existing current thread's first dynamic-binding cache on
an identity hit, otherwise uses the original dynamic-ref. The three special
parameters retain their original path. The captured getter still executes.
Non-Darwin expansion is the original dynamic-ref expression. No descriptor
cache, VM layout, native ABI or parameter representation is changed.

MCP balance passes both unedited and modified source. MCP syntax rejects the
unchanged Gambit optional-lambda grammar on both files, so it is incompatible
with this source language. The checkout-local fallback through `./run.sh gxi`
expands the actual full parameter file together with its `header.scm` macro
context via Gambit's compile-top, without running the generated parameter
definitions. It passes before STD regeneration starts.

Evidence: `.data/d932-parameter-source/original-syntax-check.log`,
`.data/d932-parameter-source/modified-source-check.log`, and
`.data/d932-parameter-build/parameter-context-syntax.log`.

D932 native binary builds with only `_std.o` replaced, original flags and
unchanged standalone GSC. The original VM and twelve candidate VMs each pass
1309 assertions covering custom getter effects, cache misses, setters, GC,
continuation escape, special output-port binding and thread isolation.
Evidence: `.data/d932-parameter-native-contract/`.

Complete 187-module preparation in ABBA order consumes 7.222, 7.071, 7.090 and
6.885 CPU seconds. The candidate range overlaps the baseline: there is no
demonstrated acceleration. Host load is 67-77. No official cold-build success
or performance claim follows. The cache-first source candidate is not promoted.
Evidence: `.data/d932-mcp-preparation-cpu/report.json`.

## Next Source Experiment D933

The original parameter read also dynamically calls its captured getter on every
read, even when that getter is exactly the immutable identity primitive. D933
tests only a Darwin source macro that returns the value directly for that exact
primitive; all other getter procedures still run. Dynamic-ref remains unchanged.
The parameter closure body and descriptor layout stay shared for both cases,
because parameter? recognizes closures by code identity. Splitting the factory
into different closure bodies would break that existing contract.

MCP unedited balance and modified balance pass; its syntax checker encounters
the same unsupported Gambit optional-lambda syntax. Checkout-local expansion of
the actual full parameter file and header context passes before compilation.
The original VM and twelve candidate VMs each pass 1412 assertions, including
parameter? recognition, getters returning multiple values and getters raising
exceptions. Evidence: `.data/d933-parameter-native-contract/`.

Complete preparation CPU in ABBA order is 7.416, 7.267, 7.354 and 7.366 seconds.
The approximately one-percent average difference is not sufficient to establish
a useful acceleration under changing external load. Neither parameter candidate
is promoted. Evidence: `.data/d933-mcp-preparation-cpu/report.json`.

D934 returns to the counted inherited structure predicate hotspot. Its loop
expander follows Gambit's existing memq recursive-IR generator, retaining the
compiler's proper-tail-call and interrupt machinery. Generated C shows a local
TYPEID/TYPESUPER backedge with POLL and no loop closure allocation. It is not an
unbounded C while loop that strands cyclic descriptors without interrupts.

The first added cyclic-interrupt fixture raises from a synchronous interrupt
action and fails with an abandoned mutex on both the new lowering and original
control; it is not attributed to the optimizer. The corrected action returns
normally, triggers GC and changes the live cycle's parent to false. Both direct
predicate and first-class original-reference loops resume and return false.
Original control and new lowering each pass 6609 assertions in an original VM
and twelve parallel VMs. Evidence:
`.data/d934-original-interrupt-mutation-control/` and
`.data/d934-structure-loop-interrupt-mutation-contract/`.

The real eleven-unit native candidate passes generation and compilation.
Complete 187-module preparation CPU in ABBA order is 6.912, 6.169, 6.215 and
7.305 seconds: approximately thirteen percent lower average CPU in these
samples, not a controlled wall-time qualification. Official MCP dependencies
and clean pass, but cold build still exceeds the unchanged ten-second
product-output gate before its first compile line. The startup problem is not
solved. Evidence: `.data/d934-mcp-preparation-cpu/report.json` and
`.data/d934-mcp-cold/report.json`.

D935 integrates the same lowering into actual Darwin/C-target Gambit compiler
source and rebuilds the complete native toolchain, without the diagnostic hook
or either rejected parameter change. See `d935-gambit-source-loop-toolchain.md`.
