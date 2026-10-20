# D1375: original official prefix versus Darwin teardown

## Identity and execution

Canonical `v0.19-staging` was checked live at
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. The isolated original Gerbil
binary SHA-256 remains
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.
MCP source is the existing D1267 head
`9a5c35e275e5d6847ff421151bb224f2eae177c1`, copied into a fresh local
checkout without build artifacts. No consumer or production source changed.
The current host has 12 physical cores and 32 GiB memory; the diagnostic uses
12 jobs and the existing Bazel-discovered GNU GCC 16 environment.

D1372 and D1373 stopped before build: official clean returned zero but old
checkouts retained 550 native images. Neither run supplies cold-start data.
No uninstall or manual removal was used to make that check pass.

D1374 used the fresh checkout. Official clean left zero project native
images; the first real compile line appeared at 6.112 seconds. Its attached
parent-process hardware trace failed native-runtime sample admission and is
not used for cost attribution. A diagnostic analyzer name change was tried
and reverted: original gerbil/gxi are identical binaries, so naming was not
the missing coverage mechanism.

D1375 prearmed CPU Profiler, ran official clean/build, observed the actual
official parent and `build.ss compile` child, and deliberately stopped after
the first real compile line. Clean took 2.576 seconds; first compile appeared
at 6.058 seconds. The original 30-second clean and 10-second output gates
passed. These instrumented observations are not a speedup or completed build.
Raw traces and analysis scripts are retained only under project `.data`.
Other-process rows from the recorder are excluded from analysis.

## A material boundary correction

The recorder's ready notification does not establish complete prefix coverage.
Effective trace duration is 5.222 seconds, shorter than the 6.058-second
build prefix. The build log contains exactly one flushed write:
`... compile util/compat`. Its retained filesystem modification timestamp,
the trace start timestamp, and a conservative 5 ms rounding margin define
the analysis cutoff. This is retained timestamp evidence, not a synchronized
in-process signpost or proof of whole-prefix coverage.

Without this cutoff, the process-family trace attributes 17.06 percent of
sampled cycles to dyld self and 16.96 percent to Atlas-inclusive stacks.
After the cutoff, 11,489 Running samples remain, with original binary
UUID/hash validation. The retained samples cover the actual build child
over approximately 3.94 seconds of trace time. Categories overlap.

| Category | Sampled active-cycle share before conservative cutoff |
| --- | ---: |
| expander core host | 12.51% |
| expander stx host | 10.86% |
| mark_array | 12.60% |
| mark_array.constprop.4 | 9.28% |
| dyld image self | 0.86% |
| dlopen stack inclusive | 0.87% |
| Atlas stack inclusive | 0.86% |

These are partial Running-cycle shares, not full wall-time attribution,
exclusive instruction latency, or proof that GC itself is Darwin-specific.
Missing initial coverage must not be filled with passive-preparation data.

The excluded post-boundary Atlas stacks include the concrete chain
`___cleanup_dyn_module -> dlclose -> removeImages -> generateAtlas`.
They carry 2,108,026,389 sampled cycles. Original Gambit os_dyn.c explicitly
loops over loaded handles and calls dlclose during dynamic-module cleanup.
Apple's published
[ExternallyViewableState source](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/ExternallyViewableState.cpp)
corroborates Atlas regeneration on image removal. Published main is not the
installed OS source identity. No claim is made that profiling alone causes
this path; here it is observed after the diagnostic stop boundary.

## Consequence

Darwin unload/Atlas work is a concrete teardown mechanism, not a qualified
solution for first-log macro execution. It may matter for full process/test
latency, but a terminating diagnostic cannot qualify normal-exit savings.
Any future process-exit mitigation must preserve explicit/embedded cleanup,
library finalizers and Linux behavior and pass actual concurrent tests.

No loader-packing candidate is reintroduced, no generic optimization is
renamed Darwin-specific, and no full toolchain build starts on this evidence
alone. The seven-to-eight-second major-cost objective remains unresolved.
