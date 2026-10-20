# D1429: feedback failure controls, not a speedup

## Scope

Follow D1423's failed execution-feedback experiment without a new MCP baseline
campaign. Determine whether its feedback failure can be attributed to ordinary
computed-goto/tail-call use, multi-process merging, or diagnostic termination.
Do not suppress GCC errors or call a diagnostic receipt a performance result.

All workloads and raw artifacts stay under `.data`; the installed toolchain,
original source, default patches and Linux behavior remain unchanged.

## Native control-flow models

D1424 runs four original C models covering computed-goto on/off and musttail
on/off, using two hosts, exported static label arrays, setup entry, repeated
local dispatch and cross-host transfers. Each performs native instrumented
compilation, training, feedback compilation, linking and checked execution.
All four pass; none reproduces the original host's flow inconsistency.

D1428 expands this to eight combinations, adding direct versus indirect host
function-pointer transfers. All eight complete every native stage with exit
zero and `HOST-CONTROL-OK`. This rules out treating these simple model shapes
as sufficient reproductions. It does not prove arbitrary Gambit host CFGs
are supported, nor measure an application acceleration.

Receipts: `.data/d1424-host-profile-reproducer/report.json` and
`.data/d1428-indirect-host-profile/report.json`.
The current generator/source additionally contain the indirect-host axis;
the older receipt pins its earlier source hash and four-case results.

## Single normal-exit training

The unchanged D1421 instrumented binary was identity-checked and used to import
std/make, std/test and std/build-script, saving feedback into an independent
GCOV prefix. This run exits normally with `IMPORT-OK`; no SIGTERM, MCP fixture,
multi-process profile merge or timeout extension supplies the training.

D1425 initially changed the object output path. GCC found feedback files but
reported missing function feedback. Its classifier missed this second form of
`missing-profile` and incorrectly set diagnostic `qualified=true`. **That
qualification is invalid and must not be consumed.** No binary or performance
qualification follows from D1425. The raw receipt/logs remain unmodified.

D1426 fixes the classifier and preserves original object output identities,
with independently captured training and evidence in a fresh directory. Both
original core/stx C files again fail feedback compilation with:

```text
corrupted profile info: profile data is not flow-consistent
```

No missing-profile error remains. Core now includes inferred negative edge
counts of -3353548. Thus the failure also exists with one normal-exit import
training run, without the prior merged/terminated MCP training.

D1426's `qualified=true` admits this diagnostic reproduction only. Both
feedback compiler exit codes are 1, `performanceQualified=false`, and there
is still no optimized executable. Failed object attempts are private D1421
objects; no baseline toolchain object was rewritten.

Receipts: `.data/d1425-single-profile-admission/report.json` (invalid admission)
and `.data/d1426-single-profile-same-object/report.json` (diagnostic failure
reproduction). Harness: `.data/d1425-single-profile-admission.py`.

## Source boundary

Gambit uses a static host-label-address initializer in `___BEGIN_HLBL`.
GCC's [label-address documentation](https://gcc.gnu.org/onlinedocs/gcc/Labels-as-Values.html)
already forbids inlining/cloning when label addresses appear in static
initializers. Adding noinline/noclone merely because the small model has those
attributes is not an admitted remedy for the actual source. No such candidate
is compiled or promoted by this receipt.

These controls do not establish a specific GCC bug, a Darwin-specific failure,
the cause of the original seven-to-eight-second cost, or an optimization gain.
They narrow the feedback failure to additional actual-host characteristics
not reproduced by the small models. A compiler-error correction flag remains
inadmissible. Do not spend a full toolchain build on this invalid feedback.
The main first-log/build/concurrent-test goal remains active and unachieved.
