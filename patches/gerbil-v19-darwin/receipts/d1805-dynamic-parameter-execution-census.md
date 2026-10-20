# D1805: actual dynamic parameter participation, not a startup win

Continue from D1513 B / original D1510, not a newer slow baseline. D1800
already rejects the three SAFE macro-module extension on real MCP gates.
This follow-up checks whether the extension actually executes before further
work is spent expanding it. It does not repeat a full performance build.

## Diagnostic construction

D1802 initially fails bundle linking on the two external counter symbols.
The failure is preserved. D1804 explicitly enables dynamic lookup for only
`gb_diag_attempts` and `gb_diag_hits` in diagnostic bundle compilation.
This is not a product linker change or security-policy bypass.

The diagnostic reuses the original D1510 carrier object and native modules,
the original runtime archive and the existing D1694 first-output observer.
Only the three candidate macro images and diagnostic I/O observer differ.
Source/input hashes are checked unchanged. GNU GCC compilation uses O1 for
the bundles and discovers 12 physical cores. The candidate home retains
original-image symlinks; the selected best-line home is never modified.

The counter increments helper attempts and successful transfers separately
for contract~6, sugar~1 and mop~1. The existing observer writes TSV snapshots
to a side channel on actual first-compile output or process exit. It does not
print synthetic progress or modify the genuine-output watchdog.

## Real MCP observation

D1803 uses a fresh unchanged MCP clone at
`9a5c35e275e5d6847ff421151bb224f2eae177c1`, official clean/build and the original
ten-second startup gate. The real builder child is verified at 4.526610 seconds:
PID 50346, binary SHA-256
`1b21ab6f124a55207383cfb3d1cc09d6df8940c466ee040e9a95368aa84e3529`.

The observation fails the unchanged startup gate before any first compile.
The verified child's exit snapshot records:

| Module | Attempts | Successful transfers | Misses |
| --- | ---: | ---: | ---: |
| gerbil/core/contract~6 | 1919 | 16 | 1903 |
| gerbil/core/sugar~1 | 4 | 4 | 0 |
| gerbil/core/mop~1 | 48 | 48 | 0 |
| Total | 1971 | 68 | 1903 |

This establishes actual participation, unlike source-site counts alone.
It is an incomplete, instrumented prefix, not the full first-compile window,
exclusive CPU accounting or a bound on eventual whole-window calls. Do not
compare its wall time to the historical best build as a speedup measurement.
No first-compile duration, full-build result or concurrent framework
performance qualification is established here.

Decision: do not expand or promote this failed candidate on an assumption of
high-frequency coverage. Keep D1510 selected. The optimization goal remains
open; the next execution-cost candidate must be grounded in the existing
high-frequency evidence and pass real startup/build/test gates.

Evidence: `.data/d1802-dynamic-parameter-census/report.json` (failed linking),
`.data/d1804-dynamic-parameter-census/report.json` (diagnostic construction),
`.data/d1803-dynamic-parameter-prefix/report.json` and its verified child's
`count.exit.50346.tsv` (failed startup gate and actual participation).
