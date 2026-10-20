# D1510 Optimizer Metadata: Reached Cost, Not A Speedup

No candidate runtime or production patch is admitted. Historical heavy cold
builds remain 47.771713 / 47.824226 / 47.927094 seconds. Whole-task gates remain
first compile <=5, cold build <=50 and complete tests <=112 seconds.

## Different From Interface Reconstruction

`compiler/optimize.ss` imports `.ssxi.ss` type/inline metadata into current
optimizer state. This is distinct from ordinary `.ssi` interface import and
the earlier real native phase serialization experiment. The selected source
marks optimizer metadata presence in the current optimizer-info instance.

`std/make.ss:gxc-compile` emits its compile line before calling compile-module;
compile-top-module then invokes optimize! under the compiler driver mutex.
Thus this metadata work cannot be offered as a remedy for that first line's
latency. It is a possible complete-build execution boundary instead.

## Original Compiler Observation

The unified `compiler-metadata` command uses the unchanged frozen binary,
original local toolchain home, and two fresh standard-library consumer
modules importing `std/list/list` and `std/encoding/json`. No MCP is imported.
Each consumer is compiled in a separate original control and observed process.
Actual Gerbil compilation emits SCM, SSI, static SCM and SSXI, with optimization
enabled; GNU C compilation is deliberately not invoked in this diagnostic.

The observer delegates the actual current-expander-module-import parameter
and records completed `.ssxi.ss` calls only. Process CPU observations subtract
immediate selected children once; instrumentation and other work inside those
calls remain included. These are reached costs, not removable CPU budgets,
whole-build timings or measurements of a Darwin/Linux causal difference.

| Consumer | Control compile CPU | Observed compile CPU | Completed metadata calls | Metadata own CPU |
| --- | ---: | ---: | ---: | ---: |
| list | 0.659318 s | 0.683932 s | 45 | 0.505387 s |
| JSON | 1.596532 s | 1.588900 s | 152 | 0.917499 s |

Builtin metadata alone contributes 0.208079 / 0.203640 observed CPU seconds.
Do not claim that 152 calls mean 152 files are reloaded on every package job,
or multiply these costs by 12 workers without reached worker evidence.

## Output And Evidence Checks

All four real compilations exit zero with final `OK metadata-compile` and
restore the original import parameter. SCM wrappers, interfaces and emitted
optimizer metadata are byte-identical between roles. Runtime SCM differs
only in the generated integer `<module>::timestamp` definition: a Scheme
reader normalizes exactly that top-level/begin definition, requires one such
definition, and compares all remaining forms. The corresponding static SCM
must be byte-identical to its own role's runtime SCM. This is compiler-output
parity, not execution of the complete library test suites.

The first report correctly fails raw byte parity because of this generated
timestamp and stops after list. It remains preserved at
`.data/d1510-compiler-metadata-v1/`. The qualified observation is
`.data/d1510-compiler-metadata-v2/report.json`; both original source/probe
and frozen binary identities are checked unchanged during that run.
Subsequent observer hardening rejects nonzero terminal metadata depth;
the parser also verifies postorder/root completeness and exact child
subtraction. Reprocessing the four existing transcripts passes. No workload
is rerun for that hardening. Thirty-five parser/import regression tests pass.

## Next Admission Boundary

Standard make uses persistent worker threads, while optimizer-info-init! sets
a dynamic parameter when absent. Its source also serializes optimize! using
the driver mutex. This suggests checking actual repeated metadata installation
across workers; it does not establish repetition or a removable serialized
wall-time budget. Measure that reached boundary before construction.

A possible prepared-code design must execute against each current optimizer
instance, retain fresh mutable type/class objects, current dependencies,
declaration ordering, global rebinding, source freshness, bootstrap and error
behavior. Sharing initialized optimizer objects or suppressing reloads is not
authorized by these observations. Existing `.ssi` declaration-only and native
phase serialization exclusions remain intact.

All owned sessions are terminal. No complete cold build/test measurement,
deadline change, production source edit, AOT-list edit or publication occurs.

## Reached Hardware-Concurrent Build: No Per-Worker Multiplier

The next observation executes actual unmodified std/make with twelve
hardware-derived workers and twelve new independent native consumers,
alternating original list and JSON dependencies. This is a diagnostic
construction, not the heavy cold-build acceptance recipe. GNU GCC is selected
explicitly through the original driver environment; output remains private.

The build finishes, emits 24 native images, and all twelve newly compiled
consumer functions run with exact checked return values. Every named consumer
completion and the final metadata marker are required, not merely process
exit zero. Original source/probe/frozen binary hashes remain unchanged.
The exact probe source is captured with the private receipt.

There are 152 completed selected metadata calls and 152 distinct metadata
paths: no repeated path in this build. Worker 0 accounts for 45 calls and
worker 1 for the remaining 107; builtin metadata is loaded only once, in
worker 0. No metadata records are reached in the other workers. This is
actual callback coverage, not proof that those other workers do no compiling:
all twelve native consumers complete and execute.

| Observation | Process CPU |
| --- | ---: |
| Whole observed make invocation | 1.945455 s |
| Selected metadata own intervals | 0.937320 s |
| Builtin metadata, one call | 0.243323 s |

The enclosing process CPU excludes child GCC/GSC CPU and is not the complete
native build's CPU sum or wall time. The callback intervals can include other
Scheme-thread work and GC; they are not exclusive per-worker CPU. There is
no control/candidate speed ratio and no new 5/50/112 acceptance result.

This disproves the proposed repeated-per-worker multiplier for the reached
build. The original sticky optimizer metadata mechanism already avoids that
repetition here. Do not create a shared optimizer state/cache or multiply
the single-consumer cost by twelve. Native prepared-code metadata remains
an unimplemented possibility, but this evidence does not justify it as a
major whole-build remedy.

Evidence: `.data/d1510-compiler-metadata-workers-v1/report.json`,
`workers.log`, and the captured `probe.scm`. The session exits zero and is
terminal. No product or std/make code is changed.
