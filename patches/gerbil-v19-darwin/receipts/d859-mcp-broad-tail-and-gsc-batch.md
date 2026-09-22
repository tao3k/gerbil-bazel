# D859: MCP broad tail and official gsc batch gate

Date: 2026-09-22. This is an **observational and atomic** follow-up, not an
end-to-end speedup or a release patch. It uses the same unchanged real MCP
revision and D858 baseline clone/12-worker instrumented toolchain. The
isolated installed header was first restored to the original definition.

## Graph and compiler-tail attribution

`std/make` graph start was 6.659 s from package-process start, graph ready
12.785 s, and graph end 45.277 s. Of 187 expected module producers, 182 had
independently parseable start/end pairs; interleaving of two logger streams
corrupted some lines. These 182 intervals total 331.435 worker-seconds.
Between graph ready and graph end they occupied an average 10.2 of 12
workers; the steady middle 22–42 s occupied about 11.5–11.7 workers. The
initial dependency ramp and final `main/lib` chain account for the lower
whole-graph average. This is worker occupancy, not CPU utilization.

The native `compile-file` tail was also occupied: from graph end 45.277 s
to the last file at 71.527 s, independently parseable compiler intervals
occupied 11.83 of 12 workers on average. The last jobs were ordinary small
modules, not the large `embedded` object. The 185 jobs for which a generated
C file persisted are only a **subset** of the 543 compiler jobs. Their
generated C contains 258,170 `___STR8` occurrences, 218,334 of them in
`embedded~0.c`; that extreme concentration explains D858's poor package
translation. Later files such as `howto-verify~0.c` and
`resolve-imports~0.c` are 166–219 KiB and finish in roughly 1–1.5 s under
the parallel package run.

GCC 16 `-ftime-report` on real `howto-verify~0.c` reported 0.39 s of compiler
work: parsing 0.10 s (25%) and optimization/generation 0.29 s (74%), with
preprocessing 0.06 s included in parsing. The report adds measurement
overhead; it is stage attribution, not a baseline timing. Unlike the huge
string module, this representative small file is **not** primarily blocked
on C preprocessing. Disabling optimization is not an admitted solution: the
user requires the executable performance to be preserved.

## Official multi-input gsc gate

Gambit V19 `gsc -help` advertises multiple inputs and an output directory.
With unchanged `-D___DYNAMIC -fPIC`, two real generated C files compiled
separately in 0.36 + 0.42 = 0.78 s. One official `gsc -obj -o <directory>`
invocation with both files took 1.01 s. Each batched object was byte-identical
to its separately compiled counterpart. Therefore one-process batching is
functionally possible but shows **no atomic time saving** here; it may also
reduce scheduling flexibility if integrated. Do not add a batch layer.

## Decision

No new optimization patch is justified. D855–D859 reject the hypotheses
that the post-graph executor is mostly idle, that a string-only macro fix
materially shortens the package, or that naive official `gsc` batching saves
the small-job tail. The remaining large cost is broadly distributed native
compilation plus the graph dependency ramp; a future candidate must target
work common to many files, preserve GCC runtime optimization, and prove a
substantial adjacent gain on the **uninstrumented** D851 toolchain. Repeat
both real-consumer gates (POO and MCP) before release admission. Do not infer
the uninstrumented D851 absolute time from this diagnostic run: per-job logs
and temporary instrumentation alter package wall time.
