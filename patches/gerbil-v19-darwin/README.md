# Gerbil v0.19 Darwin build patch stack

This directory carries the local validation stack for the Gerbil v0.19
Darwin build work.  The patches remain separate only to make ownership and
review comments precise.  They form one ordered stack: every patch is applied,
tested, and published together in one gerbil-bazel pull request after the
complete local stack is stable.

## Patch order

1. `0001-gambit-darwin-posix-spawn.patch`
   - owner: Gambit process runtime
   - scope: ordinary Darwin subprocess creation and its unit contracts
   - pseudo-terminal creation remains on the existing fork path
2. `0002-gerbil-bounded-compile-executor.patch`
   - owner: Gerbil compiler native-job executor
   - scope: bounded workers, follow-up job draining, joining, and first-error propagation
3. `0003-gerbil-build-observability.patch`
   - owner: Gerbil compiler and the existing V19 `std/make` lifecycle
   - scope: structured phase, queue, execution, worker, and wall-time evidence
   - invariant: preserves the official V19 coordinator and worker algorithm
4. `0004-gerbil-compile-job-parameterization.patch`
   - owner: Gerbil compiler native-job submission boundary
   - scope: preserve per-module compiler parameters when bounded workers execute deferred jobs
   - invariant: FFI `-cc-options` and `-ld-options` remain attached to the module that declared them
5. `0005-gerbil-libgerbil-closure-manifest.patch`
   - owner: Gerbil stdlib dependency contexts and libgerbil static closure
   - scope: retain each imported build context, project the exact ordered closure once during stdlib, and consume its validated manifest in libgerbil
   - invariant: the 338-module manifest is byte-identical to the V19 ordering; missing, malformed, or duplicate entries fail before native compilation
6. `0006-gerbil-streaming-executor-clean-closure.patch`
   - owner: Gerbil compiler executor lifecycle and `std/make` artifact lifecycle
   - scope: replace the remaining global pending-job drain with one streaming executor session across `std/make`, stage1, and Bach; derive the shared worker budget from the environment or host; remove every current-generation GXC/Gambit artifact during `make clean`
   - invariant: no Legacy pending-job API remains, producer and native work share one bounded budget, nested module artifacts are removed without basename-glob deletion, and the bootstrap compiler interface matches the source API
7. Evidence owned directly by gerbil-bazel
   - benchmark runners, schemas, tests, and machine-readable receipts

Patches 0002 through 0004 must not compensate for a failed or unvalidated Patch 0001.
In particular, Gambit process creation is validated before any std/make
scheduler comparison is admitted.

## Local admission gates

- Build Gambit and all final executables with the configured compiler.  The
  current Darwin baseline uses GCC 16; no Clang substitution is permitted.
- Remove Nix SDK, include, and library variables from Homebrew Gerbil child
  commands and set `COMPILER_PATH=/usr/bin` so GCC's `collect2` selects the
  Apple system linker.
- Run the Gambit `12-os`, `09-io`, and `prim_port` tests three consecutive
  times.
- Run compiler executor contracts with 1, 3, and 12 workers.
- Run atomic std/make graph tests before any complete build.
- Record cold and warm measurements separately.  Warm measurements cannot be
  used as cold-build evidence.
- Treat ten seconds without progress output as a failed or inadequately
  instrumented local gate.
- Complete `clean -> tests -> cold build` with the full patch stack before the
  single pull request is published.

## Current status

- The complete Patch 1 -> Patch 2 -> Patch 3 -> Patch 4 stack applies without conflict to
  the current `v0.19-staging` revision `d801e7a1`. That revision retains the
  same Gambit `dcd677cd` gitlink and does not modify any patch-owned source
  file. Timing numbers below remain receipts from the earlier `f0badc7`
  baseline and are not relabeled as D801 measurements.
- Patch 0001 focused tests: 46/46 passed in three consecutive runs.
- Patch 0001 strict spawn comparison: the same Scheme executable and compiler,
  with only `libgambit.a` changed, measured 2.27-2.31 seconds for 20 fork/exec
  operations and 0.02-0.03 seconds for 20 posix_spawn operations.
