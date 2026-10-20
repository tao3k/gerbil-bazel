# D1510 Native Loader Boundaries Tested

## Decision

No production optimization is admitted. The isolated timing host is DENY at
the retained first-log gate; it is not a new faster baseline. The existing
47.771713/47.824226/47.927094-second cold anchor remains unchanged and its
artifact/helper verifier passes. The historical complete test remains
105.750982 seconds, 39 files and 965 cases passing; the later strict 112-second
wave remains incomplete/DENY. None of those historical times is a fresh rerun.

## Code And Real Execution

tests/probe_retained_native_loader.py recompiles only diagnostic native-loader
and setup objects, linking the retained GNU GCC objects/providers, private
reader runtime objects and unchanged original archive. Every retained input
object and renamed provider is hash-checked. Activation is restricted to an
isolated Darwin output. All original checks, calls, return values and setup
marking are retained; no digest bypass or initialization suppression occurs.

The code measures elapsed intervals, not exclusive CPU time:

- Original-file SHA-256 verification inside provider lookup.
- Provider lookup including verification, with verification subtracted for
  the reported provider-own interval.
- Actual fallback dlopen calls inside the dynamic loader (not all process
  loader activity or pure kernel mapping cost).
- linker_to_mod_or_lnk and setup_modules reached from os_load_object_file.
  setup_modules does native runtime registration/fixups; it is not the whole
  subsequent Scheme module body. Initial main-image setup is not instrumented.

Private .data/d1510-native-loader-boundaries-v2/report.json contains 24 completed
fresh-process control/probe executions: four independent standard-library
imports, three rounds, alternating pair order. The later v3 adds native
registration timing and also completes all 24 executions. Export name/phase
and native-module inventories agree pairwise. This is not equality of all
export values or full Scheme semantic conformance. Observer/relinking overhead
and wall-time variation preclude interpreting pair differences as speedups.

In v3, observed elapsed ranges in milliseconds are:

| Library | Digest verification | Fallback dlopen | Dynamic native setup |
| --- | ---: | ---: | ---: |
| std/make | 19.308-24.163 | 21.729-157.050 | 19.083-70.481 |
| std/test | 8.190-20.853 | 0 | 9.381-24.137 |
| std/encoding/json | 111.829-165.477 | 12.976-43.731 | 167.569-227.066 |
| std/list/list | 6.888-23.995 | 0 | 6.025-16.983 |

std/test and std/list/list record zero fallback dlopen calls; native providers
still verify files and register modules. These observations do not support
a several-fold improvement by removing only the measured dynamic-load costs.
They do not exclude pre-main loader costs or establish Linux causal parity.

## Original Standard Tests

tests/run_loader_stdlib_controls.py runs unmodified retained list/list-test.ss
and encoding/json/json-test.ss through actual `gerbil test -v 5`. Control and
probe executions run concurrently using physical-core discovery (12 workers
on this host), isolated package home and selected toolchain HOME. Exit zero
and final OK are required. Both files pass on both hosts; source and binary
hashes remain unchanged. This is two original files, not the entire std suite
and not the full MCP suite.

.data/d1510-native-loader-stdlib-controls-v1/report.json records:

| File | Control | Diagnostic |
| --- | ---: | ---: |
| list/list-test.ss | 3.521100 s | 3.148689 s |
| encoding/json/json-test.ss | 4.988881 s | 5.490456 s |

No stable performance claim follows from this single concurrent wave. The
The later v2 wave additionally checks every CASE against CASE-OK, rejects all
failure statuses, and compares case identities between hosts: 32 list cases
and 33 JSON cases pass on each host. Its concurrent four-process wall time is
6.504591 seconds (control files 4.806155/6.406991 seconds; diagnostic files
5.129397/6.497256 seconds). This remains focused semantic validation, not full
test performance admission. Python loader-counter/import/case parsers pass
23 tests.

## Real Cold Build And Hard Denial

.data/d1510-native-loader-cold-v3/report.json records the actual clean/build:
clean completes in 3.804273 seconds, exit zero, with zero remaining native
images. Build is killed at 5.020619 seconds because no first real compile log
has appeared. Cleanup confirms the child is reaped with terminal exit -9.
There is no complete build time and no full test run for this denied host.
The 50-second build gate is unchanged, not exercised to completion here.

