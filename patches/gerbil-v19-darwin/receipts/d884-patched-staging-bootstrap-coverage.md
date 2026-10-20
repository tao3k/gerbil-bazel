# D884: apply admitted fixes and cover the archive bootstrap

Date: 2026-10-03. This is implementation and toolchain qualification, not
another investigation of the already recorded Darwin costs.

## Source and Scope

- Gerbil staging: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
- Gambit gitlink: `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
- Fresh isolated checkout: `.data/d884-patched-staging/source`.
- Real GNU GCC 16.2.0, two build jobs, existing Bazel host environment.
- Compiler O1, runtime O3, SMP, inline jumps, single-host limit zero.
- No Homebrew replacement, remote mutation, or release-stack promotion.

The checkout applies the existing performance patches: Darwin process spawn
(`0001`), streaming compile executor (`0002`), executable closure DAG (`0003`),
and GCC macro tracking policy (`0004`). Earlier gains belong to their original
receipts; they must not be summed or represented as new staging measurements.

## Bootstrap Fix

Candidate `0012-gambit-darwin-bootstrap-macro-tracking.patch` applies after
`0004`. Gambit's bootstrap recipes configure the unpatched release archive
with `CC='$(C_COMPILER)'`. The original `0004` adds the capability-probed
option to `FLAGS_OBJ_DYN`, which those recipes do not forward.

The candidate puts that same option on `C_COMPILER`, keeping the existing
Darwin/GNU/non-LLVM guard and leaving optimization levels unchanged. Both
`configure.ac` and generated `configure` are patched. This changes propagation
of an admitted diagnostic-cost optimization, not emitted Scheme semantics.

Verification already obtained:

- Reader and macro-context syntax checks before and after the Gerbil patches.
- Shell syntax validation of the patched configure script.
- Reconfiguration without injecting the macro option through `CC` or `CFLAGS`.
- Parent and actual archive makefiles contain the option in `C_COMPILER`,
  with no duplicate in `FLAGS_OBJ`.
- Actual archive/current-tree GNU GCC commands carry the option.

## Qualification Status

The complete official build and tests passed. The final report sets
`qualified: true`, `baseTestCases: 45`, and `executorContractPassed: true`.
Completed steps and their raw logs are recorded in
`.data/d884-patched-staging/report.json`; individual logs are beside it.

All official stages passed: `prepare`, `gambit`, `boot-gxi`, `stage0`,
`stage1` (including Bach), `stdlib`, `libgerbil`, `lang`, and `tools`.
The new toolchain reports `v0.19-dev-63-g1cfb032c`.

Observed stage durations, not performance comparisons:

| Stage | Seconds |
| --- | ---: |
| Gambit | 714.452 |
| boot-gxi | 5.046 |
| stage0 | 309.593 |
| stage1 | 547.702 |
| stdlib | 1445.062 |
| libgerbil | 495.979 |
| lang | 5.057 |
| tools | 15.165 |

The official list/vector/values/iterator source tests pass all 45 cases and
four modules, with `MODULE-OK`, `HARNESS-OK`, final `OK`, and process exit zero.
They exercise the newly built standard library, not libraries from the cache.
No assertion or expected result was changed.

The streaming executor contract also passes in the new toolchain with two
jobs: submission parameterization, nested task draining, propagation of a
raised `#f`, and recovery after a failed batch. The final runner extension was
checked using completed-step resume; it did not repeat the full build.

Replay with a fresh output directory:

```sh
python3 patches/gerbil-v19-darwin/tests/build_patched_staging.py \
  --source-cache .data/gerbil-gambit-bootstrap-audit \
  --output .data/NEW_PATCHED_STAGING_RUN \
  --gerbil-ref 1cfb032c7a1612637da6205f5f8a15683eba3ba0 \
  --gambit-ref ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f
```

The runner uses the official bootstrap/from-scratch build, then the Gerbil
core, standard library, native library, language and tools stages. It finally
runs the official list/vector/values/iterator source tests and executor
contract. It rejects Clang and tracks child CPU/log progress while preserving
raw logs. Future replay uses an output-local `GERBIL_PATH`; the original full
run used explicit checkout-local build paths but did not yet override that
environment variable. Machine-specific paths remain in ignored local logs.

This is functional qualification of the core toolchain with the four
performance patches and bootstrap candidate, not qualification of all release
compatibility patches. Host load exceeds the existing performance gate;
`performanceQualified` remains false. No new acceleration percentage or claim
that all macOS costs are solved follows from this build.
