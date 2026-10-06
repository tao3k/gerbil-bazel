# D1510 Balanced Link Resource Side Patch

## Decision

Retain `0017-gambit-darwin-balanced-link-resources.patch` as an independent
side-task candidate, not the main performance line or a default build patch.
It is not added to CI construction or publication patch arrays. D1510, its
original GSC, 0015 driver, GNU flags and VM profile remain selected and unchanged.
The 55-second complete cold-build ceiling is not relaxed.

## Implementation

Only Gambit's `gsc/_t-c-1.scm` changes. The original sorted binary resource
union is reused without modification. A balanced pairwise reduction replaces
repeated accumulated-list merges. Reversing module input order preserves the
original fold's effective demanders/suppliers precedence, including duplicates.
No destructive list operations, persistent cache or output reuse is introduced.

A native C predicate selects this path only when APPLE, MACH and GNU compiler
macros are present and clang is absent. All other builds select the original
portable fold. This guard also protects manual application outside Darwin.

## Evidence

The [original source audit](d1510-link-resource-source-audit.md) covers 187
actual MCP modules and 3,386 final global resources. String comparisons fall
from 697,001 to 63,610, and the complete Scheme resources agree exactly,
including supplier/demander order. This is a comparison-count benefit, not
an allocation measurement or a build-time ratio.

An isolated native GSC is compiled with the retained Bazel GNU GCC 16/SDK
environment and original optimization options. Source copying initially needed
the original config.status and GSI source dependency. A direct-shell link also
failed under the current shell environment; the recorded Bazel environment
links successfully. Neither failed attempt is a performance sample.

Candidate GSC SHA256:
`84ac59e9e46c46b51920deb41ddc2e07fa511b5a1fdbe984631db987c4954ff1`.

Original/candidate/candidate/original native GSC invocations link the same 187
real static C inputs to the same output path. All exit zero with empty stdout
and stderr. Every generated link C has identical SHA256:
`c9c9d56f66e2dfefd8a2f3036d20ee393a5448062d32d2d1a37c9a25910dad1e`.
This exercises symbol, keyword and global resource unions in the native compiler.

| Invocation | Link-stage wall seconds |
| --- | ---: |
| Original 1 | 0.360502 |
| Candidate 1 | 1.300958 |
| Candidate 2 | 0.253597 |
| Original 2 | 0.324265 |

Keep all four observations. The first candidate call is slower; this small
sample does not admit a stable wall-time win. Do not silently discard it or
claim an 11x link/build speedup from the comparison count. No complete cold
MCP build, native-test gain or startup gain is admitted for this side patch.

Three focused patch tests pass, covering application to original context,
non-destructive reversed precedence and the native guard. The guard is checked
through actual GNU preprocessing for Darwin/GNU, Linux/GNU, Darwin/clang,
Darwin without GNU and APPLE without MACH. Only Darwin/GNU selects the fast path.

## Preservation and Private Evidence

The original Gerbil, GSC and 0015 driver hashes remain respectively:

- `446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`
- `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`
- `65aba56445c2b165b667922603873aec9e58ad3edb733c6d040651eecf6d8d15`

Private persistent artifacts stay under project-relative paths:

- `.data/d1510-balanced-link-source/`: isolated source and native build log.
- `.data/d1510-balanced-link-native/`: coherent candidate GSC/0015 entry,
  generated closure C and native stage report.
- `.data/d1510-balanced-link-proof.py`: native output-parity runner.

This side patch must not displace the main-line work. Main-line adoption, if
later proposed, still requires real clean/build at most 55 seconds and the
separate semantic/test gates. Retaining a patch is not admitting a release.
