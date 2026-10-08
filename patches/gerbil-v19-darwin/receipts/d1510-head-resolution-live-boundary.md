# D1510 Head Resolution Live Boundary

No production candidate or performance gain is admitted. Historical cold builds
47.771713 / 47.824226 / 47.927094 seconds and whole-task gates 5 / 50 / 112
seconds remain unchanged. Stable complete-test admission remains unresolved.

## Failed Observation Preserved

The initial 29-case fixture tried replacing `gx#resolve-identifier` to observe
two head-resolution calls and mutate the binding after the first call. All
twelve processes fail the duplicate-call assertion after their first 26 cases.
The wrapper is not a valid probe for this native caller. This is a diagnostic
failure, not a runtime regression, nor proof that head resolution is pure.

Evidence: `.data/d1510-head-resolution-effects-v1/report.json`. The exact failed
fixture is preserved as `failed-fixture.scm` beside it, SHA256
`1de1d8a3fda6d350b855e45930e35656b9d8f67e3465942699a998f5319d53ab`.

The unchanged coalesced carrier at
`.data/d1510-source-loader-linked/gerbil-link.c:301365` directly transfers to
`gx#resolve-identifier__0` via `JUMPINT`; it does not read the replaced public
resolver global at this point. Similar direct calls exist in the native
bound-identifier helper. The corrected fixture observes zero public-wrapper
calls and one invocation of the original macro, with original form identity
preserved. Twelve processes pass all 29 ordered cases (348 total), final marker,
exit zero and unchanged binary/fixture hashes. Evidence:
`.data/d1510-native-head-call-contract-v2/report.json`.

## Reached Effect Between Resolution And Handoff

The terminal core-head path resolves a syntax binding, then invokes the live
`gx#core-expander?` predicate. Its generated call at carrier line 301375 is
`JUMPGLONOTSAFE`, unlike the internal resolver call. A new original-native
control replaces this actually reached predicate only inside `dynamic-wind`,
delegates to the original predicate and replaces the head binding in the current
context. The initial binding ID is `%#begin`; the replacement is another special
form. Original block expansion selects the replacement handler, rather than
splicing according to the stale `%#begin` binding. It preserves the body and
restores the predicate. No compiler, library or consumer source is altered.

All earlier cases remain. Twelve hardware-derived concurrent processes pass
all **34 cases each, 408 total**, with exact ordered identities, final marker,
exit zero and unchanged frozen binary and fixture. Evidence:
`.data/d1510-head-stop-live-predicate-v2/report.json`. The runner explicitly
sets child build parallelism to the observed physical core count. V1 also
passes; this contract does not launch child builds. The shared runner now uses
the Git-owned `gerbil_bench.execution` process controller and storage lease,
not the untracked historical experiment controller. This small diagnostic
creates no copied project or compiler artifacts.

## Four-Question Review

| Question | Answer |
| --- | --- |
| Is the path correct? | Unguarded terminal-binding transfer is not correct: a reached live predicate can change the binding before the caller re-resolves it. The original operation order is observable. |
| Already explored? | The architecture note proposed terminal result transfer but did not test this predicate boundary. The failed public-resolver observer is now explained, not replayed as attribution. |
| Worth optimizing? | NO to an unguarded reuse candidate. A guard would have to protect the relevant global and context mutations without bypassing their effects; this is a different, unqualified mechanism. |
| Expected benefit? | Unknown. Source duplication and these correctness checks establish no exclusive time budget. No seconds or factor forecast is justified; do not build a runtime candidate on this count alone. |

The code-versus-live-instance distinction remains useful architectural guidance,
but does not license caching an effectful instance operation. Neither 348 nor
408 passing diagnostic cases substitute for independent standard-library
build/test or MCP clean/build/full-test qualification. No unchanged MCP campaign
was launched merely to produce another timing number.
