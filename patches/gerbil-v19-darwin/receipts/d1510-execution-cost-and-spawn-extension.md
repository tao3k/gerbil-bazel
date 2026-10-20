# D1510: execution attribution and a denied spawn extension

## Admission

Retain original D1510 plus 0015. Do not install, publish or add the private
same-PATH spawn candidate to the admitted patch stack. Its complete cold build
exceeded the hard 55-second ceiling. A component benefit cannot override DENY.
Linux, consumer sources, std/make, std/test, original GSC and the retained
runtime installation were not changed.

Original binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Private candidate SHA256:
`ab4aa5362016e20cf7157da6c17df8bfbf65890f9ccf829de7306a3e3766d475`.
All 42 retained construction source hashes and all 52 actual unit-test inputs
were independently checked unchanged at the end.

## CPU Attribution, Not Admission Timing

Three private diagnostic wrappers ran 13 distinct unit files on the original
binary, with 12 hardware-derived workers. Each diagnostic completed all 13
files. They preserve the 5-second actual-output and 90-second wall gates, but
use a gxi expression dispatch instead of the official CLI. Their times are
not official startup or test performance results. Controller exit 1 is the
intentional non-qualification result for diagnostic dispatch.

The wrappers aggregate process-statistics CPU deltas in memory and subtract
nested callback intervals. Only completed phase snapshots are written; no
diagnostic output is counted as test progress. Initial interpreter startup
is outside their attribution window. Wrapper costs and GC remain included.

Mean tool-import callback CPU across 13 observations:

| Eval root | Calls | Exclusive CPU seconds |
| --- | ---: | ---: |
| begin | 186 | 0.503103 |
| symbol | 1672 | 0.006224 |
| make-type-env | 66 | 0.000962 |

A separate nested preparation census records Gambit interpreter compilation
at 0.019032 seconds, Gerbil compilation at 0.015263 seconds, Gambit execution
at 0.450757 seconds, and Gerbil import at 0.311038 seconds. These numbers are
from a different instrumented run and must not be combined with the root
census into an uninstrumented whole-process cost partition.

The loader census observes 108 runtime load-module calls at 0.223660 seconds.
Several replaced global functions have no observed entries: native direct
calls bypass those replacements. Therefore this is not complete native-loader
attribution and does not establish that file reads or path searches cost zero.
The existing module-state cache already reuses successful loads.

Allocation-counter subtraction produced negative results. The summaries retain
raw values but explicitly do not admit them as allocation attribution. Call
counts do not prove cache misses or expensive work. In particular, the symbol
fast-path route cannot be justified by its large call count.

Evidence:
`.data/d1510-test-eval-exclusive-cpu/cpu-summary.json`,
`.data/d1510-test-preparation-exclusive-cpu/cpu-summary.json`,
`.data/d1510-test-loader-exclusive-cpu/cpu-summary.json`.

## A Concrete Test Subprocess Path

Unchanged MCP proc.ss run-subprocess calls open-process with bare `sh` and a
merged explicit environment. Patch 0001 conservatively falls back to fork for
bare commands with an explicit child environment because spawnp searches the
caller's PATH, not that envp's PATH. Previous zero-fork build observations do
not cover this separate consumer test path.

The private extension allows that existing Darwin spawn path only under GNU
GCC, with exactly one child PATH, an identical caller PATH, and exclusively
nonempty absolute PATH entries. Missing, duplicate, changed, empty or relative
PATH entries keep the old fallback. Pseudo-terminal eligibility is unchanged.
No executable search cache or consumer change is introduced.

Actual process controls match original output/status for ordinary shell
commands, different PATH, executable shell text without a shebang, and missing
commands. A separately linked observer proves original fork:3 versus candidate
spawnp:1/fork:2 for same/different/relative-child-PATH controls. Observer runs
are not used as performance measurements.

The retained os_setup.o disassembly and relocations confirm that closefrom
calls sysconf at text offset 0x2b8 and repeatedly calls close at 0x2e0. The exact
configured GNU preprocessing recipe defines USE_sysconf/USE_fcntl, but not
USE_closefrom, USE_SYS_close_range or F_CLOSEM. Its fallback scans descriptors
up to _SC_OPEN_MAX, not merely the set of open descriptors.

The inherited limit is 1,048,575. A standalone reproduction makes 1,048,572
close attempts starting at descriptor 3. Its serial observation is 0.113708
seconds; 12 concurrent component observations are 0.140615-0.194630 seconds,
totaling 12,582,864 close attempts. These are component measurements, not a
native-fork cost partition, and do not establish the sole cause of startup or
test differences. No descriptor limit was changed.

