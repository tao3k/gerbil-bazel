# D870: real MCP post-index work attribution

Date: 2026-09-22. This is diagnostic evidence, **not** a performance A/B or a new patch. The real `gerbil-mcp` source is `9a5c35e275e5d6847ff421151bb224f2eae177c1`; staging Gerbil is `d801e7a1c7f77df421f638e62aaebe370f193c97`. The unchanged D866 binary is SHA-256 `f064c994fe1caaac0f3e70b7aaacf320fbae3d255df44fd625717572b34835ad`, with only 0009 `std/make` observation overlaid. The clean consumer build used GCC 16 and 12 workers. No consumer source, global installation, or applicable patch changed.

The completed diagnostic build took 79.281 s. Its 30-second *allowance* was used only to avoid discarding a process sample on an intermittent final-link silence; the actual maximum event-free interval was 4.734 s. The run was instrumented by macOS `sample`, so its wall time is excluded from speed comparisons.

| Event | Seconds from package-process start |
| --- | ---: |
| Module index starts | 6.671 |
| Module index ends; first compile announced | 12.221 |
| Executable compile announced | 45.279 |
| Final executable link begins | 74.547 |
| Build exits | 79.281 |

The front-window 12-second sample began with module indexing. Its main thread executed Gerbil expander and compiler code, including syntax/core expansion, optimizer, runtime hash/table operations, and garbage collection; it was not predominantly blocked on a compiler subprocess. Peak sampled footprint was 1.4 GiB. A separate five-second sample at about process age 46 seconds found 4106 of 4360 main-thread samples in `__select`, waiting on native subprocesses while GCC workers were active. The two samples are phase attribution, not a quantitative profile of every worker or a claim that either phase can be shortened by its full elapsed interval.

This agrees with the earlier D855/D859 per-job receipts: the native tail is already highly occupied, and the graph interval performs real expansion/compilation. The D869 source-reader experiment shortened only the visible index, not the whole build. A further `std/make` queue or index shortcut has no measured large upside. The next candidate must reduce actual generated/native work across many modules without disabling GCC optimization or weakening the unchanged 10-second package gate. No additional patch is admitted from this receipt.
