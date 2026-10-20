# D1510: repair test selection and account for all failures

## Historical 72 failures, corrected classification

The 156-invocation campaign in `d1510-source-loader-cold-build-extension.md`
had 72 rejected invocations, not 72 distinct broken tests:

| Cause | Invocations | Files |
| --- | ---: | --- |
| Real output/budget watchdog | 48 | 12 unit files and chunks 03, 07, 15, 23 |
| Actual assertion error | 12 | chunks 05, 12, 21, four runs each |
| Invalid lexical case-count oracle | 12 | chunks 06, 10, 18, four runs each |

The lexical `(test-case` count included strings containing example tests.
Chunk 18 had a separate genuine coverage defect: a missing closing parenthesis
left subsequent test declarations inside the first case. Its historical final
OK covered only one case, not the 137 actual declarations. That old OK must
not be retroactively promoted to full coverage.

## Authorized fixture repairs

The user authorizes portable test-fixture repairs, without MCP business-source
changes, deleted assertions, or increased timeouts. Both role fixtures receive
the same four-file patch:

- Chunk 12 requires `GERBIL_MCP_GXI_PATH`; no global-path default remains.
- Protocol tests inherit the selected home and four explicit tool paths;
  all hardcoded global home/tool overrides are removed.
- Chunk 18's parentheses are repaired, so all 137 cases actually execute.
- Missing-package checks in chunks 18/21 use separate temporary package roots,
  independent of packages created by other concurrently running fixtures.

Replayable patch: `mcp-selected-toolchain-fixtures.patch` in this directory.
`git apply --check` passes against the original MCP checkout. The golden source
checkout is not modified. Scanning both active test trees finds no global
Gerbil installation paths. Only those four test files differ from MCP HEAD;
MCP business code is unchanged.

`mcp_case_inventory.py` parses Scheme forms rather than matching source text.
The strict controller requires exact case names/counts, successful exit, no
test errors, final standalone OK, and unchanged test input during invocation.
After fixture repairs the 39 files declare 965 cases; chunk 18 has 137,
chunk 06 has 25, and chunk 10 has 24. Quoted examples and strings are excluded.

## Exact current build, never a global fallback

`selected_gerbil_toolchain.py` checks every explicitly selected gxi, gxc,
gerbil, and gxpkg alias resolves to the expected role binary. It also verifies
the actual PATH resolution and retained SHA256. Missing configuration,
another binary, or a changed hash fails closed before launch. The private
selected-bin directory leads PATH, so ordinary child commands cannot silently
select a different home binary. All 78 final invocations pass these checks.

Original role SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
Candidate role SHA256:
`3d727d8ac1926883934ada2a696325c404de2ab786d01def1987dbfe06d21c09`.

The isolated installation originally lacks its source tree. A test-only home
view supplies matching sources and copies 388 byte-identical textual `.ssi`
interfaces, so source lookup cannot canonicalize the interface path back to
a sourceless home. Native modules, GSC, and runtime archive remain original
symlink targets; no native images are copied, re-signed, or modified. The first
view with a whole-lib symlink did not reliably repair source lookup and remains
separate failed diagnostic evidence.

## Actual final run: not fully green

Real `gerbil test -v 5`, 12 workers, five-second real-output gap and 90-second
invocation wall gates remain unchanged. No synthetic progress is emitted.

| Role | Passed / 39 | Unit files | Assert/inventory failures | Watchdog failures |
| --- | ---: | ---: | ---: | ---: |
| Original | 32 | 13/13 | 0 | 7 |
| Candidate | 32 | 13/13 | 0 | 7 |

Both roles really execute and pass all 137 chunk-18 cases, and protocol tests
pass with the selected paths. The final campaign has 64/78 invocations passed
and 14 rejected. It does **not** qualify the full suite or prove test speedup.
Failed wave durations are not successful suite timings: original 60.928518 s,
candidate 59.117100 s. The final test fixtures differ from historical fixtures;
their pass totals must not be presented as a matched performance comparison
against the previous 156-invocation campaign.

Remaining watchdog files:

- Both roles: chunks 03, 04, 07, 12, 15, 23.
- Original additionally: chunk 05; candidate additionally: chunk 06.

The last real cases before the shared stalls involve bisect-crash preamble
preservation, build/report fallback, built-in recipe verification, scanning
the actual selected binary, comparing module exports, and a real temp-project
build/clean. These are now the concrete remaining execution-cost targets,
not a reason to erase the five-second gate or use a global gxi. The differing
seventh failure prevents claiming complete failure parity.

Raw final evidence: `.data/d1510-source-loader-selected-tests/`.
Intermediate fixture-only run: `.data/d1510-source-loader-fixture-fixed-tests/`.
The separately sampled unit diagnostic still fails and is not admission;
its dyld remote-notification frames may be observer-influenced and do not
establish a root cause for the unobserved final campaign.

## Preserve the fast anchor

`d1510-source-loader-anchor.json` seals the original/candidate binary identity,
42 original input hashes, native carrier/driver artifacts, construction
scripts, retained 0015 driver, and four measured cold-build rows. The cold
candidate stays 43.846968/45.126992 s, with an unchanged 55-second gate.
`freeze_d1510_source_loader_anchor.py` re-verifies these identities after the
fixture repairs; original inputs and candidate binary remain unchanged.
The manifest explicitly keeps `testQualified=false` and
`productionAdmitted=false`; sealing a cold-build anchor is not a green release.

Thirteen focused Python regression tests pass: selected toolchain (5),
structural case inventory (3), and cold admission (5). The fixture patch is
separate from the production patch stack. No GitHub publication or complete
toolchain/test qualification is claimed in this receipt.