The existing spawn branch uses Darwin POSIX_SPAWN_CLOEXEC_DEFAULT and explicit
inheritance actions. Apple publishes the Darwin-specific flag in
[XNU spawn.h](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/spawn.h).
Published source is not an assertion of the installed kernel revision.

Controls and source:
`.data/d1510-spawn-same-path-native/`,
`.data/d1510-spawn-same-path-controls-v2/`,
`.data/d1510-spawn-path-observer-v2/`,
`.data/d1510-closefrom-loop-component.json`.

## Actual MCP Component ABBA

This calls the unchanged MCP run-subprocess function 16 times per fresh process,
with 12 concurrent processes per wave. It is not gerbil test or the complete
integration suite. Each real child completion emits and flushes one JOB-OK
line. All 48 invocations and 768 child jobs pass the unchanged 5/90 gates.

| Wave | Role | Mean 16-job loop seconds | Entire wave seconds |
| --- | --- | ---: | ---: |
| A1 | Original | 3.800252 | 7.554757 |
| B1 | Candidate | 0.605061 | 4.282383 |
| B2 | Candidate | 0.525500 | 4.132967 |
| A2 | Original | 3.641800 | 6.978429 |

Mean loop ratio is 6.5826x. That ratio excludes module preparation and does not
apply to complete tests or builds. Actual first completion output spans
2.313808-3.161036 seconds for A and 2.296168-2.660392 for B.

The initial unflushed diagnostic used displayln without force-output. Both A
waves hit the no-output watchdog while B completed, but that is buffered output
evidence, not proof of a fork stall. Keep the failed initial record; it is
superseded only for component timing by the explicitly flushed experiment.

Evidence: `.data/d1510-spawn-real-proc-abba-flushed/report.json`.

## Official Unit Tests And Cold Build

Actual gerbil test ABBA, 13 files per wave, 12 workers, unchanged tests and
strict 5/90-second gates:

| Wave | Passed files | CASE-OK in passed files | Wave seconds |
| --- | ---: | ---: | ---: |
| A1 | 1/13 | 19 | 8.271711 |
| B1 | 5/13 | 56 | 8.343718 |
| B2 | 13/13 | 177 | 5.360422 |
| A2 | 13/13 | 177 | 4.933159 |

Twenty invocations fail the actual no-output gate. Later passing waves do not
erase them, and failed/cancelled wave durations are not successful suite times.
Overall qualification is false. The successful B2 wave is slower than A2;
this does not demonstrate a complete unit-suite speedup. The prior full
39-file baseline's 10 failures remain open; it was not rerun or declared green.

Real clean/build, GNU GCC16 and retained 0015 driver, 12 workers:

| Role/run | Clean seconds | First compile seconds | Complete build seconds | 55-second gate |
| --- | ---: | ---: | ---: | --- |
| Original independent check | 3.167663 | 5.247468 | 54.404960 | ALLOW |
| Original A1 | 3.375414 | 5.254543 | 52.283134 | ALLOW |
| Candidate B1 | 2.841556 | 5.216653 | 67.562952 | DENY |

Every completed clean exits zero and leaves zero native images; every completed
build exits zero with unchanged source inputs. Performance admission is
separate. Candidate B1 exceeds 55, so B2/A2 are not run. It is not averaged
with A or the component result. Clean time is separate from the build ceiling.
The candidate changes only the host RTS; these cold-build consumer executables
still link the retained home RTS, so they do not qualify candidate-RTS consumer
deployment or a full integration-test benefit.

Evidence:
`.data/d1510-spawn-same-path-unit-abba/report.json`,
`.data/d1510-execution-cost-baseline-cold-v2/admission.json`,
`.data/d1510-spawn-same-path-cold-abba/admission.json`.

## Diagnostic Repairs And Next Boundary

Retain negative diagnostic records: the first cold invocation supplied an
unqualified source directory and failed preflight, without running a build;
the first process control expected the wrong exception superclass; the first
observer fixture incorrectly assumed true exists in /bin on Darwin. Their
corrected runs use separate output directories. An ambient SDK/Nix C link
failure was corrected by using the existing Bazel host environment, without
changing toolchain flags or product inputs.

The subprocess component benefit is real and worth retaining as evidence,
but the native candidate remains DENY. Do not turn it into an admitted patch
or relabel its 6.58x component ratio as a whole-test improvement. Original
D1510 plus 0015 stays the performance anchor. The first-build macro/execution
window is still unresolved; build zero-fork evidence prevents claiming this
test subprocess extension fixes that window.
