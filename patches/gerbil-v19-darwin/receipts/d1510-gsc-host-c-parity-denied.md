# Compiler Host Substitution: Not Admitted

## Pre-Code Review

The hypothesis was that a standalone SINGLE_VM compiler host might generate
identical target C for a MULTIPLE_VM runtime. Target runtime flags and ABI must
not change; no compiler object/archive ABI mixing is permitted. Existing
component timings were from different contexts, not evidence of this hypothesis.
No host-only comparison was found in the scoped native generated-C receipts.
Potential benefit was unknown pending same-input comparison; a cheap byte gate
was required before any toolchain substitution or complete consumer timing.

## Real Source Evidence

The Bash fixture `tests/check_gsc_host_c_parity.sh` copies the 55 retained real
ASCENT-generated Scheme files. Both original compilers receive identical input,
output filename, target and paired module/linker alias. Each compiler executes
with its own matching runtime paths. No native generated-C producer is enabled.
The intended ABBA comparison stops on the first complete-C byte difference.

Private receipt: `.data/d1510-gsc-host-c-parity-v1`.

- Reference GSC SHA: `dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`.
- Alternative GSC SHA: `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
- Input manifest SHA: `ed4d89f06e2985ce216b6b989759af321573da2e7aaf742958db91bd94ba7c80`.
- A1 generates all 55 modules in 6.32 seconds (4.95 user / 0.63 system).
- B1 stops at `gerbil-ascent__core__relation-view`; ABBA and linking do not finish.
- Reference C SHA: `de35a977750b71554440a2739924bda84878267d70c18df48a0d3c66e839ef17`.
- Alternative C SHA: `df43b08d78e0c221265c1cd4aec320d726c4c92145e0cd10fd5fcde96cea40e0`.

This is a real optimization difference, not removable path metadata: the global
count changes 190 to 189; label count 766 to 786; the alternative omits the
`##structure-instance-of?` global call and changes generated control flow.
The owned MCP compiler source `_prims.scm` contains a Darwin-only primitive
expander for that operation (source SHA
`294de392a458f34ca7d08f79dcad38a7081d0b46a702535796ee643c21947374`).
This is an observed confound, not proof of the exact cause of every byte delta.
The two archived compiler binaries cannot establish a VM-only performance cause.

## Decision

**DENY direct substitution of these existing binaries.** No B1 completion time,
ABBA multiplier, target-runtime load correctness, complete build or test gain
is claimed. Do not rerun the unchanged pair or strip differences to force parity.
A future host-only study needs matched compiler implementation and source
identity first. This failed comparison does not prove host/target independence
impossible, nor does it qualify any existing native reuse candidate.

The retained fastest MCP patch series, runtime and 4.5 / 42 / 97-second limits
are untouched. V9/V11 whole-consumer DENY routes remain closed. All native
processes in this experiment have exited. The shell fixture subsequently gained
explicit failure/exit receipts; that formatting change is not a rerun.
