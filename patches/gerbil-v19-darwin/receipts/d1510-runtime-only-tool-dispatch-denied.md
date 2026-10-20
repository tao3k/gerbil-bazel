# Runtime-only CLI dispatch: DENY

This private candidate differs from the old separate-native-tool handoff:
it stays in the same process and loads the canonical built-in runtime module,
then reads its main procedure through Gambit eval. Only gxpkg/gxtest/gxtags
at the selected HOME's built-in tool directory are eligible; interpreter,
compiler, other tools and noncanonical paths retain original dispatch. The
private Scheme source gates the branch with Darwin. GNU GCC 16 constructs
the candidate. This is not a shipped GNU-gated source patch.

It changes no MCP, gxpkg, std/make, std/test, AOT list or CI source. Frozen
reader/runtime/provider objects are hash-checked and retained; only the main
object is replaced. Generation, compilation and native linkage finish with
exit zero. Original std/make and std/test imports give IMPORT-OK and exit zero.
These construction checks do not establish CLI semantic correctness.

The real retained MCP clean/build/test pipeline uses 12 physical workers.
Official clean produces no output and fails to complete at its unchanged
30-second safety ceiling. It is DENY at 30.026969 seconds, killed and reaped
with exit -9 and no cleanup errors. Build and all tests are skipped. First
compile, complete cold build and complete test times remain unknown, not zero.
The 5 / 50 / 112-second acceptance gates are unchanged and not reached.

Candidate binary SHA-256:
`d5208d6cd3328902a0f286091df4879843ceb82cd4691fd9720dbd42c7216ba0`.
Source: `.data/d1510-runtime-tool-dispatch-source-v1/main.ss`.
Construction: `.data/d1510-runtime-tool-dispatch-native-v1/report.json`.
Actual MCP denial: `.data/d1510-runtime-tool-dispatch-mcp-v1/report.json`
and `progressive-admission.json`.

The v1 construction report's globalsUnchanged field is overbroad: the main
defined-global set remains identical and added references are present in the
retained carrier, but its entire reference set changes. The builder now
distinguishes definedGlobalsUnchanged from globalsUnchanged. The v1 report
is not rewritten; neither field proves full flat-link ABI correctness.

Decision: do not promote, extend or retune this dispatch bypass. Native code
availability and successful imports are insufficient to justify removing
interface import from an actual tool invocation. The clean hang's exact
internal cause is unproven; do not label it a confirmed mutex deadlock,
Mach-O defect, host resource problem or whole-build regression measurement.
Return to the original dispatch and frozen historical 47-second line. No
production patch, candidate publication or new performance baseline follows.
