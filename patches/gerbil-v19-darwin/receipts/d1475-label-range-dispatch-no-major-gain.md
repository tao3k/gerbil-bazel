# D1475: single-host label-range dispatch rejected

## Source hypothesis

The previous D1469 actual census found no ordinary Gambit fork fallback in
the observed MCP compiler chain, and only two spawn calls before the first
compile line. This experiment returns to Scheme execution, without altering
consumer/std sources or widening process-launch semantics.

Gambit's `include/gambit.h` JUMPFAST reads the destination label's host pointer,
compares it with the current C host and then loads its native goto label.
For an original single-host module, the module label table provides a possible
local-range shortcut. The private candidate uses unsigned-word subtraction
and LBLCOUNT times LABEL_SIZE times WS to recognize that range. For targets
outside the range, it retains the original host-pointer comparison and
external handoff. The computed goto, descriptor layout, call ABI, allocation,
GC, polls and original host grouping are unchanged.

The override is guarded by Darwin, genuine GNU/non-Clang, single-host,
label-values, inline-jumps and a positive label count. It is a private
generated-C prototype, not an integrated Gambit compiler/header patch.

## Native admission

Common source and library inputs remain
`.data/d1391-runtime-object-source/build`, Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. Existing Bazel GNU GCC 16
discovery and 12 physical workers are used. Eleven generated modules were
rebuilt with original O1/debug flags; other module objects, runtime archive
and consumer GSC were retained. Removing the added override reconstructs
each original generated C input exactly.

Native objects, linker metadata, final link and std/make/std/test/build-script
imports all pass. Original inputs and GSC hashes remain unchanged. Candidate
binary SHA-256:
`ea532306634a404b897e131025324faf33c4e2a77593bf124eb000048d32734a`.

D1472's first preprocessing check failed because it omitted DEFS_OBJ and thus
did not reproduce actual object-build conditions. It is not evidence that the
compiled candidate was disabled. D1473 obtains DEFS_OBJ through gambuild-C's
own query command and confirms the new macro is active in all eleven modules,
covering 11,818 table labels. These selected tables contain only ordinary
INTRO/PROC/RET entries and no CFUN bodies. The original external fallback is
present. This is activation and table-shape evidence, not complete semantic
proof for arbitrary label metadata or foreign-module configurations.

## Real first-compile ABBA

Four independent unchanged MCP checkouts at
`9a5c35e275e5d6847ff421151bb224f2eae177c1` underwent official clean, with
zero native images afterward. Each actual build was deliberately stopped
after its first literal `... compile util/compat` line. The 10-second
real-output and 30-second first-window gates were unchanged.

| Role | First compile seconds |
| --- | ---: |
| Baseline | 6.131103 |
| Candidate | 5.834883 |
| Candidate | 6.202266 |
| Baseline | 6.212408 |

Means: baseline 6.171756 versus candidate 6.018575 seconds, about 2.48 percent.
Ranges overlap. This does not admit a major or stable startup improvement.
Build terminal status 70 is the deliberate first-line stop, not a completed
build or an independently passed build gate.

## Real concurrent MCP tests

The original regex CLI suite ran in four ABBA waves, twelve concurrent
processes per wave, using unchanged prebuilt project libraries and a common
library/GSC home. All 48 processes exited zero, each emitted exactly 19
CASE-OK records and final OK: 912 cases total. Input hashes remain unchanged.
Five-second actual-output and 90-second total gates were kept.

| Per-process mean | Baseline | Candidate |
| --- | ---: | ---: |
| First CASE seconds | 1.385582 | 1.441246 |
| Completion seconds | 1.764601 | 1.858211 |

Candidate process completion is about 5.30 percent slower in this run. These
are per-process means across two concurrent waves per role, not aggregate
batch makespan or OS-cache-cold testing. This is the regex suite only, not
the full MCP test suite or broad collector/continuation conformance.

## Decision

Reject this range-check override as the requested startup/test optimization.
It does not support widening to more modules or freezing a production patch.
No complete toolchain or complete candidate MCP build is qualified, and no
release profile is changed. Existing 0001/0007/preprocessing advantages remain
untouched. The major first-log and native-test acceleration goal remains open.

Do not infer from this result that all GVM dispatch improvements are impossible
or that a particular Darwin instruction explains the Linux difference. The
tested dispatch shortcut simply did not deliver the required product gain.

## Durable Evidence

- `.data/d1421-pgo-runtime.py`, range mode; original PGO/LTO modes retained
- `.data/d1470-label-range-runtime/report.json`
- `.data/d1471-label-range-first/report.json`
- `.data/d1472-label-range-admission.py`
- `.data/d1473-label-range-native-defs-admission/report.json`
- `.data/d1474-label-range-real-tests/report.json`

All private outputs remain under project `.data`. No personal absolute paths
are included in this public receipt.
