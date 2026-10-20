# Opt-In Library Producer Integration

## Direction Review

- Correct boundary: extend the existing 0007 static C/object production path,
  rather than copy ABI-incompatible ordinary dynamic C.
- Previously explored boundary: 0007 enables capture only when the normalized
  build specification includes an executable. Ordinary library-only std/make
  callers do not enable it. The native consumer previously had no producer proof.
- Worth testing: the compiled digest component has positive serial results,
  whereas its external-process version regresses. Only the compiled backend is
  used in this integration candidate.
- Expected benefit: bounded by avoided duplicate Scheme-to-C generation and
  matching object work. Extra producer cost remains real; the 55-module component
  ratio must not be advertised as a package-level result or first-log saving.

## Separate Experimental Patch

`0022-gerbil-darwin-opt-in-library-static-capture.patch` extends the existing
std/make policy only when both the compiled platform is Darwin and
`GAMBIT_DARWIN_NATIVE_GENERATED_C=1`. Linux's compile-time alternative is false,
and the original executable-specification policy remains unchanged. No MCP or
ASCENT identifiers, workload lists, package paths or reordered log output occur
in the patch. It is **not** part of `mcp-v4-driver.series` or a default feature.

Patch SHA256:
`9e8138e8c1b448224b31ce8bde1a22e346d4cb54196548579496d252dbfa30a8`.
Patched std/make source SHA:
`5d86344c01ca0344e6f427d05241c4c4677e4dc8b3faecc51bedc1417de04955`.

## Executed Independent Library Control

`.data/d1510-std-make-native-capture-v8` compiles the actual std/make module into
an owned overlay with its std package declaration and fresh optimization metadata.
It then builds a standalone library through ordinary std/make, not an executable
specification or a package-specific bypass.

Passed:

1. Disabled native flag: original dynamic path, no generation proof.
2. Enabled flag: actual native GSC emits producer proof and alias-index record.
3. Consumer context reconstruction matches the original proof (`#t`).
4. Native static-link lookup admits the existing C (`#t`), and CLI reports HIT 1.
5. Complete link C matches the original compiler at the same output filename.
6. A fresh interpreter imports the compiled dynamic library and returns 17.

Candidate log SHA:
`57d4e3c7c12477ccdd3caa0f6d3b8fc699e9686eadcc529d879b9107e5ce3263`.
Complete original/native link C SHA:
`89201c5d90a3df38070f9c2c8483ab4fa23ac481a3dfa9e65f58577b29397331`.
Fresh optimizer metadata SHA:
`6010a6961c7b85b7edbd99f10f002ac0568b343d48d05f3936d57dc73bcc490e`.

This is a mechanism/correctness control, not a timed cold-build admission.

## Fixture Failures And Corrections

v1 has a malformed patch hunk and fails before compilation. v2 lacks std's
package declaration. v3 reveals that git apply inside ignored repository
subdirectories can silently skip edits. v4/v5 produce actual proof but the harness
collects and discards the consumer's stdout, so marker admission fails. These
are not successful qualification runs and are not performance samples.

v6 uses a separate Git root, requires the patched source and generated Scheme
to contain the flag, and propagates actual child output. v7 adds whole link-byte
parity. v8 also regenerates optimizer metadata for the owned module overlay.
The frozen replay checker received the same Git-root correction; its v5 receipt
proves actual reverse deletion and forward reconstruction, not a vacuous compare.

## Consumer Isolation

The framework now supports a content-recorded owned module overlay. It checks
all original read-only image references before replacing **only the fresh copy's
links**, never their shared targets. It binds new module files by digest and
removes only the copy's stale matching static C/object. Unit tests cover original
target preservation, unrelated reference retention, new overlay drift and path
traversal rejection. The focused overlay and frozen-lock suite passes 16 tests.

`.data/d1510-native-generated-c-ascent-v2` is an APFS COW copy of the same frozen
consumer revision and dependencies. It has the independent ASCENT-ABI native GSC
and nine owned std/make overlay files, leaving 1,989 unchanged read-only toolchain
images and all 2,809 dependency images. No active checkout or shared dependency
was edited. Real cold preparation and AOT test receipt:
`.data/d1510-native-generated-c-ascent-positive-v2`.

## Matched Cold Positive-Plan Pair

Both runs are terminal with exit zero, 30/30 cases, all 512 directed graphs,
85/87/1 compiled layers and final `HARNESS-OK` / `OK`. The same frozen consumer,
native GSC bytes and std/make overlay are used in fresh isolated copies. Existing
static-object reuse remains enabled in both; only the new native generated-C path
and its in-process digest backend are enabled in the candidate.

| Metric | New Path Disabled | New Path Enabled |
| --- | --- | --- |
| Complete cold preparation plus positive-plan test | 134.72 s | 122.05 s |
| User CPU | 298.75 s | 259.77 s |
| System CPU | 74.51 s | 75.77 s |
| Native produced-C link adoption | 0 | 54 |

This single matched pair observes a 9.4 percent wall reduction. It is not a
repeat-stability result, a full ASCENT-suite pass or MCP admission. The older
196.73-second run is not the matched control and is not used to claim a gain.
0022 remains excluded from the frozen MCP patch series.

Control receipt: `.data/d1510-native-generated-c-ascent-positive-control-v2`.
Control output SHA256:
`12049dca71fe86b05cad836d82c78c6f63fadb95b7320a7e8a544525b7533bdd`.
Control time SHA256:
`72219c853cb48c1efce0ec647ee03397fd3c241efb332c6f73c10163692e2894`.
Candidate output SHA256:
`c10680f774f09a57ee6702aa52c6def5e33180d42015278f44e639cab6f29984`.
Candidate time SHA256:
`15babfc360524dd4f425cc11bc5cd4cbe3e30112a049c0d5950f050fe5678e9a`.

Full consumer qualification and MCP's three gates remain open. Do not promote
this limited correctness/performance pair to goal completion.
