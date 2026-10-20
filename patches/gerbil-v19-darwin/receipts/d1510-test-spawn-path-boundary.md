# D1510 Test Spawn PATH Boundary

## Retained Lines

No runtime candidate is promoted by this investigation. Historical complete
cold builds remain 47.771713, 47.824226 and 47.927094 seconds; corresponding
first compile times are 4.850866, 4.573628 and 4.592897 seconds. Historical
complete tests are 105.750982 seconds, 39 files and 965 cases passed. The
subsequent strict 112-second test attempts were DENY, not complete passes.
Current hard gates remain first output 5, cold build 50 and full tests 112
seconds. Missing complete durations must remain unknown.

## Source Hypothesis, Not Measured Budget

The original MCP subprocess wrapper starts bare-name `sh` with an explicit
merged environment. Patch 0001 preserves fork fallback for that combination:
child PATH resolution is not the caller PATH resolution used by spawnp.
This is a general process-API semantic boundary, not a proposed MCP-specific
optimization. Earlier zero-fork full-build and regex observations do not
establish the process counts of the complete test wave.

[Apple Libc posix_spawnp](https://github.com/apple-oss-distributions/Libc/blob/main/sys/posix_spawn.c)
searches caller PATH and handles empty components, execution errors and shell
fallback. [GLib's process implementation](https://github.com/GNOME/glib/blob/main/glib/gspawn-posix.c)
also excludes child-environment PATH search from its spawn fast path and
falls back for ENOEXEC. Neither source supports simply deleting our guard.
Any different implementation must preserve directory-relative PATH search,
error precedence, shell fallback, redirections, signal state and reaping.

## Interrupted Original-Case Observation

Artifacts: `.data/d1510-original-recipe-spawn-census-v1/`.
The frozen runtime ran the original single-recipe verification case with
the existing process observer; business sources were not changed.

| Measurement | Result |
| --- | --- |
| First real output | Not reached; deadline observed at 5.010004 seconds |
| Attempt including cleanup | 5.052033 seconds, not completed case time |
| Completion | DENY; SIGKILL, reaped, no cleanup errors |
| Complete build / complete test | Not measured |
| Observer evidence | Root PID 68143 has one loaded row, no API rows |

The observed prefix proves observer loading only. It does not prove zero
fork calls for the case, descendant coverage, 158 actual fork calls, or an
avoidable time budget. Do not repeat the unchanged denied observation or
relax the first-output gate to obtain a favorable result. The framework now
preserves partial census after termination, explicitly marks incomplete
case coverage, and never turns that census into performance admission.

The separate shared-result-storage candidate was also denied at its real
first-log gate; its static frame reduction is not a runtime speedup. It is
listed in the research exclusions. No production patch or baseline change
is justified by either negative observation.

## Different Child-PATH Mechanism: Native Semantic Probe

[libuv's Darwin process source](https://github.com/libuv/libuv/blob/v1.x/src/unix/process.c)
provides a different architecture: find PATH in the child environment and
attempt `posix_spawn` for each path component, instead of asking spawnp to
search caller PATH. Its implementation is a reference, not a Gambit semantic
proof. Gambit's no-shebang executable handling still needs original fork/exec
fallback when a spawn attempt reports ENOEXEC.

This differs from the rejected same-parent/child-PATH optimization: it does
not compare mutable parent environment state or authorize spawnp on that
equality. It does not reopen FD-cleanup. The complete-build zero-fork census
still constrains expected benefit: this cannot be claimed as a startup or
ordinary-build remedy.

Private probe: `.data/d1510-child-path-search-probe.c`, compiled with GNU GCC
16, `-std=c11 -O2 -Wall -Wextra -Werror`, the Apple SDK and
`COMPILER_PATH=/usr/bin`. Two initial link attempts omitted that required
compiler environment and failed with unresolved libc symbols; neither ran
the probe or provides performance evidence. No clang compilation was used.

The executed probe passes against actual Darwin APIs:

- Bare executable resolves from child PATH when caller PATH differs.
- Empty and relative components resolve in the child working directory.
- Missing child PATH uses the libc default.
- Missing executable returns ENOENT; nonexecutable candidate returns EACCES.
- No-shebang executable returns ENOEXEC for preserved original fallback.
- Every successful spawn is waited for and has successful exit status.

The shared execution framework observes exit zero, first probe assertion at
0.472332 seconds and completion at 0.508922 seconds. These are probe durations,
not first compile, cold build or full-test measurements. Evidence:
`.data/d1510-child-path-search-probe-v1.log`. Probe fixtures were removed.
This does not test Gambit signals/redirections, complete error precedence
across candidates, races or the fork fallback itself.

Source SHA256: `b715ab0e916f896d56be4a031889be01aa1b28d7b5755e808768a306f13ad722`.
Probe SHA256: `6d87b6e1fbbce925ae3fb758c46bb2158e823c324d6cf58eb8e4ee971f5e5866`.
Frozen runtime SHA256 remains
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.

Decision: native feasibility only, no production/performance admission.
An integrated candidate must retain original fallback, reproduce the original
runtime control first, pass actual process semantics and then the unchanged
5/50/112 acceptance campaign. No seconds-scale gain or baseline replacement
is justified by this standalone probe.

## Integrated RTS Candidate: Semantics Pass, Cold DENY

The unified `runtime-io` workflow compiles original os_io.c with the original
GNU RTS command before compiling the private transformation. The control
member exactly matches the frozen archive member, SHA256
`e371c7812a4fb16bedb90ca9c8d297ca1dc239d0c880ee31b36a47fecbf1ab0f`.
Only that archive member is replaced. A subsequent `relink` reproduces the
entire frozen runtime byte-for-byte before linking the candidate; retained
reader objects and all providers stay unchanged. Original source and archive
hashes remain unchanged.

Artifacts: `.data/d1510-child-path-runtime-v1/` and
`.data/d1510-child-path-native-v1/`. Candidate runtime SHA256:
`02408a3fcc2bf6f7c9b7874493201fe129af89c56fb6679cf574910fc864d8d6`.

The actual Gambit semantics test covers 13 exact named cases: child PATH,
empty/relative/trailing-empty PATH with child cwd, missing PATH, no-shebang
shell fallback (exit 13), child environment value, stderr redirection,
absolute-path unchanged behavior, EACCES/ENOTDIR search continuation, missing
and empty commands. Both original and candidate pass all 13 with final OK.
This is generic runtime testing; no MCP business module was changed.

Three early fixture attempts had no visible first result by 5.019478,
5.001905 and 5.018069 seconds and were killed/reaped. None tested the candidate.
The first two used the file entry, the third used the existing -e component
entry. Changing entry alone did not fix the missing output. Source review
found that the fixture lacked force-output after CASE-OK: runtime displayln
only adds a newline. The corrected fixture flushes only completed real
assertions, never a heartbeat; deadlines remain unchanged.

Corrected evidence: `.data/d1510-child-path-semantics-flushed-v1/report.json`.
Original: first assertion 0.555994, component completion 9.356052 seconds.
Candidate: first assertion 3.160390, component completion 3.800494 seconds.
This single sequential pair is semantic/component evidence, not a stable
speedup ratio, first-compile measurement or complete-suite acceptance.
The exact named inventory and final OK were rechecked after tightening the
receipt verifier; duplicate or substituted cases cannot count as passage.

Actual unchanged D1510 cold recipe evidence:
`.data/d1510-child-path-acceptance-v1/report.json`,
`progressive-admission.json` and `three-lines.json`.

| Requested line | Actual result |
| --- | --- |
| First compile <=5 seconds | No first compile by 5.004156; DENY |
| Complete cold build <=50 seconds | Unknown; terminated attempt, not completion |
| Complete tests <=112 seconds | SKIP after cold DENY; no test duration |

Clean exits zero in 9.533773 seconds and leaves zero native images. The build
is immediately killed/reaped without cleanup errors; attempted build including
cleanup is 5.012654 seconds, not complete build time. Rounds two/three and all
tests are skipped. The three-lines verifier exits one and prints all three
lines with null incomplete durations, keeping the stop visible.

Decision: DENY, no production patch, push or baseline replacement. This exact
archive deployment is now a closed route. Component improvement is not enough
to reopen it, and this record does not attribute the first-log delay to fork
or prove why it missed the gate. Do not retry the same candidate for a lucky
wall-clock result. Independent standard-library admission is not claimed;
the actual cold rejection stops the candidate campaign first.
