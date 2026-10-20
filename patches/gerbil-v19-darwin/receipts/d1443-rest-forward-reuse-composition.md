# D1443: measured rest-forwarding/object-reuse composition, not delivery

## Later Read-Only Frozen-Input Applicability Audit

No rejected candidate is rebuilt, activated or measured. The pending request
to requalify on the frozen 47-second composition remains unanswered.

Current stx/core/mop/util runtime SCM hashes match all four D1436 inputs, and
each disabled generated C file still matches its current original static C
byte for byte. Comparing disabled and enabled files also finds identical
symbol/global/constant/label resource counts, complete label-descriptor sections,
ordered label declarations and module-level register maps. Host-label counts
are respectively 582, 1828, 1913 and 1252. This rules out input drift and label
renumbering at these standalone generated-C boundaries only.

The retained coalescer's `context` function assigns module-private aliases,
per-module label offsets and shared-host register maps. Its `render` function
also injects the retained guarded helpers into original bodies. Consequently
D1436's independent native objects are not demonstrated drop-in replacements
for the frozen carrier. Standalone descriptor parity does not prove that
regenerating a carrier preserves all admitted helper selection, metadata,
global identity, polls or continuation roots.

If requalification is explicitly approved, construction must first reproduce
the unchanged complete carrier/control and retain the existing helper inventory.
Only then can isolated enabled construction, semantic checks and the original
5/50/112 gates test composition. Do not skip that proof, widen a deadline,
delete a helper or promote the old pair/allocation counts to elapsed savings.
This audit supplies no new source transformation, binary or timing, and does
not reopen this rejected route on its own. User-owned AOT/CI and production
patches remain unchanged.

## Complete Original Carrier Source Reproduction

A 2026-10-08 original-only follow-up uses the existing coalescer, all eleven
original selected C units, the retained original linker source and the exact
retained source-loader options. It does not substitute enabled rest-forwarding
units, activate that candidate or run another performance campaign. Permission
for one strict combination requalification was requested separately and is
not inferred from this control construction.

The first raw-source comparison is false, despite unchanged input hashes and
eleven byte-identical generated module metadata files. Its report remains
`.data/d1510-carrier-control-source-parity-v1/report.json`; it is not rewritten
as a pass. A second output retains the full regenerated carrier for inspection.

The differences arise from `context` iterating a Python private-name set when
building its alias dictionary: independent macro definitions have different
orders across processes. There are also eleven output-directory-specific
metadata include paths. Sorting only the 22 maximal runs of private alias
definitions, and substituting only the verified output directory, makes the
complete carriers byte-identical. Every included metadata file was checked
byte-identical separately. No executable body, guard, helper, label, constant,
poll or register map is removed by that comparison. The comparison does not
sort instructions or general preprocessor directives.

Evidence: `.data/d1510-carrier-control-source-parity-v2/report.json` and
`permutation-parity.json`. Frozen raw carrier SHA256 remains
`59385f75b21bf17f517f6752b5641b955e14cbafcad330d8f70a80cf17a3ecc4`;
the narrowly normalized source SHA256 is
`b1ca4353d909038b8088866d15be1f508061395c5122d9f8ba27d2591bfe7dcf`.
The normalization is only a source comparison, not a claim that independently
compiled objects or a linked runtime are identical. Native object control
must be examined separately before any candidate composition.

This resolves the source-level preservation question for the **original**
carrier. It does not establish preservation after inserting rest forwarding,
resolve the earlier standard-library slowdown or admit that old candidate.
The current 5/50/112 gates and frozen runtime remain unchanged.

The original-only object control then completes with GNU GCC 16, the retained
O1 recipe and diagnostic stack/RTL options. `inputsUnchanged` and
`objectMatchesReference` are both true: the entire object, not just its text,
matches frozen SHA256
`758c3dfd962ae0d5b4fc9631ad426173464076852e2c652c8d7fdcd0de6b646c`.
Evidence: `.data/d1510-carrier-control-object-parity-v1/report.json`.
Three selected compiler/relocation framework tests also pass. No new runtime
is linked and no enabled rest source is compiled. The object result closes
the original-control reconstruction prerequisite only.

The two newly generated, unneeded RTL dumps are removed after checking their
recorded hashes. The object, stack summary, compiler log and report remain;
`retention.json` records the exact removed filenames/hashes/bytes. This removes
only this turn's diagnostic artifacts, not historical profiler evidence,
frozen inputs or any unapproved numbered directory.

## Source And Admission Boundary

Live canonical `v0.19-staging` remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit is
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
The common baseline is `.data/d1391-runtime-object-source/build`, retaining
the existing object-reuse candidate. This is not pristine upstream.

D1334 already measured real rest-pair elimination from the guarded fixed-arity
and immutable captured-target forwarding prototype. Its original full-product
test failures and missing same-turn timing control remain retained. This turn
does not rerun that observer or declare those old failures resolved. It tests
composition with the current object-reuse toolchain using matched real commands.

