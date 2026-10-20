# Snapshot Reader: Native Two-ABI Verification

## Actual Build

The owned preparer now has explicit `--snapshot-reader`, and the Bash native
builder accepts `snapshot-reader` as its seventh argument. The preparer creates
a separate Git root and actually applies 0025 after copying the original native
source files. No default source bytes or previous profile lock is rewritten.
Both candidates use compiled native digests and planned producer admission.

- MCP-ABI candidate `.data/d1510-native-generated-c-gsc-v12`:
  GSC SHA `b2acde0e249bc4d02b9ede966c3b7ac9224b3d0dffe720ccd9c40134a456c314`.
- ASCENT-ABI candidate `.data/d1510-native-generated-c-ascent-gsc-v4`:
  GSC SHA `c9caaea9e777122e011fdd925f87fee578b94ff7eeac9031dce804fa8209f2e9`.
- Patched compiler journal SHA in both builds:
  `af8e298fa6a07f90a269ef7d9f305293d6ae849849c11276e5a10e80589f6b1c`.
- GSC entry remains `915ab10c1b874e91bea909ca64aae16a6f108df042380b81447046fbc0274253`.
- CLI entry remains `f17a66b53a1652d112775ab3aa56f091f45825635600989b19fcccd15a1f8d62`.

The ASCENT build uses its own MULTIPLE_VMS/segmented-global header (SHA
`8257ff05aadb634e2ef2532f7e1a21608a828c4adae35cf88276b78e7efff1e5`)
and its own Gambit runtime/compiler archives. Configuration SHA remains
`8711492af33a2b7e51c6b014e49ed3375cb218121a31270f9f2067b9904ec6b3`.
No SINGLE_VM compiler object/archive ABI mixing is performed. GNU GCC 16 and
the existing source makefile's object flags are used; object build concurrency
is two, as in the owned candidate builder, not a consumer worker cap.

## Native Controls

The race runner's `native` policy does **not load a replacement journal or
closure implementation**. Its Scheme contract invokes the compiled `c#` reuse
and digest procedures directly. Actual compiled readers on both ABIs preserve
A-byte C parity and a valid repeat HIT under the transient original-path B edit.

- MCP race: `.data/d1510-generated-c-read-race-native-v12-v1`.
- ASCENT race: `.data/d1510-generated-c-read-race-ascent-native-v4-v1`.
- Both race output SHAs:
  `ac4cc653e7ff04d6da328f635106e351da6c76864eb9197f1379373d976e76bc`.
- Native CLI controls pass at `.data/d1510-native-generated-c-snapshot-controls-v12-v1`
  and `.data/d1510-native-generated-c-snapshot-controls-ascent-v4-v1`: default and
  unrequested fallback, cold/repeat parity, digest backend invalidation, link
  adoption/parity, changed source/debug/invalid-index fallback, failed generation
  preserving prior C/proof, and temporary/lock cleanup.
- Actual concurrent compiled CLI producers pass at
  `.data/d1510-native-generated-c-concurrency-v12-v1` and
  `.data/d1510-native-generated-c-concurrency-ascent-v4-v1`: both child exit
  statuses zero, exactly one MISS and one HIT, original C parity, proof mode
  0600, producer record present and no leftover work/lock. Both statuses are
  awaited even if one fails. These are controlled concurrent writers, not a
  claim of multi-file atomicity or hostile arbitrary filesystem safety.

Preparation, profile rejection and frozen patch-lock tests: **31 pass**. Source
preparation tests prove default-byte preservation and actual reverse/apply of
0025 in a separate Git root. Shell syntax checks pass. The existing native
profile selector is deliberately unchanged: neither new binary inherits V11
identity admission or complete consumer performance claims.

## Real 55-Module MCP-ABI Component

`.data/d1510-real-native-generated-c-snapshot-v12-v2` compares retained real
ASCENT-generated sources with the MCP ABI's own original compiler. All 55 C
files and whole link C compare byte-identically. The native linker reports
55 reused producer inputs. Link C SHA is
`f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`.
The v1 attempt supplied a nonexistent source path and exited before compilation;
it is not counted as a passing run.

Raw timing fields:

- Original generation reports literal `real 21.:0`: malformed, **not admitted
  as a numeric wall time**. User 6.27/system 1.15 are retained as reported.
- Native generation real 26.20/user 7.81/system 1.99.
- Original link real 15.99/user 4.82/system 0.30.
- Native link real 1.07/user 0.30/system 0.15.
- Separate diagnostic lookup 0.255843 seconds; not added again to link totals.

No valid original total or acceleration ratio is inferred. This component has
large wall-time variation and is not an end-to-end performance admission.
Raw time hashes, unchanged:

- Original generation `5cfed5dd754e17214d9471491a2dc3361c99a3861e8191f1bcab87c0d3221ada`.
- Native generation `82e460ff12503a7cc91749510098871348fc089970f96b81228d5a05ed4eb433`.
- Original link `cdc666779e1f82af0e330f19f0b3b91a66cb644bb25bc41185786fb275e6b63e`.
- Native link `02c1a688085c5ad6db401a922d1a9ee9c441c5c2e831c10a355466d116dbbe5b`.

## Remaining Gates

The fastest MCP baseline remains first log 4.004-4.049 seconds, cold builds
36.467-37.406 seconds and one complete 87.409-second/965-case pass. Active
ceilings remain 4.5/42/97 seconds. No new complete package run or stable repeated
test admission is claimed here. Independent real ASCENT AOT correctness and
performance qualification remain required; compiler controls on its ABI are
not a substitute. Source/options/environment/tool validation is not removed,
and no producer batch tool-cache optimization is implemented yet.

All candidate builds and tests are terminal. The active ASCENT checkout/shared
dependencies, frozen five patches, existing installs and old experiment locks
were not modified. No commit/push/release or goal completion is claimed.
