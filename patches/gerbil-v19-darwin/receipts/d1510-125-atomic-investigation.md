# 125s test guard and atomic investigation

The user changed the complete-test ceiling to 125s after the complete,
39-file/965-case diagnostic measured 120.498387s. The first-log 5s and
cold-build 50s gates remain unchanged. New campaigns use these three limits;
historical receipts retain their original 52s verdicts.

## Atomic controls

Both controls use the unchanged 47s GNU-built CLI and actual `strings -n 4`
output from that selected binary, never a global gxi. They are component
controls, not substitutes for complete MCP tests.

| Work | Observed seconds | Result |
| --- | --- | --- |
| Ten audit regexes, 2000 strings, literal A | 0.135490, 0.090984 | Exact positions retained |
| Same patterns parsed once, B | 0.081983, 0.081208 | Exact positions retained |
| Actual capture read-substring, 4 MiB | 0.054915, 0.066901, 0.012246, 0.014932 | Contents and cursor retained |

Regex ABBA aggregate ratio is about 1.39x, but the warmed literal/compiled
comparison is only about 1.12x. This does not establish a large application
gain. No regex-cache production patch is admitted. The first fixture attempt
failed because it used the obsolete `json-object->string` name from the old
JSON API; fixing the fixture to staging's `json->string` produced the above
successful component control. The failed attempt is retained, not a timing.

Bulk capture reads transferred 4194304 characters and consistently reported
line 232349, column 10. Their measured cost is too small to explain a 68s test
file. Do not add a newline-scanner patch on this evidence.

Private evidence:

- `.data/d1510-pregexp-reuse-atomic-v1/report.json` (fixture error)
- `.data/d1510-pregexp-reuse-atomic-v2/report.json`
- `.data/d1510-read-substring-atomic-v1/report.json`

## Final-link C object route: DENY

The existing Darwin/GNU FD-cleanup C object has already passed compiled-consumer
semantic controls. A distinct deployment attempt preserves the original prefix,
headers, archive and Scheme flags, and adds only that object ahead of `-lgambit`
at final executable linkage through a scoped GNU compiler wrapper. Compile,
preprocessor and unrelated link commands are forwarded unchanged.

This differs from the earlier denied global consumer-prefix route. It still
does not pass admission: cold round zero produced no first compile log by
5.031288s, was immediately killed/reaped, and stopped the campaign. Clean
exited zero with zero native images remaining. Later cold rounds and all tests
were skipped. The new executable link was not reached; this result cannot
attribute the first-log delay to the C object or prove any MCP test speedup.

Frozen host binary, original runtime archive and qualified C object remained
unchanged. No failed result replaces the 47s anchor. Do not widen gates or
repeat this wrapper route to obtain a passing number.

Evidence: `.data/d1510-fork-fd-exe-link-progressive-v1/report.json` and
`consumer-link-deployment.json` in the same directory.

## Guard implementation

`run_complete_mcp_wave.py` now uses first 5s / complete test 125s with no
per-file silence gate. `run_d1510_progressive.py` invokes this runner after
successful cold admission. An explicitly selected completion diagnostic may
continue past the performance deadline, but remains diagnostic-only and cannot
admit production. Wrapper and gate regression tests: 24 passed.

No MCP business source, std/make or std/test source was changed. No new runtime
optimization is admitted by this investigation.

## Formal unchanged-baseline test acceptance

One non-diagnostic 125s-guarded wave of the unchanged frozen host and matching
cold-built MCP executable passed all 39 files and 965 cases. First actual output
was 2.656075s; complete test wave was 105.750982s. Every invocation exited zero,
had final OK, matched its complete inventory, and preserved its test source.
Verdict: ALLOW under the user-confirmed 125s test ceiling.

The runtime and MCP executable were not changed for this measurement, so its
difference from the earlier 120.498387s diagnostic is not a new patch speedup.
Cold construction was not repeated; the unchanged, verified three-round
47.771713/47.824226/47.927094s receipt remains the cold evidence.

Evidence: `.data/d1510-whitespace-125-strict-wave-v1/report.json`, SHA256
`f69698f8bddfdfbe58b03433db641b7b3d4116ce75fdb30c6cc2f086d674aea8`.

## Original-case atomic entry

`run_mcp_atomic_case.py` loads the original module via the same gxtest harness
preparation, executes the original suite initialization and cleanup, selects
one original case closure, and runs it through std/test. It checks exactly one
CASE-OK, final OK, exit zero and unchanged source; atomic passage never qualifies
the whole suite. Its first 5s and total 125s limits have no silence deadline.

The original single-ID recipe case passed: case body 0.833874s, complete atomic
invocation 1.908299s, first output 1.064553s. The two initial fixture attempts
failed on a removed staging import and a missing harness type annotation;
neither ran the selected case or counts as performance evidence.

Evidence: `.data/d1510-mcp-atomic-single-recipe-v3/report.json`. New atomic runs
use actual physical core discovery for child builds rather than the helper's
default two-core environment, and clear inherited experimental runtime flags.

Two further original-case controls run with actual 12-core child-build settings:

