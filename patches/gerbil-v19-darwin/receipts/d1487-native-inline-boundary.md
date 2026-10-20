# D1487: native inline decisions on the syntax-wrapper chain

## Scope

This is a compiler diagnostic, not an acceleration result. Existing 0001,
0007 and GNU preprocessing gains retain their separate evidence and phase
boundaries. No production patch, consumer source, installed toolchain or
Linux activation was changed. The major first-log and test goals remain open.

Inputs are the existing isolated D1391 build, Gerbil v0.19-staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, and GNU GCC 16.
The original GSC SHA256 is
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.

## Two independent observation boundaries

D1484 wraps beta reduction and reads the actual before/after parse trees of
`gerbil/expander/stx~0`, `gerbil/expander/core~0`, and
`gerbil/runtime/util~0`. Each hook ran once before and once after reduction.
Fresh control and observed C are byte-identical for all three modules.

The first attempt used different output basenames, so its parity field failed:
the file-name comment alone differed. D1484 `result2` uses `module.c` for both
roles and passes exact byte parity; the failed first result is retained.

The stx source already uses block compilation. The local `stx-apply-mark`
procedure is known, with 36 parse-tree nodes. Its four-node call has an initial
budget of 14 under the original 370-percent rule. Ten such calls remain after
beta reduction. Local stx-wrap calls disappear, while external foldl calls
increase from two to ten through their expansion. These are static node counts,
not runtime call counts or actual inline-decision observations.

D1486 therefore rebuilds only the native GSC `_ptree2.o` diagnostic object,
replaces it in a private compiler archive, and relinks a private GSC. Hooks sit
on the actual original `br-app-inline` branches; they do not override a Scheme
binding that native direct calls could bypass. They only inspect names and
increment counters. Original branch conditions, stack operations, generated
library metadata and compilation inputs remain unchanged.

| Module and target | Actual attempts | Unresolved target | Budget rejected | Accepted |
| --- | ---: | ---: | ---: | ---: |
| stx: stx-apply-mark | 18 | 0 | 18 | 0 |
| stx: stx-wrap | 8 | 0 | 0 | 8 |
| stx: foldl__0 | 18 | 18 | 0 | 0 |
| stx: foldr__0 | 1 | 1 | 0 | 0 |
| core: stx-apply-mark | 7 | 7 | 0 | 0 |
| core: stx-rewrap | 5 | 5 | 0 | 0 |
| core: foldl__0 | 1 | 1 | 0 | 0 |
| util: foldl__0 | 1 | 0 | 0 | 1 |

An attempt may revisit a call during expansion, so these counts must not be
presented as unique call sites. All three diagnostic compilations exited zero
and again produced byte-identical C. The original source, object, compiler
archive and GSC hashes remained unchanged. D1485's first native compilation
failed because Gambit's type-test macros require a local `___temp`; D1486 fixes
that diagnostic-only omission. No failed binary was admitted.

## Optimization consequence and remaining gate

This establishes two real compiler barriers on the previously measured
high-frequency wrapper chain: local inlining budget and missing cross-module
callee bodies. It does not establish their runtime cost or a Darwin/Linux
causal difference. D1336's dominant wrappers escape as real syntax objects;
these decisions do not authorize deleting them or changing observable identity.

The next candidate must reduce the call/constructor protocol on that chain,
preserve materialization and observable effects, and measure actual prefix and
concurrent tests. A broad global inlining-budget increase, deleting escaping
wrappers, or relabeling these compiler counts as speedup is not admitted.
Cross-module specialization additionally needs a sound dependency or guarded
callee-identity contract; copying an imported mutable global's body alone is
not sound. This receipt neither qualifies a new patch nor triggers a full
toolchain rebuild before a runtime benefit is demonstrated.

## Durable artifacts

- `.data/d1484-inline-boundary/observer.scm` and `run.py`
- `.data/d1484-inline-boundary/result2/report.json`
- `.data/d1485-inline-decisions.py`
- `.data/d1485-inline-decisions/report.json` (failed diagnostic build)
- `.data/d1486-inline-decisions/report.json` (native decisions and exact parity)
