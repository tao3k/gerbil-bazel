# D1510 progressive runtime gates

## Policy

- First real cold-build compile line: at most 5.5 seconds, inclusive.
- Complete cold build: at most 52 seconds, inclusive.
- Complete 39-file MCP test wave: at most 52 seconds, inclusive.
- Existing test real-output gap remains 5 seconds; no synthetic heartbeat.
- Deadline violation sends SIGKILL immediately to the owned process group.
  Reaping is cleanup, not extra performance budget.
- Cold DENY skips the entire test stage. No incomplete run is a speedup.

Entrypoint: `tests/run_d1510_progressive.py`, with `--binary`, `--test-home`,
and a fresh `--output`, all under project `.data/`. It retains the D1510
recipe and selected 0015 driver, verifies tool identities, and applies the
already approved MCP test fixture patch only after the cold gate passes.
The original private controller must be present; exact instrumentation
anchors fail closed if it drifts. This is not a standalone toolchain build.

## Real watchdog verification

Receipt: `.data/d1510-progressive-gate-verification-v2/`.
Selected binary: frozen source-loader 49-second candidate, unchanged.

- Official clean: 7.659485 seconds; zero native project images retained.
- No first real compile line by 5.514490 seconds: DENY.
- SIGKILL terminal status: -9; cleanup errors: none; process reaped.
- Build attempt including cleanup: 5.531666 seconds.
- Complete build time: unavailable, deliberately interrupted.
- Test time: unavailable, skipped because the cold gate failed.

The 14.5 ms observation overshoot is watchdog polling, not a widened gate.
This run verifies enforcement, not a new performance result. The first
sandboxed attempt failed before Gerbil launch at sysctl permission discovery
and also skipped tests. No claim is made about the cause of slow timing.

## Rejected candidates retained as negative evidence

- Two-module field elimination: first compile 6.081848 seconds, complete
  build 56.636770 seconds. DENY, not a retained gain.
- Expanded 89-site field elimination: complete build 51.261563 then
  52.571008 seconds; first compile 5.603037 then 5.949120 seconds. DENY.
- Canonical mark-fold specialization: first compile 8.688069 seconds,
  complete build 90.803216 seconds. DENY; do not repeat this candidate.
- Earlier field-candidate MCP test wave: 60.174833 seconds, revalidated
  13 passed and 26 failed. DENY for correctness and total time, even if
  individual tests passed. Historical raw receipts are not rewritten.

These observations came from the old late-check harness. The new runtime
gate prevents waiting for comparable over-budget runs to finish. The frozen
49-second baseline stays unchanged and is not promoted to full test admission.
