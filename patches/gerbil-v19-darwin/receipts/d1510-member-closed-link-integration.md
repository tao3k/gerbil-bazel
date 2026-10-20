# Member Closed-Link Integration

## Review

0041 packages the member coordinator and connects it to the existing Darwin,
explicit-binding closed-link CLI. It follows 0030 and 0040, preserves complete
ordered bindings, and is experimental. No MCP-specific package behavior is
introduced. The frozen six-patch MCP series is unchanged.

Selective invalidation remains the expected benefit. Cold generation is not
accelerated, and stable HIT has additional per-member validation cost. Do not
promote the component speedup to a cold-build or complete-test claim.

## Compiled Coordinator Safety

The external-process controls no longer rely on rebinding a compiled direct call.
They wait for a real first-member proof and active second-member snapshot work,
then atomically replace an earlier include or a tool-identity fixture file.
Both runs require exit 70 and the specific batch-context rejection, followed by
a fresh native process with exact ordinary C parity on both members.

`.data/d1510-member-external-controls-v4` passes both checks. Include mutation
retries with one MISS and one HIT; tool-content mutation retries with two MISSes.
Prior v1-v3 attempts reject mutation and preserve output correctness, but fail
the selective-HIT assertion because foreground/background launch changes SHLVL.
The final fixture explicitly aligns SHLVL and underscore environment values;
implementation environment admission is not weakened. Temporary diagnostic raw
environment files were removed, rather than retained as portable evidence.

The final CLI GSC also passes 11 compiled controls and two concurrent processes
at `.data/d1510-member-cli-compiled-controls-v1`, plus both external controls at
`.data/d1510-member-cli-external-controls-v1`. This proves coordinator-level
mutation rejection, not yet mutation safety across multiple CLI groups.

## Real CLI And Generation Results

`.data/d1510-member-cli-consumer-v1` passes 55 actual module inputs deliberately
alternating directories. Population and HIT produce exact ordinary C/flat-link
parity, identical complete ordered bindings, and 55 member proof files. Mixed
Scheme/C inputs and preload flags also preserve link parity. Disabled reuse and
unsupported options follow the ordinary path without a binding.

Population / HIT process times are 5.42 / 1.27 seconds. The same new GSC in the
original group mode at `.data/d1510-member-cli-default-consumer-v1` passes all
controls at 5.53 / 1.59 seconds and creates no member proofs. These are component
checks, not repeated whole-consumer performance samples or attributed gains.

The compiled API measurement at `.data/d1510-member-cli-real-compiled-v1` has
55-module ordinary full-generation and full-link parity, one MISS / 54 HITs
after one source change, and unchanged original input sources:

| Phase | Group proof (s) | Compiled member coordinator (s) |
| --- | --- | --- |
| Cold population | 3.903602 | 3.931255 |
| Stable HIT | 0.076804 | 0.205591 |
| One changed source | 3.840626 | 0.221787 |

This is one matched component sample. The stable HIT penalty is approximately
0.129 seconds. Cold population is effectively unchanged in this observation.

## Isolated Actual ASCENT

The first workspace preparation from the producer-recipe fixture fails the
existing read-only reference check for compiler/base. That partial copy is not
admitted and the checker is not relaxed. The next preparation uses the verified
closed-link fixture and a fresh COW workspace:
`.data/d1510-member-cli-ascent-v2`, project HEAD
`21e3638687d42ecfc36acebb28991987435ebc60`.

Its native cache is absent before the run. Actual GNU GCC and selected native
GSC execute through project-owned just/Scheme commands, with 12 detected build
cores, no Python test supervision, and the existing 135-second focused-component
deadline. Receipt `.data/d1510-member-cli-ascent-receipt-v1` records:

- Wall / user / system: **114.46 / 298.26 / 89.53 seconds**, exit 0.
- **30/30 Cases**, final OK and project PASS marker.
- One closed-link request, 224 selected inputs, 72 generated-C MISSes.
- 60 static-object MISSes; no generated-C or static-object HIT is recorded.
- After-run verification: 1989 runtime dynamic references and 2809 dependency
  references unchanged; source donor and isolated project tracked trees clean.

This is focused cold AOT correctness within its component deadline, not full
ASCENT suites, a matched speedup, or MCP qualification. Do not compare it with
44.55/50.48-second runs that reused an already compiled library. Whole-consumer
performance, cross-group CLI mutation/failure safety and release admission are
still pending. Both experimental runtime switches are selected in these runs;
the naive per-member-hashing configuration remains denied for promotion.

## Exact Identities

| Artifact | SHA256 |
| --- | --- |
| 0041 | `d56d3f9790301ca94756ab17430bc85adcb3e31415ee911055e3b8681a3b7a8e` |
| Native CLI GSC | `626d6d4934783f21d196053052cfeb387e6e9add133bb4ab852e1da8cbdb4257` |
| Compiled control identity log | `debceae318dd49f6112a9a4462c5eb01886c305376c234ebde363b9ab44dc4ae` |
| External control identity log | `210e359664a72676f6dcb017fa6c08adf343ef3a325242540e261ef65b933d2c` |
| CLI population/HIT binding | `5991ff464ddc57181462291ee04dc16ba72950e93c3f055da11d597787bd1b20` |
| ASCENT output log | `f6dff3b5b9b8ca01b02fd57204f70b40de88598bfed5c6690de2005d35cb7b2a` |
| ASCENT time receipt | `bc4099272a38024581c3a5d533d7d6e9c92a20668c3abab8e7d6fbdc52dde96e` |
| ASCENT toolchain identity log | `952f0e1fe21ca5b7c5a28e70a21995d8b75c6c79b29fa1bcd2359283df114e5d` |

Preparation/source-contract checks pass 18 focused tests, including complete
0041 reverse/forward replay and default constructor source-byte preservation.
The retained MCP identity/raw-report/performance lock still passes all three
samples at 4.5 / 42 / 97 seconds. No new MCP timing or GitHub delivery is claimed.
