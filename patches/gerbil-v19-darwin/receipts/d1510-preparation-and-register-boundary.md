# D1510 Preparation And Register Boundary

No runtime candidate, new speedup or full-test qualification. Preserve the
historical 47.771713 / 47.824226 / 47.927094-second cold anchor and whole-task
5 / 50 / 112-second gates. The original frozen binary remains unchanged.

## Existing Execution Evidence Changes The Research Choice

[The existing eval split](d1510-gambit-eval-platform-boundary.md) already
separates Gambit preparation, demand handling and execution. Observed begin
preparation is 0.004179 / 0.003445 / 0.011773 / 0.023353 seconds for
make/test/json/list; execution is 0.129284 / 0.054290 / 0.853369 / 0.214627.
These are instrumented observations, not speed measurements or an additive
whole-process budget. Do not rerun that split or construct an interpreter-code
cache as a seconds-scale remedy on this evidence.

Likewise the old test CPU split records Gambit compilation at 0.019032 seconds
versus execution at 0.450757 seconds; see
[the execution receipt](d1510-execution-cost-and-spawn-extension.md).
This does not prove that Gerbil macro preparation is cheap: Gambit compilation,
Gerbil lowering, Scheme macro execution and live interface construction are
different boundaries. It limits the idea of saving the current interpreter's
compiled code. It does not newly reject every compiled-interface architecture.

## GNU GCC Register Representation Actually Checked

The Emacs paper's section 3.8 describes isolating call argument arrays to
avoid clobbering unrelated values. Gambit's header already implements local
GVM variables with explicit processor-state import/export. The new audit
preprocesses three hash-verified, native-text-equivalent captured C inputs:
compiler/base~1, std/make~0 and std/make~1. It uses Bazel's GNU GCC environment
and the retained driver definitions, without compiling or linking a binary.

All three actual preprocessor outputs select GNU GCC 16 / Apple, 5 GVM
registers, 3 argument registers and maximum 25 local GVM registers. R0/R1/R2
expand to local r0/r1/r2 variables. R1's declaration is a local word;
processor-state loads/stores are explicit separate macros. Every original
capture input and the frozen binary is checked unchanged after the audit.

This excludes the premise that these retained translation units leave all
ordinary GVM registers in an opaque shared argument array. It does not prove
hardware register residency, absence of spills, compiler alias precision,
cross-module behavior or the representation of every retained unit. Removing
processor-state publication would require roots, GC, foreign calls, interrupts
and continuation contracts, not simply a new register flag.

Private evidence: `.data/d1510-gvm-register-layout-v1/report.json` and three
macro transcripts. Audit exit zero; five parser/branch rejection tests pass.
All subprocesses are terminal. No original Scheme source, C object, installed
toolchain, build/test deadline or consumer fixture changed.

## Next Source Boundary

Continue inside reached non-GC Scheme execution, distinguishing interface
import binding and actual phase initialization. Neither the generic Emacs
frame-layout recipe nor Gambit interpreter-code caching has a demonstrated
large uncovered opportunity here. Do not spend a cold/full-test campaign on
those premises. A new candidate still needs a distinct reached mechanism,
semantic equivalence and actual end-to-end admission.

## Multiple-VM Profile: Distinct Global Access Protocol

Current source/release recipes request --enable-multiple-vms and --enable-smp.
Gambit's configure.ac has independent options for multiple-vms,
multiple-threaded-vms and smp; SMP alone does not select either other option.
This must not be confused with the frozen SINGLE_VM measurement line. Read-only
inspection of the installed older 2591dcd release finds a receipt without
multiple-vms and configured SINGLE_VM/SINGLE_THREADED_VMS header defaults.
That older installation is not executed, benchmarked or used as a candidate.
Recipe intent and that older installed artifact do not establish a current
multiple-VM native branch or its cost.

The current multiple-vms-global-capacity patch introduces two acquire pointer
reads in glo_cell_in_vm: the VM's table root and its segment pointer. It keeps
old roots linked and segment addresses stable until VM disposal. These are
not lookup-result caches: Scheme global-cell values remain live mutable cells.
An activation-local cache of a previously acquired segment, keyed by VM and
segment index, is therefore a distinct protocol hypothesis. It cannot remove
the acquire reads on a miss or silently use another VM's segment.

