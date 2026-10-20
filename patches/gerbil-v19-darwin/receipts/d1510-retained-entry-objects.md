# Retained Entry Object Feasibility

## Review

Gerbil's separate compiler deletes executable entry C and object files after
successful linking. Missing objects cannot use the frozen existing-object proof
path. Prior closed-link work identified deleted stub C, but its integrated MCP
route failed performance admission and remains denied. This control instead
tests ordinary regenerated C against retained objects, without changing
generation, grouping, timestamps, ordering or proof validation.

The actual ASCENT diagnostic has four GCC-object invocations occupying a
15.14-second union. This is a possible investigation boundary, not proof that
all four are entry stubs or a promise of equivalent savings. Interleaved verbose
logs cannot reliably assign all invocations. True package-cold builds have no
retained objects and cannot benefit directly from retention. No implementation
cleanup change is admitted by this experiment.

## Native Controls

`tests/check_retained_entry_objects.sh` launches the isolated Multiple-VM ASCENT
GSC/GNU compiler directly through Bash, using the unchanged six-patch helper.
Fixtures are ordinary Scheme with no consumer-specific package logic. All
outputs are in a fresh owned receipt; active checkouts and shared libraries
are untouched. No Python supervises native execution.

`.data/d1510-retained-entry-objects-v3` returns zero and proves:

- Regeneration from identical Scheme gives byte-identical entry/linker C.
- Both retained objects HIT and remain byte-identical.
- Two concurrent calls on one object HIT with exact object parity.
- A real native executable returns zero and prints **17**.
- Actual source change to **42** regenerates different C and triggers MISS.
- The changed object matches ordinary compilation with reuse disabled.
- The changed native executable returns zero and prints **42**.

Bash syntax validation passes. This is not complete ASCENT Suite qualification.
The ordinary missing-object source-ABA defect remains separately unqualified.

## Timing And Negative Evidence

| Small fixture object | Proof population | HIT |
| --- | ---: | ---: |
| Entry C | 0.52 s | 0.60 s |
| Linker C | 0.81 s | 0.46 s |

One entry is slower on HIT. These single component samples do not establish
general performance gain or predict whole-consumer improvement.

V1 passes only regenerated-C/two-object-HIT/native-value controls. V2 exits one:
its source-change assertion expected MISS after `gsc -exe` had removed the
proof. V3 explicitly restores the existing-object proof before changing source.
The failed V2 is retained and excluded, not rewritten as a pass.

## Identities And Next Gate

The executed v3 runner is archived as `runner.sh`, SHA256
`c4602685abd6da0b5ac148b1539f9fd5f0aeff2f7f342abae97d1cf6e0659c02`.
Generated entry C SHA256:
`5ba6669cfd714c9f1294cca9854f450fd4404b946810152098623c916ca0f4a0`.
Linker C SHA256:
`8b9baf5679aced8823016a8d898061139dc43c13d8f8784de653e75f370ff4d0`.
Changed object SHA256:
`82444fb488a66bb87dc026901b5c7a4a966148c715fa97bc9460bdf72f74efba`.

Next gate: an opt-in Darwin-only cleanup candidate on an isolated copy of the
frozen compiler, not the denied closed-link donor. Keep Linux cleanup intact,
retain failure/locking guarantees, and validate changed entry C fully. Matched
real ASCENT rebuilds must reduce actual compiler calls and whole wall time;
complete MCP cold build/test gates must remain passing before promotion.

Frozen MCP identity and retained performance verification still pass: first
**3.950-4.038 seconds**, cold **35.552-37.770 seconds**, complete tests
**86.924 seconds, 965/965**. Limits remain **4.5 / 42 / 97 seconds**. No new
whole-consumer timing, implementation patch, promotion or GitHub delivery is
claimed here. The full goal remains open.