Two earlier cold invocations failed before execution because the diagnostic
report used the retained binary identity rather than the new host identity,
then because path resolution followed an exported symlink back to that report.
The separate export-host manifest now carries the exact copied diagnostic
binary hash. These are harness failures, not build performance observations.
The first v1 diagnostic invocation was blocked by sandbox sysctl access; v2/v3
use authorized host discovery. Original reports are not rewritten.

Per-process native counters are written at normal exit. Counters from a killed
build process are absent; surviving child/clean counters cannot be assigned
to the first-log window merely because they share the experiment directory.

The next candidate needs a remaining executed cost outside these measured
intervals, with a large removable budget. Digest skipping, narrower test
inventory, repeated rejected packing and a compiler switch are not admitted.
No numbered production patch or GitHub push is made by this experiment.

## Dynamic Registration Passes

The next diagnostic splits the existing `setup_modules` interval into three
original `for_each_module` calls, only when `collect_undef_glo` selects dynamic
setup. The initial setup path delegates unchanged. Each callback, result check
and early error return is preserved. Receipt validation requires each pass
to complete once per original dynamic setup and their sum to remain inside
the outer observed setup interval.

Importantly, `setup_modules` is registration/preparation, not execution of the
Scheme module body. `setup_module_collect_moddescrs` calls `setup_mod`, the C
setup callback. Do not call this measured interval Scheme initialization or
assign it entirely to the operating system's Mach-O fixups.

