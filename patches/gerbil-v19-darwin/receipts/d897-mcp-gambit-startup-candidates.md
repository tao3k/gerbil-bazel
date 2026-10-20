# MCP Gambit Startup Candidates

Date: 2026-10-03. No new startup acceleration is admitted. The target remains
official `gerbil clean` followed by `gerbil build`, measured to the first real
compilation line. std/make, GXPkg, HTTP and MCP sources are unchanged.

## Identity

- Latest remote v0.19-staging, rechecked this turn:
  `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
- Gambit gitlink: `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
- Real GNU GCC 16.2.0; hardware capacity 12 cores.
- MCP historical sample source: `9a5c35e275e5d6847ff421151bb224f2eae177c1`.
- Fresh native project roots and all raw evidence remain under project `.data`.
- Host load exceeds the existing performance gate; timing observations are
  candidate screening, not attributable speedup percentages.

## Completed Gates

| Run | First Compile | Complete Build | Boundary |
| --- | ---: | ---: | --- |
| D891 control | 9.255 s | 111.728 s | Original D884 toolchain |
| D892 aggregation, second access | 8.301 s | 108.429 s | 104 immutable images combined into 3 |
| D893 O1 relink control | 7.890 s | 119.935 s | Original library home, relinked binary |
| D893 phase-0 O3 | Not reached | Aborted | Strict 10-second output gate failed |
| D894 syntax-phase O3 | 8.700 s | 108.320 s | 10 macro-phase images, original binary |
| D895 C cost observer | 7.588 s | 86.316 s | Instrumented diagnostic, not performance |
| D896 Gambit core O2 | Not reached | Aborted | Strict 10-second output gate failed |
| D897 Gambit core O2, no GCSE | 7.583 s | 85.018 s | Same four Gambit runtime units |
| D899 sampled core O2, no GCSE | 7.721 s | 96.778 s | 11 unchanged core generated-C units |
| D900 original binary | 8.780 s | 121.357 s | Fresh matched MCP control |
| D903 four-unit expander bundle | 8.996 s | 113.016 s | 638 fewer global jump sites, no wall gain |
| D905 full expander bundle | Not reached | Aborted | Strict 10-second output gate failed |
| D907 kernel/thread O2, no GCSE | 9.106 s | 109.954 s | Retry of D906; no startup solution |
| D909 kernel per-procedure hosts | Not reached | Aborted | Original O1; strict output gate failed |
| D911 keyword outlining retry | 9.575 s | 111.317 s | 550 images; startup CPU 7.66 s |

D892 first preparation took 91.885 seconds despite eventually succeeding.
Its second-access timing cannot erase that first-access failure. Neither the
image aliases nor the runtime optimization levels are promoted to the patch
stack. Completed cold builds produced 550 MCP native images from empty roots.

D894 also passes 12 simultaneous native runtime probes, 12 framework-import
probes, and the three real parallel std/make/std/test fixture cases. Its native
MCP initialize response is valid, reporting application version 1.1.0 and
protocol version 2024-11-05. These are functional gates, not startup success.

## Source-Owned Cost Observer

D895 instruments only Gambit's C runtime `os_dyn.c`, `setup.c`, and `mem.c`
in an isolated copy. GNU syntax checks pass before and after editing. Timing
events go to a separate file, never product output. Original library paths and
the original GSC remain selected. Evidence:

- `.data/d895-runtime-probe-build-fixed/report.json`
- `.data/d895-mcp-cost/report.json`
- `.data/d895-mcp-cost-trace.jsonl`
- `.data/d895-mcp-cost/cost-summary.json`

Before the first compilation line, the package coordinator and its build-script
child together record approximately 1.03 seconds in native loading and
1.30 seconds in GC. Setup timers are inclusive and must not be blindly added.
The original summary estimates the offset between Python's mach_absolute_time
clock and C's CLOCK_MONOTONIC; subsequent runner events now capture the native
clock explicitly. These numbers are bounded diagnostic observations, not a
whole-build or cross-platform attribution. They do not invalidate the older
first-access dyld samples or justify changing system security policy.

## Gambit Core Candidate