D1435 rejects reuse of historical generated C at the byte-identity check:
module build timestamps differ. D1436 regenerates both disabled and enabled C
from the **current** four runtime/expander SCM inputs using the retained
prototype compiler, SHA-256
`704bbee3b74595ea86f361d1c6c2e8acad5f4e46ffe82fcaf1dd25c8f30f6a5c`.
Disabled C is byte-identical to current baseline C in all four units. Enabled
entries retain their original Darwin/genuine-GNU guards and semantic fallback.
No consumer SCM, std/make, GXPkg, runtime ABI, installed library or production
patch changes. Units are stx, core, mop and util; all other objects stay original.

The isolated candidate Gerbil SHA-256 is
`8b4216ff220642851c81027436b9ca4dba7f6b15721cc7f4e44a3ce426d5ba2a`.
Both roles use original GSC SHA-256
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`
for consumer compilation, original RTS, original GNU O1 flags, common library
home and 12 hardware-derived workers. This is a native runtime composition,
not a complete rebuilt prototype-emitter toolchain.

## Real MCP Startup And Complete Builds

D1437 first-window ABBA observations are baseline 6.602315, candidate 5.393913,
candidate 5.679870, baseline 5.872921 seconds. Mean 6.237618 versus 5.536891
seconds is approximately 11.23% lower. Builds here are deliberately stopped
after the literal first compile line; this receipt does not misreport them as
complete builds.

D1439 then executes independent complete project-cold MCP clean/build ABBA:

| Role | First compile, seconds | Complete build, seconds |
| --- | ---: | ---: |
| Baseline | 5.813122 | 55.158939 |
| Candidate | 5.382664 | 53.018177 |
| Candidate | 5.379095 | 52.483646 |
| Baseline | 5.778608 | 52.890228 |

All four cleans exit zero with zero native project images afterward. All four
builds exit zero, produce a real executable and leave checked consumer inputs
unchanged. Means are first 5.795865 versus 5.380880 seconds (-7.16%), full build
54.024584 versus 52.750911 seconds (-2.36%). The complete-build ranges overlap;
do not promote this small full-build difference to a stable general speedup.
Ten-second actual-output and 180-second complete-build gates are unchanged.
These are project-cold builds, not OS-cache-cold measurements. No historical
56-second or Linux run is used as a causal control.

D1440 verifies each of these four produced binaries through real stdio
initialize, tools/list and gerbil_eval requests. All return valid results,
including `Result: 3`; servers are deliberately stopped afterward. This is
protocol smoke coverage, not the complete MCP test suite.

## Actual Concurrent Tests And std/make

D1438 executes original MCP `gerbil test -v 5 test/unit/regex-test.ss` in ABBA
waves, each with 12 concurrent processes. All 48 processes pass 19 cases each:
912 CASE-OK, exact case counts, final OK and exit zero. Test input hashes remain
unchanged. The five-second real-output gate is retained. Baseline/candidate mean
first case is 1.417514/1.320947 seconds and mean process wall is
1.805899/1.716915 seconds. Shared installed/project libraries and OS caches are
retained; this does not qualify cold-test loading, the full MCP suite, or the
reported Darwin/Linux test gap.

D1441/D1442 separately exercise the original std/make/std/test fixture with
each role: 12 concurrent runtime startups, 12 concurrent framework imports,
then a real parallel library build with three CASE-OK checks for cold output,
no-op scheduling and dependency invalidation. Both qualify their semantic and
strict five-second progress gates. Configured concurrency is 12; sampled peak
GCC frontends are 11 and 10, not proof of full simultaneous saturation.

| std/make quantity | Baseline seconds | Candidate seconds |
| --- | ---: | ---: |
| Entire three-case fixture | 14.242402 | 14.857322 |
| Cold library build | 11.005323 | 11.539506 |
| No-op | 0.008291 | 0.014275 |
| Incremental | 1.630419 | 1.695800 |
| Maximum real-output gap | 3.769388 | 4.044972 |

The candidate is slower in this small-library observation, not a nonregression
or library-build acceleration. No timeout is relaxed or artificial product
heartbeat inserted to obtain a pass.

## Evidence And Decision

Evidence is under `.data/d1435-rest-reuse-runtime`,
`.data/d1436-rest-reuse-runtime-current-inputs`, `.data/d1437-rest-reuse-first`,
`.data/d1438-rest-reuse-real-test`, `.data/d1439-rest-reuse-complete-build`,
`.data/d1440-rest-reuse-protocol`, `.data/d1441-rest-reuse-make-control`, and
`.data/d1442-rest-reuse-make-candidate`.

The composition provides new matched evidence of a modest first-log improvement
while preserving existing object reuse. It does not remove the main startup
cost or qualify an overall build/test delivery. Do not freeze or activate it as
a successful production performance patch. Existing rejected experiments remain
rejected; all owned processes are terminal. The full goal remains active.
