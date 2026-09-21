# Gerbil v0.19 Darwin build patch stack

This directory carries the local validation stack for the Gerbil v0.19
Darwin build work. The release path is the measured four-patch performance
stack. Later observability and architecture experiments remain separate until
an adjacent dual-consumer A/B admits them.

## Four-patch release order

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
4. `0004-gambit-darwin-gcc-macro-expansion.patch`
   - owner: Gambit C compiler capability configuration
   - scope: Darwin with real GNU GCC only; Apple/LLVM and non-Darwin paths are
     unchanged
   - mechanism: disable GCC macro-expansion provenance tracking after the
     existing compiler capability probe; retain `-O1`, `--enable-gcc-opts`,
     `-pipe`, and all runtime code-generation flags
   - build invariant: the audited generated `configure` is touched after patch
     application so Gambit's make rules do not regenerate it with a host
     Autoconf version other than the upstream 2.69 baseline
   - evidence: the real MCP embedded object improved from 15.45 seconds to
     10.37 seconds; GCC frontend allocation fell from about 8.9 GiB to 97 MiB,
     and the Mach-O object remained byte-identical

The existing release-only FFI and AOT-tool patches are applied in addition to
these four Darwin performance slices. The release workflow records a digest of
that exact source, patch, and workflow set in its cache key, build receipt, and
immutable release tag. The 65.35-second complete MCP build in D804 is the best
recorded four-patch result, not a reproducible guarantee for another host or
revision.

## Observation-only patches, excluded from the performance release

Patches `0005` (build observability) and `0006` (test observability) remain
local investigation candidates. They are not applied by `publish-v19.yml` and
their later observed build cannot replace the four-patch performance baseline.

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

| real consumer / candidate | measured wall | result |
| --- | ---: | --- |
| Gerbil POO, deferred batch executor | 16.45 s | build passed |
| Gerbil POO, minimal streaming executor | 13.49 s | build passed; `-18.0%` |
| Gerbil MCP, frozen pre-closure baseline | 175.19 s | build passed |
| Gerbil MCP, deferred batch + Darwin DAG | 99.20 s | build and binary passed |
| Gerbil MCP, minimal streaming + Darwin DAG | 79.58 s | build and binary passed; `-19.78%` vs batch |
| MCP largest generated C, GCC macro tracking on | 15.45 s | byte-identical baseline object |
| MCP largest generated C, GCC macro tracking off | 10.37 s | `-32.88%`; byte-identical object |
| Gerbil POO, qualified four-patch V19 AOT toolchain | 12.01 s | native-warm rebuild passed; `-10.97%` vs 13.49 s |
| Gerbil POO, observed host-derived 12-worker run | 13.13 s | native-warm rebuild passed; frontend 12.438 s |
| Gerbil MCP, observed host-derived 12-worker run | 81.03 s | build and binary passed; `+1.82%` vs 79.58 s |
| Gerbil MCP, missing `GERBIL_BUILD_CORES` | 393.33 s | excluded diagnostic; serialized Gerbil producer |

The final MCP candidate is `54.58%` below the frozen external baseline and
`4.91%` below the earlier 83.69-second full experimental stack. Its arm64
Mach-O executable passes version reporting and MCP initialize. The real POO
consumer returns to the established 13-second native-warm rebuild range
instead of regressing to the deferred-batch result.

The qualified Git-backed V19 toolchain also completed a real native-warm
Gerbil POO consumer rebuild in 12.01 seconds after excluding a 37.24-second
macOS first-access run. A later observed native-warm run, with the host-derived
12-worker setting explicitly present, completed in 13.13 seconds. These are
not empty-`.gerbil` cold builds: the consumer's native `clean` preserves
generated native artifacts. The equivalent unchanged MCP
run completed in 81.03 seconds, only 1.45 seconds (`+1.82%`) above the earlier
79.58-second candidate, and produced a valid arm64 Mach-O binary.

Real-consumer A/B admission is fail-closed: by default a candidate may not be
slower than its adjacent same-state baseline (`--max-regression-percent=0`).
For the POO native-warm lane, pass `--max-candidate-seconds=13.13` as the
absolute anti-drift gate; 12.01 seconds remains the best qualified milestone.
An empty-`.gerbil` first-access run or an unrefactored POO source tree cannot
replace this baseline.

The 393.33-second MCP run is retained only as an excluded diagnostic: its
direct Make invocation omitted `GERBIL_BUILD_CORES`, so `std/make` used one
Gerbil producer. It is not an A/B candidate and must not be rerun as a
baseline. Phase evidence now rejects broad import/macro work as the primary
tail: all 561 import events accumulated 5.242 seconds and the maximum was 476
milliseconds, while the `main.ss` producer alone took 33.270 seconds. The next
gate therefore splits executable closure enumeration, `prepare-link`/`gsc
-link`, object submission, and final link without changing either consumer.
These phase events originated as temporary diagnostic instrumentation in D803.
Patch 0005 is retained for investigation but is outside the four-patch
performance release until an adjacent end-to-end A/B qualifies it.

The compiler atomic gate passes at two workers and covers host budget
resolution, peak concurrency, follow-up work, parameter preservation, and
first-error propagation. Historical MCP tests still contain four known
output-contract failures; they are baseline state and are not reported green.

Machine-readable evidence is in
`receipts/d801-converged-dual-consumer.json` and
`receipts/d803-frontend-dual-consumer.json`. Earlier receipts remain as the
audit trail for rejected hypotheses and attribution experiments.

## Admission gates

- Patch replay against D801 must pass without context drift.
- Gambit focused process tests must remain green.
- Compiler executor contracts run with 1, 3, and host-derived workers.
- The executor must propagate a raised `#f`, drain work submitted by a worker,
  retain submission parameters, and reopen cleanly after an error. The
  release workflow runs this contract against the built compiler, not merely
  against patch text.
- The Darwin executable closure records object success independently of the
  exception value; a failed object must never release the link barrier, even
  when the exception is `#f`.
- The Darwin process test covers environment, working directory, stderr
  redirection, child-specific `PATH` resolution, and missing executable on the
  built Gambit interpreter. Darwin `posix_spawnp` does not search the supplied
  child environment's `PATH`; only that bare-name/explicit-environment case
  keeps the original fork/exec path.
- Run tests separately before the final clean cold build.
- Validate both real consumers: Gerbil POO and Gerbil MCP.
- Record cold and warm measurements separately.
- A ten-second interval without progress is a failed or inadequately observed
  local gate.
- Do not install Homebrew or publish a new release until the exact release
  patchset and its independent consumer gates are stable.

See `REFLECTION.md` for the round-by-round evidence and rejected approaches.
