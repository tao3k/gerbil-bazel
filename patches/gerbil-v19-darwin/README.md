# Gerbil v0.19 Darwin build patch stack

This directory carries the local validation stack for the Gerbil v0.19
Darwin build work.  The patches remain separate so that each ownership layer
can be applied, tested, and reverted independently.  They are published
together in one gerbil-bazel pull request only after the complete local stack
is stable.

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
4. Evidence owned directly by gerbil-bazel
   - benchmark runners, schemas, tests, and machine-readable receipts

Patches 0002 and 0003 must not compensate for a failed or unvalidated Patch 0001.
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
- The real Gerbil POO V19 consumer completed a sanitized 26-module cold build:
  dependency graph construction took 1-2 ms and the Gerbil compilation phase
  took 4.872 seconds before bounded native jobs completed.  Its eleven test
  files then passed independently in 0.87-3.76 seconds each.  The unsanitized
  control reproduced the Darwin `_pow` link failure, confirming that SDK,
  include, and library isolation remains part of the admission environment.

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
