# D858: reject header-only STR8 optimization after real MCP package gate

Date: 2026-09-22. This is a **negative performance result**, not a release
patch. The consumer was the unchanged real gerbil-mcp checkout at revision
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. The isolated V19 D851
toolchain retained the D855 observation instrumentation in both arms; its
`gerbil` SHA-256 was
`058b456de550d3c03273fdd5d6b47a704ed07e1e6ca1528664da49fad5df4dd2`.
Both arms used real GCC 16, the same Gambit optimization level, 12 Gerbil
workers, distinct clean consumer clones, and the strict 10-second package
silence gate. The temporary candidate changed only the *isolated installed*
`gambit.h`, not MCP source, the global toolchain, or the admitted patch set.

## Hypothesis and atomic screen

On Darwin GCC with 64-bit little-endian words and 4-byte characters, a
direct `___STR8` definition removes nested vector-packing casts. Every other
platform/word/character branch remained on the original definition. The
real `gerbil-mcp/data/embedded` C-to-object atomic measured 6.58 s with the
installed candidate versus 12.22/11.85 s in the D857 original pairs. The
candidate object SHA-256 matched the original exactly:
`c41c4d95762463bfea51af88ff9a89a3f249010d9b79e25c5a23ccf6b886ee34`.
A version retaining all original 32-bit casts measured 10.79 s, confirming
that most of this atomic gain requires simplifying the character-value
expression, not merely selecting a macro branch.

## Adjacent package gate

| Real MCP cold build | Baseline | Header candidate | Delta |
| --- | ---: | ---: | ---: |
| Whole package | 77.650 s | 77.013 s | -0.637 s (-0.82%) |
| Longest output silence | 3.789 s | 4.004 s | +0.215 s |
| `embedded~0.scm` compiler job | 42.483 s | 40.101 s | -2.382 s |

Both clean builds exited zero and passed the 10-second silence gate. This
single adjacent pair is *not* evidence of a stable 0.82% improvement; it is
evidence that the large atomic result does not turn into a material package
win under the current parallel schedule. The baseline graph ended at
45.277 s and its final `compile-file` job at 71.527 s; the large `embedded`
job ended earlier, at 57.152 s. After graph completion, parsed compiler-job
intervals occupied an average 11.83 of 12 workers until the last file. The
late jobs were many modest files: for example `lib~0` (0.686 s),
`resolve-imports~0` (1.417 s), and `howto-verify~0` (1.214 s).

Of the 185 compiler jobs with persisted C files matched to this baseline
receipt, four files over 1 MiB account for 72.209 worker-seconds, and
`embedded~0.c` alone contains 218,334 of the 258,170 observed `___STR8`
groups. This persisted-C subset is **not** all 543 compiler jobs; the
remaining representations do not all leave a corresponding C file in the
clone. The concentration explains why a header change aimed at string-heavy
C does little for the broad late tail.

Raw local receipts: `/private/tmp/d858-mcp-baseline.json` and
`/private/tmp/d855-mcp-native-jobs.json` (the latter path was reused by the
candidate run). The installed-header candidate was removed immediately
after the A/B; the isolated toolchain is back on the original header.

## Decision

**Reject this header-only variant.** Do not add a patch merely because one
module's atomic compile improved. The broad package bottleneck is occupied
native workers processing many C jobs and the final executable closure; a
larger optimization must reduce work across that distribution or shorten the
actual last-job/link critical path. The D857 fully packed emitter candidate
remains an atomic hypothesis only and is not implied to qualify by this
negative result. Preserve the D851 release hold and independently qualify
both gerbil-poo and gerbil-mcp before any new release patch.
