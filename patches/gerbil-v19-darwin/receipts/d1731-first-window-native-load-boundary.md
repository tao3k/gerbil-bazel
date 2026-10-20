# D1731: first-window source categories are not instruction latency

D1729 reuses the retained D1611 entry-gated hardware capture and its exact
native image. No build, profiler attachment or new timing workload is run.
It verifies the image SHA256 against the profile, disassembles the eight
largest native functions and maps every selected sampled PC to its exact
instruction and enclosing native function. All 1,454 selected PCs map.

Image SHA256:
`9fdc3e7b8f12139415c400dc6c9810ac95b5b6f9a30d479e2bae4eb0a56ca65c`.

## Instruction Boundary

| Native function | Non-SP loads | SP loads | SP stores | Conditional branches |
| --- | ---: | ---: | ---: | ---: |
| gb_coalesced_host | 61.0615% | 3.5793% | 0.0034% | 1.9053% |
| mark_array | 42.3316% | 19.4568% | 8.2758% | 2.4886% |
| mark_array.constprop.4 | 38.7004% | 15.0165% | 7.6996% | 1.6283% |
| ___gc_hash_table_ref | 40.7283% | 20.6062% | 0.1898% | 0.5038% |
| gb_trace_native_11 | 72.1959% | 15.2124% | 0.6120% | 3.0553% |

Percentages are sampled PC weights within each function, not time per
instruction, cache-miss rates, exclusive latency, or expected speedup.
The classifier recognizes scalar load/store families and SP-based addresses;
SP accesses include ABI state, saved locals and possible spills. It does not
prove all SP accesses are spills or all other loads are pointer chasing.
The original capture remains a perturbed diagnostic, not an uninstrumented
complete-build split or Darwin/Linux causal comparison.

This corrects a possible misuse of D1612: a source macro category such as
`___IF` or `___IF_NARGS_EQ` does not exclusively represent branch instructions.
Source-line weights cannot justify a branch-layout optimization by themselves.

## Source Connection

D1730 maps all 745 sampled host load PCs through the already byte-identical
debug object's DWARF lines. Source, mapping receipt, profile and instruction
audit hashes are checked. Actual examples include:

- A load `ldr x0, [x19, #0x68]` at an `___IF_NARGS_EQ(1,___NOTHING)` line.
  Current Gambit header definitions read `___ps->na` for arity tests and write
  it in `___SET_NARGS`. Caching it would require an explicit external-transfer,
  handler and callback coherence proof; no register-cache patch is admitted.
- A load `ldr x21, [x20, #0x18]` at `___JUMPRET(___STK(1))`.
- A load `ldr x0, [x19]` at an original `___POLL` line, and the corresponding
  load in the existing outlined helper's stack-trip eligibility guard.
- The largest sampled GC instruction is `ldr x19, [x23]`, at the marker's
  current-cell read, not proof that a scalar object-copy loop dominates.

DWARF attribution may reflect compiler-merged or shared code. No load is
ascribed exclusively to a Scheme procedure, and no correctness check, poll,
live root or runtime ABI field is removed based on this audit.

## Decision

Use actual load dependencies and their coherence boundaries when selecting
the next Gambit source transformation. Do not repeat branch-layout sweeps or
claim that register caching alone can eliminate the seven/eight-second prefix.
No performance patch is promoted. Historical full-build mean 52.617045 seconds,
55-second ceiling, genuine first-log and concurrent make/test gates remain.
The requested startup/build/test optimization is not achieved.

Private evidence and reproducible controllers:
`.data/d1729-native-instruction-audit.py`,
`.data/d1729-native-instruction-audit/`,
`.data/d1730-host-load-source-audit.py`,
`.data/d1730-host-load-source-audit/`.
Controllers use exclusive output directories and do not modify retained inputs.
No Gerbil, std/make, std/test, package, security-policy or Linux source is edited.
