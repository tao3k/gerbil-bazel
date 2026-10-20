# Compiled Native Digest: V9 Component Qualification

## Implementation

The optional `native-digests` build mode compiles the unchanged tracked Darwin
GNU-GCC SHA implementation into the private GSC entry. Activation requires
`GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1`; producer/link adoption still requires
the existing explicit native generated-C flag. Hashes cover the same complete
file bytes. Source/options/environment/tool identities and final revalidation
are not removed. Nonselected helper paths retain external behavior.

The FFI output buffer is now private to a lexical closure and always allocated
as a 32-byte Scheme vector; callers cannot supply an undersized buffer. This
source revision differs from the earlier dynamically loaded v4 fixture module.

The default preparation mode remains byte-identical to the v8 GSC source entry,
as checked by `.data/d1510-native-generated-c-source-default-v1`. The fastest
five-patch stack, installed tools and active consumer checkouts were not modified.

## Real 55-Module Component

These are retained ASCENT-generated paired sources, tested with the matching
MCP-baseline ABI. They are **not full MCP builds, complete tests or ASCENT suites**.
The direct Bash fixture compares all 55 producer C files and the complete
incremental link C with the original compiler. Native CLI adoption reports 55
inputs in each run; all byte comparisons pass.

| Receipt suffix | Native digest enabled | Original generation | Native generation | Original link | Native link | Original total | Native total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v5 | yes | 6.53 | 7.81 | 3.87 | 0.31 | 10.40 | 8.12 |
| v6 | no | 6.82 | 10.47 | 3.76 | 0.89 | 10.58 | 11.36 |
| v7 | yes | 5.80 | 7.80 | 5.89 | 0.49 | 11.69 | 8.29 |

All times are seconds. Receipt roots are
`.data/d1510-real-native-generated-c-gsc-v5`, `v6` and `v7`.
Totals sum generation and CLI linking; the separate diagnostic lookup is **not**
added a second time. Diagnostic lookups are 0.146306 / 0.743859 / 0.182858 seconds.
The same v9 binary is used for the on/off control. This supports eliminating
digest process overhead; it does not establish a stable whole-package multiplier.
Original link wall time fluctuates substantially, so retain both observations.

The enabled runs reduce serial component wall time by about 21.9% and 29.1%.
The disabled run regresses. Producer overhead remains positive even when enabled.
Unconditional dynamic-to-static adoption remains rejected, as documented in
`d1510-native-generated-c-ascent-admission-gap.md`.

Whole link C SHA256 in both enabled runs:
`f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`.

## Safety

`.data/d1510-native-generated-c-gsc-controls-v9` passes default/cold/repeat C
parity, CLI consumer adoption, changed static source fallback, debug fallback,
invalid producer-index fallback, failed compilation preserving prior output and
proof, and owned temporary/lock cleanup.

`.data/d1510-generated-c-compiled-digest-contract-v1` tests the compiled GSC
digest through the existing proof protocol: all 15 generation contracts and
both concurrent producer controls pass. Its output hash is
`9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`.

Focused native profile and frozen patch-lock tests: 16 pass. Shell syntax passes.

The extended CLI controls in `.data/d1510-native-generated-c-gsc-controls-v10`
also disable and restore the in-process flag: both transitions force MISS with
unchanged C bytes, proving that the backend environment switch cannot silently
reuse a prior context proof.

## Independent ASCENT ABI

The separately built `.data/d1510-native-generated-c-ascent-gsc-v2` links the
frozen ASCENT MULTIPLE_VMS/segmented-global-table headers and archives, not the
MCP binary. GSC SHA is
`a3362162b859c951ed1269ab148fc1015e3508bff803e2c7d469d83d018060da`.
`.data/d1510-native-generated-c-ascent-gsc-controls-v2` passes the native CLI
controls. Its actual source-component run is
`.data/d1510-real-native-generated-c-ascent-gsc-v1`:

- Original generation 9.25 + original link 9.15 = **18.40 seconds**.
- Native generation 11.27 + native link 0.69 = **11.96 seconds**.
- Diagnostic lookup 0.161303 seconds, not double counted.
- All 55 producer C files and the whole link C are byte-identical to this ABI's
  own original compiler. Whole link SHA:
  `5f8f90a4e9aee1b2c0fa975372254403fea8feb130da00de9f4c71edf54f1924`.

This single component observation saves about 35.0%, not a complete ASCENT
performance result. [Structured times and raw digests](d1510-native-generated-c-in-process-times.json)
preserve all four runs, including the disabled regression.

## Exact Identity

- GSC: `6493053bdc3c6f544e47642ba2de0888768010acad949351b6887d3b482d5d5c`.
- External helper retained: `1f81c3639b332dfa0cd5301b6487b4156c569357fbf4e8371c87d4ce9f0b95f8`.
- Native digest source: `4d1c5f71a0118471c61bb6aeb713cbf4aa85032c923f83036bae0cbbf43c1ca8`.
- Native install source: `36a87afc7084ccfba3088f16e1ccbfaf4677c45f3ec172311641b3f1d629345b`.
- Compiled contract adapter: `af443e0d51455e04c486eb2742014fbe5f11fb624fd2ed5957f89829ec4d70b1`.
- GSC entry source: `de4de52b594b20f68969b44c1d8ba3c2a4f812d6992691accee9628fd0963782`.
- Interpreter/CLI source: `1377f168f89d3bc92b665fede8109bed40e8264f670edfedc5ebc4837a65db0d`.

`identity.log` and `abi-identity.log` in the private build retain the executable,
header, configuration and linked archive identities. The entry was compiled
with genuine GNU GCC using the matching configured object rules and SDK.

## Remaining Admission

This candidate is not in `mcp-v4-driver.series` and cannot pass the existing v8
native profile by pretending to be that binary. Full consumer preparation must
explicitly bind the new source/entry identities and digest flag. Actual ordinary
dynamic library generation still needs a generic, ABI-preserving producer path.
Full MCP and isolated ASCENT correctness/performance gates remain unmet for v9.
The goal stays active and the frozen MCP ceilings remain 4.5/42/97 seconds.
