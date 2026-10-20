# Native GSC MCP First-Log Gate

The real MCP progressive framework now accepts only the explicitly locked
native experiment profile, checks driver/helper/GSC bytes and compiled/tracked
Scheme source before and after execution, and propagates the same choice to
the full-test phase. Native and rejected dynamic-wrapper options are mutually
exclusive. The selected GSC hash may differ from the original only through
that lock; a general compiler identity bypass was not introduced.

The active policy remains 4.5 seconds first compile, 42 seconds whole cold
build and 97 seconds whole tests. No thresholds were widened.

| Run | Observation | Decision |
| --- | --- | --- |
| Native v6 MCP candidate v2 | No first compile by 4.541035 seconds; stopped/reaped by 4.550713 | DENY |
| Exact frozen v4 control v1 | No first compile by 4.519932 seconds; stopped/reaped by 4.530706 | DENY |

Both official clean operations succeeded with zero retained native images.
No complete build duration exists for either interrupted attempt. Full tests
were skipped, not passed. The frozen control also fails the current first-log
gate, so these two observations do not establish candidate-specific regression
or a new optimization. No unchanged candidate repeat is admitted.

The initial sandbox attempt v1 did not launch a build: real Darwin memory
discovery was denied by sandbox permissions. V2 ran with the permitted host
capacity discovery; no fabricated capacity values were substituted.

Candidate raw report SHA-256:
`d2b69e22b675199f642d70a2c65cebbed61a156b952a3f60f8a0eff15594c762`.
Frozen control raw report SHA-256:
`f8e241f14a6bbf96e20b393a9362aa71a0c771e59b0c5e0f2ec1e6fcd92539e1`.
The new profile identity/drift and existing cold/full-test/patch-lock focused
suite passes 36 tests. Historical best measurements remain untouched.

Separately, native GSC build inspection found that the handcrafted object
compiler command omitted configured FLAGS_OBJ, including explicit sibling-call
optimization required by the trust-C-TCO configuration. The build script now
uses the original configured Makefile object rules (with matching config header
and explicit SDK), rather than approximating those flags. Freshly generated C
is explicitly retained for these object-only make targets. This is a build
correctness repair, not evidence that it resolves the first-log failure.
The v6 lock is not silently updated to admit a rebuilt binary. A new build
must independently pass native controls and receive a distinct identity before
consumer qualification. Both complete consumer gates remain unproven.

Fresh build v8 successfully compiles through the original object rules,
including explicit sibling-call optimization, and passes all native CLI
controls in `.data/d1510-native-generated-c-gsc-controls-v8`. Its GSC SHA-256
is `48d50acad500dda9457d45e8ae4a818d276384d68be68a397b95f5709a274091`.
The earlier v7 object-only make attempt stopped on an absent header prerequisite
in the deliberately minimal fixture; v8 marks the already-generated C files
as supplied inputs to those object-only targets. No source prerequisite is
silently skipped during C generation. The profile lock still identifies v6;
v8 cannot inherit its component results or pass profile preflight by accident.
No new MCP or ASCENT end-to-end performance result is claimed for v8.
