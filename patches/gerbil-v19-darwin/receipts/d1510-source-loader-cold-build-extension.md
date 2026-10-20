# D1510: pure-loader compilation extension

## Decision

The private compiler candidate passes complete cold-build admission, but is
not promoted to the patch stack, release, or full-toolchain qualification.
The first compile window is not improved. The real MCP test gates still fail.
The retained original D1510 binary, objects, runtime archive, and library home
are unchanged. No consumer, std/make, std/test, or package transport source is
modified. No Git push is made by this experiment.

## Mechanism and ownership

`src/gerbil/compiler/driver.ss:generate-runtime-code` emits a separate loader
containing only nested `begin` and `load-module` forms. The original path
compiles this into a native loader separately from runtime and phi code.
The private candidate writes the same loader source but does not invoke GSC
for that loader, only under Darwin/GNU, static compilation, invoke-GSC, and
a bounded pure-loader shape guard. All other shapes retain the original path.
Runtime object reuse from 0007 and the retained 0015 driver are unchanged.

The installed runtime's source-loader fallback is exercised, not a new result
cache or a scheduling-only change. This intentionally changes loader artifact
classification from native to Scheme source; it is not universal observable
artifact parity. Previously emitted contiguous `.oN` loader versions are
removed from the private output after successfully writing the new source,
so the runtime cannot select an obsolete native loader.

An initial external driver overlay was inactive: the retained D1510 main
program already links the compiler driver. The first control caught an
unbound helper. That construction is not timing evidence. The corrected
candidate replaces only the native compiler driver module and regenerates
the original guarded outline carrier with the same eleven outlined modules,
module order, flags, GSC, runtime archive, and other native objects.

Native construction: `.data/d1510-source-loader-linked/`.
Candidate SHA256:
`3d727d8ac1926883934ada2a696325c404de2ab786d01def1987dbfe06d21c09`.
Original SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Fourteen actual native controls pass, including platform selection, nested
and empty loaders, non-loader/foreign/dotted/malformed input rejection,
cyclic and oversized input rejection, source emission, and old-version cleanup.

## Complete cold builds

Actual unmodified MCP checkout:
`9a5c35e275e5d6847ff421151bb224f2eae177c1`.
Each run uses a separate project clone, official `gerbil clean`, and official
`gerbil build`. Twelve workers come from the host's physical CPU count.
GNU GCC16 and the established Bazel host environment are selected.
The original single-VM D1510 profile and retained 0015 driver apply to both
roles. No later rejected composition is included.

| Run | Clean (s) | First compile (s) | Complete build (s) | 55 s gate |
| --- | ---: | ---: | ---: | --- |
| A1 original | 3.478864 | 5.132524 | 49.869531 | PASS |
| B1 candidate | 2.654380 | 5.218240 | 43.846968 | PASS |
| B2 candidate | 2.603315 | 5.198488 | 45.126992 | PASS |
| A2 original | 2.613274 | 5.611670 | 52.800909 | PASS |

Mean complete build: original 51.335220 s, candidate 44.486980 s;
approximately 13.34 percent less elapsed time in this ABBA, not a startup or
test speedup. Clean is outside the build ceiling. Every clean leaves zero
project native images; every build exits successfully with the MCP executable
present and checked consumer inputs unchanged. The unchanged admission helper
returns ALLOW; its five regression tests pass. Candidate over-ceiling runs
would stop the campaign immediately rather than be averaged away.

The loader audit finds **187**, not the older approximate 186, pure loaders
with 605 load calls. All 187 loader sources are byte-identical across A1/B1.
Original has 186 native loaders; candidate has zero. The final `lib` loader
accounts for the distinction between generated loader count and native count.

Raw evidence: `.data/d1510-source-loader-cold-abba/`,
`.data/d1510-source-loader-baseline-audit/`,
`.data/d1510-source-loader-cold-audit/`.

## Repeat-build and test boundaries

Untouched A2/B2 fixtures are tested with a real repeat `gerbil build`:
original 6.206430 s, candidate 6.212161 s. Both exit zero, compile zero modules,
and leave all captured artifacts byte-identical. This is freshness validation,
not a cold-build speed claim. The earlier check on fixtures already exercised
by consumer tests compiles three modules in both roles; it is retained as a
failed no-op control, not silently substituted with the pristine result.

