# D857: real MCP generated-C string-lowering atomic experiment

Date: 2026-09-22. **Diagnostic only; no release patch or package-level A/B.**
The source is the real `gerbil-mcp/data/embedded` generated C from the D855
strict cold build (source revision `9a5c35e275e5d6847ff421151bb224f2eae177c1`).
No MCP source, global toolchain, optimization level, or admitted patch changed.
The diagnostic source and objects are under `/private/tmp/d856-embedded.OvBUDp`
and `/private/tmp/d857-str8-atomic`; temporary files are not durable release
inputs.

## Attribution

The 11,425,281-byte generated C has 218,334 numeric `___STR8` groups, including
characters above 255. The installed Gambit header defaults to
`___MAX_CHR=0x10ffff` (`___CS=4`). GCC's `-ftime-report` on the original C
reported 13.97 s total, 13.68 s parsing, 7.59 s preprocessing, and 0.28 s
optimization/generation. Instrumentation increased that invocation's wall time
to 14.98 s; it is not a baseline timing. The original preprocessed file was
101,577,593 bytes. An isolated split of the same generated Scheme module was
approximately 1.55 s Scheme-to-C, 11.70 s C-to-object, and 0.46 s dynamic
bundle. The package-level 37.841 s worker interval occurred alongside 11
other workers and must not be equated with isolated CPU time.

## Rejected hypothesis

Changing only `___STR8` to select the active character-width branch before
expansion was tested through a temporary quote-include header. `-I` alone
did **not** override the installed Gambit header; `-iquote` did, as verified
in the preprocessed line markers. The `-iquote` result was 101,575,742 bytes
versus 101,576,702 bytes for the saved-temporary control. The initial
11.80 s `-I` run was a false comparison because it still used the installed
header. No material size reduction supports this macro-selection approach.

## Packed-value atomic A/B

For this host's 64-bit little-endian and `___CS=4` representation only, a
temporary mechanical transformation replaced each numeric `___STR8(a,b,c,d,e,f,g,h)`
with four `___WORD` literals whose pairs are `a | (b << 32)`, etc. The
transformed C is 37,587,418 bytes, larger than the original C but much
cheaper for GCC to parse. Both paths used the same installed GCC 16,
`gsc -obj`, `-D___DYNAMIC -fPIC`, and unchanged Gambit optimization flags;
only the generated C representation differed.

| Pair | Original C-to-object | Packed C-to-object |
| --- | ---: | ---: |
| 1 | 12.22 s | 4.54 s |
| 2 | 11.85 s | 3.32 s |

All four Mach-O objects have the identical SHA-256
`c41c4d95762463bfea51af88ff9a89a3f249010d9b79e25c5a23ccf6b886ee34`.
This is strong atomic bit-equivalence evidence for this one module and target,
not proof for all Gambit configurations or an end-to-end package speedup.
The measured mean C-to-object time falls from 12.04 s to 3.93 s (about 67%).
Do **not** multiply this saving by 543 `compile-file` jobs: most are small,
the worker intervals overlap, and this module was not the final straggler.

## Admission boundary

Do not ship the temporary postprocessor. A proper implementation belongs in
the Gambit C emitter and must preserve its portable 32/64-bit,
little/big-endian, and 1/2/4-byte character contracts, including `NSTR` and
short/tail chunks. First write focused generated-object equivalence tests,
then validate representative real modules in both gerbil-poo and gerbil-mcp,
then rebuild the exact AOT toolchain and run adjacent strict package A/B with
12 native workers and the 10-second silence gate. Keep D851 held until both
consumers pass their own non-regression gates. This receipt alone warrants an
upstream emitter investigation, not inclusion in the release patch set.