The new 24 control/probe processes complete three alternating pairs for each
original independent standard library. Export/native-module inventories match
pairwise, all original objects and sources remain unchanged, and the frozen
binary SHA256 remains `1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
The isolated diagnostic SHA256 is
`82cf657d9ad7fea4d085a148806b30c01f9c56ed4c3fd003f4c56aa2ab064cc0`.

| Library | Original dynamic setup calls per process | Fixup range over three probes |
| --- | ---: | ---: |
| make | 98 | 20.141-36.841 ms |
| test | 69 | 8.159-9.205 ms |
| encoding/json | 254 | 107.560-124.148 ms |
| list/list | 60 | 4.488-5.471 ms |

Across these probes undefined-global collection is 4-68 microseconds and the
descriptor/C-setup pass is 10-90 microseconds. Fixup is the dominant reached
registration pass, but not a seconds-scale whole-import explanation. Its source
includes name/global interning, alignment and reference/label preparation.
These are Gambit operations; measured time may also include faults/scheduling.
No removable budget or Darwin-specific causal share follows from the totals.
Do not reopen the rejected relative-label/GOT routes from this result.

The original list and JSON test files also finish on original and diagnostic
hosts: all 65 cases per host pass, with exact case outcomes, final OK and exit
zero. The four processes run concurrently. Probe wall times are slower in
this observation; neither diagnostic timings nor these two files qualify a
full test suite, cold build or speedup.

Evidence: `.data/d1510-dynamic-runtime-passes-v1/report.json` and
`.data/d1510-dynamic-runtime-stdlib-controls-v1/report.json`.
Selected Python diagnostic regression tests: 36 passed. All processes are
terminal and reaped; no complete build/test run, performance gate change,
runtime optimization admission or publication occurs.

### Fixup Detail Follow-Up

The optional `--fixup-detail` instrumentation times four disjoint regions
inside the original dynamic `setup_module_fixup`: global names, symbol and
keyword names, constant/object references, labels and frame descriptors.
Initial registration, already-fixed modules, version/ABI checks and original
early errors remain unchanged. Successful receipts require four matching
completed segment counts and a sum within the outer fixup-pass interval.
The untimed residual includes preceding preparation and observer overhead;
it is not assumed to be zero or exclusively OS work.

All 24 original/probe standard-library executions finish and match inventories.
The frozen binary and original object/source identities remain unchanged.
Private diagnostic SHA256:
`17c9f2af072ff5c24b094c9026bbc525d802ff719afd84d97b06cfbe66bcf25d`.

For JSON's 254 observed dynamic modules, three probe intervals are:

| Fixup region | Round 0 | Round 1 | Round 2 |
| --- | ---: | ---: | ---: |
| Global names | 19.117 ms | 18.316 ms | 17.788 ms |
| Symbol/keyword names | 51.732 ms | 86.566 ms | 48.067 ms |
| Object references | 28.322 ms | 18.546 ms | 15.260 ms |
| Labels/frames | 3.983 ms | 2.320 ms | 2.049 ms |

These elapsed observations are not candidate/control gains, pure CPU budgets
or measurements of exclusive page faults. In particular, this label/frame
coverage does not support reopening the rejected relative-label/GOT routes
as a seconds-scale solution. The source's UTF-8 symbol lookup already returns
an existing interned symbol before allocating its name; do not assume every
loaded global/symbol name causes a new permanent string allocation.

Original list and JSON tests also finish on the new diagnostic and frozen
control: 65/65 cases per host, exact outcomes, final OK, exit zero, unchanged
test sources and binaries. Four independent processes run concurrently.
This is focused correctness, not full-suite or performance qualification.

Evidence: `.data/d1510-dynamic-fixup-detail-v1/report.json` and
`.data/d1510-fixup-detail-stdlib-controls-v1/report.json`.
Selected Python diagnostic tests: 37 passed. All processes are terminal.
No runtime optimization candidate or changed acceptance baseline is admitted.

## Initial Runtime Boundary Follow-Up

The optional initial-setup diagnostic closes an explicit gap in the earlier
v3 coverage, rather than rerunning that dynamic-only experiment unchanged.
It times five disjoint original calls: setup_os_and_mem, initial
linker_to_mod_or_lnk, init_symkey_glo1, init_symkey_glo2 and initial
setup_modules. Every successful observed process must execute each once.
Original calls, result checks and early returns remain intact. This is not
a production performance patch or complete continuation/error conformance.

.data/d1510-initial-runtime-boundaries-v1/report.json records 24 completed
control/probe imports of the same four standard libraries. Export/phase and
native-module inventories agree pairwise. The five initial intervals sum to
3.424-13.684 ms across its twelve probe processes. These intervals do not
include all runtime initialization or pre-main Mach-O loading, but do not
justify treating static module registration as the remaining seconds-scale
optimization target on this retained composition.

A separate diagnostic adds parent/child timestamps from the same
CLOCK_MONOTONIC API. It verifies that the child's first observed setup point
and normal-exit report lie within the parent process interval. The initial
point is before setup_os_and_mem, not the C main entry; time before that point
also includes process creation and preceding runtime/argument setup. It must
not be labeled exclusive dyld time.

.data/d1510-initial-runtime-clock-v1/report.json records one completed empty
startup: 1.701884 s total, 1.251970 s before that initial point, 0.415761 s
between the initial point and exit reporting, and 0.033941 s until the parent
observes completion. Its five measured initialization calls total 10.775 ms.
No kernel/provider cause is assigned to the large initial prefix.

tests/run_initial_runtime_clock.py reuses that exact diagnostic binary without
another link or mutation. Five alternating empty-startup pairs all emit the
original BOOT-OK and exit zero. The diagnostic's launch-to-initial intervals
are 5.947, 12.398, 17.257, 22.411 and 11.113 ms; its five initialization sums
are 4.570, 5.507, 17.717, 4.939 and 6.476 ms. All five boot processes record
35 native-provider calls and zero fallback dlopen calls. This does not include
all process loader work. Control wall times are 0.185588-0.264073 s; diagnostic
wall times are 0.198864-0.456978 s, with no acceleration claim. Parent timeout
polling/report cleanup is separately visible and remains inside command wall
time. The first new-host prefix is not a sustained cost in these repeats and
cannot be extrapolated into the real build's macro-expansion interval.

Private repeat evidence: .data/d1510-initial-runtime-clock-repeats-v1/report.json.
The diagnostic identity is
aeb2713eaaa6eed6b2fe1ce5e4dac1bf4c8c688fa9363f5146c601756782eea1.
The retained original binary, all selected native objects and source setup.c
remain hash-verified and unchanged.

The clock host also passes the two original standard test files on both
roles: 32 list cases and 33 JSON cases per role, original CASE/CASE-OK
inventories matching, final OK and exit zero. Concurrent wave duration is
reported in .data/d1510-initial-runtime-stdlib-controls-v1/report.json; these
focused cases are not full std or MCP test admission. Loader/clock/import
parser regression checks pass 26 tests. No complete cold build is rerun for
this diagnostic, no threshold changes, and no new baseline follows. The
next candidate still needs a distinct executed cost with a major removable
budget; static registration shortcuts are not supported by this follow-up.
