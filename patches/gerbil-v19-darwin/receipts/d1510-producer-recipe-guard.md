# Producer Recipe Guard

## Admission Review

Correct path: reuse a producer object only under its actual successful worker
recipe and a complete backend proof. The options-change native control already
rejected the 0037 fresh-object bypass: a default dynamic producer returns 17,
while an executable consumer using `-U___DYNAMIC` requires 29. Both the original
reference and the fresh bypass returned 17. This is an existing reference gap,
not proof of a new regression or a license to bypass validation.

Already explored: all-producer 0034 capture and unchanged MCP native capture /
check waves failed the fixed build ceiling. They remain denied. This guard is
not a retry of those MCP configurations. It composes with 0038, which removes
the independently demonstrated binding-only false MISS without omitting any
actual GCC environment field from validation.

Worthwhile: safe dynamic-object handoff requires matching the consumer options
to the successful producer options, rather than trusting a filename or queue
registration. Expected direct speed gain from metadata is zero; any gain must
come from genuine full-proof HITs avoiding another GNU GCC optimization pass.
No whole-consumer speedup or release admission is claimed for this patch.

## Implementation Boundary

Experimental `0039-gerbil-darwin-producer-recipe-guard.patch` follows the
0034 compiler donor, **not 0037**. Enable explicitly with
`GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF=1` alongside the producer-proof and
closed-link switches. Existing executor/result structure layouts are unchanged.

Only Darwin opt-in workers evaluate the recipe callback. They snapshot copied
option strings under the actual captured compiler parameterization before
executing the producer. Publication occurs only on successful completion, under
the existing executor mutex and before releasing dependents. Recipe reads
require completion without failure and return new copied strings. Pending,
failed, disabled and non-Darwin recipe queries return false. The existing
registered-output query keeps its prior semantics.

The closed-link consumer uses the dynamic producer recipe only if its current
GSC C options match the recorded options. Otherwise it follows the static
consumer recipe and lets the backend invalidate / rebuild normally. Source,
CPP, actual environment, options, object and tool-content proof remain required.
There is no fresh/timestamp-only acceptance, package identifier or special-case
test shortcut in the patch. Actual Linux execution has not been qualified.

## Source And Native Identity

| Artifact | SHA256 |
| --- | --- |
| `0039-gerbil-darwin-producer-recipe-guard.patch` | `1086c89b116aea1fade942946cac8ebaacd804749d566e2e32d44ea20a6fb3af` |
| Candidate `compiler/base.ss` | `f5826c63e04e72a84c73dc69b2dc408ee76fb00942ac807fcff00e3ffabd049f` |
| Candidate `compiler/driver.ss` | `8e14d27881c452f31cf970791b05872801851feab54cc3af6e3d05d9453c954e` |
| Compiled `base~0.o1` | `c564b5a5e6f1e24f451d3600775a02d93aabdacd01ea45ebbb57ab70994d394b` |
| Compiled `driver~0.o1` | `4a59873889caf8e6c5ce443ed90be4c00b11152d493693da5359390c377c428a` |
| Selected Multiple-VM GSC | `7f8423a0c1ab30313cd37b6482d1b931a076a6d91c5a9c2527664b3d897aeeff` |
| 0038 installed backend helper | `6b071f05f5e92bacba23c67b9825dbef2e89634a8d63580da9871ccb2ed82dd9` |

Source donor: `.data/d1510-gerbil-producer-recipe-driver-v1`.
Native control home: `.data/d1510-producer-recipe-ascent-home-v1`.
Both compiler modules compiled successfully using actual Gerbil and GNU GCC.
The qualification launcher loads these two compiled images; it is not a rebuilt
published AOT runtime. No single-VM MCP GSC is substituted for the ASCENT VM.

## Actual Controls

| Receipt | Result |
| --- | --- |
| `.data/d1510-producer-recipe-steady-v3` | Reference / candidate both 17; exact producer / consumer object bytes and candidate proof bytes; candidate backend HIT; two GSC object calls, not two GCC object compiles |
| `.data/d1510-producer-recipe-options-v2` | Reference 17, candidate 29; candidate object differs after actual consumer option change; `PRODUCER-RECIPE-OPTIONS-OK` |
| `.data/d1510-producer-recipe-lifecycle-v2` | Enabled / disabled native worker-pool contracts pass; 12 configured workers; barrier requires two producers overlap; pending / failed recipes hidden; snapshot and read mutations isolated; `#f` producer and recipe failures propagated |

