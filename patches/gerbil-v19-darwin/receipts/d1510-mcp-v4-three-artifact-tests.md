# MCP v4: Three Cold Artifacts And Complete Test Attempts

## Frozen Configuration

The three cold-built artifacts use the frozen v4 composition (0019/0020/0021,
after 0014/0015), unchanged runtime, driver and native digest backend recorded
in d1510-static-object-reuse-v4-checkpoint.json. No generated-C prototype or
ASCENT workflow changes are mixed into these MCP commands.

| Cold Artifact | First Compile | Complete Cold Build | Test First Output | Complete Test Wave | Verdict |
| --- | --- | --- | --- | --- | --- |
| 0-candidate | 4.049027 s | 37.365152 s | 1.663563 s | 87.409175 s | 39/39 files, 965/965 Cases; ALLOW |
| 1-candidate | 4.044168 s | 37.406373 s | 2.185625 s | 99.545633 s | 39/39 files, 965/965 Cases; ALLOW |
| 2-candidate | 4.003500 s | 36.466995 s | 1.703407 s | 112.039056 s | 38/39 files; DENY |

All three cold builds pass the frozen first-5/build-50 gates. The third full
test attempt does not pass the 112-second gate or complete correctness gate.
test/chunk-07-test.ss is killed at the whole-wave deadline; elapsed time at the
violation is 112.018421 seconds. Cleanup reaps the child, terminal status -9,
with no cleanup errors. The 38 admitted files account for 882 Case-OK events;
the unfinished file's Case inventory is not admitted. It is not a semantic
assertion failure and must not be counted as 965/965 through partial progress.

Do not label these three complete test attempts as three complete passes.
Preserve the 87.409-second historical result, but do not promote it to stable
three-run test performance. No unchanged retry, timeout increase or deletion
of assertions follows this denial. This candidate remains frozen/opt-in and
is not admitted as a default general-purpose optimization.

## Execution And Provenance

Second/third tests use run_complete_mcp_wave.py with whole-task gates, the v4
driver, explicit static-object reuse, unchanged selected runtime/home and
hardware-derived 12 workers. Each binary matches a passing row in the original
cold report by SHA-256. Only the already approved selected-toolchain fixture
is applied to each owned MCP clone; no global Gerbil path or business-source
change is introduced. Each passing file must match its expected Case inventory
and final OK verdict. No per-file silence rule is used.

The first second-artifact invocation failed sysctl hardware discovery under
sandbox policy before creating a workload receipt. The authorized native run
then used the same hardware-discovery command outside that restriction; no
performance result was discarded or retried by that preflight recovery.
ASCENT's three native commands were terminal before these MCP tests started.
No claim of exclusive machine-wide execution or causal variance attribution
is made; other task activity is not controlled by this receipt.

Raw report SHA-256:

- .data/d1510-static-reuse-mcp-v4/tests/report.json:
  b76e7ac843d1db2021745ae800731be3154bdbf2415779d277294045d458a294
- .data/d1510-static-reuse-mcp-v4-tests-round2/report.json:
  90bf2ff64778a7f406025661baf66b73624c61d22d4d637e320714b51e7116fa
- .data/d1510-static-reuse-mcp-v4-tests-round3/report.json:
  7acdd72bd69c2df916a3bfcf6f91d1ae84ad46d3e1eecb912ab596c9b67ef9f0

Original cold report SHA-256:
4affc9a0c4c901e36eb50b16983d66eb67a67dcd33c17f43de3659f8f00a775d.
The original faster checkpoint is not overwritten by these follow-up reports.
