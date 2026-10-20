# D1416: existing advantage extensions, not a major speedup

## Scope

Continue from the admitted Darwin spawn and executable-object-reuse results.
No Linux profile is required for this investigation. No package HTTP changes,
consumer Scheme edits, installation replacement, or default patch activation
were performed. Private workloads remain under `.data`, using 12 physical
workers and the existing Bazel GNU GCC 16 environment.

Common toolchain: `.data/d1391-runtime-object-source/build`, current qualified
v0.19-staging revision `1cfb032c7a1612637da6205f5f8a15683eba3ba0`, Gambit
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.

## Parameter-only first-window result

The separate-host parameter lookup candidate and its always-inline variant
passed 12 concurrent native semantic controls each. Neither removes the major
first-window cost. The inline candidate's real fresh-fixture MCP ABBA measured:

| Role | First compile seconds |
| --- | ---: |
| Baseline | 6.064250 |
| Candidate | 5.902439 |
| Candidate | 6.239362 |
| Baseline | 6.527847 |

Means: 6.296049 versus 6.070900 seconds, about 3.58%. Each fixture underwent
actual `gerbil clean`, with zero project native images afterward. These builds
were deliberately terminated after the first literal `... compile util/compat`
line; they are not complete build or full test receipts. Candidate variation
overlaps the baseline range. No major startup acceleration is admitted.

Raw receipt: `.data/d1413-parameter-inline-first/report.json`.

## Spawn source audit

The compiler driver `invoke` passes no explicit child environment. Its usual
gsc/GCC subprocesses are eligible for 0001's existing spawn path. Gambit's
`##gambuild` expands the build-driver path under `~~bin` before passing its
explicit environment to `##run-subprocess`; this path contains a slash and is
also eligible. Package build scripts use expanded paths as well.

The documented bare-name plus explicit-child-environment fork fallback remains
a semantic boundary, not evidence that the ordinary compiler chain still
forks. Removing it without preserving child PATH lookup is not admitted.
This is source evidence, not a measured census of every subprocess in a full
MCP build or test suite.

## Object-producer fusion contract

0007 currently invokes gsc first to generate C, then again to compile the PIC
object. Gambit supports `-obj -keep-temp` with the same explicit module reference
and linker name. A private producer experiment compared these paths without
changing the formal patch or compiler sources.

Twelve original MCP runtime SCM modules were checked at identical per-module
input paths. Generated C and Mach-O native text matched byte for byte. A second
experiment ran four complete 12-concurrent-module waves in ABBA order:

| Producer | Wave wall seconds |
| --- | ---: |
| Separate | 3.546643 |
| Fused | 3.368758 |
| Fused | 3.406415 |
| Separate | 3.522765 |

Means: 3.534704 versus 3.387586 seconds, about 4.16%. All 48 compilations exited
successfully and preserved generated-C/native-text identities across waves.
The fused path makes one rather than two gsc invocations per object producer.
This receipt does not qualify bundle linkage, complete compiler integration,
complete MCP cold build, tests, or first-window performance. It does not justify
an end-to-end speedup claim or a full toolchain rebuild for a major-gain claim.

Raw receipts: `.data/d1414-fused-object-probe/report.json` and
`.data/d1415-fused-object-waves/report.json`. Executable harness:
`.data/d1414-fused-object-probe.py`.

## Admission

Keep the previously qualified 0001 and 0007 benefits and their original evidence
boundaries. Neither new candidate meets the requested major-gain threshold.
Do not promote either into the default profile. Installed/toolchain static
modules and foreign SCM producers remain separate reuse boundaries; this
receipt does not prove that either contributes a large duplicate-compilation
cost in MCP. The major first-log and full native-test optimization remains open.
