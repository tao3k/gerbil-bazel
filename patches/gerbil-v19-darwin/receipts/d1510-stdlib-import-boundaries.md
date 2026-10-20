# D1510 Standard Library Import Boundaries

Decision: target first-process interface import/expansion, not another cache
for same-process module lookup. No runtime optimization is admitted by this
diagnostic. The frozen binary and existing 5/50/112 MCP gates are unchanged.

## Independent Consumers

Four original standard libraries each run in three fresh processes. The
diagnostic uses an empty package home and only the selected standard-library
load path; no MCP package, recipe, test inventory or business module is loaded.
The root library must not already be in the expander registry. Dependencies
already present in the toolchain remain present, so this is not a claim of a
fully empty dependency graph or a filesystem-cache-cold measurement.

All 12 processes exit zero, complete all four ordered phases, preserve the
cached module-context identity and print final OK. These are import protocol
controls, not complete standard-library build/test or behavioral qualification.

| Library | First import range | First eval range |
| --- | ---: | ---: |
| std/make | 0.252911-0.734415s | 0.027448-0.059262s |
| std/test | 0.173703-0.680694s | 0.026759-0.034859s |
| std/encoding/json | 0.628947-1.828397s | 0.071364-0.126907s |
| std/list/list | 0.123703-0.534821s | 0.016140-0.036700s |

Repeated import is 1.9-10.0 microseconds and repeated eval 1.0-31.9
microseconds in the same process. Wall times vary substantially. There is no
control/candidate pair, CPU attribution, stable speedup ratio or extrapolation
to the complete first-log interval. The import phase includes dependency work,
potential compile-time execution and native loading; it is not pure parsing.

## Public Source Correspondence

Gerbil expander/module.ss core-import-module first checks __module-registry.
On a miss it resolves/normalizes paths, reads the interface, expands the module
body and constructs the context/code before publishing registry entries. It
stores eval-syntax* in a delay-atomic promise. core-eval-module separately
forces the module and its prelude under the appropriate context.

Gerbil runtime/loader.ss load-module has its own cached builtin/loaded/error
states and loading synchronization, separate from the expander context cache.
Thus repeated-import success does not establish that all first-import native
loading is deferred to the measured eval phase, nor justify dropping either
cache or changing synchronization/error replay.

The next investigation must split actual executed first-import expansion,
binding and native-loading work without global wrappers that record no hits.
Any optimization must act on shared toolchain behavior with Darwin activation,
not pre-import named consumer modules, trim imports, pool MCP recipe processes
or introduce benchmark-specific provider inventories. Earlier rejected AST
serialization, symbol-hash and timing-only wrapper paths remain closed.

## Evidence And Fixture Repairs

Private report: .data/d1510-stdlib-import-boundaries-v4/report.json.
The binary identity remains
1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21.
Report parsing and existing import-tree controls: 13 Python tests pass.

Earlier diagnostic attempts are retained separately: v1 could not run Bazel
host discovery inside the sandbox; v2 used Gambit's table API against Gerbil's
hash abstraction; v3 requested the absent legacy std/sort identity. The fixture
now uses hash-get and the verified current std/list/list module. None of these
fixture failures indicates a production toolchain regression. No full cold
build/test wave was rerun and no source/runtime patch was pushed.
