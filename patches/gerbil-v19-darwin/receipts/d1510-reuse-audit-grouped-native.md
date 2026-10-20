# D1510 Reuse Audit and Grouped Native Emitter

The selected line remains the original D1510. The historical D1513 B and D1878
timings remain separate from current observations. The complete-build ceiling
is still 55 seconds; no later slow candidate is used as a new baseline.

## Runtime Object Reuse Audit

Compare the retained D1513 B1 MCP artifacts to the completed, rejected whole
context memo build. Both have 186 runtime C modules. For every module:

- Normalize only the module's X0 BIGFIX timestamp and its timestamp global
  assignment, first requiring their hexadecimal/decimal values to agree.
- The remaining generated C is byte-identical between the two builds.
- Each runtime C is byte-identical to its own corresponding static C copy.
- The static object and dynamic bundle exist. No static object's modification
  time is later than its dynamic bundle's modification time in either build.

Both logs have the same job counts: 550 compile-file, one prepare-executable-link,
189 compile-executable-object and one link-executable. A job log does not prove
that its compiler invocation executed rather than skipped. Artifact timestamps
are not syscall tracing. This audit therefore supports preservation of 0007's
output structure, not exclusive CPU attribution, a performance cause or complete
live invocation coverage. It does not support a claim that the 72-second build
lost the historical runtime-object reuse configuration.

Private evidence: `.data/d1510-mcp-reuse-artifact-audit-v3/report.json`.

## Previously Unbuilt Grouped Emitter

[D1720](d1720-grouped-packed-emitter-contract.md) retains semantic checks for the
grouped D1714 emitter but explicitly lacks a native compiler. The old per-pair
0013 emitter's failed complete builds remain rejected as documented in
[D1883](d1883-existing-packed-emitter-full-build-boundary.md). Do not substitute
that compiler or those times for the new grouped compiler.

An independent copy of the original configured Gambit source changes only the
emitter Scheme source to the byte-identical D1714 source:
`3ca0743a5d0a3607f884ac7b00857170ba6a5a5f5b7b57fb04c97c94bce1fba4`.
Existing GNU flags and twelve workers regenerate the compiler module and link
native GSC. Build exits zero in 4.096167 seconds. No original GSC, RTS, build
driver, Gerbil binary or installed toolchain is overwritten. The coherent
candidate entry supplies the unchanged original gambuild-C beside GSC.

Candidate native GSC SHA256:
`815b0fb8ea1df2b9389083484e1e60b27883eedc280d1a589208b2b0d1b8f2a9`.

Both native compilers process the same retained real embedded Scheme input,
including its fixed timestamp. They generate four packed words per row in the
candidate and preserve the inactive portable branch and Darwin/GNU target guard.

| Operation | Original seconds | Grouped seconds |
| --- | ---: | ---: |
| Native Scheme-to-C emission | 1.055442 | 3.103835 |
| GNU C-to-object compilation | 10.269169 | 2.813457 |
| Sum of both operations | 11.324612 | 5.917292 |

Both actual objects have identical SHA256:
`1a93f6de27bce9a3ceca787caea7e9c231600566352b6527ca726d9bf6944c1a`.
Original C is 11,423,503 bytes; grouped C including fallback is 36,640,611 bytes.
This single sequential observation includes the additional emitter cost and
shows an observed 5.407319-second difference for this module only. It is not a
matched whole-build ratio, first-log gain, native-test acceleration or release
admission. The original artifact hashes remain unchanged.

Private evidence: `.data/d1510-grouped-emitter-native/report.json` and
`.data/d1510-grouped-emitter-real-module/report.json`. Actual official clean/build
with the original D1510 and only GERBIL_GSC changed is independently required.
The original selected entry is not changed by constructing or testing GSC.

## Complete Cold Build: Not Admitted

The independent MCP clone uses the original D1510 binary and original runtime
home. Only GERBIL_GSC points to the coherent grouped entry. Official clean exits
zero and leaves zero project native images. With twelve workers and unchanged
GNU options, actual first compile is 5.027805 seconds and complete build is
60.991300 seconds, exit zero. Consumer input hashes remain unchanged. Maximum
real output gap is 5.505175 seconds, within the existing ten-second build gate.

The 55-second complete-build performance gate fails and the controller exits
one. No matched original control is taken in this single candidate run; do not
infer a whole-build slowdown or gain relative to historical D1878 or a different
candidate. This result does not restore the historical 51/53-second line and
does not admit the grouped compiler to the selected profile. No package suite,
PR or whole-toolchain release build follows this failed performance admission.

Keep the module object-equivalence and included-emitter-cost evidence, but do
not widen this candidate merely because its module result is positive. Preserve
the original D1510 GSC, carrier and RTS as the fallback; do not use 60.991300
seconds as a replacement performance baseline.

Private evidence: `.data/d1510-grouped-emitter-mcp-cold/report.json` and its
`0-candidate/real-output-events.json`. Performance restoration remains open.
