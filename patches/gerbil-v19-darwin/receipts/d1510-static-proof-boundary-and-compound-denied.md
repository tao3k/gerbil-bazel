# Object Proof Boundary and Compound Producer Review

## Actual Object Boundary

The corrected ASCENT qualification's 74 object MISS events comprise **57 native
capture events** and **17 native check events**. Capture means object or proof
was absent; check means both existed but full proof comparison rejected reuse.
The helper deliberately does not publish a proof for a first unbound compile
whose output is missing. Thus ordinary cold library production can leave an
object without a reuse proof. Do not describe all 74 events as redundant
validation or assume a cross-process HIT is available.

`check_static_proof_boundary.sh` uses real generated C from the compiled ASCENT
`core/binary-relation` SCM. The private diagnostic helper copies its exact sorted
environment and records CPP/key digests; it does not change cache admission.
The original producer compilation is first seeded, then these controls pass:

| Change | CPP digest | Object bytes | Cache result |
| --- | --- | --- | --- |
| Add only the expected-source SHA binding variable, same dynamic recipe | Identical | Identical | MISS |
| Repeat that exact bound recipe/environment | Identical | Identical | HIT |
| Change dynamic to static recipe | Different | Different | MISS |
| Repeat static recipe/environment | Identical | Identical | HIT |

Sorted environments differ only by `GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA` in
the binding-only pair. Removing this variable from a key alone is not admitted:
the compiler process currently receives it too. A future separation of proof
metadata from compiler environment would need to remove it from the actual
compiler environment as well, while preserving independent source-pin/binding
validation. Even that would not solve the 57 missing-proof captures or justify
ignoring genuine mode/option differences.

Successful receipt: `.data/d1510-static-proof-boundary-v1/run-v3`.
The first attempt referenced a generated C file already cleaned by ASCENT; the
second omitted ordinary object seeding, correctly producing no unbound proof.
Those setup failures are excluded. The successful run generates actual C from
the retained SCM and proves all five cache outcomes.

| Identity | SHA256 |
| --- | --- |
| Input SCM | `e3f2562690f42d97ff3a76f175635f2a8aa33c7adac3793d923083df002f2b27` |
| Generated C | `c32aaf784e326527c060312d3c2c7480218d19de058f584e763944b75f639e36` |
| Producer and bound-same-mode object | `83a4cc82ec8887b15389f5ec0d36336492300b1ff037317a52150bdf02ab4f1b` |
| Static object | `3bbaa1427e88f3a7a6a23ee9c24e3c6531295be2317a260d74d4c288247de820` |
| Producer context receipt | `9d170415ca1386c05c4d3885f362806cce3d8555ff6562b65a66192d3637e349` |
| Bound-same-mode context receipt | `04f9c7ac1848e8e6a1fca8c058dca6f60e40c60e03317a0fb90d92f524f20bbc` |
| Static context receipt | `0a19937ad7598909f7bb2adb1df4dad5515c125c092c3d95e92afe65b75029cb` |

## Compound Producer: Not Promoted

Review before implementation: Darwin production starts GSC separately for
SCM-to-C and C-to-object. Existing `compile-file-to-target` and `compile-file`
APIs can run sequentially in one GSC process without changing the compiler.
This is distinct from the denied eager-proof path. Expected benefit was one
less process/VM initialization; it was deliberately not assigned an unmeasured
percentage. The prototype is test-only, not a patch or an installed option.

Actual ABBA uses the same real compiled module, fixed input/output paths, module
reference, dynamic/PIC recipe, matching Multiple-VM runtime and genuine GNU GCC.
All generated C and object bytes are exactly equal across four phases.

| Phase | C generation (s) | Object generation (s) | Total (s) |
| --- | --- | --- | --- |
| Ordinary A1 | 0.20 | 1.65 | 1.85 |
| Compound B1 | Combined | Combined | 1.85 |
| Compound B2 | Combined | Combined | 1.84 |
| Ordinary A2 | 0.20 | 1.68 | 1.88 |

At this reporting precision, there is no meaningful speedup to promote. Do not
spend whole-consumer qualification on this unchanged standalone composition.
The prototype establishes API/byte parity, not native execution, arbitrary
compiler-option compatibility, failure safety or release readiness.
Receipt: `.data/d1510-gsc-compound-producer-control-v1`.
Exact common generated C SHA256:
`c598e51c8776a1012b06bcc65b3b5b2d6312f516043c1e991ec6dd586ac54c3d`.
Exact common object SHA256:
`a81c21f5411f2ef60be89b1a832eb2ac9d1bfe9991662f6c956b126170516f28`.
Both diagnostic Bash scripts pass syntax validation.

## GCC Cost Boundary

A separate ordinary object compilation of that generated C with GNU GCC
`-ftime-report` succeeds. GCC reports **1.24 seconds / 84%** in optimization and
generation, **0.23 / 15%** parsing, and **0.10 / 7%** preprocessing. Detailed
subphases overlap parent phases; their percentages must not be summed. This
is one module's compiler CPU report, not package wall time or first-log Scheme
macro expansion. It cannot establish the macOS/Linux ratio.

Raw stage report:
`.data/d1510-gsc-compound-producer-control-v1/gcc-stages.log`, SHA256
`e89746396d5c7c35b9d25a289d903008554385252be3a2da0dd08b4e38d2d638`.

The useful large-cost target remains preventing an unnecessary second GCC
optimization/code-generation pass when the full requested recipe genuinely
matches a proven object. Ignoring environment or mode is not that proof. The
next production-side design must account for proof availability and consumer
recipe identity without repeating the rejected all-producer configurations.
No frozen patch, policy, runtime or recorded benchmark bytes changed. The
active gates remain 4.5 / 42 / 97 seconds. Complete source-aware MCP still lacks
admission; the 30-Case ASCENT component alone does not close the thread goal.
