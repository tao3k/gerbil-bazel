# Terminal driver exec: MCP validation denied

The requested real MCP validation used the frozen D1510 reader binary,
retained MCP cold-build recipe and 12 hardware-derived physical workers.
No MCP business source or production patch was changed. The optional driver
selection is shared by the cold controller and complete-test runner; test
selection checks the cold receipt's driver digest.

| Metric | Original 0015 control | Terminal exec candidate |
| --- | --- | --- |
| Official clean | 5.680777 s, exit 0 | 10.016587 s, exit 0 |
| Native images after clean | 0 | 0 |
| First real compile log | Not observed by 5.027163 s | Not observed by 5.024941 s |
| Complete cold build | Unknown, interrupted | Unknown, interrupted |
| Complete tests | Skipped | Skipped |
| Admission | DENY | DENY |

Both build processes were forcibly stopped and reaped. The roughly 5-second
values are deadline observations, not first-log timings or complete builds.
The gates remained first compile 5 s, complete build 50 s, full test 112 s.

Candidate SHA-256:
`68fa34863567707300f480e03f91532fa3c3585cf2c8fc8f1281d4cf2203935a`.

Raw candidate evidence: `.data/d1510-driver-exec-mcp-v1/report.json` and
`progressive-admission.json`. Control evidence:
`.data/d1510-driver-exec-mcp-control-v1/report.json` and
`progressive-admission.json`.

The independent standard-library figures (3.603313 s first compile,
11.551909 s build) are not MCP results. This run proves neither a MCP win
nor candidate-specific regression, since the unchanged control also failed
before executing this final-compiler-command optimization. No candidate
promotion is supported by these receipts.
