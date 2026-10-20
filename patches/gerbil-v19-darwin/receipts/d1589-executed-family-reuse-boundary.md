# D1589: prove actual child reuse before optimizing remaining execution

## Progress And Scope

D1585 extended object coverage but did not establish actual embedded hits in
the builder child. D1586 adds private Gambit events distinguishing embedded
hits from ordinary loader fallback. The source branch requires Darwin, Mach
and GNU GCC, excludes Clang, preserves errno around observation and leaves
ordinary fallback and setup semantics unchanged. Original 317 objects, registry,
carrier and RTS inputs remain; only os_dyn.o receives diagnostic instrumentation.
Compile, link and startup smoke succeed. This observer is not a shipped patch.

The family parser now accepts both the original nine-column load census and
explicit ten-column reuse census. Matched start/end events retain the reuse
kind in their identity; successful loads are separated from successful hits.
Missing child, failed clean/boundary, unrelated process, unmatched completion,
pending operation and unknown reuse kind cannot qualify. Seven focused tests
pass. Python private drivers also pass syntax checks.

## Actual Clean And First Compilation

D1587 runs the unchanged MCP project with the observer and lookup enabled.
Actual clean exits zero in 2.990724 seconds; zero project native images remain.
The genuine first compile line appears in 7.043809 seconds, within the original
ten-second real-output and thirty-second prefix gates. The group is deliberately
stopped at that line and reaped, not claimed as a complete build.

| Executed process | Unique paths | Embedded hits | Native fallbacks |
| --- | ---: | ---: | ---: |
| Outer gerbil | 277 | 274 | 3 |
| Actual builder gxi | 198 | 198 | 0 |

All selected paths have successful matched completion; union coverage is 314,
with the previously identified 37 child-only paths present. The three ordinary
loads are the unmodified FFI images. This establishes executed reuse, not merely
presence in a generated registry or planned child PATH.

Outer native events span launch +0.045865 to +1.117337 seconds. Child native
events span +1.182003 to +2.236110 seconds. There are no further observed native
load/reuse calls before first compilation at +7.043809. The roughly 4.8-second
interval after the last completed native event remains. This is a bounded
instrumented event timeline, not full CPU attribution or a clean speed ratio.

Event duration sums are 0.037871 seconds outer and 0.029681 seconds child. These
exclude the registry lookup performed before recording a hit, Scheme module
initialization and setup work after the loader returns. Do not equate them to
all native/initialization costs, or compare instrumented sums to uninstrumented
elapsed times as an acceleration claim.

## Remaining Executed Path

D1588 samples the actual same candidate's builder child with lookup explicitly
enabled and libproc-verified binary identity. The corrected sampler drains
product output during child discovery. Real first compilation is observed and
the group is reaped. It is a disturbed build-only diagnostic, not a replacement
pass for D1581's failed clean/build ABBA or a product performance comparison.

Its short stack contains expander core/stx, runtime mop/hash/table, GC scanning,
symbol lookup and directory normalization rather than the earlier child's
dominant dynamic-loader stacks. Counts are overlapping wall-stack samples;
they do not establish whole-window CPU shares. Existing D1088/D1246-D1252 already
bound directory normalization and reject a filesystem-cache rewrite as the major
fix; that research is not repeated as a new candidate.

## Decision

Do not reinterpret D1581/D1584 failures or the D1582 regex-test benefit as a
resolved cold-build objective. Keep existing 0001, 0007 and GCC preprocessing
patches unchanged. Further adding native paths to this already observed family
cannot remove the measured post-load interval. The next major source change
must reduce remaining executed work and preserve escaping object identity,
poll/GC semantics, rebinding and initialization order; prior failed broad
inlining, fold fusion, generic O2/O3 and GC-only routes remain negative evidence.

Full toolchain delivery and the seven-to-eight-second objective remain open.
No consumer/std/make/std/test/HTTP source, installed toolchain, timeout, security
policy, Git commit or push is changed. All owned sessions are terminal.

Private evidence: `.data/d1586-family-reuse-census-source/`,
`.data/d1586-family-reuse-census/`, `.data/d1587-family-reuse-hit-census/`,
`.data/d1588-family-reuse-enabled-child-stack/`.
