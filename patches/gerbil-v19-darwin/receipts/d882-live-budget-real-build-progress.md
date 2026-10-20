# D882: real build/test validation in progress

This receipt preserves recovery history. The isolated build and official
base-library suites subsequently pass in D883; there is no new speedup claim.

## Durable location

At the user's request, the active process group was suspended with SIGSTOP,
the source/build tree, preliminary outputs and logs were moved into this
project's `.data/`, and the same group was resumed with SIGCONT. The move did
not restart compilation. `.data/` is ignored by Git and survives reboot.

All paths in this receipt are project-relative unless expressed as variables.
Current source/build root: `.data/gerbil-gambit-bootstrap-audit`.
Current log: `.data/d882-staging-resumed-build.log`.
Current installation destination: `.data/d881-staging-install`.
The old temporary source and installation paths are symlink aliases, not the
storage locations. Machine-specific aliases stay in ignored local state.
After reboot, run `sh tests/restore_d881_build_aliases.sh` from this
patch directory to restore aliases used by previously configured build files.
Future validation outputs go directly into the project's `.data/`.
The subsequent actual reboot preserved the checkout and artifacts. Recovery
inventoried 186 retained stage1 Scheme files, reused 97 native outputs after
timestamp/load-command checks, and compiled the remaining 89 with two workers.
Input hashes and results are in `.data/d882-core-resume/report.json`; trace
`.data/d882-core-resume.log` ends with `D882-CORE-NATIVE-JOBS-OK`.
These structural checks are not a substitute for runtime suite validation.
Official remaining stages continue through `tests/continue_d882_gerbil_stages.sh`;
log `.data/d882-staging-final-stages.log`. A GNU GCC wrapper carries the admitted
macro-tracking option into direct Gerbil compiler invocations as well.

The first continuation completed `stage1-bach`, then stdlib failed compiling
`std/crypto/libcrypto~0.c`: `openssl/rand.h` was not found. The continuation
harness had cleared the dependency include/library environment. This was a
harness configuration error, not evidence against the staging compiler.
Recovery now directly executes the Python-compatible discovery functions from
`gerbil/host_system.bzl` through `tests/bazel_host_environment.py`. Thus SDK,
assembler, Homebrew OpenSSL/SQLite/zlib include/library/pkg-config paths and
link flags come from the existing Bazel implementation. GNU GCC/G++ 16 remain
explicit overrides; the compiler profile and macro-tracking option are unchanged.
Ambient SDK/dependency paths are cleared before discovery, not after it.
The same environment is used by the real-library runner. Resume starts at
`stdlib` using the official incremental builder and two tasks, without repeating
Gambit or completed core stages. Log: `.data/d882-bazel-env-stages.log`.
GNU GCC 16.2.0 successfully checks `#include <openssl/rand.h>` in this
environment. The incremental stdlib stage reports success, but `libgerbil`
then fails loading the missing native `std/struct/queue~1` macro module.
Source inspection explains the false completion: `gxc-outputs` in
`src/std/make.ss` tracks only `.ssi` and static Scheme output, not dynamic
native artifacts. Both tracked outputs may exist before deferred native jobs
finish. A failed/interrupted native batch can therefore be skipped on retry.
`tests/repair_d882_std_checkpoints.py` inventories retained Scheme/native
outputs, and moves only the corresponding premature static checkpoints into
ignored backup storage. It found 271 affected owners and preserved 271
checkpoints in `.data/d882-std-checkpoints/`; report records project-relative
artifact paths. Native validation uses file existence/size and `otool -L`;
it is not a runtime conformance check. Official stdlib compilation resumes
with the same Bazel environment and two tasks; log
`.data/d882-bazel-env-repaired-stages.log`. The repaired official stdlib stage
completed successfully (`D882-STAGE-OK stdlib`). The official `libgerbil`,
`lang` and `tools` stages also completed successfully; the continuation process
exited zero. Together with the earlier Gambit, bootstrap and core receipts this
completes the isolated source build. It does not install over Homebrew.
Real suite validation subsequently passes in D883.
Before libgerbil emits its first static compilation event, a one-second sample
has 735/738 main-thread samples under `___dynamic_load -> dlopen`, and 709/738
under dyld's segment mapping `fcntl`. Local sample:
`.data/d882-libgerbil-sample.txt`. The corresponding Gambit source path is
`src/gambit/lib/os_dyn.c`, which invokes `dlopen(cpath, RTLD_NOW)`. This is a
bounded observation of native-module loading, not a whole-build attribution or
a speedup result. No system security/signature policy is changed.

