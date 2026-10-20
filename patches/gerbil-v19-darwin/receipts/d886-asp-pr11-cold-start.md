# D886: PR 11 real-consumer cold startup and build

Date: 2026-10-03. The requested project is cloned under
`.data/d886-asp-pr11/source`, without tracked source edits.

## Identity and Isolation

- Repository: `tao3k/asp-gerbil-scheme`, PR 11.
- Branch: `fix/native-build-test-contracts`.
- Exact head: `e6e1a82a0835ccf9afa9936df9e2d3448c24c8f4`.
- Dependency Gerbil POO: `099b381588360a8a49fd772f666a1a00351366f5`,
  checked against the installed dependency checkout, not just the manifest.
- Toolchain: D884 latest-staging isolated binary, real GNU GCC 16.
- Hardware-derived build concurrency: 12, not the earlier two-job setting.
- Dependency/native root: `.data/d886-asp-pr11/run/gerbil-path`.
- Final report/logs: `.data/d886-asp-pr11/consumer/`.

Dependencies were acquired/built before the project cold build. The project
had no native outputs at the start of its official `gerbil build`; dependency
preparation time is separate. The final package contains 416 native `.o1`
files excluding dSYM contents. The library build projects 207 targets;
separate provider product entrypoints are not claimed to be qualified.

The runner fingerprints both gxi and gsc. It uses the repository's existing
Bazel SDK/GNU/dependency environment and validates GCC predefined macros.
No Homebrew install, checkout removal, remote push, or PR modification occurs.

## Actual Results

| Entry or Phase | Observed Seconds |
| --- | ---: |
| Official cold library build | 53.949 |
| Cold build first compile log | 6.409 |
| Cold build first sampled GCC frontend | 7.424 |
| Official warm build, no compile jobs | 7.987 |
| Native direct `gxi build.ss compile`, warm/no jobs | 3.620 |
| Wrapped `gerbil env gxi build.ss meta` | 3.693 |
| Native direct `gxi build.ss meta` | 0.678 |

The official build succeeds with a sampled peak of 11 simultaneous GCC cc1
processes. Twelve is the configured capacity, not a guarantee that the
dependency DAG always supplies twelve eligible native tasks. Sampling can
miss short-lived frontends. First GCC sample time is an observation bound,
not an exact kernel process-start timestamp.

Both warm entries have no compilation messages/jobs in their retained logs
and no sampled GCC frontends. Therefore the approximately eight-second
official warm command is not time spent compiling C. The cold command also
spends several seconds before the first compilation log. These observations
reproduce the user's startup concern in the requested real project, not a toy
fixture substituted for it.

Twelve independent startup processes per scenario exercise direct std/make
import and package-environment source-bootstrap import. Their ready markers
are pipe-reader timestamps; process startup, framework import and wrapper
startup are kept distinct. The wrapper scenario includes another Gerbil
process and must not be compared as though it were only a std/make import.

Four original focused test modules pass using explicit upstream exit-result
propagation, all four `MODULE-OK`, `HARNESS-OK`, final `OK`, and exit zero:
`build-script-command-test`, `package-build-contract-test`,
`build-api-source-bootstrap-test`, and `build-api-startup-scenario-test`.
Tests run with their normal verbosity environment. Expected results, startup
limits and assertions are unchanged. This is not the complete project suite.

## Rejected Scope Diversion

The command-entrypoint observations above do not establish a Gambit speedup.
The proposed GXPkg lazy-HTTP experiment was rejected by the user as outside
the task's scope. Its isolated source copies were restored byte-for-byte to
the toolchain originals, and generated overlay artifacts were quarantined.
The qualified toolchain and PR project sources were not modified by it.

These measurements remain bounded observations, not a recommendation to
change GXPkg, package lifecycle behavior, or HTTP imports. Further optimization
work must target the Gambit costs already established in the Reflection
records and validate gains with real native builds and original tests.
No new Gambit optimization or cold-build speedup is admitted here.

## Measurement Limits and Entry Repairs

Host load starts at approximately 16.84/14.24/15.29 and ends at
18.99/20.26/18.25, above the 12-CPU gate. The final report sets
`qualified: true` for the bounded build/test flow and
`performanceQualified: false`. These single, ordered entrypoint controls are
not a repeatable matched speedup percentage or a macOS/Linux causal proof.

Initial probes remain as diagnostic logs, not valid comparisons:

- Source-build `run.sh` sets `GERBIL_BUILD_PREFIX`; runtime initialization
  deliberately omits the package user library in that mode. The consumer
  runner instead uses the binary directly, explicit `GERBIL_HOME`/load paths,
  and no build-prefix override.
- `build.ss` is a script entrypoint, not an ordinary library import. Its
  script-only source-file binding is unavailable to the rejected import probe.
- Inherited diagnostic verbosity writes `[asp-build]` before a command's
  machine-readable meta result. Focused tests clear that measurement setting.
- The outer `gerbil env` process can append a deprecation warning after the
  harness's `OK`. Final tests use direct gxi in the explicit package environment,
  preserving the strict final marker rather than ignoring arbitrary trailing
  output. Earlier failed steps are retained in the audit trail.

Replay with fresh paths; omit `--package-root` to prepare dependencies in the
new output root as well:

```sh
python3 patches/gerbil-v19-darwin/tests/run_asp_cold_start.py \
  --project .data/d886-asp-pr11/source \
  --toolchain-source .data/d884-patched-staging/source \
  --output .data/NEW_ASP_COLD_START_RUN \
  --head e6e1a82a0835ccf9afa9936df9e2d3448c24c8f4
```
