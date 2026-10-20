# D1510 bounded marked-tail cursor: DENY

## Distinct source hypothesis

The original syntax-split-splice->vector consumes both fields of syntax-e,
then traverses the newly wrapped tail again. Historical D1344/D1345 counts
record 834,790 result-pair returns into this consumer. Those counts are not
new candidate coverage, removable-byte proof, or current timing.

The isolated prototype handles only suffix zero and an exact syntax-wrap
whose body is a raw pair. A cursor keeps one mark and raw tail, creates the
original marked head, and materializes the final returned tail. Structured
tails, nested initial wrappers, nonzero suffixes and changed canonical
bindings resume the original loop. Binding checks remain inside the traversal;
a changed binding after head evaluation retains the original tail fold.

This is not the rejected unused CAR/CDR field projection, adjacent mark
cancellation, mark-fold dispatch specialization, returned-pair-only elision,
GC tuning, or an unbounded virtual-wrapper representation. No persistent
result cache or consumer change is introduced. That distinction justifies
one new experiment, not repeating it after rejection.

## Construction and controls

Only the generated expander stxcase module changes. The original eleven-module
guarded-outline recipe, retained 0018 compiler driver, 0015 command driver,
original GSC, GNU GCC, runtime archive and single-VM profile remain selected.
Physical worker count is twelve, discovered from this host.

Construction directory: `.data/d1510-splice-cursor-native-v1/`.
Candidate SHA256:
`44cf606cbe1688a9549de06f67d84c6087646a46ed3b1bade2734e454f62eb17`.
Original input hashes are verified unchanged. Construction and framework
import succeed. Native carrier compilation is construction, not MCP time.

Sixty-eight controls pass on the native candidate against the original
generated lambda evaluated as a reference. They cover input/suffix shapes,
marked and dotted tails, nested wrappers, cancellation preserving existing
identity, no input-spine mutation, live results across GC, terminal source,
rebound fold effects and exceptions. They are focused controls, not complete
interrupt, continuation/debug, FFI, or product-test conformance. Four source
tests also check actual preprocessor platform selection and bounded fallback.
Only Darwin/Mach with GNU and without clang selects the prototype.

## Real progressive admission

Receipt: `.data/d1510-splice-cursor-progressive-v1/`.
Fresh unchanged MCP checkout, official gerbil clean then build, retained
selected-toolchain identities and the new runtime watchdog:

| Measurement | Result |
| --- | --- |
| Official clean | 5.041994 s, exit zero |
| Native images after clean | 0 |
| First-compile deadline observation | 5.549435 s, no compile line |
| Forced termination | SIGKILL, terminal status -9 |
| Attempt including reap | 5.558481 s |
| Complete cold build | Not available; deliberately interrupted |
| Complete gerbil test wave | SKIP; cold gate DENY |
| Cleanup errors | None |

The observation interval is polling, not permission to widen the 5.5-second
gate. Do not publish the partial attempt as complete build/test timing, or
infer regression causality by comparing it to another historical batch.
No successful speedup or actual hot-path coverage is established. This exact
cursor prototype is closed; do not expand or retune it on the main line.
The frozen 49-second binary remains untouched and unqualified for full tests.

## Additional reuse boundary checked without another rebuild

Existing candidate MCP phi files contain real generated syntax transformers:
175 MCP ~1.scm files contain lambda forms. The proc and registry examples
include fresh syntax-quote construction, contextual mark deserialization and
actual transformer procedures. They cannot be classified as pure loaders or
shared merely because printed scaffolding looks alike. Global names, captured
expander context, fresh-object identity and rebindings are observable.

No phi-source shortcut, cross-module transformer sharing, speculative object
cache or new full toolchain build is admitted by this source check. Future
reuse work needs exact equivalent-code and identity/capture evidence first.
