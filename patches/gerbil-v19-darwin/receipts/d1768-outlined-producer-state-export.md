# D1768: outlined producer passes concurrent fixture, not complete-build ceiling

The canonical remote v0.19-staging and retained source HEAD are rechecked as
1cfb032c7a1612637da6205f5f8a15683eba3ba0. The original D1513 B / D1510 line
remains selected and unchanged. Its historical timings are not replaced.
No production performance patch or complete staging-toolchain qualification
is admitted.

The experimental whole-producer emitter moves the same four bounded trees
outside the large GVM host into GNU O3 C helpers. The host entry becomes 85
lines. Each helper keeps its own heap/frame pointers and register values.
Stack writes are staged as address/value pairs in a bounded private result;
nargs and poll resume are also deferred. A guard miss publishes no GVM
state. Normal return or an original poll exit exports state to the caller,
which commits stack/register/frame/heap state and performs the original GVM
transfer. Raw original-stack reads without a proved shadow mapping, unknown
transfers, registers outside R0-R4 and shared-state writes are refused.

Five focused Python tests pass. They test emitted exports/refusals, not native
GC/continuation execution. The emitter does not erase polls or relax original
tree/path/work budgets. Its typed root input remains the syntax-e invocation;
this is not a general arbitrary-GVM-state ABI proof.

D1761/D1762 initially place helpers inside BEGIN_M_COD and GNU rejects their
static declarations. Those artifacts/failures are retained. D1763/D1764 move
them to file scope before BEGIN_M_COD, matching the existing native helpers.
Real GNU compilation, linking and framework imports then succeed. All
original B native inputs remain unchanged. Candidate SHA256:
`313769585f8cf57ea2d948c04938aad2d2792a90a1be958d5da1f28de4f07495`.

D1765 passes the exact existing 42-case producer fixture across twelve
concurrent original/candidate runs: 504 CASE-OK results, including 252 from
the candidate. Returned data, post-return GC and fold rebinding/restoration
are covered. Forced native poll snapshots, every rollback state and
exception/continuation recovery remain unqualified. Dynamic tree coverage
and execution-cost savings are unmeasured.

D1766 uses a fresh unchanged MCP clone, original GSC/runtime, twelve GNU
workers and original gates:

- Separate clean: 4.101561 seconds, exit zero, zero retained native images.
- Literal first compile: 5.816227 seconds, `... compile util/compat`.
- Complete build: 72.530385 seconds, exit zero; executable produced.
- Maximum actual output gap: 5.816227 seconds; consumer inputs unchanged.
- The 55-second complete-build ceiling fails; controller exit one.

No ratio against historical B or differently timed failed candidates is
admitted. The first-log observation is not proof that the major startup cost
has been eliminated.

D1767 passes twelve native starts, twelve framework imports and the unchanged
std/make/std/test fixture. Exact CASE-OK, SUITE-OK and D885-OK lines plus exit
zero are verified. Fixture wall time is 20.581939 seconds; maximum output gap
is 3.987998 seconds under the original five-second gate. Configured workers
are twelve; peak observed GNU frontends are eleven, not full twelve-way GCC
observation. This is functional concurrency, not a matched test speedup.

Unlike D1759's failed fixture, this run passes, but the different observations
do not establish a causal speedup. The candidate is not stacked onto the
best line or promoted. Complete-build acceptance, major first-log reduction,
forced-poll safety and integrated toolchain delivery remain open. All owned
sessions are terminal.

Evidence: `.data/d1761-outlined-producer-carrier/`,
`.data/d1762-outlined-producer-native/`, `.data/d1763-outlined-producer-carrier/`,
`.data/d1764-outlined-producer-native/`, `.data/d1765-outlined-producer-contract/`,
`.data/d1766-outlined-producer-real-mcp/`, `.data/d1767-outlined-producer-concurrent/`.