| Case | Case body | Complete invocation | First output |
| --- | --- | --- | --- |
| Single recipe ID | 1.650246s | 2.832565s | 1.168433s |
| Recipe syntax plus GNU compile check | 4.333561s | 8.387110s | 4.038975s |

Both pass their original assertions with exit zero and unchanged test source.
They are not speedup comparisons. Evidence: `.data/d1510-mcp-atomic-single-recipe-v4/`
and `.data/d1510-mcp-atomic-recipe-compile-v2/`.

## Direct driver final-link route: DENY

A further distinct deployment changes only two existing final executable
link argument sites in the private generated compiler driver. Its existing
Darwin/GNU predicate guards object injection; absent configuration or a false
platform predicate preserves original arguments. It retains the actual GNU
compiler path, original prefix/archive, all 280 embedded native providers,
47s reader objects and coalesced carrier. No compiler wrapper is used.

The generator parses/re-writes Scheme forms, not C/SCM text fragments. Initial
construction attempts were stopped for a missing helper binding and an added
`getenv` global. Using the driver's existing `##getenv` binding retained exactly
the original global interface. Candidate v3 builds and imports successfully;
all 45 reader controls pass. Construction success is not performance admission.

Cold round zero: clean exit zero, zero native images; first compile 4.947258s.
Complete-build deadline was exceeded at 50.002098s; process was immediately
killed/reaped. Later rounds and tests were skipped. No completed build time or
test gain is claimed. This candidate also remains DENY and does not replace
the frozen host. Do not repeat the same deployment by widening its gate.

Evidence: `.data/d1510-fd-final-driver-native-v3/report.json`,
`.data/d1510-fd-final-driver-reader-controls-v1/report.json`,
`.data/d1510-fd-final-driver-progressive-v1/report.json` and
`final-driver-deployment.json` beside that cold report.

## Original Recipe Case And Import Attribution

The original `gerbil_howto_verify checks built-in recipes` case passes without
changing its closure, assertions, data or selected toolchain. Body time is
75.617631s; complete atomic harness time is 77.046448s; first output 1.417366s.
This is one case, not a new complete-suite result. Its report SHA256 is
`8c5742a1a49031412b066355ae2b498139f5776fcb533a4e8c9b58d087f01c58`.
Evidence: `.data/d1510-mcp-atomic-all-recipes-v1/report.json`.

Actual `load-recipes` returns 789 records. The unchanged verifier partitions
them into five-recipe batches and launches each fresh gxi sequentially. The
new diagnostic calls the original `build-verify-expressions` and compares
original command results with observed phase results. It does not change the
production verifier or pool processes, and it is not performance admission.

| Original batch | Import wall | Check wall | Import allocation | Check allocation |
| --- | ---: | ---: | ---: | ---: |
| 0, file/port recipes | 0.127591s | 0.001672s | 82,635,080 bytes | 2,928,832 bytes |
| 1, JSON/HTTP recipes | 0.650865s | 0.003640s | 282,071,328 bytes | 6,188,824 bytes |

Both batches retain all five exact PASS/FAIL identities and exit zero. Batch 2
exits 70 in both original and observed execution because an original import
cannot find a library module. It has no complete recipe outcomes and is not
called a successful recipe verification. The existing full-suite assertion
only checks report text for this tool; 965 passing cases do not imply that
every cookbook example passed syntax verification.

The two measured batches identify repeated import work as a stronger target
than recipe-body expansion. They do not attribute all 75.6 seconds, establish
Linux causality, or prove an optimization. Wall variability is substantial;
observed/control wall differences are not speedup measurements.

Evidence: `.data/d1510-mcp-recipe-batch-cost-v5/report.json`, SHA256
`f688aa8dcfdfa8fb108defec0aca3b263ea5dc923209f396a5cebb40b1e3189b`.
The phase protocol does not import a JSON observer dependency. Earlier v1/v2
failed on an unbound fixture helper, v3 on Scheme-number JSON formatting, and
v4 preloaded JSON and biased import attribution. Do not use those phase times.

A global `gx#core-read-module` wrapper preserves outcomes but records zero
calls. Attribution is explicitly unqualified: zero wrapper hits do not prove
zero module reads; compiled callers may bypass global rebinding. Its historical
controller exited zero for matching semantics, not successful attribution.
The updated controller returns failure when the requested attribution has no
observed calls. Evidence: `.data/d1510-mcp-recipe-module-read-cost-v1/`.

Native samples retain original results and show symbol interning, GC and
dynamic loading. They also show dyld synchronous debugger notifications;
sampling materially changes wall time. No native sample percentage or sampled
wall time is admitted as unobserved cost or a speedup. Do not reopen the already
rejected symbol-hash filter because it appears in these stacks. Evidence:
`.data/d1510-mcp-recipe-native-sample-v1/`, report SHA256
`79e95a46bf7971198a8ec0e6811cd0f27dd685fc78a77753f1edf70417e6651f`.

Combined controller, attribution and cold/full-test gate regression checks:
41 passed. Frozen 47-second source/evidence verification still succeeds.
No original archive, binary or MCP source was replaced; no new optimization
patch was admitted or pushed. The next useful execution-cost target is the
fresh-process import chain, with original import results and demand-loading
semantics retained, not deferred logging or a smaller recipe/test inventory.
