# Generated C Context And Private Publication

## Admission Review

- Direction: establish the actual invalidation and publication requirements for
  cross-process generated C reuse, beyond the existing native object proof.
- Prior evidence: 55 real module Scheme inputs cost 3.72 / 3.89 seconds versus
  C inputs 0.11 / 0.12 seconds, with byte-equal generated and linker code.
- Worth pursuing: this repeated work remains even when object reuse hits.
- Expected benefit: at most the measured generation difference for that set,
  less admission cost. No complete cold-build gain is assumed.

## Real Compiler Context Contracts

check_generated_c_context.sh invokes the isolated installed-profile GSC
directly. All five checks pass in .data/d1510-generated-c-context-v1:

1. Unchanged direct include and main source regenerate byte-identical C.
2. Changing the included file changes generated C while the main source digest
   remains unchanged.
3. Changing the command-line prelude macro changes generated C while the main
   source digest remains unchanged.
4. A macro emits an include form. Changing that dependency changes generated C
   although the unchanged main source has no literal include invocation.
5. A malformed included dependency makes GSC fail. The previously generated C
   remains present and byte-identical: GENERATION-FAILURE-LEAVES-OLD-C.

These are actual compiler observations, not a simulated cache or static text
scan. Therefore a main-Scheme hash, file existence or timestamp cannot certify
generated C. A textual include scan cannot discover the macro-emitted dependency.
An unsuccessful compilation must never publish a proof or admit the leftover C.

Gambit _front.scm normalizes prelude/postlude options. _ptree1.scm recognizes
compiler macro and include forms; _source.scm read-source handles resolved source
paths and include-expr->source reads included sources. Transitive source and
macro context must be represented by a real compiler dependency record, or an
unsupported path must use the original compiler without caching. Existing
static-object proofs do not provide this frontend dependency record.

## Private Emission Parity

check_private_c_generation.sh copies the same 55 paired ASCENT modules into a
fresh source directory, compiles them with the actual GSC, then generates C into
a private directory using -c -o. Every private C file matches its original-path
counterpart byte-for-byte. Linking the private C files yields identical linker
code when the link output path is fixed. Source hashes remain unchanged.

Passing output: .data/d1510-private-c-generation-v2, final marker
PRIVATE-C-GENERATION-PARITY-OK modules=55. This qualifies private emission for
this real input set; it is not a completed persistent cache or consumer build.

The v1 attempt passed all 55 module C comparisons but compared differently
named link outputs. Their linker code differs starting at line 2. The corrected
v2 keeps the same closure.c output identity and compares an immutable reference.
The failed v1 result is retained. Output/linker naming belongs in the generation
context rather than being omitted from a cache key.

## Implementation Boundary

Private generation is now demonstrated as a viable building block for a
transactional producer: retain the original source identity, generate into a
private output, validate source/dependency/compiler/context stability, then
publish only after successful compilation. Full dependency collection, cache
admission, locking and atomic object/proof coordination still require an
implementation and native failure/concurrency tests. No generated-C cache is
enabled, no unsupported macro/include path is silently reused, and no previous
package-cold rejection is reversed by these component controls.

The existing MCP first/cold/test gates and ASCENT full native Cases must be
rerun against any resulting integrated producer candidate before promotion.
