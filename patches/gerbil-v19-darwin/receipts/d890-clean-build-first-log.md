# D890: Official Clean Build First-Log Baseline

Date: 2026-10-03. The immediate optimization target is command launch to the
first real `... compile` line, not whole-build duration or an artificial
early progress message. No startup optimization is admitted by this receipt.

## Native Measurement

- PR 11 checkout: `e6e1a82a0835ccf9afa9936df9e2d3448c24c8f4`.
- D884 staging toolchain: Gerbil `1cfb032c7a1612637da6205f5f8a15683eba3ba0`,
  Gambit `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, GNU GCC 16.
- Concurrency: 12 hardware-derived workers.
- Dependency: existing native POO, pinned to
  `099b381588360a8a49fd772f666a1a00351366f5`; no network installation.
- Isolated root: `.data/d890-empty-project-path`.
- Native project images before and after official clean: 0 and 0.
- Commands: official `gerbil clean`, then official `gerbil build`.
- Both exit zero. Project native images after build: 416.

| Event | Seconds From Build Launch |
| --- | ---: |
| First output line | 2.185 |
| First real compilation line | 8.587 |
| First sampled GCC frontend | 12.696 |
| Build completion, secondary only | 46.464 |

Reader timestamps use a monotonic clock and preserve original subprocess
output in `.data/d890-clean-first-log-fresh/`. First GCC observation is a
sampling bound, not an exact start time. The runner's progress messages are
not counted as product output. The log is not changed to fake earlier work.

The baseline confirms the requested startup symptom. It is not an A/B gain;
`performanceQualified` remains false. The approximately 6.402 seconds between
the first output and first compilation line has not been removed.

## Clean Boundary

An earlier cloned, previously built root failed the cold-artifact gate:
official clean left all 416 `.o1` images while removing `.ssi` and static
sources. The original `std/make` clean path uses `spec-outputs`, whose module
output projection does not enumerate these native images. That diagnostic
run is retained at `.data/d890-clean-first-log/` and is not called a genuinely
empty native build. Neither the package cleaner nor GXPkg was changed.

## Next Candidate Boundary

The existing Reflection section `D801 full-build phase ownership` already
places the native loading cost at Gambit's `___dynamic_load` / `dlopen` and
Darwin's image mapping. Do not repeat that investigation or infer that host
function partitioning fixes image loading. D889's host grouping has not
qualified the first-log target and has an observed runtime CPU regression.

Any startup candidate must retain Linux behavior, GNU GCC identity, module
loading/initialization semantics, and the same official clean/build entry.
Its primary comparison is repeated first-compilation-line latency against
this baseline. Whole-build duration and runtime regressions are separate
gates; neither substitutes for the startup result.

## Replay

Prepare a fresh project-local root containing only the pinned dependency,
with no project artifacts, then run:

```sh
python3 patches/gerbil-v19-darwin/tests/run_asp_cold_start.py \
  --project .data/d889-asp-candidate/source \
  --toolchain-source .data/d884-patched-staging/source \
  --output .data/NEW_FIRST_LOG_RUN \
  --head e6e1a82a0835ccf9afa9936df9e2d3448c24c8f4 \
  --package-root .data/FRESH_DEPENDENCY_ONLY_ROOT \
  --prepared-dependency-head 099b381588360a8a49fd772f666a1a00351366f5 \
  --clean-first --build-entry-only
```

The first output/compile timestamps are now also reported live by the driver;
there is no need to wait for build completion to observe startup latency.
