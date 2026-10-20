# Fresh Producer Fixture Diagnosis

## MCP

The original candidate result remains DENY: three cold builds pass at
36.188334 / 35.808262 / 35.796654 seconds, but complete testing at 81.999996
seconds passes only 963/965 cases. No patch or assertion was changed to turn
that result into a pass.

Both the candidate and frozen reference resolve `:std/encoding/json` and
`:std/list/list` into the selected runtime's `lib/*.ssi`. That runtime has no
`src` directory; the original checkout still contains the corresponding source.
The two failing cases require a `/src/` result. Correct symbol-typed resolver
queries succeed for both binaries. Earlier ad hoc queries passed strings to an
API expecting symbols; their exit 139 is not candidate-regression evidence.

The generic `experiment_framework/source_runtime.py` creates an owned APFS clone
of the selected runtime, independently copies 627 real source files and binds
them in a relative-path manifest. Runtime header/archive bytes are verified
against the originals. It does not modify the selected runtime or MCP business
source and does not remove assertions. Manifest verification rejects changed
source/runtime content, parent symlinks and escaping paths.

| Complete-test fixture | Result |
| --- | --- |
| Copied images, source-aware home v1 | DENY: no real first output by 4.5 seconds; stopped at 4.612172 seconds |
| Source-aware home v2, 3850 content-checked original `.o1`/`.o2` read-only references | First output 1.747711 seconds; both source-lookup cases pass; whole test stopped at 97.042178 seconds, 38 files complete / 882 case markers |

The second result is still DENY: `chunk-07` is interrupted at the complete-task
97-second gate. It is not 965-case correctness or an admitted speedup. The
source-aware fixture's source/runtime manifest and original-image identities
verify after termination. Do not repeat either unchanged denied configuration
or widen its ceiling. These runs change fixture topology, not optimization
semantics, and do not form a causal matched speed comparison.

| Relative raw receipt | SHA256 |
| --- | --- |
| `.data/d1510-fresh-produced-source-aware-mcp-tests-v1/report.json` | `f785b973a939090edabfd7f41e33718a4a1824e94be05a42302b078f69158edb` |
| `.data/d1510-fresh-produced-source-aware-mcp-tests-v2/report.json` | `a0fac5e09880f87b866a898dfa0359bc002203d087694932121ea68797af7de4` |
| `.data/d1510-source-aware-mcp-home-v2/source-fixture.json` | `ccf049bc788893320af81d45d0bfb8be9ad58692ea22595818030e8017879676` |

## ASCENT Launch Admission

The first isolated run reports 103.16 seconds / 30 Cases / final OK / exit zero,
but has no closed-link selections. It is excluded from candidate mechanism and
performance admission. The copied `gxi` wrapper lacked executable permission,
so PATH could skip it. The native handoff control explicitly exposed permission
denial; this is not a reason to credit the candidate with that duration.

The runner now requires executable `gxi` at the exact selected toolchain path.
The qualification launcher initializes the compiler before loading its owned
driver overlay, preventing later compiler import from replacing the overlay.
Its empty leading-runtime-options case is made safe for macOS Bash 3; leading
heap/debug options remain in their original position. Two launcher tests pass.
This remains qualification infrastructure, not a delivered AOT replacement.

With corrected executable installation, real controls pass:

- `.data/d1510-fresh-produced-ascent-handoff-v3`: 20 closed-link selected inputs,
  original producer object byte parity, one producer object compilation and
  successful native execution.
- `.data/d1510-fresh-produced-ascent-mismatch-v1`: changed static C rejected,
  original object preserved and no executable.

The original AS fixture remains clean; its measured helper hash is unchanged.
Owned toolchain/dependency dynamic-reference checks pass at 1989 / 2809 images.
Old library caches are moved inside the new owned fixture, not deleted from
active checkouts. Corrected qualification uses direct Bash/just/native Scheme,
matching Multiple-VM Gambit and GNU GCC, with the original 135-second component
deadline. Full 94-Suite or complete package speed admission is not inferred from
the 30-Case component. The MCP frozen six-patch anchor remains unchanged.

## Corrected ASCENT Result

