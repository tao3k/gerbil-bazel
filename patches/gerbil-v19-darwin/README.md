# Gerbil v0.19 Darwin build patch stack

This directory carries the local validation stack for the Gerbil v0.19
Darwin build work. The patches are review slices, but they form one ordered
stack and are published together only after the full local stack is stable.

## Active patch order

1. `0001-gambit-darwin-posix-spawn.patch`
   - owner: Gambit Darwin process runtime
   - scope: ordinary subprocess creation; pseudo-terminal creation remains on
     the existing fork path
   - evidence: controlled 120-module cold A/B improved the median from 28.853
     seconds to 10.465 seconds (`2.76x`)
2. `0002-gerbil-streaming-compile-executor.patch`
   - owner: Gerbil compiler native-job executor
   - scope: a host-derived fixed worker pool starts on the first native job and
     closes at the official `execute-pending-compile-jobs!` boundary
   - contracts: bounded concurrency, producer/native overlap, follow-up drain,
     first-error propagation, and submission parameterization
   - invariant: official V19 `std/make` source and graph algorithm are unchanged
3. `0003-gerbil-darwin-executable-closure-dag.patch`
   - owner: Gerbil compiler driver separate-linkage executable closure
   - scope: Darwin submits independent static objects and one final barrier
     link to the existing compiler executor
   - invariant: non-Darwin retains the official V19 single closure job

## Convergence decision

The former Patch 0002-0007 series was an investigation history, not six
independently admitted optimizations. It has been replaced by the two Gerbil
patches above:

- bounded executor, parameter capture, and streaming lifecycle are one compiler
  responsibility in Patch 0002;
- the measured Darwin executable tail is one driver responsibility in Patch
  0003;
- report structs, `make/contexts`, build-entry caching, slot admission,
  expanded clean semantics, and the `std/make` lifecycle rewrite are absent;
- the libgerbil closure-manifest experiment is not in the active stack until it
  has a same-revision clean end-to-end A/B independent of this consumer round.

## D801 evidence

Base revision: `d801e7a1c7f77df421f638e62aaebe370f193c97`.
Darwin builds use GCC 16 with Nix SDK/include/library variables removed and
`COMPILER_PATH=/usr/bin`. Worker count is supplied by the host/environment; no
source constant fixes it at 12.

| real consumer / candidate | cold wall | result |
| --- | ---: | --- |
| Gerbil POO, deferred batch executor | 16.45 s | build passed |
| Gerbil POO, minimal streaming executor | 13.49 s | build passed; `-18.0%` |
| Gerbil MCP, frozen pre-closure baseline | 175.19 s | build passed |
| Gerbil MCP, deferred batch + Darwin DAG | 99.20 s | build and binary passed |
| Gerbil MCP, minimal streaming + Darwin DAG | 79.58 s | build and binary passed; `-19.78%` vs batch |

The final MCP candidate is `54.58%` below the frozen external baseline and
`4.91%` below the earlier 83.69-second full experimental stack. Its arm64
Mach-O executable passes version reporting and MCP initialize. The real POO
consumer returns to the established 13-second cold-build range instead of
regressing to the deferred-batch result.

The compiler atomic gate passes at two workers and covers host budget
resolution, peak concurrency, follow-up work, parameter preservation, and
first-error propagation. Historical MCP tests still contain four known
output-contract failures; they are baseline state and are not reported green.

Machine-readable evidence is in
`receipts/d801-converged-dual-consumer.json`. Earlier receipts remain as the
audit trail for rejected hypotheses and attribution experiments.

## Admission gates

- Patch replay against D801 must pass without context drift.
- Gambit focused process tests must remain green.
- Compiler executor contracts run with 1, 3, and host-derived workers.
- Run tests separately before the final clean cold build.
- Validate both real consumers: Gerbil POO and Gerbil MCP.
- Record cold and warm measurements separately.
- A ten-second interval without progress is a failed or inadequately observed
  local gate.
- Do not install Homebrew or publish upstream until the complete local patch
  stack and its independent consumer gates are stable.

See `REFLECTION.md` for the round-by-round evidence and rejected approaches.
