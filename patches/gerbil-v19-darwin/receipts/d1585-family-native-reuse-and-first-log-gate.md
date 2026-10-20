# D1585: child closure, test benefit, failed first-log gates

## Correction To Prior Evidence

D1575 verifies that build.ss's /usr/bin/env removes DYLD_PRINT_LIBRARIES but
retains the ordinary Gambit observation variable. D1547 and D1560 therefore
describe the outer process, not the whole builder family. D1555/D1565 cannot
establish that native loading was eliminated in the child, or exclude child
loading from the remaining cost. The unchanged regex test has no such builder
child; its narrower load evidence remains valid. Preserve all raw results.

D1559/D1571 selected a custom baseline outer binary without prepending its
directory for the shebang child. Their first-log comparisons are not same-binary
family controls. The driver now locks both PATHs and records expected child
hashes. D1574 verifies actual child identity with libproc, but the sampler could
delay reading stdout during child discovery. Its stacks/identity are diagnostic;
its gate failure is not clean timing. The sampler now drains output first.

## Actual Family Census

D1576 links a Darwin/Mach/GNU-only Gambit load observer, excluding Clang. It
writes private TSV, preserves errno, leaves loader policy unchanged, and uses
the same CLOCK_MONOTONIC clock as the Python first-log observation. Its variable
survives the shebang; it emits no heartbeat or synthetic product output.

D1577 passes actual MCP clean, verifies zero project native images and reaches
genuine first compilation at 6.017429 seconds, then deliberately stops and reaps
the group. This is instrumented diagnosis, not performance admission.

| Process | Successful unique loads | Observed loader duration sum |
| --- | ---: | ---: |
| Outer gerbil | 277 | 0.702370 s |
| Actual builder gxi | 198 | 0.371389 s |

The union is 314 paths; 37 are child-only, including compiler, std/make and
std/build-script modules. Sums are observer-local durations, not clean speedup
or whole Scheme cost attribution. The native_load_family parser requires root
and child coverage, matched completions, correct parentage and successful gates.
Its five tests pass.

## Reuse Extension

D1578 unions the actual family and existing actual regex closure. Twelve physical
workers reuse 280 verified objects and reconstruct only 37 added modules. All
317 retain exact native text, dependencies and original inputs. Current inventory,
GSC, header and runtime archive identities are locked. Its legacy report scope
string still says two-module; the 317 rows and family census receipt define this
run's actual coverage. The script now names the family scope for future runs.

D1579 uses the existing opt-in Darwin/GNU embedded loader, identity predicate
and ordinary fallback. Linking succeeds, but first disabled import fails the
original five-second gate. D1580 separately checks that exact linked binary:
disabled 2.753711 seconds, enabled 2.029288 seconds, both exit zero/IMPORT-OK.
These subsequent checks do not erase the first-launch failure.

D1581 fixes parent/child PATH and runs same-binary, same-home actual clean/build
ABBA. All cleans pass with zero project native images. All four builds fail the
unchanged ten-second real-output gate and are reaped. No mean or speed ratio is
admitted. D1583's corrected child sampler reaches first compilation, but is a
disturbed build-only diagnostic, not a replacement clean/build qualification.

D1582 actual unmodified MCP regex ABBA uses twelve processes per wave, same
binary/home/fixture, changing only the embedded switch. All 48 exit zero with
19 CASE-OK records and final OK: 912 cases. Five-second output and 90-second
wall gates remain unchanged.

| Observed mean | Disabled | Enabled |
| --- | ---: | ---: |
| Complete process | 3.486622 s | 1.825032 s |
| First CASE | 2.716031 s | 1.815302 s |
| Wave user CPU | 12.568628 s | 5.892541 s |

This is about 1.91x complete-test improvement and 53.1% lower user CPU in these
waves, not an incremental gain from the 37 objects over D1561, an entire MCP
test-suite proof, or CI-wide/fresh-launch performance qualification.

D1584 passes twelve starts and twelve make/test imports with the candidate and
twelve workers. Macro-heavy std/make cold construction then fails the unchanged
five-second real-output gate. No no-op/invalidation or whole make pass follows.
No new complete MCP build is admitted after the first-log gate failures.

## Separate Return-Trace Candidate

D1566-D1569 expands bounded O3 native outlining from two reentry paths to all
fourteen selected readonly traces; original Scheme/global O1 policy remain.
Initial C compilation fails for missing terminal target temporaries. Terminal
gb_t liveness is repaired with a regression test. Native imports and D1570 tiny
native/concurrent contracts pass; 44 guarded-trace and two outlining tests pass.
The expansion remains opt-in. D1573 actual MCP regex ABBA passes 912 cases but
means 2.672355 versus 2.677968 seconds show no gain. D1571 mixed-child controls
and gate failures do not qualify startup acceleration. Do not promote it.

## Decision

Keep 0001, 0007 and existing GCC preprocessing advantages. No std/make/std/test,
consumer, package or HTTP product code changes. Preserve verified object inputs
and the real test benefit, but do not ship the embedding prototype: startup and
progress gates fail, and lifetime/reinitialization, replacement and installation
semantics remain unqualified. The seven-to-eight-second objective and complete
toolchain delivery remain open. All owned sessions are terminal. No commit/push.

Private evidence: `.data/d1566-*` through `.data/d1584-*`.
