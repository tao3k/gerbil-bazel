# D1510 Whitespace Reader Cold Checkpoint

This checkpoint fixes the selected Darwin/GNU GCC cold-build configuration,
not a full-test-qualified release. The parent token-reader checkpoint remains
unchanged. No rejected FD, string-span or private-archive candidate is included.

| Round | First actual compile | Complete cold build |
| --- | ---: | ---: |
| 0 | 4.850865875 s | 47.771712542 s |
| 1 | 4.573628042 s | 47.824226292 s |
| 2 | 4.592897458 s | 47.927093625 s |

All three builds clean native images to zero, retain MCP source identity,
complete with exit zero, and pass first-log 5-second and build 50-second gates.
The test wave takes 49.983260167 seconds, below its separate 52-second ceiling,
but only 22/39 files pass. Thus `coldQualified` and `testDurationQualified` are
true; `testQualified` and `productionAdmitted` remain false. The historical
test wave used a 5.5-second first-output ceiling with a five-second silence
watchdog; new campaigns use the requested five-second first-output ceiling.
No old receipt is rewritten to pretend it used a new policy.

Binary SHA256:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.

## Fixed Configuration

- Retained D1510 GNU GCC driver, compiler flags, GSC, 12 physical-core workers,
  original runtime HOME and program carrier.
- Frozen token reader plus no-allocation, actual-readtable-handler whitespace
  batching; original fallback, GC safety and line/column behavior retained.
- Private replacement `_io.o` and regenerated `_gambit.o`; original archive
  unchanged. Only the Darwin/GNU feature enables this path.
- Exact configuration snapshots, source helpers, binary/object hashes and raw
  reports bound by `d1510-reader-whitespace-47-baseline.json`.
- Independent reproduction entrypoints contain no rejected string-span path.

## Verification And Reproduction

All build/output paths remain project-relative and persistent under `.data/`.
The existing private parent inputs are required; no global installation is used.

```sh
python3 patches/gerbil-v19-darwin/tests/verify_reader_whitespace_47_baseline.py
python3 patches/gerbil-v19-darwin/tests/build_reader_whitespace_runtime.py \
  --output .data/reader-whitespace-rebuild-runtime
python3 patches/gerbil-v19-darwin/tests/build_embedded_provider_candidate.py \
  --output .data/reader-whitespace-rebuild-native \
  --runtime-object .data/reader-whitespace-rebuild-runtime/_io.o
python3 patches/gerbil-v19-darwin/tests/run_reader_whitespace_controls.py \
  --binary .data/reader-whitespace-rebuild-native/gerbil \
  --output .data/reader-whitespace-rebuild-controls
python3 patches/gerbil-v19-darwin/tests/run_d1510_progressive.py \
  --binary .data/reader-whitespace-rebuild-native/gerbil \
  --output .data/reader-whitespace-rebuild-cold \
  --test-home .data/d1510-mcp-test-source-home-v2/build --cold-runs 3
```

For another checkout without private binaries/reports, `--source-only` verifies
the committed helper hashes and policy only. It explicitly does not reproduce
or certify the local performance evidence. Wall-time guard failures stop and
reap the owned process immediately; later cold rounds/tests are skipped.

Future research starts from this checkpoint's identities and reports each new
candidate separately. Three cold passes cannot be invalidated by a different
candidate's deadline stop, and test duration cannot substitute for correctness.
