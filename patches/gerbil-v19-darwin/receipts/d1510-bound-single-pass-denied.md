# Bound Single-Pass Proof: Not Admitted

## Review

The previous missing-object-only branch executed zero times in real MCP. It is
not rerun. This separate experiment covers a missing proof even when the object
already exists. GNU GCC's internal `-save-temps=obj` obtains preprocessing input
and an object in one compilation invocation; the ordinary proof key is built
from that input. Source/tool/options/environment/object validation remains.
The expected benefit was one fewer independent preprocessing invocation on
initial proof creation, not a claimed numeric package speedup.

Only Darwin/GNU and an explicitly source-bound invocation may opt in through
`GAMBIT_DARWIN_BOUND_SINGLE_PASS=1`. Existing proofs retain the complete
preprocess-and-validate HIT path. No consumer filename or package rule is used.
Complex quoted/escaped/globbing object flags retain the original path. The
internal capture removes the transport-only `-pipe`, because GCC otherwise
warns it is ignored with `-save-temps`. User diagnostics are not suppressed.

Experimental patch 0033 applies after 0027, **not after 0032**:
`ba5c1d67d75849ff91360879cf02461d991e5742f827af9c0a344d004505dab8`.
Helper: `e4e2c15e0b053e05f4349f55b920441d293d9d53a688cae551774d41bbb221af`.
It remains outside both frozen series and is not performance-admitted.
Actual isolated apply/reverse and exact helper parity pass in
`.data/d1510-bound-single-pass-patch-replay-v1`.

## Native Controls

- `.data/d1510-bound-single-pass-controls-v2`: real cold compilation and HIT,
  exact ordinary-object parity, changed source rejection with existing/missing
  objects, recovery, unsupported/debug/invalid-digest rejection and concurrency.
- `.data/d1510-bound-single-pass-aba-v1`: actual source mutation during compile
  A to B then back to A; trigger recorded, exact object and runtime parity.
- `.data/d1510-bound-single-pass-semantics-v1`: relative headers, filename/base/
  short-name macros, 2020 timestamp, line/include levels, full later HIT and
  unchanged unbound debug/prefix-map fallback.
- `.data/d1510-bound-object-modes-v1`: the identical C source deliberately has
  different dynamic/static objects. A mode change must MISS; repeating the exact
  mode HITs. Every result matches its ordinary GCC reference bytes.

V1 controls rejected GCC's `-pipe`/`-save-temps` warning before publication;
that failed launch is excluded. V2 does not filter the warning out of diagnostics:
the internal capture command no longer asks GCC to use incompatible transports.
Focused controller/profile/full-test admission checks: 43 passed.

## Real MCP Result

Native runtime and compiler ABI are the same as the prior closed-link candidate;
only the separate helper and explicit mode changed. Receipt:
`.data/d1510-bound-single-pass-mcp-qualification-v1`.

- Actual first compile: **3.818606 s**, below 4.5 s.
- Build: **DENY at 42.034061 s**, forced kill/reap with no cleanup errors.
- Complete build duration: unknown. Complete tests: skipped.
- 66 single-pass captures / 66 object MISSes; zero object HITs.
- Two generated-C MISSes, zero generated-C HITs.

Raw report/admission/log hashes and terminal fields are preserved in
`d1510-bound-single-pass-denied.json`. The branch is active, unlike 0032's real
MCP run, but this still does **not** pass package performance. The number of
completed objects before a watchdog is not an end-to-end speedup. The helper
cannot affect the pre-first-compile phase, so the lower first-log observation
is not attributed to this change.

## More Fundamental Producer Mismatch

The authoritative Gerbil `gsc-compile-file` Darwin branch compiles the module's
`static-o` with `-D___DYNAMIC -fPIC`, then uses that object in the dynamic-image
link. It has already copied the matching runtime C to static C. The original
`compile-obj` may retain that object when source timestamps do not require a
rebuild. The new bound separate-compiler definition instead forces a backend
call for every selected object, using the static-link options rather than the
original dynamic producer options. This can trigger a real extra compilation;
it is not evidence that the original producer object was absent.

Do not ignore this option mismatch or weaken tool/header validation. The mode
control above proves C equality alone is insufficient to reuse across options.
Next implementation must capture the actual producer's source/options/toolchain
proof during its original compilation, and validate that same producer recipe
when the unchanged object is handed to the native link. Reconstructing a static
recipe and demanding its proof of a dynamic-produced object loses the earlier
Darwin shared-object advantage.

## Frozen Boundary

The six-patch safety candidate remains byte-identical: first compile
3.950–4.038 s, cold builds 36.414 / 35.552 / 37.770 s, complete test 86.924 s,
39 files / 965 cases. Its patch/runtime/GSC/raw-evidence/per-sample check passes.
Limits remain 4.5 / 42 / 97 s. No new MCP full-test result, complete ASCENT Suite
qualification, general release admission, latest-staging rebuild or GitHub
delivery is claimed. The goal remains open.
