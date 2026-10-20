# D935 Darwin Structure Predicate Source Candidate

## Identity And Scope

- Gerbil staging: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
- Gambit gitlink: `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
- Actual compiler: GNU GCC 16.2.0; hardware-derived capacity: twelve cores.
- Durable isolated source and build under project `.data`; no existing install
  replacement, package removal, commit or push.
- New source behavior is confined to Gambit `gsc/_prims.scm`, registering the
  inherited structure predicate expander only for Darwin and the C target.
  std/make, consumer source and flags are unchanged. D932/D933 parameter
  experiments are not included.

## Evidence Before Integration

D934 lowers inherited structure traversal into the caller's generated host,
using the existing recursive-IR pattern used by memq. Native generated C has a
TYPEID/TYPESUPER loop backedge, interrupt POLL and no loop closure allocation.
The original-reference oracle and twelve parallel VMs pass 6609 assertions,
including deep inheritance, wrong arity, explicit GC, cyclic traversal and an
interrupt action that performs GC and changes the live parent descriptor.

Actual complete 187-module MCP preparation CPU in ABBA order is 6.912, 6.169,
6.215 and 7.305 seconds. Average CPU cost is approximately thirteen percent
lower in these samples, with external host load around 44-46. This is bounded
execution-cost evidence, not controlled wall-time admission or a fivefold gain.

The real MCP dependencies and official clean pass, but cold build still exceeds
the unchanged ten-second no-output gate before its first actual compile line.
Startup is not fixed and no complete cold-build success is claimed.
Evidence: `.data/d934-mcp-preparation-cpu/report.json` and
`.data/d934-mcp-cold/report.json`.

## Actual Compiler Source

The callback is integrated in Gambit's existing setup-structure-primitives,
using its canonical symbols, gen-check-run-time-binding and proper-tail-call
environment. It changes no primitive arity, descriptor representation, native
VM ABI or mutable type cache. Linux and non-C targets retain the existing path.
Source hash: `294de392a458f34ca7d08f79dcad38a7081d0b46a702535796ee643c21947374`.

Unedited and modified MCP balance checks pass. MCP syntax cannot resolve this
Gambit compiler include context; checkout-local `./run.sh gxi` checks the full
modified primitive file under its actual c# namespace and header context and
passes before compilation. Reading a snippet is not used as qualification.

## Full Build Status

The first configure attempt forcibly checks out the Gambit submodule when no
MANIFEST exists, erasing modifications in the newly created isolated copy. It
is stopped before compilation; baseline and existing installs are untouched.
The rejected copy is retained under `.data/d935-configure-reset-rejected`.

A fresh copy is restored from the immutable baseline, the same source edit is
reapplied and checked again. The runner now uses upstream manifest.sh for
prepared source checkouts and verifies all four protected Gambit source hashes
after configure, before any compile stage. This guard passes. Prepared source
does not reapply the superseded 0004 macro-tracking placement over 0012.

The twelve-core full source pipeline completes, including bootstrap and
from-scratch Gambit rebuilds followed by Gerbil core, stdlib and tools. Actual
GNU commands inherit macro tracking policy from C_COMPILER. All 45 base cases
and the executor contract pass. This qualifies the complete toolchain's
functional build, not startup performance or a complete MCP build/test.

Evidence: `.data/d935-full-toolchain/report.json` and per-stage logs.

The initial native build is interrupted by the runner's process observer when
its ps query times out, not by a native compiler diagnostic. Observation now
falls back to known descendants on timeout and does not treat unavailable
observation as product progress. No product-output performance gate is relaxed.

Continuation first completes the saved WIP GSC with make all and verifies its
primitive source hash. It then copies the completed WIP bootstrap, completes
head bootstrap, cleans generated core artifacts and rebuilds core with twelve
jobs. This avoids discarding the completed release bootstrap, while ensuring
that a stale executable cannot qualify merely because copied Scheme files
already match. WIP completion, head bootstrap and fresh core pass.

Fresh Gambit core, boot-gxi, stage0 and stage1 subsequently pass. Actual new GSC
generates native TYPEID/TYPESUPER loops with POLL backedges in the static
expander; stx's twelve original structure primitive references are removed.
The shallow matching path still enters an eight-word GVM frame before its
first type comparison. A bounded shallow prefix before the proper loop is a
possible follow-up, not a measured improvement or a change to this candidate.

The actual new GSC, without a diagnostic hook, compiles the 6609-assertion native
contract. The original VM and twelve concurrent candidate VMs all pass,
including live parent mutation, GC and returning interrupts inside cyclic
descriptor traversal. This check does not need stdlib and runs while its
remaining native compilation finishes; it is not a performance sample.
Evidence: `.data/d935-native-structure-contract/report.json`.
GSC SHA256: `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
GXI SHA256: `cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.

The CPU diagnostic now has an explicit complete-toolchain mode that selects
each variant's own HOME, library, include directory and GSC, recording compiler
hashes separately. The official cold runner no longer blocks its output reader
on a synchronous global process query. Its bounded observations are explicitly
labelled sampled CPU with their sample timestamp; unavailable CPU is null, not
zero. Actual compile output timestamps and strict output-gap gates are unchanged.

## Complete Toolchain Measurements

The complete-toolchain ABBA measurement uses each variant's own runtime,
compiler, library and include directory, with identical 187-module MCP inputs.
Every run exits successfully after importing all 187 modules. Total process CPU
seconds are 8.550 (original), 6.585 (candidate), 6.061 (candidate), and 7.130
(original). Mean CPU falls from 7.840 to 6.323 seconds, approximately 19.3%.
External host load is 79-97; these samples do not qualify wall-time performance.
Evidence: `.data/d935-complete-toolchain-cpu/report.json`.

Concurrent runtime and std/make/std/test qualification completes 49 runs,
including real cold, no-op and incremental make cases. All pass; observed GNU
frontend concurrency reaches twelve. This is functional evidence, not a timing
claim. Evidence: `.data/d935-concurrent-make-test/report.json`.

Official MCP clean succeeds and leaves zero project native images. The first
unchanged actual compile line arrives at 35.758 seconds under external load.
The strict ten-second output gate fails. The diagnostic deliberately observes
the delayed line and then stops its own build process group; it does not report
build completion or relax admission. Compatibility-generation and dependency
CLI timeouts from earlier attempts are not cold-build samples.
Evidence: `.data/d935-mcp-first-compile-observation/report.json`.

## D936 Follow-Up Boundary

A separate isolated hook tests a shallow descriptor comparison before entering
the recursive IR loop. Deep traversal retains POLL and the proper loop; no
descriptor cache or ABI change is introduced. MCP balance and syntax checks
pass before compilation. The original VM and twelve candidate VMs each pass
6609 native assertions. Eleven measured hot units compile with unchanged GNU
O1 settings. This is a partial runtime experiment, not an actual new compiler
source integration or complete-toolchain qualification. Its incremental CPU
measurement must qualify separately before promotion.
Evidence: `.data/d936-shallow-loop-native-contract/report.json` and
`.data/d936-shallow-loop-profile/report.json`.