## Latest staging full build

Source: `.data/gerbil-gambit-bootstrap-audit`, Gerbil
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.

Successful isolated configuration (local paths parameterized):

```sh
GNU_GCC=$(command -v gcc-16)
GNU_GXX=$(command -v g++-16)
# INSTALL_ROOT is the isolated installation destination in local build state.
env -u SDKROOT -u CPATH -u C_INCLUDE_PATH -u CPLUS_INCLUDE_PATH \
  -u LIBRARY_PATH COMPILER_PATH=/usr/bin \
  CC="$GNU_GCC" CXX="$GNU_GXX" \
  ./configure --prefix="$INSTALL_ROOT" \
  --with-gambit=ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f \
  --disable-shared --enable-march= --enable-single-host=0 \
  --enable-c-opt=-O1 --enable-c-opt-rts=yes --enable-gcc-opts \
  CFLAGS='-pipe -foptimize-sibling-calls'
```

Configuration needed network-enabled execution because it always fetches the
Gambit remote, even when the exact commit is already local. No remote write.

The full build is running with two tasks, preserving O1 and GCC optimization
options. An existing admitted macro-tracking option is passed to the native
compiler, including bootstrap compilers:

```sh
env -u SDKROOT -u CPATH -u C_INCLUDE_PATH -u CPLUS_INCLUDE_PATH \
  -u LIBRARY_PATH COMPILER_PATH=/usr/bin GERBIL_BUILD_CORES=2 \
  make -j2 "C_COMPILER=$GNU_GCC -ftrack-macro-expansion=0"
```

Build log: `.data/d881-staging-build.log`.
Installation prefix configured as
`$INSTALL_ROOT/v0.19-dev-63-g1cfb032c` (local alias of the durable destination).
The existing Homebrew installation is untouched.

The initial invocation was interrupted before later Gerbil stages: configure
does not persist the shell's `CC`/`CXX`/`GERBIL_GCC` environment for those
stages, and this host's bare `gcc`/`cc` resolve to Clang. Recovery uses
`tests/resume_d881_staging_build.sh`, exporting all three GNU compiler entries,
running Gambit's official `from-scratch` target with the completed bootstrap
seed, then installing build-tree artifacts and running Gerbil stages in order.
Recovery log: `.data/d882-staging-resumed-build.log`.
Gambit's `from-scratch` target completed successfully. The continuation shell
then failed with an EOF parse error after its executing script had been edited
for path portability; this is a harness failure, not a Gambit compile failure.
Continuation uses the validated `--skip-gambit` option, installs the completed
artifacts, and proceeds through Gerbil stages without recompiling Gambit.
Gerbil-stage log: `.data/d882-staging-gerbil-build.log`.
The copied GSC reports `v4.9.8-19-gea114fc3` and the configured GNU GCC 16,
O1 compiler/O3 runtime optimization profile.
All 13 synthetic GVM guard/merge regression checks pass with this fresh GSC;
marker `GVM-LIVE-BLOCK-GUARD-OK`, log `.data/d882-gvm-regression.log`.
This does not prove a real-library speedup.
The configured runtime is non-SMP; it is not a profile-matched replacement
for the installed SMP Homebrew runtime. Candidate/baseline fixture runs must
both use this same fresh runtime.

