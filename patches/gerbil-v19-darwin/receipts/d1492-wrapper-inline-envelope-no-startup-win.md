# D1492: wrapper-inline envelope does not resolve startup

## Experiment and identity

D1487 established actual budget rejection for the locally known
`gx#stx-apply-mark`. This experiment checks that specific opportunity before
designing a broader compiler change. It is deliberately a named-callee
envelope, not a production optimization rule or a new release patch.

Only a private Gambit compiler budget branch changes: under Darwin/GNU,
negative remaining budget becomes zero for that known callee. The original
callee lookup, procedure check, inline declaration, cloning and beta reduction
remain in force. No global budget increase, wrapper deletion, source reorder,
consumer modification or Linux activation is introduced. Names alone would
not be a sound general-purpose production rule.

The canonical v0.19-staging remote was checked again and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit remains
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. The common input is
`.data/d1391-runtime-object-source/build`, with GNU GCC 16 from the existing
Bazel host environment. All original compiler/source/object/archive hashes
remain unchanged.

Private `_ptree2.o` and the copied compiler archive are rebuilt and relinked.
The original static stx Make recipe is reproduced with original GSC first:
fresh control C is byte-identical to the baseline static C. The envelope GSC
then compiles the same unchanged SCM. Only this candidate stx object replaces
its original in the relinked Gerbil runtime. All other Gerbil objects, RTS and
the compiler used by consumer builds remain original common inputs.

The four direct generated-C jumps to stx-apply-mark disappear. C size increases
from 337,982 to 339,050 bytes. That verifies a real code-generation change,
not runtime frequency or saved CPU. Imports of std/make, std/test and
std/build-script pass. Candidate binary SHA256:
`5db861f622df402f58363b31449a257d1aaf5b8c01e7e8403af945ea33e25f18`.

## Actual MCP first-log ABBA

Four fresh unchanged fixtures at MCP
`9a5c35e275e5d6847ff421151bb224f2eae177c1` undergo actual clean, with zero
native images afterward, then build until literal `... compile util/compat`.
The original ten-second silence and thirty-second prefix gates remain. Exit
70 is the deliberate first-line stop, not a successful complete build.

| Role | First compile seconds |
| --- | ---: |
| Baseline | 5.797824 |
| Candidate | 6.133936 |
| Candidate | 5.791417 |
| Baseline | 5.744267 |

Means are 5.771045 versus 5.962677 seconds: the candidate is about 3.32 percent
slower in this batch, with overlapping ranges. No startup win is admitted.
The diagnostic counters and omitted jumps cannot override this actual result.

## Actual concurrent test and make controls

Four ABBA waves run twelve unchanged MCP regex `gerbil test` processes each.
All 48 processes exit zero, return exactly 19 CASE-OK markers and final OK,
and preserve the input hash: 912 cases. The original five-second real-output
and ninety-second total gates remain.

Baseline/candidate mean first-case times are 1.415797/1.327751 seconds;
completion means are 1.799604/1.706193 seconds. The latter is about 5.19 percent
lower in this single batch. It is not an independently repeated stable gain,
the complete MCP suite, or justification for a production patch.

The candidate also executes the actual std/make/std/test fixture with hardware
concurrency twelve, twelve runtime starts and twelve framework imports. Cold
build, no-op build and dependency invalidation all pass with final
`SUITE-OK parallel std/make build contract` and `D885-OK`. Cold/no-op/incremental
phases are 11.508998/0.008253/1.630342 seconds. Maximum actual output gap is
3.925862 seconds, within the unchanged five-second gate; observed peak GNU
frontends is eleven. This is a semantic/concurrency control, not a matched
build-performance comparison or complete MCP build.

## Decision

Do not solidify this envelope into a patch, broaden a named exception, or run
a complete toolchain build on the strength of call-count elimination. Local
wrapper-call elimination alone has not removed the major first-log cost.
Existing 0001, 0007 and macro-tracking benefits remain intact. Cross-module
higher-order loop specialization is a different opportunity and needs a sound
callee/dependency contract, preservation of initialization order and escaping
syntax identity, and measured execution savings before admission.

The full goal remains unresolved; this receipt narrows the implementation
choice rather than redefining success as passing controls or a small test gain.

## Durable artifacts

- `.data/d1488-wrapper-inline-envelope.py`
- `.data/d1488-wrapper-inline-envelope/report.json`
- `.data/d1489-wrapper-inline-first/report.json`
- `.data/d1490-wrapper-inline-tests/report.json`
- `.data/d1491-wrapper-inline-concurrent-make/report.json`

All owned build/test processes reached terminal states before this receipt.
