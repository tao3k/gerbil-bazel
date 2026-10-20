# D1371: existing first-window and CI coverage

## Purpose

Keep retained evidence tied to its actual executable and workload before
selecting a Darwin-specific major-cost patch. This is an identity/coverage
audit of existing records and the user's referenced CI, not a new test,
baseline campaign or speedup. No source or flag experiment is admitted.

The durable audit is under `.data/d1371-existing-evidence-coverage/`.
Current executable hashes match all retained image identities checked by
the audit. The exact-head CI workflow, installer and suite are retained
there as read-only source snapshots; neither repository is modified.

## Two local profiles are not interchangeable

| Record | Execution | Executable SHA-256 | Scope |
| --- | --- | --- | --- |
| D1102 | Original 187-module passive MCP preparation | cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928 | Diagnostic preparation, not official first-log timing |
| D1220 | Actual official MCP build, composition candidate | 6c50ce6cad0d8bbb984e2d39bd0f0196aaa61b3ef8712e05c9a129e94e08dafc | Partial pre-first window, first compile 19.716867 seconds, strict gate failed |

D1220's active-cycle record has a coalesced host and a packed startup image.
It is not the original executable's seven-to-eight-second prefix. Its
previously recorded expander/GC hotspots remain usable diagnostic inputs,
but do not qualify the candidate or attribute the original prefix.

D1365-D1370's original-object/linked-code checks remain valid within their
declared original-code scope. D1366's passive loader cycle shares must not
be turned into an upper bound on official first-log wall time. In particular,
4.897 percent dlopen-inclusive cycles in passive preparation does not prove
that original official startup spends only 4.897 percent in loading.
Likewise D1220's coalesced-host cycle share must not be attached to original
individual host functions. No actual original first-window timing is replaced
with a synthetic preparation number or an overrun composition receipt.

## Exact referenced CI

Both jobs use gerbil-parser source head
`f35b14193db7cfc89444b0f9a82b81c3862bc795` in run 37192692593 and finish
successfully. GitHub step timestamps give 273 seconds for the whole
[macOS Native step](https://github.com/tao3k/gerbil-parser/actions/runs/37192692593/job/111408043087)
and 113 seconds for the matching
[Ubuntu Native step](https://github.com/tao3k/gerbil-parser/actions/runs/37192692593/job/111408043179).
This confirms a substantial existing disparity. The approximately 2.42
whole-step ratio is not a per-case ratio and does not contradict larger
startup/per-case differences recorded elsewhere.

The exact-head installer pins Gerbil revision
`2591dcd9b7c6d2c4e9dd8611a17c5b1a5d82bbdb`, with separate Linux-x86_64 and
Darwin-arm64 release assets and SHA-256 checks. The exact-head suite launches
one gxi child per test owner, watches actual child output with a five-second
silence limit and a 90-second batch limit, and requires cases plus final
status. These are existing consumer contracts, not new proposed changes.

The referenced run is not a latest-staging execution profile and supplies no
matched native-PC or exclusive platform-cost attribution. Its release
revision differs from the canonical staging identity used by the current
source investigation. Its elapsed test step includes repeated startups,
imports, tests and final collection. Do not identify that entire time as
macro expansion, dyld work or a particular GCC/ABI instruction sequence.

## Consequence for optimization work

The Darwin test/build disparity remains a required target, not something
dismissed by this audit. Existing Native loader improvements retain their
original qualification boundaries. Neither their ratios nor recent passive
CPU census numbers close the current MCP requirement. The next source patch
must have relevant cost coverage and preserve the actual unchanged output
gates; no standard library/consumer edits, flag sweep, reordered first log,
synthetic progress or cached substitute is introduced here.
