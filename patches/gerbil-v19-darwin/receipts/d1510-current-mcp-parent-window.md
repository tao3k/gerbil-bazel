# Current MCP pre-builder observation

This is diagnostic evidence, not an accelerator or a new baseline. Historical
47.771713 / 47.824226 / 47.927094-second cold builds remain separate. The
whole-task 5 / 50 / 112-second gates are unchanged. Final admission still
requires actual MCP cold construction and all 39 files / 965 test cases.

The original frozen binary and original 0015 driver run the retained MCP
clean/build recipe with 12 physical workers. The framework's optional
observer does not alter environment, inputs or deadlines. Observation always
forces performance admission to DENY, even if the observed build completes.

V1 cannot identify a build child in its bounded observation window and does
not sample anything. That missing observation is retained, not called a
macro profile. V2 permits an explicitly labelled official-parent sample after
one second, verifies its executable through proc_pidpath against the selected
binary, and joins the bounded observer before returning.

V2 official clean exits zero in 6.775475 seconds, leaving zero native images.
Build is DENY at 5.043265 seconds with no first real compile log. Its process
is killed and reaped with exit -9 and no cleanup errors. Complete build/test
times are unknown; tests are skipped.

The observer attaches at 1.074476 seconds to the official parent, with no
children in the last process query. The one-second sample completes with
exit zero. It contains 882 main-thread samples. The first getcwd_long_path
stack accounts for 199 samples, and a later root adds one. Other stacks
reach path normalization, stat, native-provider digest verification, symbol
interning, GC and Scheme execution. Sample counts include wait and observer
effects: they are neither exclusive CPU intervals nor predicted savings.
The absent child is a snapshot, not proof that no child appears throughout
the entire five-second window.

Retained main.ss build aliases reach the generic tool dispatch, and retained
src/tools/gxpkg.ss:624-625 subsequently launches build.ss with compile.
Therefore this sampled window cannot be assigned exclusively to the
builder's macro expansion. No gxpkg source or dispatch is changed here.

The existing path-cache/realpath/F_GETPATH, digest-skipping and old native
CLI-handoff exclusions remain closed. These samples do not authorize
reopening them or establish a macOS/Linux causal gap. An eligible candidate
still needs a distinct source mechanism, semantic controls and three actual
MCP timing metrics; standard-library measurements cannot substitute.

Raw evidence:
`.data/d1510-current-mcp-hard-gate-sample-v2/report.json`,
`0-candidate/first-window-observer.json`, `first-window.sample.txt` and
`progressive-admission.json`. The incomplete v1 evidence is preserved in
`.data/d1510-current-mcp-hard-gate-sample-v1/`.

Framework regression checks: 28 passed, including executable identity
rejection, bounded sampling failure, terminal-product rejection, explicit
parent/child selection and unchanged cold admission gates. No runtime patch
is promoted or published by this observation.
