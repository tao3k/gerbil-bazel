# D1510 Complete-Test 112-Second Guard

The active acceptance limits are first output <= 5 seconds, cold build <= 50
seconds, and the complete 39-file / 965-case test wave <= 112 seconds. There is
no additional per-file or per-case silence deadline. Exceeding a hard gate
terminates and reaps owned processes; partial completion is never acceptance.

The unchanged 47-second host's completed test evidence is 105.750981875 seconds,
first output 2.656074625 seconds, all 39 files and 965 original cases passed.
This run was executed under the former 125-second guard; its results also fit
112 seconds. Tightening the policy is not a new runtime improvement or a new
timing measurement. The historical 125-second report is preserved verbatim.

The original cold results remain 47.771713, 47.824226 and 47.927094 seconds.
These were not rerun when changing the test gate. Binary SHA256:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.

Evidence: `d1510-125-test-baseline.json`, plus private report
`.data/d1510-whitespace-125-strict-wave-v1/report.json`, SHA256
`f69698f8bddfdfbe58b03433db641b7b3d4116ce75fdb30c6cc2f086d674aea8`.
Do not rewrite earlier 52-second or 125-second receipts to imply they used the
new policy. A completion diagnostic can finish beyond the guard only when
explicitly requested; it still cannot admit an over-budget result.

## First Strict 112-Second Revalidation

The first fresh run with this guard is **DENY**, not a replacement baseline.
First output is 3.267112s; 38 files / 882 cases have completed and passed.
`chunk-07` is still running when the whole-wave deadline is observed at
112.084893s. Its process group is killed with SIGKILL and reaped without errors;
the controller finishes cleanup at 112.115557s and exits one. The complete
suite's natural duration is unknown. No assertion failure is established for
the unfinished file, and it is not counted as passed.

Evidence: `.data/d1510-whitespace-112-strict-wave-v1/report.json`, SHA256
`cceb4e1a75daee2c9e65c20c304501a73f003db1b0375344744244ffe0f6936b`.
The historical 105.750982s run remains valid but does not establish stable
112-second admission. Keep the tightened guard and this negative result.
Selected publication-tree controller regression tests: 35 passed.

## Second Strict Revalidation

The unchanged frozen host again receives **DENY**. First output is
4.583063042 seconds. Of the original 39 files / 965 cases, 38 files / 882
cases finish successfully. `test/chunk-07-test.ss` remains unfinished when
the 112-second deadline is observed at 112.069314458 seconds. Its owned
process group is killed and reaped with terminal exit -9 and no cleanup
errors. Whole-wave duration including cleanup is 112.124076500 seconds.
The active all-recipes case is not an established assertion failure; neither
that case nor the entire suite has a known natural completion time in this run.

Evidence: `.data/d1510-whitespace-112-strict-wave-v2/report.json`, SHA256
`1cb4b66953da71ab74695e84b0c5fc62976f7da4d9c3fbba9ac2e59320135e76`.
This is baseline revalidation, not a runtime candidate or an optimization.
Two strict failures do not erase the earlier completed 105.750982-second
measurement, but they rule out claiming stable current 112-second acceptance.

## Follow-Up Boundary Checks

The original `gerbil_build_and_report parses C compiler errors from FFI modules`
case passes independently: body 4.423527s, complete harness 6.155433s, first
output 1.695674s, unchanged selected binary and source. It was the active case
at the strict-wave stop, not an established assertion failure or the largest
individual cost. Evidence: `.data/d1510-mcp-atomic-ffi-errors-v1/report.json`.

Source review confirms admitted patch 0018 only handles pure `load-module`
wrappers. It does not eliminate the semantic work in generated compile-time
phase bodies. A focused extension of the earlier successful compiled-code
serialization controls uses the original 145,912-byte `util/strings~1.scm`,
SHA256 `3878c6047c31a2ab50b844b6152daa90926d417b147d379a8063cbcf29378ab3`.

The producer compiles and serializes that actual body without initializing its
phase globals. However, the source execution control fails to import a contract
submodule in this isolated context; restore controls are therefore skipped.
Adding the parent import did not establish the required context. This was an
unqualified fixture/loading-boundary result, not proof of broken serialization
or a speedup. Do not construct a deployment candidate from the simple 19-case
control alone. Evidence: `.data/d1510-real-phi-strings-body-v2/` and `v3/`.

Later controls identify and correct the diagnostic reader's argument-forwarding
boundary, preserving generated identifier case. Actual-body and ordinary-load
controls pass, but restoration allocates about 24 times as much as original
native initialization and establishes no stable native-path gain. See
`d1510-real-phase-import-boundary.md`; do not repeat the earlier fixture failure
as an unresolved dependency error, serialize raw ASTs, or claim a module/body
cache hit as full-test qualification.

## Focused Investigation

The original all-recipes case consumes 75.617631 seconds in its body. Original
recipe merging returns 789 records, processed in sequential five-recipe gxi
batches. For two successful batches, import cost was 0.127591 / 0.650865 seconds
and allocated 82,635,080 / 282,071,328 bytes, while recipe checks consumed only
0.001672 / 0.003640 seconds. These observations select repeated fresh-process
imports as the next target, not a claim of whole-suite attribution or speedup.

Continue from the admitted source-loader and reader improvements with original
module identity, demand loading, mutable state and compile-time phase semantics
preserved. Do not change std/make, std/test, MCP business source or recipe
inventory. Avoid the already rejected symbol-hash, token-fusion and consumer
deployment variants. See `d1510-125-atomic-investigation.md` for negative controls
and observer limitations. Any new runtime candidate must pass atomic semantics,
then all three cold builds and the complete test wave under these gates.
