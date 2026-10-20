# D1602: retained tail-task CPU evidence, failed complete-build gate

The preceding turn made progress by enforcing the user's 55-second complete
MCP cold-build ceiling. This turn extends the existing D1467 launch observer
with waitpid-to-wait4 diagnostic interposition to collect child resource usage
and launch-to-reap upper bounds. This is not a production process change.

Canonical staging was checked again and remains
1cfb032c7a1612637da6205f5f8a15683eba3ba0. GNU GCC is resolved through the existing
Bazel host environment, and hardware discovery supplies twelve physical
workers. The diagnostic relinks D1590's original outline/317-object composition
and original GSC inputs with an observer dependency; no consumer source changes.

The initial sandbox attempt fails hardware discovery before workload execution.
The authorized isolated attempt is retained under
`.data/d1601-composed-process-lifetime/`. A native control matches all three
fork/spawn/spawnp launches with successful child reaps. This validates the
observer's basic completion path, not its full workload coverage.

Actual MCP head remains 9a5c35e275e5d6847ff421151bb224f2eae177c1. Official clean
passes in 2.951710 seconds and leaves no project native images. First literal
compile appears at 4.931916 seconds. Build subsequently fails the unchanged
real-output/diagnostic watchdog; terminal exit is 70. The failed run's report
does not distinguish the two watchdog reasons or record failure elapsed time.
Do not invent a complete-build duration. Future driver output separates these
reasons and records both clocks. The build does not qualify the 55-second gate.

The partial build yields 1,481 launches, 1,478 successful matched terminal
reaps, three unmatched launches and zero unmatched reaps. Observed gxi/GSC
loading is retained; completed tasks include 739 GSC, 552 gambuild-C, 186 env
and one git child. The last matched reap is at +77.646521 seconds. Incomplete
coverage and the failed run cannot qualify full-build correctness or speed.

One matched gxi-to-GSC task starts at +10.603410 and is reaped at +58.655901:
48.052491 seconds. Its GSC-to-gambuild-C child starts at +10.621335 and is reaped
at +58.649088: 48.027753 seconds, with 11.851653 user and 0.670548 system CPU
seconds. This localizes the long observed interval to the downstream C-build
task rather than its short preceding GSC setup. It does not distinguish GCC
phases, identify the module, explain scheduling/wait time or prove why the
historical D1592 build took 68.561755 seconds. Reap time is an upper bound on
exit time. Parent and descendant CPU counters must not be summed as independent
work or subtracted from wall time as an available speedup.

The existing observer logs only target program basenames, not argv/module
identity. The next missing datum is the selected compiler task's input/output
and mode, followed by its GCC-stage cost or proven equivalent reusable output.
Do not expand a cache, alter optimization defaults or blame machine resources
from this partial trace. Keep first-log and native Scheme-test work independent.

Both owned tool sessions are terminal, and a scoped live process-table check
finds no members of the build process group. No product patch, installed
toolchain, deadline relaxation, commit or push is admitted. The goal remains
active and unachieved.