`tests/gambit_glo_segment_cache_probe.c` implements an isolated native memory
protocol prototype, not a changed Gambit header or generated GVM macro. GNU
GCC 16, O1, the existing Bazel SDK/compiler environment and strict warnings
compile it. Twelve hardware-derived concurrent invocations each pass seven
exact cases and final PROTOCOL-OK: initial identity, live cell read/write,
last-cell boundary, VM isolation/return, stable old segments across table
growth, segment misses/in-capacity publication and concurrent publication.
All owned processes exit zero. Source SHA256 is
`338182d8d26962b18ee9d2632db5d0de4f8ab02dc6953ef8de4c41dd4ce83dab`.
Evidence: `.data/d1510-glo-segment-cache-protocol-v2/report.json`.
The v1 attempt is blocked by sandboxed hardware discovery before compilation
or any probe launch; it is not a protocol failure or timing observation.

Read-only inspection of the GNU-built ARM64 probe shows two LDAPR instructions
in original_cell. cached_cell retains two on misses, while its hit path uses
ordinary cache-field loads, comparisons and branches. Fewer acquire operations
does not prove fewer instructions, lower latency or a speedup. This is also
not evidence that ARM acquire behavior uniquely penalizes Darwin relative to
Linux. No component ratio or whole-toolchain saving is measured.

The probe covers its synthetic stable-segment publication protocol only. It
does not establish current-profile hit coverage, complete Gambit VM switching,
GC/FFI/continuations, arbitrary external publication, teardown safety or global
cell synchronization semantics. Its ready/done handshake explicitly provides
publication ordering; that cannot be assumed for every runtime caller.
Integration must prove those boundaries and preserve ordinary fallback.
No production patch, compiler-option change, release or frozen-runtime change
is made. No new first-log/cold-build/full-test result follows. Historical
47.771713/47.824226/47.927094 cold results and 5/50/112 gates remain separate.

## Ideal-Hit Cost And Mainline Eligibility

The same private C probe now has an optional ideal-hit rejection check. Both
accessors inline into their respective loops; both perform the same volatile
live-cell loads, index traversal and checked checksum. One VM and one segment
remain selected throughout. Each invocation executes original/cached/cached/
original/original/cached, 8,388,608 reads per loop. Process CPU is sampled only
around each loop, after the joined publication test. This intentionally ideal
locality is not a captured runtime trace or a current-profile hit distribution.

GNU/Bazel compilation and twelve physical-core-derived concurrent invocations
complete: all seven protocol cases and all six checksum-verified loops pass
per invocation. Thirty-six original CPU observations average 5.590306 ms;
thirty-six cached observations average 4.062583 ms. The median per-process
original/cached mean-CPU ratio is 1.396494; observed ratios range 1.078443 to
1.620032. These small, synthetic process-CPU intervals establish only reached
component work under ideal locality. They do not estimate whole build/test
gains, miss penalties, actual GVM register/spill behavior, core-class residency
or a Darwin/Linux ratio. No ratio here is performance admission.

The GNU native original loop retains both LDAPR reads on every iteration.
The cached loop performs them on misses and retains the acquired segment in
a register on hits; ordinary reads and checksum updates remain in both loops.
This confirms that the benchmark executes its accessors rather than having
the source reads or whole loops optimized away.

Evidence: `.data/d1510-glo-segment-cache-ideal-cost-v1/report.json`.
Updated probe source SHA256:
`cbba11be26c4acbe5fcbfd9cc0cd855e0e0307b70923b6bdacc29ee8d7be08b7`.
The prior protocol binary/receipt remains unchanged; the new source version
is not represented as the old SHA's content. All child processes are terminal.

Most importantly, the three already captured GNU preprocessing transcripts in
`.data/d1510-gvm-register-layout-v1` select SINGLE_VM and expand GLOCELL(x) and
GLOCELL_IN_VM(vm,x) directly to x. This segmented lookup is absent from that
retained measured configuration. Therefore the idea is not selected for
integration into the 47-second mainline. Adding activation caches there would
not remove the measured original operation, and rebuilding the host merely
to manufacture the different branch would not be a matched optimization.
Retain the private component finding for separately qualified multiple-VM
work; require an actual selected artifact and reached-cost/hit evidence before
runtime integration. No cold-build or full-test campaign follows this check,
and no production patch, commit or publication occurs.