`.data/d1510-fresh-produced-ascent-receipt-v2` completes at **96.11 seconds**
(user 299.47 / system 76.26), with **30/30 Cases**, final `OK`, exit zero and
entry cache MISS. The native library cache was absent before this run. All
source-aware producer controls completed successfully before qualification.
Actual branch markers now show **224 closed-link selected inputs**, 8 generated-C
MISS events and **74 object MISS** events / 74 object calls. This passes the
fixed 135-second component deadline, but does not establish whole 94-Suite or
matched causal speed improvement. The original v1 103.16-second result remains
excluded; it is not the comparator for an optimization claim.

The exact installed launcher SHA256 is
`6ca6941c8b1436f46cc8df02651b1031b34706f9e62b765bb8e56906b50dc5d7`.
The compiled driver overlay image SHA256 is
`8b61c5f638cbeacfa45268d8aa09df75e77a5c2ce6aa016b6e8774145093dd8a`.
Terminal receipt extraction:
`.data/d1510-fresh-produced-ascent-cases-v2.json`, SHA256
`802e4411bb291cd5f6b2a822b14b83ca460e99c48804ad8f121c523f1f5d002c`.
Raw output SHA256 is
`4972c5f08b70b457bbab31634183b259201865d4dd9f752588a5e44f51d8d479`.
Post-run toolchain and dependency reference checks again pass at 1989 / 2809
images. The original isolated project remains clean and its frozen helper bytes
remain unchanged. Launcher/source-fixture/reference-image focused tests pass
**17 checks**.

## Next Admission Review

The generic current-queue scheduling path is now demonstrated in both native
toolchains, but complete source-aware MCP admission still fails. Do not promote
0037 or replace either frozen series. No processes from these runs remain live.

The 74 ASCENT object MISS events show a concrete cross-process boundary: current
queue freshness does not prove objects left by earlier library compiler
processes. A future composition must preserve exact source, mode/options,
preprocessor/environment and toolchain proof, rather than trust old timestamps
or merely bypass selected-object compilation. The rejected all-producer capture
configurations cannot be repeated unchanged. Whether selective production
proof plus current-queue handoff removes meaningful duplicated work remains
unproven and requires a separate pre-edit review and native controls.

## Historical Test Home Restored, Still Denied

The recorded framework's `retained_47` selects
`.data/d1510-mcp-test-source-home-v2/build`, not the original source-less build
directory used by the first fresh-candidate wave. This home has the recorded
source-tree reference and matches every locked fresh-candidate runtime header
and archive digest. Selecting it directly is rejected by the native profile
verifier because its two Gambit archives are symlinks; that preflight rejection
is not a timing sample. The earlier sandbox CPU-discovery failure also precedes
test execution.

An independent APFS clone, `.data/d1510-fresh-produced-frozen-test-home-v1`,
preserves this historical image/source topology. Only `libgambit.a` and
`libgambitgsc.a` are materialized as identical regular files from their original
targets inside the clone. No verifier is weakened and the original home is not
modified. Full native-profile identity verification passes before execution.

The actual complete wave is
`.data/d1510-fresh-produced-frozen-home-mcp-tests-v2`. It uses the first original
fresh-candidate cold-built artifact and unchanged flags, tests, original-file
scheduling and 12 physical workers. Result: first output **2.701248 seconds**;
whole wave **97.060801 seconds**, **38/39 files** pass, with 882 passing-case
markers in completed files. Both source-lookup failures are resolved, but
`chunk-07` is interrupted at the fixed **97-second** whole-task deadline. Its
terminal log is in the `gerbil_trace_eval works with imports` case; it does not
contain a final OK. Overall admission and process exit are **DENY / 1**.

| Relative evidence | SHA256 |
| --- | --- |
| `report.json` | `77cb9318d484007bcdb56c649420e962909c5538cdc7390f83c67d3aa67dc1e2` |
| `19/test.log` | `2f24c120fd965956c6bce666a46c85db8a042adc4e623c6492aab676b4d6d581` |

This corrects the selected home, not the measured optimization. It neither
relabels the earlier denials nor restores complete admission. Do not repeat
this unchanged whole-wave configuration. Source topology alone does not remove
the observed full-test overrun; the next investigation must isolate repeated
interpreter/import execution costs before another consumer wave.

The separate [mode-sensitive semantic control](d1510-producer-mode-semantic-control.md)
passes with the selected ASCENT reference and 0037 overlay. It does not change
this MCP DENY, the frozen six-patch anchor, or the missing complete ASCENT scope.