The make override enables macro-tracking suppression for Gambit core native
compilation, but it does not automatically persist into generated `gambuild-C`.
Before subsequent Gerbil stages, the generated local driver and its generated
`.unix` counterpart were explicitly updated to retain the same admitted option.
No Scheme compiler source or optimization level was changed. The real-library
harness additionally passes the option explicitly to every fixture module.

The host has 12 CPUs and load averages around 100-136 during this work.
Wall-time comparisons are not qualified performance evidence in this state.

## Harness and discarded preliminary runs

Runner: `tests/run_gambit_live_budget_build.py`.
It copies current staging list-builder/list/vector/values/func/iter libraries
plus list/vector/values/iter upstream tests into a separate namespace. The only
upstream test-source substitutions redirect list/values/iter imports to rebuilt
copies; iter macros also import the rebuilt list-builder dependency.
`defbuild-script` compiles native library artifacts with real GNU GCC and keeps C.
The default test path invokes latest-source `src/tools/gxtest.ss` on the four
unmodified test files (apart from documented import redirections). The optional
`--native-tests` retains the extra AOT-test path used in preliminary attempts;
it is reported separately as a different test flow. No test expectation changes.
The runner builds a native GVM hook with the selected toolchain, then builds
baseline and candidate cold outputs, executes suites, records GVM invocation
counts, source/C hashes, artifact counts, load and exploratory timings. All four
suites execute before reporting a test failure; both mode results are retained.
The report includes exact source commits and GCC/GSC version output.
The runner rejects Clang using compiler predefined macros and requires GNU
major version 16. Runtime paths are resolved locally, not hard-coded in Git.
The hook observes block counts after the pipeline's existing dead cleanup;
it does not execute extra cleanup passes to collect statistics. The fourth
counter is the net live-block delta through the natural follow-up cleanup,
not an isolated timing or instruction-count measurement.

Two important preliminary failures must not be hidden:

1. Replacing `c#bbs-remove-common-code` alone does not intercept the compiled
   GVM's direct `JUMPINT` call. Initial counters were zero. These runs do not
   compare an active candidate. The corrected hook replaces the external
   `purify-procs` entry (called via `JUMPGLONOTSAFE` in `_front.c`) and retains
   the exact purification sequence/fixed point. The corrected entry probe
   reports four real invocations on generated list-builder Scheme input.
2. Latest-source list tests rebuilt with the installed Homebrew Gerbil core
   fail because `(push! 10 l)` returns a list rather than the required void.
   Log: `.data/d881-real-libraries-fifth/baseline-test-repaired.log`.
   No test expectation is changed to bypass this failure. The source document
   `doc/reference/std/misc/list.md` explicitly specifies an unspecified return
   value for `push!`. Thus a native test requiring void is not itself evidence
   of a compiler semantic regression, and version mixing is not an established
   diagnosis. The latest staging toolchain and the official source-test flow
   must be checked separately from this extra native-test assumption.

Earlier fixture setup attempts also exposed root resolution, buildspec and
TestConfig constructor issues; the runner now supplies the explicit runtime
root, uses `gxc:` specs, copies list-builder, and uses required keyword fields.
None of those failed attempts is admitted timing evidence.

## Subsequent validation

The isolated latest staging build is complete. The corrected native-hook
harness builds real libraries, retains C/native artifacts, and the official
four upstream suites pass in both modes. D883 records 807 GVM invocations and
zero eligible/changed cases; this candidate is rejected for that scenario.
Synthetic three-to-two GVM block reduction alone is not proof of faster builds.

The first fresh-toolchain real run (`.data/d883-live-budget-real-libraries/`)
fails during fixture expansion before GCC: the fixture metadata omitted the
upstream `prelude: :gerbil/base`, so iterator `HashTable` signatures were not
bound. The runner now preserves that prelude; the failed run is discarded.
