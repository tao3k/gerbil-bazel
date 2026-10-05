# D1404: actual MCP CLI tests, not a startup accelerator

## Current identity and missing gate

The canonical `v0.19-staging` remote is checked again at
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. D1403's two isolated built
toolchains and unchanged MCP fixtures remain the inputs. No product source,
Gambit flag, consumer test, or release default is changed.

D1403 covers protocol smoke and basic concurrent std/make contracts, not
the actual MCP `gerbil test` CLI. This round fills a bounded part of that
gap; it does not repeat or overturn existing failed startup candidates.

## Actual command and strict concurrency

Each toolchain runs a wave of 12 simultaneous processes, using the measured
12 physical cores, executing this unchanged MCP command:

```sh
gerbil test -v 5 test/unit/regex-test.ss
```

Test source SHA256:
`22f260d38ef5a1476b02e1421d54d3788be9aae92f631931cd609f2fa1eaa575`.
All 24 processes execute exactly 19 CASE-OK tests, report final standalone
`OK`, exit zero, and preserve the test source hash. That is 228 successful
case executions per role, not 228 distinct test cases. No product heartbeat
or process/CPU activity resets the five-second real-output silence gate.
The total bound is 90 seconds; all owned processes are terminal.

| Role, one concurrent wave each | First CASE range | Whole-process range | Largest output gap |
| --- | ---: | ---: | ---: |
| D935 control | 4.715-4.739 s | 5.064-5.129 s | 4.739 s |
| Reuse candidate | 3.697-3.730 s | 4.112-4.210 s | 3.730 s |

The control wave precedes the candidate wave. These are not order-balanced
performance samples or a causal speedup estimate. The selected CLI test
does not exercise executable-graph C-object reuse, and the candidate contains
rebuilt library artifacts. Do not attribute the difference to that patch,
claim the major build first-log cost is eliminated, or multiply this result
into a full-suite acceleration.

Raw helper, per-process product logs and structured receipt are retained in
`.data/d1404-real-mcp-test.py` and `.data/d1404-real-mcp-test/`.

## Test and optimization boundaries

The complete MCP suite is not qualified. Other test inputs include hardcoded
shared temporary paths and an external `/opt/gerbil` environment; running
the whole suite concurrently without first isolating these contracts would
not establish a clean toolchain comparison. They are not edited or silently
excluded from a claim of full-suite success.

Existing source/receipts already exclude pstate TLS under SINGLE_THREADED_VMS,
libc setjmp, per-object Darwin malloc and default-lowopt restoration as the
main startup mitigation. They remain exclusions, not newly found accelerators.
The live staging check changes no source premise. There is still no admitted
new Darwin-specific Gambit transformation removing the dominant normal
macro-execution prefix. Default release enablement remains held and the full
startup/build/test goal remains incomplete.