- Patch 0001 strict 120-module A/B: baseline internal cold samples were
  28.673/28.928/28.853 seconds and Patch 1 samples were
  10.465/10.161/11.456 seconds. The medians are 28.853 and 10.465 seconds,
  respectively: -63.73% or 2.76x faster. All six performance receipts pass.
- Patch 0002 source contract: bounded concurrency, follow-up draining, and
  first-error propagation passed with 1, 3, and 12 workers using the current
  source-built V19 test executable.  Admission also rejects any gxtest
  `ERROR HARNESS`, `ERROR MODULE`, `ERROR SUITE`, `ERROR TEST`, or
  `ERROR CHECK` marker instead of trusting exit status alone.
- The dependency-graph scheduler experiment was rejected and removed from the
  applicable patch stack: on the 120-module fixture it changed cold build time
  from 29.832 seconds to 30.505 seconds (+2.26%). Its evidence and rejection
  rationale remain in `REFLECTION.md`; none of its scheduler or cache code is
  carried by Patch 0003.
- Patch 0003 adds structured evidence while retaining the official V19
  coordinator-per-entry and bounded build-worker algorithm. Verbose level 3
  reports build, Gerbil, and native phases; level 9 retains individual compiler
  invocations.
- Patch 0004 closes a correctness regression exposed by the bounded executor:
  OpenSSL, SQLite, and zlib compiler/linker options are captured when each job
  is submitted and restored inside the shared worker.  Its regression contract
  passed with the source-built D801 compiler executor.
- The focused D801 recovery run rebuilt 733 stdlib native jobs with 12 workers
  and zero errors after Patch 0004.  The GCC 16 AOT jobs then completed in
  171.172 seconds for `gxpkg` and 140.855 seconds for `gxtags`.  These are
  diagnostic receipts, not an admitted cold end-to-end A/B: the run followed
  earlier failed and incremental attempts and therefore contains warm state.
- A subsequent sanitized `make clean` D801 build with the complete patch stack,
  GCC 16, 12 detected cores, `-pipe`, and `GERBIL_BUILD_AOT_TOOLS=yes`
  completed successfully in 1,352 seconds.  Its target receipts were Gambit
  296 s, stage0 60 s, stage1 224 s, stdlib 235 s, libgerbil 228 s, languages
  3 s, and tools 306 s.  The stdlib native phase completed 800/800 jobs with
  12 workers, zero errors, and a 181.876 s wall time.  The tools target
  included independent whole-program AOT builds for `gxpkg` (159.246 s) and
  `gxtags` (138.118 s).
- The resulting `gerbil`, `gxpkg`, and `gxtags` are arm64 Mach-O executables;
  `gxi`, `gxc`, and `gxtest` resolve to the AOT `gerbil` executable.  With the
  build-tree `GERBIL_HOME`, repeated startup measurements were 0.10-0.12 s for
  `gxi`, 0.00-0.01 s for `gxpkg` and `gxtags`, and 0.87-0.90 s for warm
  `gxtest`.  The first `gxtest` access took 26.88 s and is reported separately,
  not averaged into the warm measurements.
- A two-second sample of the silent libgerbil startup phase showed a 1.0 GiB
  footprint with the main thread dominated by
  `___dynamic_load -> dyld4::APIs::dlopen -> Loader::mapSegments/fcntl` while
  loading hundreds of `.o1` images.  This identifies Darwin loader granularity,
  rather than the bounded native-job worker count, as the owner of that phase.
- Patch 0005 removes that second Darwin load pass.  `std/make` retains the 294
  contexts it already imports, and the ordered libgerbil closure is projected
  from them with zero fallback imports.  Per-root HashTable visitation reduced
  closure projection from 26,389 ms to 14 ms while preserving the exact
  7,222-byte manifest (`sha256 aa60c38c15c49eadf62d7f37c35f5f29b1c8cefae875a51b5cee082c4dd607f9`).
  The focused stdlib target fell from 58.76 s to 29.73 s, and the complete
  libgerbil target completed in 62.62 s versus the 228 s D801 cold-build phase
  receipt.  These are focused local receipts, not a replacement for the
  required clean end-to-end cold A/B.
