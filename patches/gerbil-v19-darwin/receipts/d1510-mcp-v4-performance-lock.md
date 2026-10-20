# MCP V4 Performance Lock

The user's latest policy is about 10 percent fluctuation allowance over the best
verified measurements. The machine-readable authority is
`d1510-mcp-v4-performance-lock.json`; active cold and complete-test controllers
read it instead of retaining independent 50/52/112-second defaults.

| Metric | Frozen Measurement | New Hard Ceiling |
| --- | --- | --- |
| First compile log | 4.003500 / 4.044168 / 4.049027 s | 4.5 s |
| Complete cold build | 37.365152 / 37.406373 / 36.466995 s | 42 s |
| Complete tests | 87.409175 s, 39 files, 965 cases, all passed | 97 s |

Ceilings use maximum measured duration times 1.1, rounded upward to half a
second for first log and whole seconds for complete tasks. They are allowances,
not revised measured performance or promises of repeat stability. Cold margin
is 12.3 percent after whole-second rounding; first/test margins are about 11 percent.

Every candidate, including historical binary identities, uses the new hard cap.
A slower run cannot be averaged away. Complete tests still require all 39 files
and correctness controls. There is no single-file silence watchdog. Completion
diagnostics may gather evidence but cannot widen performance admission.

The original raw receipts' SHA-256 values were checked locally when installing
this policy and match the frozen v4 checkpoint. Three cold samples and one
complete-test pass are established. The later 99.545633-second complete-test pass
fails this new performance gate, and the interrupted 112-second attempt is not
a complete pass. Repeated complete-test stability and general ASCENT admission
remain open; this policy does not erase negative evidence or enable a candidate
by default.

The proposed 4.1/38/90 and 5/45/105 policies were superseded by the user's latest
10-percent instruction before any workload ran under them. The earlier generated-C
dispatch cold denial remains recorded under its then-active 5/50-second policy;
it is not retroactively relabeled.