Gerbil's `src/gerbil/expander/init.ss` selects Gambit `##eval` as the expansion
evaluator. Gambit's `lib/makefile.in` uses `FLAGS_OPT` for Scheme-implemented
runtime objects such as `_eval.o`, `_io.o`, `_std.o` and `_system.o`, while
handwritten C runtime objects use `FLAGS_OPT_RTS`. D896 recompiles only those
four unchanged generated C inputs at O2 and relinks native Gerbil. Consumer C
flags, original GSC, headers, Scheme inputs and library image count are unchanged.
Its import smoke passes, but official MCP startup fails the strict output gate.

`configure.ac` first assembles `FLAGS_OPT` with `-fno-gcse`, then replaces it
for explicit optimization arguments. This is a source fact, not proof of a
configuration bug or the original startup root cause. GCC specifically warns
that computed-goto programs may run better with GCSE disabled:
[GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
O1 does not normally enable GCSE, so this cannot by itself explain the O1
baseline's delay. D897 tests O2 with that computed-goto constraint restored,
only for the same four Gambit runtime objects. It completes MCP with 550 native
images, passes 12 concurrent runtime probes, 12 framework-import probes and
three real std/make/std/test cases. It does not demonstrate a startup solution.

## Critical-Window Sample And Subsequent Candidates

D898 samples only the build-script child between roughly seconds three and
five of a fresh official build. First compilation occurs at 8.604 seconds;
the build is intentionally stopped there, not claimed complete. The retained
sample has 1496 main-thread samples and places the dominant observed work in
expander/core, stx, top and runtime dispatch, with GC also visible. Reader and
eval are relatively small in this window. Tail-call unwinding artifacts mean
these are hotspot observations, not exact whole-startup percentages.

Evidence: `.data/d898-mcp-first-window/report.json` and
`.data/d898-mcp-first-window/first-window.sample.txt`.

D899 applies O2 with GCSE disabled to 11 unchanged core C inputs on that path.
This is a compiler-chain experiment, not an admitted Gambit source patch. Its
original GSC and consumer flags remain unchanged. The first compile snapshot
records 6.79 CPU seconds across the live coordinator and build-script child;
this is a lower-bound snapshot, excluding already exited processes. A matched
original-binary run is recorded separately as D900. Wall-clock differences
alone are not qualification, especially on this overloaded host.

D901's first bundle-driver attempt fails on GSC option order and a relative
macro-prelude path. D902 corrects the driver to use the official absolute
prelude and SMP feature. The experimental bundle uses Gambit's existing
`##supply-module` aliases and includes the four unchanged, consecutive
common/stx/core/top inputs in official initialization order. No hand-edited
Scheme implementation, Gerbil build script, register ABI or Linux behavior
change is made. D902 reaches linking but exposes a driver identity mismatch:
the final supplied module name must match the emitted C linker ID. D903 uses
that final name for the generated filename and completes compilation, import
smoke, a 550-image fresh MCP build, 12 runtime probes, 12 framework probes and
the three std/make/std/test fixture cases. No startup acceleration is admitted.

The original-binary D900 first-compile live-process CPU snapshot is 7.65 seconds;
D903 records 7.23 seconds. These single lower-bound snapshots under differing
host load do not establish a reproducible optimization. Generated jump-site
counts are static code locations, never dynamic execution counts.

D904 extends the same unchanged-input experiment across 28 consecutive runtime
and expander units. Global jump sites drop from 6670 to 2128, but the generated
C is 14,131,202 bytes. One actual GNU cc1 process is observed at 8,161,584 KiB
RSS and 68.59 CPU seconds. Compilation exceeds the 180-second experiment bound;
its process group is terminated. The candidate never reaches a linked binary
or MCP startup measurement and is not a practical delivered optimization.

D905 limits the same strategy to the full consecutive expander slice. Its
5,128,492-byte C input compiles in 18.157 seconds; native imports and every
original Gambit module alias pass. Nevertheless, its fresh official MCP build
fails the 10-second first-output gate. This closes the current bundle strategy
as unsuccessful against the requested startup target, not as evidence of a
Scheme semantic defect or an excuse to relax the output gate.

D906 therefore returns to two sampled Gambit-owned runtime units, `_kernel.o`
and `_thread.o`, using the original Gerbil core, libraries, GSC and consumer
flags. This is distinct from D897's eval/io/std/system probe. D906 fails the
startup gate; fresh D907 completes 550 native images but records 7.60 live
process CPU seconds before first compilation. No production runtime policy is
changed.

## Exact Kernel Hotspot Mapping

D908 recompiles the original kernel with its exact official O1 command plus
debug information and disabled variable tracking. The Mach-O text section is
byte-identical to the original kernel object:
`3742a24fa4590a7f42dbeb23d41757c040cfd0fac877ab11fda69518abe31ecc`.
Only after this identity check does DWARF map sampled host offset 13604 to
generated `_kernel.c:29662`, the `END_M_SW` host-exit boundary.

The native entry reserves 16,592 bytes and the exit restores callee-saved
registers before a proper tail branch. Source inspection identifies two
`key_vals[MAX_NB_PARMS]` arrays in the keyword and keyword/rest handler blocks.
This is precise source/assembly attribution, not proof of a Darwin/Linux root
cause. The assembly has no per-entry stack-probe call or 16-KiB clearing loop;
large reserved frame size must not be mistaken for copying that many bytes.

D909 selects existing per-procedure hosts only for the original O1 Gambit
kernel. Syntax, linking and framework imports pass, but official MCP startup
fails its output gate. Both keyword buffers remain inside the same kernel
handler Scheme procedure, so this mode does not isolate them from rest/heap
handlers.

## Guarded C Keyword Outlining Prototype

D910 reads the original Scheme forms with Gambit's reader and extracts exactly
the two original C handler strings. It outlines those algorithms into private,
noinline C helpers with explicit existing heap/frame/register save and restore.
No heap allocation, Scheme implementation edit or VM register ABI change is
introduced. The generated C guard requires Darwin, genuine GNU GCC, single-host
mode and the existing five-register configuration. All other branches retain
the original C handler bodies. This is an ignored isolated generated-C
prototype, not a production SCM patch.

The first syntax attempt catches a missing terminator in the new jump macro;
only that introduced error is repaired. The authoritative repaired source hash
is in `.data/d910-kernel-outline-build-fixed/report.json`, not the earlier
preparation receipt. GNU syntax, native linking and original-library imports
then pass. Disassembly shows the common kernel host frame is now 192 bytes.

Functional gates pass:

- 12 native runtime probes, 12 framework import probes and three real
  std/make/std/test cases: `.data/d910-native-contract/report.json`.
- One identical original-GSC native fixture on the original VM, then 12
  simultaneous candidate VMs, each passing 1512 assertions:
  `.data/d910-keyword-contract-fixed/report.json`.
- Coverage includes defaults, duplicate and invalid keyword arguments, both
  rest/keyword orders, 1500 500-rest-argument calls, 60 explicit GCs per run,
  continuation escape and an actual C-to-Scheme callback. The first fixture
  attempt uses an unsupported generic C-function conversion and fails on the
  original VM too; it is corrected to Gambit's documented c-define callback.

D910's first MCP run fails the strict startup gate at about 6.06 observed CPU
seconds. Fresh D911 completes with 550 native images and peak 12 GCC workers,
but records 7.66 live-process CPU seconds before first compilation, essentially
the same single-observation value as D900's 7.65 seconds. The physical frame
reduction is real; it is not a demonstrated startup acceleration and is not
promoted. The native MCP executable still links the original library archive,
so these prototype receipts qualify the new GXI macro execution, not a fully
rebuilt runtime in every tool or final MCP binary.

D912 next tests per-procedure hosts only for the two most sampled expander
units, core and stx, with original O1, INLINE_JUMPS, headers, GSC and consumer
flags. It targets register-load scope and indirect-target fan-out, not the
rejected keyword frame hypothesis. It records a 10.142-second first compile and
8.53 live-process CPU seconds, then fails the strict product-output gate. It is
not a completed build or an acceleration. The observer now also checks each
line's arrival gap, closing a one-second polling race without relaxing the
existing ten-second gate.

## Actual Host Entry Counts And Further Rejections

D913 adds isolated, Darwin/GNU-only generated-C entry counters to the eleven
previously sampled units. The original O1, single-host mode, GSC, VM ABI and
consumer flags remain unchanged. Each process/module has its own mapped counter
and the observer reads only this command's descendants. Counter increments add
execution work; this is diagnostic evidence, not a timing candidate.

Before the ten-second output gate aborts the run, the build child has entered
these eleven hosts 482,024,162 times. Core and stx account for 113,359,729 and
104,375,927 entries; mop, interface and hash account for 71,659,859, 58,408,818
and 60,019,960. These are incomplete-window actual counts, not percentages of
startup CPU, and they do not independently establish the Darwin/Linux cause.
Raw samples: `.data/d913-mcp-measure/report.json`.

D914 uses Gambit's existing compilation-unit mechanism for the contiguous mop,
mop-system-classes, error, interface and hash modules, preserving contents,
initialization order and module aliases. Generated C is 4,089,088 bytes; GNU
compilation takes 15.799 seconds. Twelve native probes, twelve imports and the
real std/make/std/test fixture pass. The first MCP timing overlaps this task's
contract test and is explicitly excluded from performance inference. A fresh,
non-overlapping D915 run records first compile 10.329 seconds and 7.81 live CPU
seconds, fails the strict output gate, and does not qualify an acceleration.

D916 tests distributed external host exits only under Darwin/GNU, existing
single-host, INLINE_JUMPS and exclusive proper-tail-call configuration. It
retains original PC and full VM state saving and calling conventions. Distinct
zero-instruction asm operands prevent merging identical exit sites. Original
generated inputs are retained, and only isolated generated-C copies change.
Disassembly confirms native indirect branch sites increase from two per core,
stx and mop object to 1810, 571 and 2053 respectively; these counts include
computed-goto sites and must not be read as dynamic branch counts. The initial
MCP run fails before first compile at 10.725 seconds with 6.83 live CPU seconds.
There is no completed-window CPU or first-log gain to claim. Raw build and
measurement receipts remain under `.data/d916-distributed-exits/` and
`.data/d916-mcp-measure/`.

## Complete Preparation CPU And Register Bridge

D917's framework/compiler imports and D918's unchanged MCP script expansion
cost only about 0.54--0.61 CPU seconds. They do not reproduce the long window.
The source preparation loop in std/make imports every build-spec module before
workers can emit their first compile line. D919 therefore executes those same
import-module calls for all 187 original MCP specs in an isolated process,
without calling main, compiling files or changing std/make. This is a CPU
diagnostic, not a substitute for official clean/build or its ten-second gate.

The initial diagnostic uses a nonexistent stx->datum alias and fails on the
baseline. The corrected syntax->datum version passes all four ABBA executions.
D916 distributed exits consume 6.698 and 6.701 CPU seconds versus baseline
7.085 and 7.289. These limited observations do not remove the main cost or
qualify official startup acceleration.

D920 applies Gambit's existing bounded inlining heuristic only to the same
five runtime modules: limit 1000 versus default 370, original GNU O1 and unchanged
module inputs/order. Generated C grows to 5,050,747 bytes, below the six-MiB
experimental budget. Its first CPU diagnostic times out on the original
baseline, before testing the candidate. The progress-recording repeat imports
all 187 modules in each run: candidate CPU 6.996 and 7.062 seconds, baseline
7.261 and 7.406. Host load is about 93--97; no official first-log gain is claimed.
Per-module diagnostic progress never changes official MCP output or its gate.

D921's isolated private register bridge retains original one-argument public
hosts, label layouts, GSC and archive. Its private eight-register-argument
calls carry PC, FP and all five GVM registers only between selected builtin
hosts. Heap and PC are synchronized at exits; original full state synchronization
and reloads remain on GC/FFI paths, and legacy exits save all original fields.
It admits only Darwin/GNU, single-host, label-value, exclusive proper-tail-call,
five-register and single-processor configuration, and verifies complete register
declaration/read/write sets. Unregistered hosts or registry collisions fall back
to the public path. Dynamic bridge image unloading is not qualified.

The first GNU compile catches the prototype's missing host forward declaration;
the fixed candidate links and passes imports. Native disassembly confirms the
public stx wrapper tail-branches without adding a C frame. Twelve runtime probes,
twelve imports and the real parallel make/test fixture pass. An identical old-ABI
image compiled by the original GSC then passes on the baseline and twelve
candidate processes, each with 992 assertions, 330 explicit GCs, C callbacks,
five-value transfer, exceptions and continuation escape. Original effective
bridge sources are retained as `.data/d921-private-register-bridge-fixed/`
`gambit-private-register-bridge.original.h` and `.original.c`; later builders
freeze and hash their effective helper sources directly inside each output.

Despite functional qualification, complete preparation CPU is 7.301 and 7.358
seconds versus baseline 7.522 and 7.292. The ranges overlap: the generic bridge
does not establish acceleration and is not promoted.

D922 records real directed exits over complete 187-module preparation, not a
performance result. The 527,837,195 observed exits include hash->table 33,002,588,
mop->interface and interface->mop each 31,866,928, interface->hash and reverse
each 31,866,835, core->hash 31,864,703, table->core 31,742,370, core->stx 25,479,912
and stx->core 24,840,469. Large unregistered/legacy destinations remain: core
57,402,874, stx 55,248,018 and mop 42,160,040. This motivates inspecting actual
primitive lowering instead of assuming only core/stx boundary removal is enough.
Raw graph: `.data/d922-host-edges/11988-edges.tsv`.

Generated C explicitly calls Gambit's structure-instance-of? primitive from many
stx/core/mop sites. `_kernel.scm:4932` defines a nonallocating structure predicate
and type-id/super-chain loop. D923 is a count-only generated-C probe for this
exact primitive; its first syntax gate catches an incorrect FFI-only argument
macro, repaired to the existing SET_NARGS state field. Neither an inline
acceleration nor a production primitive patch is qualified yet.

### D923-D924 Bounded Structure Primitive

The completed D923 preparation records 115,153,945 actual calls to the exact
primitive: stx 43,487,060, mop 37,234,516 and core 33,954,993 dominate. These
diagnostic counts are not timings. The C backend already lowers direct-instance
checks, but does not inline this inherited-instance predicate.

D924's isolated Darwin/GNU generated-C probe walks at most four descriptor
nodes without allocation. Deep or cyclic unresolved chains retain the original
primitive; wrong arity retains the original exception path. No descriptor cache,
VM layout change or consumer flag is introduced. The effective helper hash is
`55ba3a84d285948c768bdee24ea8d9d8ba0275d01e15eb02ce984b8b0186402f`.

The first native fixture did not use extended bindings and therefore did not
exercise JUMPPRM. The corrected fixture does: retained C independently shows
the optimized primitive calls and the first-class original reference calls.
Baseline and twelve processes pass 6607 assertions each, including twelve-level
inheritance, bounded fallback, cyclic cutoff, wrong arity and explicit GC.
Evidence: `.data/d924-structure-primitive-contract/`.

Complete 187-module preparation in ABBA order consumes CPU seconds:
baseline 7.222, candidate 6.395, candidate 6.326, baseline 6.884. This is a
directional reduction in actual execution cost, not removal of the startup
bottleneck and not a qualified wall-time acceleration under external host load.
Evidence: `.data/d924-mcp-preparation-cpu/report.json`.

The candidate passes twelve runtime probes, twelve std/make/test imports and
the real cold/no-op/incremental make/test fixture. Configured capacity is twelve;
observed peak is eleven GNU frontends, not twelve. The fresh MCP official
clean/build still fails the unchanged ten-second no-output gate before the
first compile line. It is not delivered as a successful cold-start fix.
Evidence: `.data/d924-native-contract/` and `.data/d924-mcp-cold/`.

D925 next tests the measured table/mop/interface/hash boundary with a contiguous
nine-unit bundle, unchanged initialization order and a six-MiB C budget. Its
first launch used the candidate's cloned runtime HOME and stalled at metadata
import (0.52 seconds child CPU after 37 seconds wall); its own process group
was stopped. The corrected builder uses the verified original runtime HOME,
admits candidate objects only with identical GSC/archive/header hashes, and
retains each overlaid object hash. Neither outcome is an acceleration claim.

The experiment builder rejects non-Darwin hosts and Clang, verifies GNU GCC 16,
and uses hardware-derived parallel capacity. No production source patch, Linux
behavior change, installation replacement, commit or push is claimed.