- Patch 0005 atomic gates passed with the build-tree AOT `gerbil`: manifest
  order/round-trip/rejection contracts, both one-worker and parallel
  `std/make` cases, and compiler executor concurrency, parameterization, and
  error propagation (1.05 s total).  Three controlled warm `std/make` test
  samples were 7.77/7.98/8.13 s (7.98 s median); the 9.13 s first run after
  recompiling `std/make` is retained as a cold post-rebuild sample, not mixed
  into the warm median.
- The real Gerbil POO V19 consumer completed repeated sanitized 26-module
  artifact-clean builds.  With `GERBIL_BUILD_CORES` absent, upstream V19
  selected one build worker and needed 59.21 s.  Dynamically selecting the 12
  physical cores reduced the deployed `f0badc7_1` build to 18.50 s.  The D801
  build-tree with the complete patch stack then produced 13.66/13.65 s samples;
  the second receipt decomposed into 4.526 s of Gerbil compilation and 8.410 s
  for 64 native jobs, with `peakActive=12` and zero errors.  The deployed and
  D801 samples are an external-consumer integration comparison, not a
  single-revision causal A/B.  All eleven POO test files passed through the
  built artifacts in three atomic groups taking 2.42/2.41/2.56 s.  A partially
  sanitized control failed at `fq` with Darwin `_pow` unresolved after 45.60 s;
  clearing SDK/header/library variables and selecting `/usr/bin` for GCC
  `collect2` closed that environment boundary.
- Patch 0006 atomic gates pass on D801 for the compiler executor and both
  one-worker and parallel `std/make` graphs.  The cleanup contract removed all
  401 accumulated POO `.ssi`, `.ssxi.ss`, `.scm`, and versioned `.oN`
  artifacts, including nested modules, while retaining an unrelated
  same-prefix sentinel.  A subsequent true clean build emitted 180
  current-generation artifacts and zero `.o2+` files.
- The D801 source-built runtime completed the real 26-module POO clean build
  with 64 native jobs, 12 host-derived workers, zero errors, and 13.262 s
  internal wall time; the full POO test harness then passed.  The installed AOT
  runtime is `f0badc7`, two commits behind the patched `d801e7a` source.  Those
  commits change HTTP/interface source and regenerated bootstrap output, but no
  Patch 0001-0006 owned source file; the AOT runtime is therefore retained as
  the integration launcher, while patch attribution continues to use the
  complete ordered D801 stack.

## Verbose evidence contract

- Verbose level 3 emits structured `build-observe` records for the existing
  Gerbil scheduling lifecycle, native queue/execution progress, worker
  construction, totals, and wall time. It is the normal diagnostic level.
- Verbose level 9 additionally prints individual compiler invocations. It is
  intentionally opt-in because command lines obscure the phase-level decision
  surface during scale builds.
- The benchmark runner retains every raw line in the JSON receipt but streams
  only structured observations and errors to the terminal. Its final stdout is
  a compact decision summary, not a duplicate of the receipt.
- A ten-second silent interval terminates the observed process and reports
  `reason=silence`; a total deadline reports `reason=total`.
- Artifact counts and SSI hashes are recorded. Raw Darwin Mach-O hashes are
  not treated as semantic equivalence because UUID and temporary-path metadata
  make them nondeterministic even between repeated baseline builds.

See `REFLECTION.md` for the evidence decomposition, rejected repair tactics,
and the next falsifiable architecture experiments.

## D801 dual-consumer baseline

`receipts/d801-dual-consumer-baseline.json` freezes the admission boundary for
the next generic `std/make` round. Gerbil POO is the small-graph regression
gate: its stable three-sample clean-build median is 12.550 seconds internally
and its full unit harness passes. The first-access 19.459-second sample is kept
separately and is not part of that median.

Gerbil MCP is the primary large-graph scenario. Its clean build contains 187
entries and 551 native jobs, keeps all 12 host-derived workers active, and
takes 168.733 seconds internally (175.190 seconds externally). Compilation
completes without errors, but the maximum job execution is 121.032 seconds and
the maximum queue delay is 23.700 seconds. Its existing test suite has four
known output-contract failures in three files and no crashes; those failures
are recorded as baseline state rather than reported green or attributed to the
executor.

The next patch is admitted only if it materially improves the MCP clean build,
does not regress the POO median, and contains no consumer-specific scheduling
branch.
