# D867: attribute and close the Darwin pre-compile silence gap

Date: 2026-09-22. Source: staging V19 `d801e7a1c7f77df421f638e62aaebe370f193c97`, with the existing four Darwin patches and candidates 0007/0008. Real gerbil-mcp is `9a5c35e275e5d6847ff421151bb224f2eae177c1`; real gerbil-poo is `16edc0164cc4c00d81dd4d5e0fed0b24414d4a40`. The consumer sources and global Gerbil installation were unchanged. All package builds used GCC 16, 12 workers, verbose level 3, and a PTY-backed 10-second output watchdog.

The failed uninstrumented four-patch original MCP receipt `/private/tmp/d866-mcp-preflight-order-ab.json` stopped 10.048 seconds after `... build in current directory`, before its first `... compile`; this is an interrupted run, not a build-time result. Two complete uninstrumented D866 A/B candidate runs placed that same interval at 6.886 and 6.293 seconds. Sampling the actual `gxi build.ss compile` process (not its preceding `/usr/bin/env` launcher) showed Gerbil expander/compiler activity, including module and syntax expansion; this was real work, not a blocked GCC subprocess or missing PTY output.

An isolated `std/make` phase probe pinpointed the work. In a complete real MCP cold build, `make-build` entered at 8.733 seconds, indexed 187 build-spec modules from 8.734 to 13.818 seconds (5.084 seconds), and announced the first compile at 13.819 seconds. The initial 25 imports took 1.316 seconds; subsequent groups of 25 took roughly 0.45–0.64 seconds. The source is the official eager completion-table pass, whose `module-id` calls `import-module` for each spec. It remains the same algorithm in candidate 0009.

Patch 0009 emits flushed, actual module-index start/progress/end events every 16 indexed specs only on Darwin and only at `GERBIL_BUILD_VERBOSE >= 3`. The existing runner already streams `... build-observe` events. It neither changes module identity nor hides or relaxes the watchdog.

Validation used the exact D866 `source/build` binary (SHA-256 `f064c994fe1caaac0f3e70b7aaacf320fbae3d255df44fd625717572b34835ad`) and library, with only the compiled 0009 `std/make` module (SHA-256 `a159e57254625f477e063b0e8fb7cd9c222f38033f2ff82a9f85f78aefac0537`) overlaid through `GERBIL_LOADPATH`; the source passed checkout-local `gxc -S` and reverse patch application. A strict real MCP cold build completed in 73.923 seconds; the indexed phase began at 8.483 seconds and first compile appeared at 14.953 seconds. Its largest event-free interval was 5.322 seconds (final link to process exit). A strict real POO cold build of 26 specs completed in 13.584 seconds; its index progress appeared at 0.431, 2.028, and 2.521 seconds; largest interval was 4.095 seconds. Both builds and their unchanged 10-second watchdogs passed. These are functional/observability validations, **not** a new performance improvement claim or an A/B speed admission. An earlier probe using the stale `install/` binary (`944dda73…`) is excluded from qualification.

The common pre-compile silence is now attributed and reports genuine progress. A single module import can still take over 10 seconds on a pathological host; candidate 0009 does not prove that impossible. The 187-module eager-import cost remains a possible future algorithmic optimization, but changing its identity/dependency semantics requires a separate correctness and real-consumer A/B gate. Do not activate 0009 in the release workflow solely because the silence gate passes.

## D869 follow-up: source-reader index shortcut rejected

An isolated Darwin-only experiment replaced the completion-table ID lookup for `.ss` specs with Gerbil's own `core-read-module`, leaving the official `import-module` call in the coordinator. It did not introduce a parser or change non-Darwin code. The experimental source was reverted after the test; no algorithmic patch was added to the stack.

Using the same D866 binary, real MCP revision, 12 workers, GCC 16, and 0009 instrumentation, both cold arms completed. The watchdog allowance was 30 seconds for this diagnostic because a prior baseline run was interrupted during final executable linking at 10.055 seconds; the **measured** largest gaps in these two complete runs were both below the unchanged 10-second admission limit. The 30-second allowance is not an admitted watchdog setting.

| real MCP cold build | 0009-only | reader-ID experiment |
| --- | ---: | ---: |
| module-index phase | 6.240 s | 0.068 s |
| first `... compile` | 12.964 s | 6.926 s |
| final compile scheduling | 43.841 s | 42.191 s |
| whole build | 76.162 s | 75.294 s |
| maximum event-free gap | 5.871 s | 5.241 s |

Both generated executables answered `gerbil-mcp --version` with `1.1.0`. The reader shortcut brought the first compile forward by about six seconds but saved only 0.868 seconds end-to-end in this pair; an earlier pair showed 73.923 versus 69.051 seconds for MCP while real POO worsened from 13.584 to 14.053 seconds. These inconsistent whole-build effects do not establish a substantial, repeatable cold-build optimization. The full imports remain necessary to discover dependencies and are serialized by the existing import mutex; the shortcut mostly shifts their timing. The next performance candidate must reduce or safely overlap the measured downstream cost, not claim that a faster completion-table pass eliminated the import work.
