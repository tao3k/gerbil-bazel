# D1388: retain CC gains without replacing the cold-build baseline

The user's historical approximately 56-second MCP best remains an unresolved
receipt lookup, not a baseline that can be replaced by D869's 76.162/75.294
pair. No new consumer build or speedup is claimed in this reconciliation.

## Verified current CC policy

Both `build/bin/gambuild-C` and `src/gambit/bin/gambuild-C` in the original
`.data/d935-staging-source` contain a GNU GCC 16 `C_COMPILER` with
`-ftrack-macro-expansion=0`. Its `config.status` also retains that setting.
The earlier admitted macro-tracking policy has therefore not disappeared from
this local toolchain. D802's isolated real-module object result is
15.45 to 10.37 seconds. D802's 393.33-second single-producer MCP invocation
is explicitly excluded; D803's corrected 12-producer result is 81.03 seconds.
Neither receipt establishes the user's approximately 56-second build.

D857's packed strings reduce one real MCP module's mean C-to-object time
from 12.04 to 3.93 seconds with identical objects. D966's emitter patch 0013
does not establish complete consumer performance; its extra Scheme-to-C
emission time must be included. Keep atomic and whole-build claims separate.

## Recoverable complete-build improvement

D851 records unchanged MCP revision `9a5c35e` with GNU GCC 16 and 12 workers:

| Strict pair | Original whole build | D851 whole build |
| --- | ---: | ---: |
| Candidate first | 72.130 s | 60.690 s |
| Original first | 74.727 s | 59.555 s |

This was executable-graph-scoped PIC object reuse, a Gerbil compiler/build
graph change, not solely a Gambit CC flag. Its source baseline was staging
`d801e7a`, not current staging `1cfb032`. It remained held for POO
non-regression and intermittent MCP silence failures. Do not silently import
it into the current Gambit-only scope or treat it as proof of 56 seconds.

## Excluded nearby numbers

The durable D1139 report's 50.915-second run explicitly has scope
`paired-import-CPU-diagnostic-not-official-cold-build`. Its `qualified: true`
does not qualify a complete cold build. Other nearby 50-59-second numbers
in module-image construction and toolchain steps are also not complete MCP
builds. D1085's 56.723 seconds is a failed first-output latency, not the
historical best whole build. Preserve these distinctions when reconstructing
the baseline; do not choose a number by proximity alone.

The first-compile gate and concurrent real build/test delivery remain open.
This turn changes the evidence ledger only; it adds no product patch and
does not repeat the already established GCC flag benchmark.
