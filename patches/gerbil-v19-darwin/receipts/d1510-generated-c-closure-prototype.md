# Generated C Closure Prototype

## Admission Review

- Direction: avoid actual repeated Scheme-to-C generation before native object
  reuse; use the demonstrated compiler source-read journal.
- Prior routes: missing-object overhead is small and not the main target. The
  object-only package-cold regression remains rejected. No whole-expander memo
  or timestamp-only C admission is retried.
- Worth implementing: 55 real module generation/link inputs showed about
  3.69 seconds of avoidable work, separate from subsequent C object compilation.
- Expected benefit: less repeated frontend/backend work, minus content admission
  cost. First proof population may cost more and must remain visible.

## Implemented Experimental API

gambit-generated-c-closure.scm provides reuse-generated-c-closure! for a closed,
fresh GSC adapter. It is not wired into the installed compiler or release list.
The implementation has no package-name tests and accepts arbitrary nonempty
sets of unique output module names. The 55-module inventory is a test fixture,
not a condition in the producer.

Context binds normalized input/output identities, primary source SHA-256,
options, current directory, system type, sorted environment and explicit tool
content digests. The test adapters supply the actual GSC executable, native SHA
backend, read journal, producer and caller script. A listed tool-content change
invalidates reuse. This is not a native compiler-upgrade consumer test.

The v2 proof schema stores only a SHA-256 of the structured context, not raw
environment values. Serialization uses a temporary file with mode 0600 inside
the owned lock directory; it is deleted immediately after hashing. Published
proofs also use mode 0600. Dependency/output paths and content digests remain
in the private local proof; these proofs are not exported into Git receipts.

A bounded directory lock serializes same-proof writers. Cache hits validate
the complete recorded dependency and output content and recheck tool contents.
Misses generate C privately, verify every before-read snapshot against current
source content, recheck primary inputs/tools/environment, then rename complete
C files and publish the proof last. Failed generation before publication keeps
old C/proof untouched and releases the lock. Unsupported nonempty options do
not cache. Source macro/namespace contexts do not cache and mark the GSC process
ineligible for subsequent hits; unsupported options other than the known pure
target-C selector also contaminate the process conservatively.

Individual C renames are atomic, not a single atomic multi-file transaction for
uncoordinated downstream readers. The closed writer test does not prove that
arbitrary consumers can concurrently read changing output paths. This boundary
must be addressed by the integrated adapter rather than hidden by the lock.

## Native Controls

check_generated_c_closure.sh, passing receipt
.data/d1510-generated-c-closure-contract-v9:

1. Actual repeat HIT; no generation work in the new private work directory.
2. Changed included source, unchanged main Scheme bytes: MISS and changed C.
3. Tampered published C: regeneration matches the original compiler byte-for-byte.
4. Nonempty option context: uncached generation, no proof published.
5. Listed tool file content change: MISS followed by a true repeat HIT.
6. Invalid dependency: old C/proof preserved, no remaining lock.
7. Compiler macro context: uncached generation, no proof published.
8. Subsequent ordinary input in the macro-contaminated GSC: still uncached.
9. Repeated warning-producing fallback: exact original diagnostic bytes,
   no cache proof on either call.
10. Environment change: MISS and changed proof, then a true unchanged-context
    HIT; proof stores a context digest rather than the environment structure.

Final marker: GENERATED-C-CLOSURE-CONTRACT-OK 10. Two independent native GSC
processes then request the same restored ordinary closure. Both succeed; one
MISS and one HIT, final C equals the original compiler reference and no lock
remains. Final marker: GENERATED-C-CLOSURE-CONCURRENCY-OK 2.
The shell verifier checks published proof mode 600 and absence of the injected
private environment name/value. The v8 attempt reached these MISS/HIT checks
but failed fixture cleanup: Gambit removes an environment binding with one-arg
setenv, not a false second argument. It was not admitted; v9 corrects that
documented API usage without weakening any assertion.

Earlier v1/v2 contract and real-probe preflight failures were Scheme parenthesis
and internal-definition placement errors, not accepted workloads; receipts are
retained. Subsequent revisions add real content and process-contamination
controls rather than repeating unchanged failed timing candidates.

## Actual Real-Source Cost And Parity

check_real_generated_c_closure.sh runs the 55 paired ASCENT sources in an owned
directory. Every published module C matches original GSC -c generation exactly.
The second call emits a true HIT and performs no source generation.
Current passing receipt: .data/d1510-real-generated-c-closure-v6.

| Phase | Measured Time |
| --- | --- |
| Original generation, whole native process | 3.68 s |
| First generation + proof population, API stage | 4.159404 s |
| Repeat proof-validated reuse, API stage | 0.312971 s |

The original figure includes native process startup; the two API timings are
wall-clock stage observations within one native process and do not include its
startup. This is a component comparison, not an integrated consumer result.
First population is about 0.479 seconds slower than the recorded original;
the repeat avoids approximately 3.37 seconds for this source set. No complete
build multiplier is claimed. Earlier lighter-key observations are not promoted
over the current primary-source-bound result.

## Next Integration Requirements

Current producer SHA-256:
`3f2439fddc145a2eb03f63d3451ecd2ef88414411b382334eb3ab5a0a67c7e0a`.
Contract source SHA-256:
`90992b8dcfb2fd6929004a0f3d6b36f80f618e73431db9963cc9cb6cf7192030`.
Contract-v9 output.log SHA-256:
`32029a345a61d1757a92e9a483b1d9a936ddaaa28b1318ab02be796b0d500d53`.
Real-source-v6 output.log SHA-256:
`2b8a3bbf002435200c782449a8673285978fb517ba395adb67ff85cce09801dc`.

The original driver gsc-link-options strips C compiler/linker options and keeps
Scheme-generation options. Its native runtime producer can supply explicit
module-ref/linker-name aliases and copy generated runtime C to static C. These
actual option and output relationships must be represented by an adapter; raw
CLI options cannot simply be passed to this prototype API or discarded.

Explicit warning-option diagnostic parity is covered above; default-option
diagnostic admission remains unproven. Remaining gates include current loaded-image identity,
arbitrary reader/compile-time context fallback, malformed/nonregular proof
controls, mid-flight mutation/publication failures, downstream reader safety,
and actual cross-process consumer invalidation. First population overhead also
needs reduction or an admitted producer path that eliminates duplicate generation
within a real build. Default enablement is not justified by this component HIT.

The prototype is not yet called by MCP or ASCENT's native Justfile qualifier.
The complete first/build/test gates therefore remain required against the
integrated candidate. Existing MCP receipts are preserved, and the ASCENT
package-cold rejection is unchanged. Active checkout/shared dependencies were
not modified, and Python never launches or supervises native tests.
