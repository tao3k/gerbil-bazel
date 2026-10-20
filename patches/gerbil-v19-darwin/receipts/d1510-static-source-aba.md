# Frozen Static C Input: Release Blocker

The frozen V4 helper hashes the original C file before preprocessing and again
afterward, but GCC reads that mutable original path. An A -> B -> A change during
preprocessing passes both source checks while producing an object for B. This is
a C/GCC input race, separate from experimental 0025's Scheme snapshot reader.

## Deterministic Native Counterexample

Receipt: `.data/d1510-static-source-aba-vulnerable-v1`.
Script: `tests/check_static_source_aba.sh`.
The isolated fixture copies the exact frozen helper and uses the matching
Multiple VM toolchain. A private compiler wrapper modifies only the fixture's
known original C input during preprocessing, executes genuine GNU GCC 16, then
restores the original source. It does not change global tools or other checkouts.

- Original A returns 17; transient B returns 29.
- Reuse disabled: the ordinary native object returns 17.
- Reuse enabled: GSC exits successfully and logs `GAMBIT-STATIC-OBJECT-MISS`.
- Source A is restored byte-for-byte; both digests match.
- Linking the candidate object with genuine GNU GCC produces a program that
  returns 71 because its function returns 29, not the expected 17.
- The reproducer exits 0 only because this known failure was reproduced. This
  is **not** passing correctness or a performance sample.

| Artifact | SHA-256 |
| --- | --- |
| Frozen helper | `08d8ebe59d24a7098561c909c5b8e04c66aff78794d5f68f1cedddf1f2168646` |
| Source A and restored source | `78a5330cc923a5f6ee044bc60b7e043675c7b21eceda68c1ccdcf903fe248275` |
| Ordinary object | `63bdabdf011323e437e0e25485d3406aef3b5de4b0e73159a3bfae76bf3e3d0b` |
| Wrong candidate object | `f955b391cddf6f63485440010e69bf74356750eec56ce6d383bc1b301a8eec34` |
| Candidate log | `1150b9fc90d5dc511723125718151f495c958fa9081931e78e515da539cab22f` |

## Admission Decision

Keep the best measurements and exact five-patch reference immutable. Do not
promote this helper to general production admission or combine the unfinished
generated-C link integration with it. No new safety fix is claimed here.

Before a hardened patch can replace it, GCC must read bound input bytes, not a
mutable path merely checked before/after. Preserve relative include lookup,
filename macros, line/debug metadata, diagnostics and existing tool/options/
environment invalidation. The protected reproducer must return 17 and preserve
ordinary object bytes, followed by the existing native controls and fresh full
consumer correctness/performance validation. MCP gates remain 4.5 / 42 / 97
seconds; freezing old timings does not qualify a behavior-changing replacement.
