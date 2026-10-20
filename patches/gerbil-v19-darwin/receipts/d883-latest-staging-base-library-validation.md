# D883: latest staging real base-library validation

Date: 2026-10-03. The isolated full source build and real base-library tests
pass. The live-block-budget candidate has no effect in this scenario and is
rejected for it. This receipt makes no new speedup claim.

## Identity and environment

- Gerbil staging: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
- Gambit: `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
- Real GNU GCC 16.2.0; the runner rejects Clang using predefined macros.
- Source/build: `.data/gerbil-gambit-bootstrap-audit`.
- Isolated build root: `.data/gerbil-gambit-bootstrap-audit/build`.
- Full-stage log: `.data/d882-bazel-env-repaired-stages.log`.
- Fixture/report: `.data/d883-live-budget-real-libraries-base/`.

Both modes use the same fresh non-SMP toolchain and configure profile from
D882: O1 compiler, O3 runtime, GCC optimization options, and the admitted
`-ftrack-macro-expansion=0`. It is not a profile-matched replacement for the
installed Homebrew SMP toolchain; Homebrew was not overwritten.

`tests/bazel_host_environment.py` directly calls the host discovery functions
in `gerbil/host_system.bzl`, preserving the repository's SDK/assembler and
Homebrew OpenSSL/SQLite/zlib include, library, pkg-config and link settings.
GNU compiler selectors remain explicit. Machine paths are confined to ignored
local environment/log/report files, not this receipt. Full build used two tasks;
fixture native compilation is sequential in both modes.

## Actual build and tests

All official stages completed: Gambit, bootstrap/core, `stage1-bach`, `stdlib`,
`libgerbil`, `lang`, and `tools`. Earlier failures and their recovery remain in
D882; a successful incremental-stage message before native artifact recovery
was not treated as sufficient evidence.

The fixture preserves upstream `prelude: :gerbil/base`, changes only its package
namespace and documented local import redirections, and copies latest-source
list-builder/list/vector/values/func/iterator libraries. `defbuild-script`
compiles ten library modules in separate cold `GERBIL_PATH` roots. Each mode
retains 15 generated C files and 25 native artifacts. All native library builds
exit zero, and both modes exercise the GVM hook.

The official `:gerbil/tools/gxtest` module evaluates the four copied upstream
test files against those rebuilt libraries. Both modes pass all 45 cases and
all four modules/suites, with `MODULE-OK`, `HARNESS-OK`, final `OK`, and process
exit zero. No assertion or expected result was changed. The earlier direct-file
tool invocation lost its relative `./env` import context; only tests were rerun
after fixing the entry. Source heads, source hashes and retained C hashes were
checked before retesting; native libraries were not rebuilt.

Replay from project root:

```sh
python3 patches/gerbil-v19-darwin/tests/run_gambit_live_budget_build.py \
  --source .data/gerbil-gambit-bootstrap-audit \
  --toolchain .data/gerbil-gambit-bootstrap-audit/build \
  --output .data/NEW_UNIQUE_RUN
```

`--native-tests` is a separate, extra AOT-test path, not the official source-test
flow. In the earlier installed-toolchain attempt its `push!` void assertion
failed. Upstream documents that macro's return as unspecified; that failure is
not proof of a candidate semantic regression or a version-mixing root cause.

## Candidate Decision

Candidate totals: **807 purification/common-code calls, zero sparse eligible
cases, zero changed cases, zero net live-block delta**. Therefore this guard
change does not remove real work from these base libraries. No timing matrix
is warranted for a branch that never activates.

Instrumented single-pass build times were 24.053 seconds baseline and 22.057
seconds candidate. Official test reruns took 32.052 and 8.017 seconds. These
are exploratory receipts, not acceleration evidence: load averages exceeded
the existing 12-CPU host gate, order/cache effects were uncontrolled, and the
candidate did not activate. `timingQualified` is false.

Raw generated-C hashes are not all identical. An inspected vector C difference
is its generated module timestamp (both the numeric constant and initialization
assignment). `src/gerbil/compiler/driver.ss:compile-timestamp` uses current time.
No claim of full C/object byte equality is made.

The D881 synthetic three-to-two block reduction remains valid but has no
demonstrated real-library incidence here. This is a rejected bounded candidate,
not a fundamental resolution of macOS build/test slowness. The successful Bazel
environment and admitted flags should remain the fixed foundation for further
source-level work, not be rediscovered in another benchmark matrix.