Receipt identity-log SHA256 values in that order:
`0b48fc68738d91bd50316c958ada067265ca611b3e7df70322b86df6bdc859a0`,
`5ac83f3adf04333c579ac9369a04dd6c29f06b054d39c5c1da1b7bd15dc52e25`,
`5b13fa734f20966a0924af58c5255147e70e3d56f01a3027f813fdff1bc7db0a`.

The pre-existing native output-dependency contract also passes with the new
images and recipe switch enabled: early / late subscribers, multiple outputs,
duplicate producer rejection, unknown dependency rejection and raised `#f`.
The focused producer harness tests pass 12 checks, including forward application
of 0039 with exact two-file source parity and reverse restoration. Bash syntax
validation passes.

The first steady receipt v1 compiled and ran native 17 with a real HIT, but its
combined stdout / stderr corrupted the command-count line. That receipt is not
admitted. Stream separation retained both count and backend-marker assertions;
final v3 uses the current images. Original options-change control v1 used the
same logic but printed an incorrect generic parity label; v2 now explicitly
reports the intentional 17 / 29 difference.

## Pending Consumer Admission

The six-patch MCP lock remains unchanged: first **3.950--4.038 seconds**, cold
build **36.414 / 35.552 / 37.770 seconds**, full test **86.924 seconds**, all
**39 files / 965 cases**. Whole-task gates stay **4.5 / 42 / 97 seconds**.
0039 is outside this lock. It requires fresh whole-MCP evidence before promotion.
Isolated real ASCENT cold AOT Cases and full ASCENT closure admission are also
not implied by the small native controls above.

## Real ASCENT Cold Result: No Reuse Gain

Terminal receipt `.data/d1510-producer-recipe-ascent-receipt-v1` runs the
repository's own `just test-native` / Scheme qualifier directly, with a
135-second whole-component deadline. No Python process supervises the native
run; `experiment_framework/native_receipt.py` reads only the terminal files.
The clean isolated consumer retains HEAD
`21e3638687d42ecfc36acebb28991987435ebc60`, uses 12 build cores, and has no
pre-existing native-library cache. Original toolchain / dependency references
were verified before replacing only the fresh copy's compiler images, launcher
and helper. Original checkout and shared dependencies were not modified.

| Metric | Actual result |
| --- | --- |
| Complete cold preparation plus focused test | 110.32 s |
| User / system CPU | 292.33 / 80.86 s |
| Correctness | 30/30 Cases, final OK, exit 0 |
| Closed-link selected inputs | 224 |
| Static-object reuse | 0 HIT / 74 MISS |
| GSC object calls | 74 |
| Generated-C events | 0 HIT / 8 MISS |
| Native entry | Cache MISS |

This is a focused cold AOT result, **not all 94 Suites**, an improvement claim,
or admission under the MCP gates. It must not replace the frozen MCP numbers.
There is no matched old/new pair establishing an effect on this duration.

The actual source boundary explains why the single-executor recipe control
does not transfer automatically. `t/native/qualification.ss` runs library layers
in separate compiler child processes through ordinary library-only `std/make`.
Its `compile-test-layer` request has no executable specification. The unchanged
`std/make` policy therefore passes `static: #f` to `compile-module`. The recipe
mode also clears the native-generated-C switch. Consequently these producers
do not enter `gsc-compile-file`'s static-runtime-object branch, nor register the
output recipes required by 0039. Later executable compilation is a separate
phase, without those executor records. Its 74 object requests legitimately take
the static fallback and compile, rather than reuse nonexistent producer proofs.

This library-only eligibility boundary was already recorded in
[0022's integration evidence](d1510-library-native-producer-integration.md).
The present cold launch is consequently **not a performance test of successful
producer handoff**, even though its native Cases pass. Do not repeat this
configuration to look for HITs, expand ephemeral executor metadata into global
unchecked state, or enable rejected all-library capture without reviewing its
recorded costs. 0039 remains a separately tested safety building block; a real
cross-phase mechanism needs explicit, content-proven production and consumption.

Terminal summary: `.data/d1510-producer-recipe-ascent-cases-v1.json`, SHA256
`a4db1ca04554d59c1bf737120c66e50ed4de57ad36b9b97631f57096201ad772`.
Raw output SHA256:
`455bffff83dea825f10f80e6c53ae389435b0cfe51ca3ba40ff234acb487493f`.
Time receipt SHA256:
`44f9ee304fc714a262de8c0e392b3a039ce0804bf24cc78cab02667e35a165ab`.
Toolchain identity-list SHA256:
`97ccf819cf954ac1c6088346918d0f0d915755328d0c09e7ec4a77ec194ceb91`.
