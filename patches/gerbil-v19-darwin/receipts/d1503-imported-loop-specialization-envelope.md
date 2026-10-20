# D1503: imported-loop specialization envelope, no major startup gain

## Scope and compiler contract

This continues D1487/D1492 with actual compiler AST transformations and native
execution, not an admitted production dependency mechanism. Existing 0001,
0007 and preprocessing gains remain unchanged. No consumer SCM, module
initialization order, original source/object/archive, installed toolchain or
Linux activation changes. The full first-log goal remains unresolved.

Common inputs remain D1391 Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0` and Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, built with GNU GCC 16.
The [Gambit declaration contract](https://gambitscheme.org/4.9.7/manual/)
allows treating file-defined, unassigned block globals as immutable. This
does not by itself supply an external callee body or establish a general
cross-module dependency/initialization contract.

The private Gambit beta-reduction hook reads the exact original util SCM
with Scheme's structured reader, selects foldl__0 and __foldl1 definitions,
parses their expression into the caller's actual compiler environment, runs
assignment conversion, and replaces eligible unresolved three-argument calls.
Original argument evaluation and the copied contract-check/error body are
retained. Local definitions/assignments and non-global callees are excluded.
This is a trusted-current-library envelope, not permission to substitute
arbitrary same-named external functions or unchecked stale bodies.

Three successive native candidates replace only the stx static object:

1. D1493 imports the function body. Two original calls are selected. Generated
   stx C no longer references external foldl__0, but its loop still carries
   the callback in a register and uses JUMPGENNOTSAFE each iteration.
2. D1495 additionally specializes a literal callback into the copied loop
   before AST parsing. The stx-wrap loop now directly calls stx-apply-mark.
3. D1496 composes that specialization with D1488's named wrapper-inline
   envelope. Generated stx-wrap now allocates wrappers in its loop, without
   an indirect callback or a stx-apply-mark call at that boundary.

Each native construction reproduces original static stx C byte-for-byte with
original GSC first, then generates candidate C from the same unchanged SCM.
Compiler generation, object compilation, metadata generation, native linkage
and std/make/std/test/build-script imports all exit zero. Original input hashes
remain unchanged; consumer builds continue using common original GSC and RTS.

The private generator was subsequently hardened to reject non-Darwin,
non-GNU16/Clang hosts and snapshot/hash the observer for future runs. Existing
outputs were not regenerated or retroactively given that snapshot coverage.
The original three construction receipts retain their actual generated C,
input hashes and commands; do not infer a general compiler qualification.

## Actual clean/build first-log measurements

Each row summarizes its own four independent ABBA MCP fixtures at
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. Actual clean exits zero with
zero native images afterward. The literal boundary is `... compile util/compat`.
Original ten-second silence and thirty-second prefix gates remain. Builds
are deliberately stopped at that line (exit 70), not complete build receipts.

| Envelope | Baseline mean seconds | Candidate mean seconds | Change |
| --- | ---: | ---: | ---: |
| Imported body | 5.940871 | 6.131430 | 3.21% slower |
| Fixed literal callback | 5.863315 | 5.912356 | 0.84% slower |
| Fixed callback plus wrapper inline | 6.043511 | 5.750506 | 4.85% lower |

For the combined batch, baseline samples are 6.156764 and 5.930259 seconds;
candidate samples are 5.618311 and 5.882701. This is not an independent repeated
major gain, and it does not resolve the first-log objective. Successful code
fusion is not a substitute for actual runtime improvement.

## Original native wrapper semantics and GC

D1500 executes baseline, fixed-callback and combined native runtimes in three
waves of twelve processes. Each process calls the actual preloaded native
stx-wrap, not a copied implementation. All 36 processes exit zero, return eight
CASE-OK records and final OK: 288 case records and 354,276 tested mark streams.
The original five-second real-output and ninety-second total gates remain.

Cases cover empty/cancelled result identity, improper-list termination, fresh
wrapper identity, source-token identity, input mutation aliasing, quoted-syntax
identity and all 9,841 three-mark streams through length eight. Every 200
streams an explicit GC occurs while the result is live and is rechecked.
A final GC checks retained wrapper/input identity. These are focused controls,
not complete language, callback-capture or module-loader conformance.

## Actual MCP test and std/make/std/test controls

D1501 runs four ABBA waves of twelve unchanged MCP regex gerbil-test processes.
All 48 exit zero, preserve the input hash, return 19 CASE-OK records and final
OK: 912 cases. Five-second actual-output and ninety-second total gates remain.
Mean completion is 1.752823 seconds baseline and 1.694356 candidate, about
3.34 percent lower in this single batch. No full-suite or stable test gain is
admitted.

D1502 runs twelve starts, twelve framework imports and the actual concurrent
std/make/std/test fixture. Cold/no-op/dependency-invalidation phases pass with
final SUITE-OK and D885-OK. Configured concurrency is twelve; observed peak GNU
frontends is eleven. Cold/no-op/incremental times are
10.673483/0.012982/1.640820 seconds; maximum real output gap is 3.636208 seconds,
within the unchanged five-second gate. This is not a matched performance
comparison or complete MCP/toolchain build.

## Decision and next boundary

Do not promote these named/current-library envelopes into production patches
or a full toolchain rebuild on the strength of call elimination. The native
loop/callback protocol can actually be fused, but this path has not produced
the required major first-log or test improvement. Additional design is needed
for any generic external-body dependency, lexical capture, initialization and
fallback contract; passing these focused controls does not supply it.

The next major opportunity must reduce more actual work than these dispatch
boundaries. Escaping syntax wrappers and their identity cannot simply be
deleted. Preserve existing advantages and these negative results rather than
repeat body import or broad inlining-budget experiments as a new discovery.

## Durable artifacts

- `.data/d1493-imported-fold/observer.scm`, `run.py`, `build-envelope/report.json`
- `.data/d1494-imported-fold-first/report.json`
- `.data/d1495-fold-fixed-callback/report.json`
- `.data/d1496-fold-inline-composed/report.json`
- `.data/d1497-fold-fixed-first/report.json`
- `.data/d1498-wrapper-controls.scm`, `.data/d1498-wrapper-controls.py`
- `.data/d1499-fold-composed-first/report.json`
- `.data/d1500-wrapper-identity-controls/report.json`
- `.data/d1501-fold-composed-tests/report.json`
- `.data/d1502-fold-composed-concurrent-make/report.json`

All owned compiler/build/test sessions are terminal. No new performance patch
is admitted and the full objective remains active.