All 39 unmodified MCP test files are run through actual `gerbil test -v 5`,
12 concurrent workers, using each role's own cold-built artifacts. The
five-second real-output-gap and 90-second invocation wall gates are unchanged.
Exact CASE count and final standalone OK remain required; exit zero alone
cannot qualify a swallowed harness failure.

| Wave | Passed / 39 | Wave elapsed (s) | Output/budget failures | Terminal/count failures |
| --- | ---: | ---: | ---: | ---: |
| A1 | 17 | 47.911119 | 16 | 6 |
| B1 | 17 | 46.413051 | 16 | 6 |
| B2 | 25 | 41.864426 | 8 | 6 |
| A2 | 25 | 42.315171 | 8 | 6 |

Total: 156 invocations, 84 passed, 72 failed. These failed wave durations are
not successful suite timings and establish no test speedup. A1/B1 have exactly
the same failed files; B2/A2 do not, despite equal totals: candidate fails
`proc-test.ss` while original fails `parse-test.ss`. Do not claim complete
failure parity or a fully green product. Independent post-run hashing confirms
all 41 Scheme test source files in each consumer checkout remain unchanged.

The first test harness invocation failed during role-relative path preflight;
no real tests ran in that output directory. The corrected v2 preserves that
failed preflight and qualifies neither directory as a passed test campaign.
Evidence: `.data/d1510-source-loader-full-tests-abba-v2/summary.json`,
`.data/d1510-source-loader-noop-build/`,
`.data/d1510-source-loader-noop-pristine/`.

## Larger scope did not solve the first window

A read-only audit identifies 388 pure loaders with native versions in the
original toolchain library. A private symlink view omits those loaders' native
versions and associated debug directories; it copies no native files, removes
no original files, and changes no signatures or extended attributes. Runtime
and macro native code remain selected from the original home.

The same compiler candidate with that private view completes official cold
clean/build: clean 2.822411 s, first compile **5.150402 s**, complete build
46.289818 s. The single cold build passes 55 seconds, but is not matched ABBA
evidence of any additional gain. It does not reduce the first window and is
not promoted. Construction counts include debug directories and must not be
reported as an exact native-binary count.

Evidence: `.data/d1510-toolchain-pure-loader-audit/`,
`.data/d1510-source-loader-home/`, `.data/d1510-source-loader-home-cold/`.
No complete latest-staging toolchain rebuild or Linux qualification follows
from these private experiments. The remaining priority is actual macro-phase
execution/loading cost and strict test progress, not cosmetic early logging.

## Timestamp-Only Runtime Coverage Check

A subsequent read-only census distinguishes metadata-only runtime bodies from
the already retained pure dependency loaders. It uses the original GSC reader,
not regular-expression parsing, and validates GSC SHA256
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
Each file is read to EOF. The narrow classifier accepts only declaration
forms, recursively pure begin forms, and three-element definitions whose
symbol ends in `::timestamp` and whose value is a numeric literal. It does
not execute the source, resolve imports or change any artifact. This is a
syntactic census, not a proof of source/native equivalence.

| Existing source group | Parsed files | Timestamp-only files |
| --- | ---: | ---: |
| Original standard-library static runtime SCM, std__*.scm | 330 | 49 |
| Retained MCP generated runtime SCM, gerbil-mcp/**/*~0.scm | 187 | 0 |

Both reader processes reach EOF, emit the final CENSUS-OK marker and exit
zero. Standard-library examples include actor, actor/api, db, deprecation,
encoding/json, encoding/json/api and encoding/protobuf/lang. Their eligible
shape is distinct from a dependency loader: they initialize global metadata,
whereas 0018's accepted code consists only of begin/load-module forms.
Do not broaden load-only-code? to admit definitions under a purity label.

This finding prevents an unsupported extension claim: there are no such
empty runtime bodies among this heavy workload's 187 runtime producers, so
source execution of timestamp-only bodies cannot remove those compile jobs.
The earlier loader CPU observation aggregates boundaries across modules and
does not isolate the 49 metadata modules' reached cost. It cannot establish
a large saving from their count alone. The existing 388-loader home-view
experiment is also already recorded above and is not rerun.

No metadata-runtime candidate is constructed or admitted from this census.
Any later source/native classification change must preserve global-cell
initialization, dependency/loading identity, reload and error behavior, and
must first establish a reached cost budget. No new compiler, runtime, home
view, consumer source, independent library build or complete MCP build/test
is changed or qualified here. The retained 47-second host and current
5/50/112-second gates are unchanged; the census supplies no speedup estimate.
