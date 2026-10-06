# D1510 Best-Line Input Closure

This extracts the construction inputs referenced by the retained successful
full-build evidence. It is not a new candidate or a timing-restoration claim.
Experiment numbers are not cumulative patch versions.

## Historical Anchor

The D1513 B rows execute the same D1510 binary:

| Row | First compile seconds | Complete build seconds | Exit |
| --- | ---: | ---: | ---: |
| B1 | 4.789153 | 51.737180 | 0 |
| B2 | 4.933479 | 53.496910 | 0 |

Mean complete build: 52.617045 seconds. Both use fresh project clones, official
clean, zero remaining project native images and twelve workers. The complete
build ceiling remains 55 seconds. These are complete exits, not embedded-C
completion times. Historical performance is not currently reproduced.

## Construction References

| Input | Output | Direct evidence |
| --- | --- | --- |
| D935 retained base | D1392 core build | `.data/d1392-runtime-object-build/report.json` |
| D1392 core | D1394 completed library/tool home | `.data/d1394-runtime-object-toolchain/report.json` |
| D1394 home, D1083 selection, D994 module order | D1508 carrier | `.data/d1508-outline-current-preflight.py` |
| D1508 carrier, 42 original static objects, original RTS | D1510 binary | `.data/d1510-outline-current-native.py` |
| D1510 binary and original home | D1513 measurements | `.data/d1513-current-outline-full/report.json` |

The D1392 source build retains 0002 and 0003 already present in its base and
applies 0007 and 0008. D1394 finishes stdlib, libgerbil and tools. These are
actual inherited inputs; removing them would not reconstruct the measured
line. This does not authorize new std/make or consumer changes. The four-patch
reuse profile is not a complete manifest of the earlier base's patches.

D1508 uses eleven selected modules and fourteen guarded readonly traces from
the D1083 selection. It preserves parameter entry/identity/environment paths,
bounded primitive entries, poll boundaries and lookup-return branches. Only
the two reentry lookup traces are outlined. Broad return outlining is disabled.
D1510 compiles the retained carrier at O1, with the two bounded helpers at O3,
and links the original ordered objects and RTS. GSC is unchanged.

No D1509, D1511 or D1512 output is consumed by the D1510 construction script.
Those records describe validation or measurement. D1501 is a separate fold
test route. Later candidate binaries are not part of this closure, regardless
of their numbering or whether their tests passed.

## Locked Artifact Identity

| Artifact | SHA256 |
| --- | --- |
| D1510 binary | `446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3` |
| D1508 carrier | `e4a2ffde9b4dc329bf44db818f8241a30ef0c8ecaa7fc220c3fe6521936277e1` |
| Original GSC | `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00` |
| Original RTS | `fd3725c9cc68525efbd8c0385f242f72334de37d5c56a96fd7db8666bb873501` |

The readonly extraction verifies 50 stored hashes: 42 original C inputs,
carrier, binary, GSC, RTS and four frozen patch files. It also checks the gxi
alias and records current hashes of all 42 ordered static objects. The retained
historical report contains C input hashes, not historical object hashes; the
new current object inventory must not be presented as historical proof.

Private extraction: `.data/d1510-best-line-input-closure.py`; machine-readable
closure: `.data/d1510-best-line-input-closure/report.json`. No product source,
original binary, runtime home or selected performance baseline is modified.

## Exact Relink Check

The retained D1510 carrier object, all 42 original ordered static objects and
original RTS are linked with the original GNU command shape (`-ldl -lm`). No
C source is compiled, no generator is rerun and no later candidate is consumed.
Linking exits zero in 0.225229 seconds. The resulting entire binary, not just
its text section, has SHA256
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`:
it is byte-identical to the retained D1510 executable. All protected inputs
and the original binary remain unchanged.

This closes executable reproduction from the retained object closure. It does
not establish unique historical identity of every discarded object byte, a
fresh source-to-object rebuild, a performance gain or restored 51/52-second
cold builds. The relinked file is not selected as a new baseline.

Private check: `.data/d1510-relink-closure-check.py`; exact ordered object
hashes and link result: `.data/d1510-relink-closure-check/report.json`.

For source-recipe drift and bounded carrier parity, see
[the recipe audit](d1890-original-d1510-recipe-detail-audit.md). Regeneration
with today's helpers is not implicitly the original retained artifact. Further
optimization must branch explicitly from the locked D1508/D1510 inputs, keep
the original available, and must not inherit slower later candidates.
