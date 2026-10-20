# D1469: real MCP process census and advantage-extension boundary

## Scope

This is a diagnostic receipt, not an acceleration admission. Keep the existing
0001 spawn, 0007 object-reuse and GNU preprocessing results and their separate
phase boundaries. The major first-compile delay and native-test acceleration
remain unresolved. No production patch, consumer Scheme, package HTTP code,
installed toolchain or Linux activation was changed.

Common library/object inputs: `.data/d1391-runtime-object-source/build`, Gerbil
v0.19-staging `1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`. GNU GCC 16 was resolved through
the existing Bazel host environment. The machine supplied 12 physical workers.
The original MCP checkout head was `9a5c35e275e5d6847ff421151bb224f2eae177c1`.

## Observer admission and rejected attempts

The private observer interposes fork, posix_spawn and posix_spawnp in the
diagnostic Gerbil/gxi/gsc binaries. The method follows Apple's
[dyld interposing header](https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/dyld-interposing.h).
No security policy was changed. It records API intervals, parent program,
target basename, status and child PID, not argument contents or personal paths.

Retained attempts must not be used as complete coverage:

- D1463 stopped before workload execution because sandbox hardware discovery
  was denied.
- D1464's control assertion failed: libc PATH search made nested spawn calls
  inside spawnp, causing double counting. Thread-local call depth now admits
  only outermost calls.
- D1465's workloads passed, but its positive qualification field does not admit
  a complete process census. Environment-based observer loading did not reach
  the shebang-launched gxi or its GSC children. Its prefix filter also mixed
  Python monotonic and C CLOCK_MONOTONIC epochs. Those empty prefix/child counts
  are invalid, not evidence of no process creation.
- D1466 stopped before the workload because GSC needed an explicit isolated
  runtime directory mapping.

D1467 links the observer as a required dependency of private Gerbil and GSC
executables, retaining the original generated-module objects and runtime
archives. The build child and all 740 GSC launches have loaded-observer records.
The prefix filter uses C CLOCK_MONOTONIC on both sides; Python monotonic remains
only the watchdog/duration clock. The native control observes one each of fork,
spawn and spawnp, with successful statuses.

D1468 additionally checks the actual Gambit eligibility boundary: an absolute
program path with an explicit environment uses spawnp, while a bare program
name with an explicit environment uses fork. Both children and GUARD-OK pass.
Thus zero fork in the workload is not an observer that cannot see the retained
fallback.

## Actual clean and complete build

The fresh isolated fixture underwent official `gerbil clean` with zero project
native images afterward, followed by complete `gerbil build`. Both exited zero;
the MCP executable exists, and build/test input hashes remain unchanged. The
existing 10-second product-output and 180-second total build gates were kept.

| Observed boundary | Spawnp calls | Fork calls | Summed API interval |
| --- | ---: | ---: | ---: |
| Before literal first compile line | 2 | 0 | 0.000963 s |
| Complete build, observed Gambit parents | 1482 | 0 | 3.711499 s |

The first literal line was `... compile util/compat`, at 5.934667 seconds in
this observer run. It is not an uninstrumented performance comparison. Both
prefix launches belong to the outer Gerbil process: git and build.ss.

Complete-build parent counts: Gerbil 2, gxi 927, GSC 553. Targets: GSC 740,
gambuild-C 553, env 186, git 1, build.ss 1, GNU GCC 1. All observed API calls
succeeded. Summed intervals include concurrent parents; they must not be
subtracted from wall time or advertised as available speedup.

Coverage is the admitted Gerbil/gxi/GSC process-creation paths. Shells, env,
GNU compiler internals and arbitrary FFI subprocess creation were not given
permanent observer dependencies. This is not a census of every descendant's
internal process APIs, nor a proof about every possible Gerbil build.

## Actual concurrent tests

Twelve concurrent `gerbil test -v 5 test/unit/regex-test.ss` processes ran the
unchanged original MCP regex suite. All exited zero, each returned exactly 19
CASE-OK records and final OK: 228 cases total. The five-second real-output and
90-second total gates were unchanged. Each root has a loaded-observer record;
these tests recorded no subprocess-creation calls.

This is the regex suite only, using the just-built project libraries. It does
not admit the complete MCP suite, OS-cache-cold testing or test acceleration.

## Source policy and next optimization boundary

The current isolated `gambuild-C` already places
`-ftrack-macro-expansion=0` on its common C_COMPILER command. Object and dynamic
compilation inherit that command. Merely moving this already-present option
between output flags cannot create a new major gain in this fixture. Bootstrap
propagation and Scheme macro execution remain distinct questions.

The new census closes D1416's source-only uncertainty for this real MCP sample:
ordinary Gambit compiler-chain fork fallback is not a remaining dominant
target. Existing spawn gains remain valuable, but removing another fallback
does not address this observed first-log window or these in-process tests.

There are many actual compiler launches after the first line. Reducing their
number or avoiding equivalent generated/native work remains relevant to total
build experience. However, D1415 already measured the simple object-producer
fusion at about 4.16 percent for producer waves; do not repeat it or label the
740 launch count a new end-to-end speedup. Wider reuse must first identify an
equivalent producer/output contract, and then pass actual complete build and
test checks. The first-window optimization still needs actual Scheme execution
cost reduction, not reordering logs or broadening an irrelevant fork path.

## Durable evidence

- `.data/d1463-process-census.c`, `.data/d1463-process-census-control.c`
- `.data/d1463-process-census.py`
- `.data/d1467-process-census-linked-home/report.json`
- `.data/d1467-process-census-linked-home/build/events.json`
- `.data/d1468-process-census-guards.py`
- `.data/d1468-process-census-guards/report.json`

Earlier failed attempts remain under their original `.data` directories. None
of these diagnostic outputs is a production performance patch.
