# D879: latest staging Gambit process and bootstrap source audit

Date: 2026-10-02. Source attribution and bounded capability checks only.
No new timing comparison, toolchain build, performance patch, or release.

## Exact source

The user selected the latest official staging, superseding the installed
Homebrew release as the source under investigation. A fresh fetch from
`https://git.cons.io/mighty-gerbils/gerbil.git` resolved `v0.19-staging` to
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. Its Gambit gitlink is
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f` in
`https://git.cons.io/mighty-gerbils/gambit.git`, branch `gerbil-patches`.
The fresh mirror's branch head matched that gitlink.

The source checkout is `.data/gerbil-gambit-bootstrap-audit` relative to the
project root. Both repositories were clean at these commits during this audit.
Local checkout availability is not a source pin; reproduce by fetching the
full hashes above.

Gambit `ea114fc3` changes only `include/gambit.h.in`, `tests/makefile.in`, and
`tests/stack-overflow-undo.c` relative to the historical `dcd677cd` baseline.
The process runtime, bootstrap Makefile, configure inputs, and C emitter
`gsc/_t-c-1.scm` are unchanged. The new continuation ownership fix must remain
part of any candidate; an older Homebrew compiler does not qualify this source.

## Darwin subprocess cost has a concrete source mechanism

At `lib/os_io.c:9156`, ordinary subprocess creation still calls `fork()`.
Before `execvp`, its child calls `___closefrom(fd + 1)` at line 9237 and
closes the remaining lower descriptors, excluding the required descriptors.

`lib/os_setup.c:225` implements `___closefrom` with this priority:

1. Native `closefrom` when configure finds it.
2. `SYS_close_range` when configure finds that syscall.
3. `fcntl(F_CLOSEM)` when the platform exposes it.
4. Otherwise, one `___close_no_EINTR` per descriptor up to
   `sysconf(_SC_OPEN_MAX)` (or the resource-limit fallback).

The accompanying `tests/gambit-process-capabilities.c` queries capabilities
without spawning a compiler workload or closing descriptors. It compiled with
both Apple Clang and Homebrew GCC 16 using `-Wall -Wextra -Werror`. Both native
executions returned:

```text
openMax=1048575 softLimit=1048575 hardLimit=9223372036854775807 closefromSymbol=absent SYS_close_range=absent F_CLOSEM=absent
```

Thus this host falls into the per-descriptor loop. For the usual small start
descriptor, every Gambit subprocess launch attempts nearly a million closes,
including closed descriptors. The source cost scales with the descriptor
limit, not the number of open descriptors. Linux installations that configure
with `closefrom` or `SYS_close_range` take a bulk-close path; no fresh Linux
runtime was measured here.

This gives a concrete explanation consistent with the existing controlled
Darwin `posix_spawn` result (28.853 s to 10.465 s on the 120-module fixture),
without re-running that benchmark. It does not separate fd cleanup time from
the remaining `fork` cost, nor assign either an unmeasured share of a complete
build. `0001-gambit-darwin-posix-spawn.patch` applies cleanly to `ea114fc3` and
bypasses this child loop for its eligible ordinary subprocesses. Its documented
fallbacks, including pseudo-terminal jobs, still need the original path.

## Gambit's own make stage has a different call path

`configure.ac:3298-3300` constructs `BUILD_OBJ_RTS` and `BUILD_OBJ` as direct
C-compiler commands. The makefiles invoke those commands themselves;
Scheme-to-C rules use `gsc-boot -c`, and link-file generation uses `-link`.
Consequently the fd sweep above is an explanation for Gambit/Gerbil-initiated
native subprocesses, not a direct attribution of the historical `gambit=487`
release stage. That stage cannot inherit the 120-module spawn speedup by
assumption.

The actual staging bootstrap graph is:

```text
Gerbil src/build.sh:115
  remove boot and gsc-boot
  make bootstrap
    core
    copy built gsc to gsc-boot
  make from-scratch
    bootclean
    make bootstrap
      core
      copy rebuilt gsc to gsc-boot
    bootclean
    make core
```

This follows `Makefile.in:140-144`, its `bootstrap-pre: core` dependency, and
`gsc/makefile.in`'s `bootstrap-post` copy. `bootclean` removes the generated
C family (`GENDISTFILES`) as well as objects/libraries/executables, while
retaining the root bootstrap compiler. Hence the last two passes regenerate
Scheme-to-C and recompile native objects; they are not merely repeated no-op
make commands.

For this non-release Git revision, `gsc-boot` creation may also build the
`v4.9.8` release compiler under `boot/`, then rebuild that bootstrap compiler
with the current `gsc/*.scm`. The source archive and `BOOTSTRAP_CONFIGURE_FLAGS`
form a separate build environment. Current `lib/os_io.c` and current configure
patches are not copied wholesale into that release archive.

The first bootstrap supplies an executable compiler because the initial dummy
`gsc-boot.unix` deliberately cannot regenerate the checked-in C. Removing it
before `bootclean` would delete the input needed to break this circular
dependency. The later self-compilation rounds are a candidate for reducing
duplicate work, but source inspection alone does not prove that their output
is interchangeable. A reduction requires a comparison of generated C from
successive compiler generations under identical final flags, followed by
latest-staging compiler/runtime qualification. No bootstrap step is deleted
by this audit.

Both release platforms select single-host unlimited mode. That increases the
native compiler's per-module function size, so it explains baseline compile
cost but not the platform difference on its own. The release workflow's
Darwin GCC 16 profile also differs from Linux's compiler/configure profile.
The historical large-object macro-tracking receipt remains applicable as an
owner hypothesis: `0004-gambit-darwin-gcc-macro-expansion.patch` applies cleanly
to the latest Gambit. Its measured gain is still the old receipt, not a newly
qualified latest-staging result.

## Reproduction and decision

From the gerbil-bazel repository, the bounded Darwin capability probe is:

```sh
GNU_GCC=$(command -v gcc-16)
mkdir -p .data
env -u SDKROOT -u CPATH -u C_INCLUDE_PATH -u CPLUS_INCLUDE_PATH -u LIBRARY_PATH \
  COMPILER_PATH=/usr/bin "$GNU_GCC" -Wall -Wextra -Werror \
  patches/gerbil-v19-darwin/tests/gambit-process-capabilities.c \
  -o .data/gambit-process-capabilities-gcc16
.data/gambit-process-capabilities-gcc16
```

Read-only gates passed: exact staging/gitlink identities, clean source trees,
unchanged historical owner files, both existing Gambit patch applicability
checks, and both compiler capability probes. No broad build or performance
qualification was repeated.

The fd-limit-dependent child cleanup is a concrete Darwin runtime cause and
the existing spawn patch targets it. The bootstrap graph independently
multiplies native compiler work; preserving its producer dependency is the
constraint on any simplification. Neither finding admits a new worker-count,
batching, optimization-level, or release change.
