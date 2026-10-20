# D1376-D1380: default-lowopt restoration rejected as major optimization

## Source premise, not a Darwin algorithm

The original Gambit configure.ac default low optimization includes
`-O1 -fexpensive-optimizations -fno-gcse`. The explicit Darwin release
`--enable-c-opt=-O1` takes a branch replacing that string with bare `-O1`.
The current Linux workflow does not supply that explicit override.
This is a source-recipe difference, not proof of historical Linux artifact
flags, Darwin-only compiler semantics or a platform-specific paper solution.

The installed GNU GCC 16 reports expensive optimizations disabled with bare
O1 and enabled after restoration. GCSE is disabled in both O1 configurations.
The single experiment adds only the default options; it does not sweep flags.

## Actual code and isolated binary

D1376 recompiles unchanged original core/stx C through original gambuild-C
into `.data`. Core text changes from 136,540 to 136,356 bytes; stx changes
from 43,232 to 43,248 bytes. Size alone is not the admission premise:
1,115 core direct branches to shared target 0x19b4 disappear, while the
indirect br count rises by 1,115. Stx similarly loses 263 direct branches
to 0xc64, with 263 additional br instructions. This is static instruction
evidence, not measured branch prediction, exclusive latency or a speedup.

D1377 rebuilds eleven original native runtime/expander modules and relinks
an isolated executable. All generated C hashes match the original inputs.
GSC, gambit.h and the RTS archive retain original identity; no consumer flags
or source change. The executable SHA-256 is
`fe6a4697cb95b5a6745aeab50cb6493044c498fad5fc7ad20cc7b9a03e3730b3`.
The original GSC SHA-256 remains
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
The existing std/make/std/test import smoke passes, but that is not actual
test-case qualification or full toolchain installation qualification.
The diagnostic builder gains an explicit O1-default mode, not a product
default or production patch.

## Preserve the failed whole-home lane

D1378's first original run passes: clean 3.594 seconds, first compile
6.700 seconds. The candidate run, using its copied library home, produces
no clean output within the unchanged 30-second gate and is terminated.
ABBA is incomplete and unqualified. No larger timeout is substituted.

D1379 uses the same candidate binary with original library/GSC home.
Actual clean passes in 2.222 seconds, before the three-second sampler attach
threshold, so no stack sample is created. This does not diagnose the copied
home failure conclusively or turn D1378 into a pass. It motivates a common
library-home binary comparison with a distinct receipt.

## Strict actual first-window ABBA

D1380 uses the original MCP head
`9a5c35e275e5d6847ff421151bb224f2eae177c1` in the fresh project checkout,
12 physical-core concurrency, original library/GSC home for both binaries,
and no profiler. Every run executes official gerbil clean then gerbil build;
clean leaves no project native images, and build is deliberately terminated
after the real first compile line. All original output/budget gates pass.

| Order | Binary | First compile seconds |
| --- | --- | ---: |
| A1 | original | 5.850987 |
| B1 | default-lowopt candidate | 5.911150 |
| B2 | default-lowopt candidate | 5.853864 |
| A2 | original | 6.060097 |

Means are 5.955542 versus 5.882507 seconds, a diagnostic ratio of 1.012416
and reduction of 1.2263 percent. The observed ranges overlap. This is not
a stable speedup claim and is far below the requested major-cost reduction.

## Decision

Reject default-lowopt restoration as the major first-log optimization.
Do not solidify it as a production Patch, start a full toolchain build for
it, or spend a full concurrent test campaign on this failed speed premise.
No whole-build, actual std/test-case or Darwin platform-cause success is
claimed. The main seven-to-eight-second objective remains unresolved.
All owned runs are terminal; existing negative records remain intact.
