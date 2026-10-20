# D1510 source-loader repeat and tightened gate

## Exact-profile cold repeat

The original candidate binary and retained 0015 driver are unchanged. GNU
GCC16, 12 physical workers, single VM, and embedded-native disabled match the
retained B1/B2 configuration. Each project is freshly cloned, then real
`gerbil clean` and complete build run. Clean leaves zero project native images.
All four builds exit successfully and retain consumer input identity.

| Role | Clean seconds | First compile seconds | Complete build seconds |
| --- | ---: | ---: | ---: |
| A1 original | 3.819661 | 5.753728 | 60.826134 |
| B1 candidate | 2.782183 | 5.862122 | 49.742614 |
| B2 candidate | 2.814925 | 5.447785 | 49.938471 |
| A2 original | 3.182089 | 5.902094 | 61.230725 |

Clean is outside the complete-build measurement. The candidate pair differs
by 0.195857 seconds. Relative to the historical 43.846968/45.126992-second
candidate pair, these runs are slower by 5.895646/4.811479 seconds. Original
control timings also increased; that observation does not identify a cause.
No resource-contention or runtime-regression diagnosis is claimed.

The 45-second result is **not reproduced** in this campaign. The historical
anchor remains intact and is not overwritten with a new performance claim.
The original candidate SHA and all 42 original input hashes pass revalidation.

Raw evidence: `.data/d1510-source-loader-cold-repeat-exact-abba/`.
The initial `cold-repeat-abba-r1` attempt accidentally enabled embedded-native
for the candidate. It was interrupted, recorded as DENY, and excluded from
the exact-profile results, not silently treated as a repeat.

## User-tightened candidate policy

The candidate now targets complete builds at or below **50 seconds**, with an
inclusive **52-second hard ceiling**. Any individual candidate over 52 seconds
is DENY; averages cannot conceal a slow run. Product, source, binary/driver,
and clean checks remain required. Historical 55-second policy is not rewritten.

`admit_source_loader_repeat.py` implements this stricter check on top of the
original admission checks. Both candidates pass: `ALLOW`, `targetMet=true`.
Three new regression cases and five existing admission cases pass.

The ABBA harness itself returns nonzero because its older all-role 55-second
check includes both controls, which exceed 55 seconds. This is retained;
candidate-only 52-second admission does not turn that exit status into zero.

## Real tests on newly cold-built projects

Both roles receive the same authorized four-file fixture repair. Each CLI
invocation validates selected gxi/gxc/gerbil/gxpkg paths and SHA; no global
Gerbil fallback is allowed. Tests use the matching source-home view described
in `d1510-mcp-test-failure-repair.md`, with the same 12 workers, five-second
real-output gap and 90-second invocation budget. Build and test waves do not
run concurrently.

| Role | Wave seconds | Passed / 39 | Rejected |
| --- | ---: | ---: | ---: |
| Original | 55.778328 | 15 | 24 |
| Candidate | 55.633622 | 14 | 25 |

Every rejection is recorded as the unchanged real-output/batch watchdog gate.
These durations include terminated failures: they are **not successful full
test-suite times**. No test-speedup claim or complete test admission is made.
This result is worse than the previous 32/39 campaign and is retained rather
than replaced by that older result. Full test qualification remains false.

Raw evidence: `.data/d1510-source-loader-repeat-selected-tests/`.
This receipt preserves the repeat, policy and failures; it does not promote
the prototype into a production patch or claim GitHub publication.
