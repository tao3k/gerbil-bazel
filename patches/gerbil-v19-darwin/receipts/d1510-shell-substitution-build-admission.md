# D1510 Gambit shell substitution: build-only admission

## Decision

Retain patch `0015-gambit-darwin-literal-build-substitution.patch` as an isolated,
build-only candidate on the original D1510 line. Do not replace the retained
D1878 56.255963-second fallback lock. Do not admit startup or full-test speedup.
The candidate's three measured complete MCP builds satisfy the unchanged
55-second gate. The original-driver controls below are not a new baseline.

## Exact change

Only Gambit's `bin/gambuild-C.unix.in` changes. On Darwin with the configured
GNU compiler, sequential literal parameter substitution uses POSIX shell
builtins instead of spawning `sed` for every replacement, including unused
parameters. Filename quoting, metadata parsing, compiler flags, optimization
levels, runtime-object reuse and final command evaluation remain unchanged.
Non-Darwin/non-GNU execution retains the original substitution functions.
Values containing newline or the original sed delimiter use the original path.
The guard adds one `uname` probe for a configured GNU driver; this is not a
claim of zero additional Linux process overhead.

The original Gerbil binary, GSC bytes, runtime home, SDK, libraries and GNU GCC
flags remain selected. Neither std/make nor std/test nor the consumer changes.
An identical GSC copy next to the candidate driver plus `~~bin` selects it;
`~~lib`, `~~include` and `GERBIL_HOME` still reference the original home.

## Actual cold builds

MCP head: `9a5c35e275e5d6847ff421151bb224f2eae177c1`.
Every row used a fresh local clone, official `gerbil clean` then `gerbil build`,
12 hardware-derived physical cores, GNU GCC 16.2.0 and embedded-native reuse
disabled. The existing C-object reuse profile remains enabled and unchanged.
All clean/build exits were 0; project native images after clean were 0;
all checked consumer source hashes remained unchanged.

| Run | Driver | First compile (s) | Complete build (s) | <=55 s |
| --- | --- | ---: | ---: | --- |
| Initial | Candidate | 5.185094 | 52.498548 | Yes |
| A1 | Original | 5.082323 | 66.164491 | No |
| B1 | Candidate | 5.058586 | 47.211369 | Yes |
| B2 | Candidate | 5.129310 | 48.705787 | Yes |
| A2 | Original | 5.821420 | 64.919734 | No |

These are current observations, not reconstructed historical D1513 timings.
The two candidate ABBA runs average 47.958578 seconds; original controls average
65.542113 seconds. This small local sample is not a universal speedup estimate.
A 0.100-second compiler-stub process trace and a 0.067-second portable test ran
during the ABBA sequence; no parallel toolchain build or SDK hash audit ran.
The ABBA controller exits 1 because its all-row ceiling includes original
controls. Its four product builds succeeded; both candidate rows passed the
ceiling. Do not rewrite that controller failure into an all-row pass.

## Mechanism and semantic checks

- Actual shell execution trace: no-metadata object command invokes 20 external
  `sed` commands originally, versus 2 plus one `uname` in the candidate.
- Actual identical GSC compilation: 25 versus 7 external `sed` invocations,
  both exit 0 and produce an object. This verifies selection reaches the driver,
  rather than merely recording environment variables.
- 27 obj/dyn/exe command cases compare stdout, stderr and status exactly,
  including quotes, backslashes, shell metacharacters and fallback values.
- Actual MCP generated C and metadata compile with GNU GCC: complete emitted
  command, stderr, status and object bytes are identical. Object SHA-256:
  `3c6c615e9608420772b45457b00d0448a9ccab36e502b4fa1a7282e6dfea7ffb`.
- Five portable helper/dispatch tests pass, including Linux, clang, literal glob
  characters, no recursive replacement and newline/delimiter fallback.
- Patch application check passes against the retained staging Gambit template.
  Applying the patch to an isolated copy of the original configured driver
  reproduces the tested candidate driver byte for byte.

## Test boundary

Official 12-worker regex positive control: 12/12 executions pass, 228 CASE-OK,
every final OK present and every exit 0; wave wall time 1.882480 seconds.
This is not an A/B test-speedup claim or a substitute for the full suite.

Official 13-file unit wave with 12 workers: only regex passes; the other 12
exceed the unchanged five-second real-output gate. The controller exits 1.
Timeouts were not widened. This patch does not remove Scheme/native-load cost
before the first compiler log. Full test/startup admission remains false.

## Retained identities and evidence

- Gerbil: `446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.
- GSC: `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
- Original driver: `8aec2c5424dc4489c05016226301bb924ecb703b2fc62f4805fa3e7b9482c92e`.
- Candidate driver: `65aba56445c2b165b667922603873aec9e58ad3edb733c6d040651eecf6d8d15`.
- Patch: `73f3e74faad485a1a6678cbc1b398e9fa934247e642e24a588f0254b97a49e1f`.

Private persistent evidence, relative to the project root:

- `.data/d1510-shell-substitution-mcp-cold-v2/report.json`, SHA-256
  `f26f080c037e09dd8d29abb125bf002a1d5d261840016a6b6ace90b2889fb72d`.
- `.data/d1510-shell-substitution-mcp-abba/report.json`, SHA-256
  `a0f20aeb12b54926d1345958407e47fb2fa08cce436ecbfc42b52c32352ee427`.
- `.data/d1510-shell-substitution-unit-wave/report.json`, SHA-256
  `66966b68d476c417033f203e98b154bba2f581b638f5a2f1ef93d4d1f5197e19`.
- `.data/d1510-shell-substitution-regex-wave/report.json`.
- `.data/d1510-shell-substitution/`: candidate driver/GSC, command parity,
  driver-only ABBA, real object equivalence, process trace and actual GSC proof.

The first cold-run configuration lists the original home driver, while its
environment and top-level candidateDriverSha256 identify the selected override.
The later harness corrects that file-list reporting; this is not a changed
candidate. Private artifacts are not uploaded. No complete from-source
toolchain rebuild or exact-head GitHub CI admission is asserted here.
