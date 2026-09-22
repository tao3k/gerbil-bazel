# D853: MCP cold-build 10-second silence boundary

Date: 2026-09-22. No Gerbil or gerbil-mcp source was changed. The strict
10-second package-build silence gate remained enabled. The original four-patch
AOT binary and frozen D851 AOT binary retained their D851 SHA-256 identities.

## Location of the interrupted interval

The interrupted D851 run in `d851-mcp-ab.json` emitted the `std/net/request`
deprecation warning at 5.483 s, then no complete line before the silence
watchdog terminated the process at 16.073 s. The receipt records a 10.590 s
warning-to-watchdog boundary (including termination overhead); the watchdog
reported 10.08 s of silence. No `... build in current directory`, `std/make`
graph, or compile event had occurred. Its 16.073 s is **not** a completed build
time.

The V19 `gerbil` dispatcher imports `:gerbil/tools/gxpkg` before calling its
`main`; `pkg-build` prints `... build in current directory` before manifest
generation and the build-script subprocess. Thus this failure is on the
gxpkg import/dispatch side of the first package-build log, not the measured
Darwin executable-object DAG or GCC compilation. The warning is only a nearby
timestamp, not evidence that the deprecated module itself is defective.

## Focused startup probe

`/private/tmp/d853_startup_probe.py` used the existing consumer harness,
identical sanitized build environment, real GCC 16, and 12 Gerbil build cores.
It alternated `gerbil pkg version` eight times per toolchain from the real
gerbil-mcp checkout, exercising gxpkg import without compiling MCP. All 16
commands succeeded under the 10-second silence gate. The warning-to-version
interval ranged roughly 0.42-1.20 s; the first observed command wall times
were 3.710 s (original) and 4.195 s (D851). This does not reproduce the
intermittent outlier, nor does it prove what the interrupted process was doing.

## Strict real-consumer replay

`/private/tmp/d853-mcp-strict.json` is a clean-clone, same-revision
(`9a5c35e275e5d6847ff421151bb224f2eae177c1`) MCP cold A/B with the
existing runner, 12 workers, real GCC 16, and a hard 10-second silence gate.
Both builds and executable checks passed.

| Boundary | Original | D851 |
| --- | ---: | ---: |
| Complete cold build | 99.469 s | 85.333 s |
| Warning to `... build in current directory` | 0.548 s | 0.477 s |
| Build entry to first `... compile` | 6.923 s | 6.831 s |
| Build start to `... compile main` | 43.277 s | 45.856 s |
| First executable object to link | 20.591 s | 0.069 s |
| Maximum output gap | 6.923 s | 6.831 s |

D851 was 14.2% faster **within this pair**. The combined 184.8 s is two
separate builds, not one candidate build. Compared with the earlier strict
pair (74.727/59.555 s), both variants became about 25 s slower. The original
and D851 binaries, consumer revision, core count, and build state stayed
fixed. Time increased before `main` and between `main` and executable-object
submission in both variants; D851's object-to-link boundary stayed near zero.
This is common-mode timing drift, not evidence that the D851 object-reuse
algorithm lost its benefit. The exact host cause is not established by these
receipts; process-level sampling was unavailable in the sandbox.

## Decision

Keep the 10-second gate and the D851 release hold. The single interrupted
interval is localized to pre-build gxpkg import/dispatch, while normal
startup probes and this strict cold replay do not reproduce it. Do not label
it a `std/make` graph stall, a proven `std/net/request` bug, or a resolved
first-access issue. On the next occurrence, capture the gxpkg process state
or an import/dispatch timestamp before relaxing any gate. Report package
build wall time separately from the total wall time of an A/B pair.
