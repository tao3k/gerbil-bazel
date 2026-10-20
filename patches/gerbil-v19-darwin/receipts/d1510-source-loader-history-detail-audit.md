# D1510 source-loader history detail audit

## Historical 43/45 versus current 49 seconds

Compare captured evidence, not another uncontrolled full rebuild:
`d1510-source-loader-cold-abba` versus
`d1510-source-loader-cold-repeat-exact-abba` in `.data`.

All four corresponding runs agree on:

- Selected original/candidate binary SHA256.
- Original 0015 driver SHA256 and compiler/backend/header/archive hashes.
- GNU GCC version and the complete captured compiler environment.
- SDK, include/link options, static home, disabled embedded-native mode.
- Twelve hardware-derived workers, single-VM retained image.
- MCP head, recorded consumer source hashes and cold-build controller hash.

Only the fresh project directory differs in the captured environment.
`audit_source_loader_repeat.py` normalizes that directory before comparison.
No missing patch or captured flag drift is found. Both observed profiles use
the very same candidate binary, so a missing candidate patch is not supported
by this evidence. The audit does not cover unrecorded machine state and does
not identify a cause for wall-time variation.

Both campaigns compile successfully from zero project native images. Some
parallel log lines are interleaved with compiler diagnostics and truncated
mid-job. Complete logged job-name multisets therefore differ. They cannot
establish omitted jobs or exact job parity; retain that limitation instead of
interpreting broken log text as missing compilation.

No targeted reversal is justified by a concrete omission found here. Preserve
43.847/45.127 seconds as historical evidence, and keep 49.743/49.938 seconds as
the current repeat baseline, with a 50-second target and 52-second hard gate.

## Boundaries for expanding the successful mechanism

Read-only parsing of the current candidate project's generated Scheme files:

| Category | Files | Source bytes | Pure loader forms |
| --- | ---: | ---: | ---: |
| Module loaders | 187 | 41,309 | 187 |
| Macro/phi sections | 178 | 3,609,067 | 0 |
| Runtime sections | 187 | 9,070,544 | 0 |

The pure predicate admits only nested proper `begin` and exact
`load-module STRING` forms after declarations are excluded. No Scheme is
evaluated by this inventory. Counts describe the available generated corpus;
bytes are not CPU-time measurements or a proof that one category dominates.

The existing loader shortcut already covers all 187 eligible module loaders.
Blindly applying it to phi or runtime bodies is not an equivalent extension:
these contain real code. Source inspection confirms phi compilation uses a
separate `compile-scm-file ... #t` path. It is not silently covered by 0018.

The executable runtime-object path already checks object freshness and uses
ready runtime C for linking. Do not count queued job labels as redundant
compilations or remove freshness checks. Keep the closed metadata-probe,
builtin-quoting, PCH, naive GSC batching, whole-context memo and grouped-image
routes excluded as documented in `d1510-research-exclusions.md`.

Further gains need a distinct mechanism with equivalent runtime/macro output
and actual cost evidence on this retained profile. This audit introduces no
new performance candidate, no new speedup, and no complete-test qualification.
