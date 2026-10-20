# Snapshot Reader: Bind Proof To Actually Parsed Bytes

## Root Cause And Admission Review

Before implementing shared producer tool validation, the source-read proof must
be sound. The original experimental journal copies source A to a snapshot, then
calls the real compiler reader on the original path. A transient edit to B during
that read, followed by restoration to A, passes the later A/snapshot digest check
while generating C from B. Prior final-state mutation controls do not cover this
case; their passing receipts are not proof of transient-read safety.

This is not an optimization or grounds for a wall-time claim. It is a necessary
source-invalidation prerequisite to the generic reuse goal. Frozen MCP static
object reuse does not use this experimental generated-C journal and is unchanged.

## Reproduced Counterexample

`tests/check_generated_c_read_race.sh` runs original GSC directly. A deterministic
Scheme delegate changes the original file from `(define (answer) 17)` to 29 only
while the actual reader executes, then restores it to 17. No timing luck,
concurrent user edits, native test supervisor or source timestamp manipulation
is involved. Original compilation of A is retained as the byte-parity control.

`.data/d1510-generated-c-read-race-original-v1` exits zero **because the expected
counterexample is reproduced**, not because old reuse is safe. It emits MISS,
then HIT, then `OLD-JOURNAL-TRANSIENT-SOURCE-COUNTEREXAMPLE`: generated C differs
from A while an unchanged-A repeat accepts the proof.

## Experimental Implementation

`0025-gambit-darwin-generated-c-snapshot-reader.patch` follows experimental 0024
at its Gambit source root. It redirects the real compiler read to the owned
snapshot, keeps the original suffix for reader start syntax, and preserves
GSC's explicit original-container wrap/unwrap closures for source locations and
relative include resolution. It admits only that four-argument compiler-reader
shape; default port-derived locations and unknown shapes are rejected.
Digest/dependency revalidation, macro-context fallback, locking and proof-last
publication are retained. No tool digest check is removed or shared yet.

`tests/gambit-generated-c-snapshot-reads.scm` is an independently loaded test
adapter implementing the same policy without replacing existing experimental
source locks or compiled V9/V11 binaries.

## Verification

- `.data/d1510-generated-c-read-race-snapshot-v1`: adapter compiles A despite the
  transient original-path edit; C equals original A and repeat HIT remains valid.
- `.data/d1510-generated-c-snapshot-patch-v1`: separate Git root; actual 0025
  forward apply and reverse-check pass. The initial incorrect relative path and
  malformed manually counted hunk were corrected before the passing application.
- `.data/d1510-generated-c-read-race-patched-v1`: runs the **applied patch's reader**,
  not the adapter; source-byte parity and repeat HIT pass under the same injector.
- `.data/d1510-generated-c-snapshot-contract-v1`: 15 existing contracts pass,
  including transitive source/options/tool/environment invalidation, mid-hit and
  pre-publication source changes, corrupt pins, failure preservation, macro
  fallback/stickiness and diagnostic parity. Both concurrent producer controls
  finish and pass. The launcher now waits for both statuses even if one fails,
  and explicitly uses Darwin's `/usr/bin/stat` for permissions.
- `.data/d1510-real-generated-c-snapshot-v1`: all 55 real retained ASCENT-generated
  C files equal their original-compiler controls; repeat hits without generation;
  linking canonical versus immutable pinned C is byte-identical. This is not an
  ASCENT AOT test run or a complete package performance qualification.

The real-source fixture records control 9.88 seconds, population 14.164347 and
repeat 2.288848 seconds. These dynamically loaded/external-digest component times
are not comparable to native V9 timings as an optimization win. No total MCP
or ASCENT test time is claimed. Ordinary compiler source locations, include
behavior and diagnostics are covered by these fixtures; arbitrary custom reader
or macro APIs are not qualified.

## Content Identities

- 0025 patch: `b9c3d77450c214db149a6fb1f5a75fba4b3ade80b399e62df284f57ca91d718e`.
- Old counterexample output: `bfb20d60791350f168cb43575c7836f8f4e7b63ea67f85a032f828df65c1ea56`.
- Applied-patch control: `ac4cc653e7ff04d6da328f635106e351da6c76864eb9197f1379373d976e76bc`.
- Fifteen-contract output: `9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`.
- Real 55-source output: `8110b4d278fb5793f3fa862588809ee6ea1f825f81e42278486dde3d9eabef6a`.

Old V9/V11 journals retain this reproduced defect. Their binaries are not
admitted and were not patched in place. Native recompilation plus new exact
profile identities, complete consumer correctness and all current performance
gates remain required. No release, commit, push or goal completion is claimed.
