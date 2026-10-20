# D1801: keep the original best line; do not admit the SAFE macro candidate

Human direction: do not investigate the twenty-second discrepancy. Return to
D1513 B / original D1510 and develop from that line. Historical complete builds
remain 51.737180 and 53.496910 seconds (mean 52.617045); the complete-build
acceptance ceiling remains 55 seconds. Later slow runs do not redefine it.

## Baseline identity

`python3 .data/best-line.py --identity` passes on Darwin with 12 physical cores.
It verifies the retained binary, original GSC/runtime/carrier and all 42 native
inputs. Binary SHA-256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.

The default execution entry remains `.data/best-line.py`, with original home
`.data/d1391-runtime-object-source/build`, embedded native disabled and the
existing GNU GCC/object-reuse configuration. No experimental library home is
selected by this entry. Identity verification is not a current performance
reproduction.

## Isolated extension validation

D1792/D1793 extend the private Gambit parameter-entry emitter to SAFE calls,
using SAFE transfer for checked getter dispatch and retaining the original
fallback. Default emitter output remains unchanged. No consumer, std/make,
std/test or package HTTP code is changed.

- Seven focused emitter unit tests pass.
- D1794 compiles and executes all 15 native SAFE parameter cases, including
  rebinding, throwing getters, nested dynamic bindings, escape and GC.
- D1798 uses 12 concurrent workers: 540 exact case checks pass, including
  separate diagnostic helper-hit verification. This is semantic evidence,
  not isolated performance evidence.
- Actual generated core macro modules have 18, 4 and 2 eligible source sites
  in contract~6, sugar~1 and mop~1 respectively. Site counts are not CPU costs
  or runtime hit counts.
- D1797 compiles all three native macro images and preserves their original
  dynamic entry symbols. Its copied-home framework import fails the 15-second
  bound; the candidate is not admitted.
- D1799 keeps untouched native images symlinked to original canonical files,
  copying only the three candidates and Scheme metadata. Real imports of
  std/make, std/test and std/build-script return exact SAFE-MACRO-IMPORT-OK,
  exit zero. Original input hashes remain unchanged. Import qualification is
  not proof of startup acceleration or candidate macro execution frequency.

## Real cold MCP gate

D1800 uses the original selected D1510 binary, the isolated D1799 library home,
GNU GCC, 12 physical cores and a fresh MCP fixture at unchanged head
`9a5c35e275e5d6847ff421151bb224f2eae177c1`.

Official clean exits zero in 7.206776 seconds and leaves zero project native
images. The literal first compile line is `... compile util/compat`, at
8.252911 seconds. The build then fails the unchanged real-output/total-budget
gate; terminal exit is 70. There is no completed build duration to report.
Both qualification and the 55-second performance gate are false. The run's
generic timeout message does not distinguish silence from the total budget;
do not infer that distinction or a root cause from it.

Raw reports remain in `.data/d1794-safe-native-emitter-contract`,
`.data/d1798-safe-emitter-concurrent`, `.data/d1797-safe-macro-home`,
`.data/d1799-linked-safe-macro-home` and `.data/d1800-best-line-safe-macro-mcp`.
No matching candidate/build subprocesses remain after the failed run.

Decision: do not promote this candidate or alter the original best-line home.
Subsequent optimizations must derive from D1510, preserve its existing wins
and pass the original full-build and genuine-output gates. No acceleration,
current 52-second reproduction or full-toolchain qualification is claimed.
