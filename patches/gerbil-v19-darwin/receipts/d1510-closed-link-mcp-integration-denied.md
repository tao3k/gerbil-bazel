# Closed Link Native Integration: Denied

## Review And Frozen Boundary

The real link stage is the correct integration boundary. Singleton producer
hooks remain excluded. Entry-role separation is worthwhile because changing
the real entry must not invalidate an unchanged ordered library group. It is
not permission to reorder generation or normalize the entry timestamp.

The original five-patch reference and six-patch 0026 safety candidate are
unchanged. The six-patch retained MCP samples remain 3.950–4.038 s first compile,
36.414 / 35.552 / 37.770 s cold builds and 86.924 s complete tests, 39 files /
965 cases. The active ceilings remain 4.5 / 42 / 97 s. Its identity, raw evidence,
GSC and per-sample performance checks still pass after this work.

## Native AOT Integration

`prepare_closed_link_aot_driver.scm` reads the frozen and donor Scheme forms,
requires exactly one separate compiler definition in each, replaces that one
definition, and checks that every other frozen form is unchanged. This preserves
the private Darwin loader instead of overwriting the entire module.

The existing native builder supports this transform without creating another
native build runner. It verifies the six-patch baseline, frozen objects and
providers; checks the exact eleven added imported references; regenerates
matching linker metadata using the unchanged coalescing configuration; and
passes the standard-library import smoke test. The candidate runtime is
`.data/d1510-closed-link-mcp-aot-v3/gerbil`, SHA-256
`efae13a287d4bd850a99a53391122f4f66ca003059d8ca3a9d5e0551271a37c2`.

The first attempt rejected changed global references. Inspection established
these were imported references, not new module definitions. The next attempt
failed linking because the old carrier lacked a new symbol. Both failures are
retained and excluded. V3 regenerates the matching carrier; no existing runtime
or shared dependency is replaced.

## Whole MCP Gates

| Candidate | First compile | Build watchdog | Completed build/test |
| --- | ---: | ---: | --- |
| Native closed-link integration | 4.172981 s | DENY at 42.005289 s | Unknown / skipped |
| Missing-object cold snapshot branch | 4.061399 s | DENY at 42.037365 s | Unknown / skipped |

Both processes were killed and reaped, without cleanup errors. Later rounds and
full tests were not run. These are not 42-second successful builds. Exact raw
report/log hashes and terminal records are in
`d1510-closed-link-mcp-integration-denied.json`.

The first log has two generated-C MISS events, zero generation HITs and 36
static-object MISS events before interruption. The second has two generation
MISS events, zero HITs and 42 static-object MISS events. Its new missing-object
capture branch has **zero executions**. The component can work correctly while
not covering this consumer's actual cost. Do not rerun either unchanged candidate
or promote a component's speed to a whole-package claim.

Next audit: the existing-object path and the absence/availability of reusable
producer proofs. Determine which actual objects were already compiled and why
the bound driver forces them through full validation/recompilation. Reuse needs
verified source/options/toolchain provenance, not a timestamp-only exemption.

## Reviewable Experimental Patches

None is added to either measured series or enabled by default.

| Patch | Scope | SHA-256 |
| --- | --- | --- |
| 0030, after 0029 | Explicit entry role, contiguous generation order, exception cleanup, overlapping-C-target fallback | `7af0fcd529525ab64397f7cb32aeb2632e67a4dcf35bd95fa00e96a72b91202e` |
| 0031, after 0028 | Pass the real entry role; retain verbose actual object calls | `c17a27332cba644975ae388a60819b1b4cb24e30a3a165b57cd044441eb899b8` |
| 0032, after 0027 | Opt-in direct bound snapshot compile only when the object is missing; no reusable proof is published | `5527548c32ffd333596557ac5fa019c6b646a9945487a0a11be68be466237be1` |

0030 passes actual reverse/apply and exact source parity in
`.data/d1510-closed-link-role-patch-replay-v1`. 0031/0032 pass actual forward,
reverse and reapply checks with exact source/helper parity in
`.data/d1510-role-cold-patch-replay-v1`. The two explicit native build profiles
lock compiler/runtime ABI, driver/helper, compiled sources and patch identities;
they are identity checks, not performance admission.

## Native Controls And ASCENT Scope

- `.data/d1510-closed-link-entry-role-v5`: 56 modules, 3.99 s population / 0.26 s
  HIT / 0.26 s entry change. Entry change is one stable-group HIT and one entry
  MISS. Complete C/link parity, invalid-role cleanup and two concurrent links
  with exact per-output-name reference/manifest parity pass.
- `.data/d1510-closed-link-overlap-v3`: C-first and Scheme-first overlapping
  targets retain the original path with exact C/link parity and no binding.
  A genuine macro source is rejected with typed failure and owned-work cleanup.
- `.data/d1510-bound-cold-capture-controls-v2`: exact ordinary-object parity,
  no cold proof, full later MISS/HIT validation, wrong-source rejection and
  concurrent publication pass. V1's foreground-HIT expectation after a
  background context failed; no cache guard was weakened. The foreground is
  independently validated, then its repeated identical invocation must HIT.
- `.data/d1510-bound-cold-capture-aba-v1`: a real compiler wrapper changes
  source A to B during actual object compilation and restores A afterward.
  The mutation trigger is recorded; the bound private snapshot still returns
  17 with exact ordinary-object parity and no reusable proof.
- `.data/d1510-closed-entry-role-ascent-receipt-v1`: direct native Bash/just cold
  preparation, 119.35 s, 310.89 user / 94.38 system, 74 object MISSes, eight
  generation MISSes, 30 Cases, final `OK`, exit 0. This is not all 94 Suites and
  does not establish complete ASCENT performance. Python only extracts the
  terminal receipt; it does not supervise the native test.

Two role fixture attempts are excluded: one reused the synthetic entry as an
input; the other compared different output basenames even though GSC embeds
them in linker metadata. V5 uses the original paired sources and compares each
concurrent output against its own genuine ordinary-GSC reference.

Focused lock, controller, complete-test admission and native-profile checks:
**100 passed**. No complete latest-staging release rebuild, general performance
admission, Git commit or GitHub push is claimed. Both consumer gates remain open.
