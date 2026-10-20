# Native Producer And Linker Handoff

The experimental GSC now compiles the journal, proof validator and hook into
its native executable. Explicit `GAMBIT_DARWIN_NATIVE_GENERATED_C=1` enables
the Darwin path; default CLI compilation remains original. Existing explicit
`-c -o` calls produce C once, journal their actual source reads, and publish
proofs and immutable pins. There is no dynamic Scheme wrapper load or second
generation pass. CLI `c/o` envelope fields are validated (unique operation and
matching output) before projecting the otherwise unchanged effective options.

An explicitly selected `GAMBIT_GENERATED_C_PRODUCER_INDEX` directory receives
atomic, mode-0600, per-module data records. A supported `-link` reads records
as data, checks the entire producer batch, and substitutes proven C inputs
before the existing GSC file dispatch loop. Missing records retain Scheme;
invalid batch context retains all original arguments. Debug/prelude/other
unsupported options retain the original linker path. No default enablement
or change to the measured five-patch MCP series is made.

## Native Qualification

`.data/d1510-native-generated-c-gsc-controls-v7` passes:

- Default, cold producer and cross-process cache-hit C byte parity.
- Real CLI native-link adoption and whole link C byte parity.
- Changed static source, debug options and invalid index fallback/parity.
- Failed compilation preserves old C/proof, releases locks and removes work.

`.data/d1510-real-native-generated-c-gsc-v3` uses 55 copied paired modules
from the frozen isolated ASCENT fixture. All producer C files match the
original GSC. The native `-link` receives the original Scheme arguments and
reports `GAMBIT-NATIVE-PRODUCED-C-LINK-HIT 55`; it is not supplied hand-picked
C arguments. Both whole link C files have SHA-256
`f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`.
Native commands run directly through Bash, without Python supervision.

| Serial component | Original seconds | Candidate seconds |
| --- | ---: | ---: |
| 55 CLI producer calls, including proof creation in candidate | 7.95 | 8.83 |
| Metadata link, including batch validation in candidate | 3.81 | 0.92 |
| Sum | 11.76 | 9.75 |

Separate diagnostic native lookup measured 0.729155 seconds; it is not added
again to the 0.92-second native CLI link. These serial component numbers do
not prove parallel complete-package performance or causality across prior
runs. The earlier producer-only v5 experiment was essentially neutral in
serial total (9.40 versus 9.439246 seconds) and remains unpromoted.

## Retained Failed Attempts

- Build v1 lacked the source runtime configuration header and failed to link.
- Build v2 omitted Gambit's native compiler prelude and produced an unusable
  entrypoint. Build v3 repaired it; admission still fell back because CLI
  transport options were not projected after validation.
- Build v4 used command-line text instead of the executable-path API; its
  opt-in producer failed to find the digest helper. Build v5 repaired that.
- Real CLI v2 used external `/usr/bin/time`, changing the `_` environment
  entry relative to production. The conservative environment-bound proof
  correctly refused adoption. V3 uses Bash timing without that child wrapper;
  no environment key was removed from admission to obtain a hit.

## Identities And Boundary

Native hook source:
`31b6cb3b88846d248b703ebaa23dbb613fbb82146f875ca60b9e54918152c870`.
Native GSC v6:
`7684b99b0f95d92bbd8a196e76f123f8c6ffb4e7fccd9771551dc59016649093`.
Batch digest helper:
`1f81c3639b332dfa0cd5301b6487b4156c569357fbf4e8371c87d4ce9f0b95f8`.
Native link log:
`93a81a0bf6adf5add7093f72095f4ccdaf1ed8fbd3b884f6249ddfa24b31a03d`.
Original/candidate producer time receipts respectively:
`fdc65930300d546b953ac4535c3a321e00e2a286d659edc9a720a458d3526061` /
`286764eaa6e32f6c62bb5d84f7cb51c372f768a2b1b19e0c51daded270d57785`.
Original/candidate link time receipts respectively:
`12c7ab4cda6e2f12a08c9b0e12a563b91af4cc857728ed2977eb93e258052150` /
`8dfa1d7b08adf1fc4a46ea4d9be4a4752e73018035d981b19348bf971f3a2db1`.

The build uses GNU GCC 16.2.0, the owned configured Gambit source/header and
matching static libraries. It rebuilds the GSC entrypoint, not the complete
latest-staging toolchain. Existing generic source/options/tool/environment
and concurrent-writer tests remain component evidence, not complete native
consumer admission. The frozen MCP gates remain 4.5 / 42 / 97 seconds.
Parallel MCP cold build, complete MCP tests and full isolated ASCENT AOT
correctness/performance remain to be qualified before promotion.
