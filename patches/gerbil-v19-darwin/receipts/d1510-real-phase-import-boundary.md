# D1510 Real Phase Import Boundary

Decision: do not deploy phase serialization as a replacement for the current
native phase path based on this evidence. The frozen host and 5/50/112-second
acceptance limits are unchanged. No complete cold build or test wave was run
for this mechanism; no runtime patch was admitted.

## Actual Generated Module

The fixture uses the unchanged 145,912-byte MCP `util/strings~1.scm`, SHA256
`3878c6047c31a2ab50b844b6152daa90926d417b147d379a8063cbcf29378ab3`.
This is a real compile-time phase body with syntax quotes and lexical marks,
not the earlier simple-function example. Its producer compiles and serializes
code without executing initialization. Fresh consumers test source execution,
restoration, GC, ordinary `load-module` wrapper execution, repeated-load object
identity and module-load-order stability. Dependencies use the original runtime.
No MCP business source, native module or frozen binary is modified.

Controls v9 pass 20 assertions across producer, source and two fresh restore
processes. Ordinary-module v1 passes 34 assertions across six processes. The
native-cost v1 run adds three original native module controls: eight independent
processes, 44 assertions, all exit zero and final OK, source unchanged.

These checks do not establish macro expansion parity for the complete module,
type-info behavior across all consumers, concurrency, exception replay, demand
module equivalence or full toolchain semantics. The wrapper module uses a new
test identity and does not replace the original phase module path or context.

## Why the Earlier Source Control Failed

The original source spelling `Interface` appeared as `interface` in the error
irritants, resolving to a syntax transformer rather than the submodule. The
parent module's real `Interface` binding is a module context and was present.
Explicitly passing a no-fold argument to `from-string` did not fix the read.

In the retained Gambit `_eval.scm`, `##read-all-as-a-begin-expr-from-port` has
optional `start-syntax`, `close-port?`, `case-conversion?`, `raise-exception?`.
The `from-string` call supplies only the first, third and fourth arguments;
it omits `close-port?`, shifting the remaining two. The default true exception
flag consequently becomes the case-conversion flag. The direct port-reader
control supplies all arguments and preserves generated names; all real-body
controls then pass. This is a retained-source correctness observation, not
Darwin-specific cost evidence or authorization to change other platforms.
The production runtime has not been changed for this finding.

Earlier failed fixture reports remain preserved. Adding a parent import or
changing the readtable alone did not solve the argument-forwarding mismatch.
Do not interpret those failures as serialization corruption or missing parent
modules. A raw parsed-AST serialization attempt was previously rejected and
is not repeated here.

## Component Costs, Not End-To-End Wins

Dependencies are loaded before measuring the actual phase initialization.
This excludes the larger dependency-import cost; whole-process times vary.

| Path | Initialization time | Allocation |
| --- | ---: | ---: |
| Original native, first process | 0.007957s | 78,944 bytes |
| Original native, later process | 0.001339s | 78,944 bytes |
| Original native, later process | 0.000774s | 78,944 bytes |
| Source parse/compile/run | 0.030200s | 6,645,464 bytes |
| Restore code directly | 0.001200s | 1,486,080 bytes |
| Restore via ordinary wrapper | 0.001655s | 1,902,800 bytes |
| Restore via ordinary wrapper | 0.001597s | 1,902,800 bytes |

Restoration beats interpreted source locally but does not show a stable gain
over the currently used native phase path. It allocates about 24 times as much
as native initialization. These observations do not justify a compiler/runtime
candidate, even though the focused semantics pass. No ratio from the first
native time alone is called a speedup.

The next meaningful boundary is the original dependency import and interface
loading chain. The earlier JSON/HTTP batch allocated 282 MB during imports,
whereas this isolated native phase initialized with only 79 KB after its
dependencies. Do not extrapolate this one phase's allocation to all imports.
Preserve the admitted source-loader/reader mechanisms and their exact paths;
do not reopen rejected symbol hash filters or raw AST restoration.

Private evidence:
`.data/d1510-real-phi-strings-body-v9/report.json`,
`.data/d1510-real-phi-ordinary-module-v1/report.json`,
`.data/d1510-real-phi-native-cost-v1/report.json`.

## Actual Import Parameter Entry

The `current-expander-module-import` parameter probe observes real calls, unlike
the earlier global reader rebinding. Both successful batches retain all five
original outcomes and exit status; the original missing-library batch still
exits 70. Frozen sources remain unchanged. Attribution is qualified only for
this observed call boundary, not performance admission.

The file/port batch records 504 entries; JSON/HTTP records 3,525. The JSON batch
has the following nested inclusive chain:

| Interface | Observed inclusive time | Observed inclusive allocation |
| --- | ---: | ---: |
| std/encoding/json | 0.845278s | 197,379,704 bytes |
| std/encoding/json/api | 0.808358s | 165,962,944 bytes |
| std/encoding/json/io | 0.747495s | 156,779,688 bytes |
| std/io | 0.683865s | 142,935,552 bytes |
| std/io/api | 0.683328s | 142,061,552 bytes |
| std/io/socket/api | 0.442066s | 67,434,552 bytes |

These nested values must not be added together. The probe allocates records and
collects process statistics on every call, and observed wall time changes;
these are not uninstrumented module timings or exclusive cost attribution.
The evidence selects the std/io interface/dependency chain for deeper source
analysis. It does not authorize changing MCP HTTP logic or reducing imports
without semantic proof. Private evidence:
`.data/d1510-mcp-recipe-import-cost-v1/report.json`.
