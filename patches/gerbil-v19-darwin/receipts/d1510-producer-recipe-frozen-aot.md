# Producer Recipes In Frozen AOT

## Decision

Correct path: retain the actual successful worker recipe, not force every
selected object through a different static compilation. The latter failed the
MCP gate in the existing 0033/0034 receipts and remains denied. This integration
has not previously been qualified in the frozen AOT binary. Metadata alone has
zero expected speed benefit; a gain requires actual backend proof HITs that
avoid a second GNU GCC pass. Complete MCP and ASCENT admission are pending.

## Implementation And Construction

`build_fd_final_driver_native.py --closed-link-recipe-proof` requires the explicit
compiled donor and producer-proof selection. It composes 0039's tested executor
and driver changes without replacing the entire compiler. The AST merger changes
four existing executor definitions, adds two recipe entry points, and changes
three driver definitions. Every selected definition must occur exactly once;
the complete unselected AST must remain identical. Missing, duplicate,
pre-existing new definitions and disabled base merge are rejected.

Only executor/driver objects and matching link metadata are rebuilt. All frozen
provider and runtime objects retain their verified hashes; the original private
loader and eleven optimized coalesced modules are preserved. Imported references
are checked against explicit per-module allowlists, not accepted wholesale.
The isolated constructor completed at `.data/d1510-recipe-aot-mcp-v1` with genuine
Homebrew GNU GCC 16.2.0. Carrier compilation took 44.248 seconds; that is toolchain
construction time, **not MCP package build time**. Standard make/test import
smoke passes. No measured patch or frozen six-patch lock changes.

## Native Executor Qualification

`.data/d1510-recipe-aot-lifecycle-v2` passes enabled and disabled controls with
12 workers: two producers must overlap, incomplete/failed recipes remain hidden,
copied option snapshots and reads cannot mutate the stored recipe, and producer
or recipe failures propagate without releasing dependents. Function identities
for the executor, output-job API and recipe query are checked before and after
loading the contract, so dynamic replacement cannot masquerade as AOT evidence.
The focused AST/frozen-contract/driver/handoff/summary suite passes **35 checks**.

An initial control using Multiple-VM donor macro images was rejected as ABI
incompatible. Those images are not admitted. Single-VM metadata was subsequently
rebuilt with the frozen MCP compiler selected explicitly by `GERBIL_GSC`; a prior
invocation without that variable hit a removed embedded compiler path and failed.
The final controls use matching metadata and verify the linked AOT functions.
These are fixture/construction failures, not full consumer benchmark results.

| Artifact | SHA256 |
| --- | --- |
| Candidate binary | `acf1b2cc591b33da88fff73d97e0b95fd5126d569eacae1dbdd7f2bfd6510538` |
| Merged driver SCM | `f1a472a6f1f69b166e6431004ea9a2f539425dbf750fbbbcd64f94040a509e57` |
| Merged executor SCM | `063283cdf8449198a7360139baafcfdf78cd6d61962a46b252002c6bbc03c7ed` |
| Lifecycle identity log | `bb8f4fcbd3489f548815860b43d5ffdc2dabd18ff418190b899c86637f7b130b` |
| Disabled output | `bc9fea77d3d5938a283d52a189c0eb2fb0d2291ac0abbcf3af536f2ba40074e8` |
| Enabled output | `19986e0cdf2af231afdd20bcdb90e7a6dcd023b1c0b99c09457198a9ab0fea53` |

The next prerequisite is to prove a real AOT producer/consumer object handoff
under unchanged and changed options, then compose the validated Gambit backend
before running whole MCP gates. This construction and executor qualification
alone do not establish a speedup, complete consumer correctness or release
admission. Frozen MCP remains 3.950--4.038 seconds first log, three cold builds
36.414/35.552/37.770 seconds, and full tests 86.924 seconds (39 files/965 cases),
with unchanged per-sample gates **4.5 / 42 / 97 seconds**.

Subsequent actual AOT controls pass same-recipe HIT/object/proof parity and
changed-option rebuilding (reference 17, candidate 29) at
`.data/d1510-recipe-aot-handoff-steady-v1` and
`.data/d1510-recipe-aot-handoff-options-v1`. Their identity-log digests are
`82bcdffc86a1ecc017d8ebf1703b8a03a544c052b6f5097c1dc2bdf14a5e99a8`
and `4bd8cefff473c1e8a0368b5b895c2402dff6258a62dd97555e98b95c9ffaf14f`.
All 46 frozen native inputs and 280 providers remain byte-identical. Whole MCP
still fails the 42-second gate; see the
[compiler-prefix correction and denied receipts](d1510-native-compiler-prefix.md).
