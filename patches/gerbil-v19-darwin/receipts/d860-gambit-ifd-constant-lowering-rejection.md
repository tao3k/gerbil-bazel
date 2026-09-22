# D860: reject broad IFD constant lowering after atomic GCC gate

Date: 2026-09-22. Diagnostic only, with the unchanged V19 D851-derived
isolated toolchain and real generated MCP C from the D858 baseline clone.
No Gerbil/Gambit source, MCP source, global binary, or release patch changed.

## Source hypothesis

The V19 Gambit emitter in `gsc/_t-c-1.scm` emits many
`___IFD(kind,fs,link,gcmap)` frame-descriptor expressions. `gambit.h.in`
defines fixed widths (`___IFD_FS_WIDTH=5`, `___KIND_WIDTH=2`) and return
kind constants (`___RETN=1`, `___RETI=2`, `___RETT=3`). A source generator
could precompute the integer descriptor and save GCC repeated constant
folding. This is a plausible *portable emitter* change, not a compiler-flag
workaround.

An isolated mechanical transformation replaced all 153 `___IFD` calls in
real `howto-verify~0.c` and all 1,222 calls in `lint~0.c` with their exact
hexadecimal values. Both transformed objects were byte-identical to their
original counterparts. The formula used was
`(gcmap << 12) + (link << 7) + (fs << 2) + kind`.

| Generated C | Original C-to-object | Lowered C-to-object | Result |
| --- | ---: | ---: | --- |
| `howto-verify~0.c` | 0.34 s | 0.55 s | No gain; short-run noise is material |
| `lint~0.c` | 2.59 s | 2.57 s | No material gain |

The representative `howto-verify~0.c` GCC 16 `-ftime-report` attributed
0.10 of 0.39 compiler seconds to parsing and 0.29 seconds to optimization/
generation. This contrasts with the string-heavy `embedded~0.c` case and
supports D859's finding that most small native jobs are not dominated by
one large preprocessing macro. The report itself adds instrumentation
overhead; do not use its 0.39 s as an uninstrumented package baseline.

## Decision

Do **not** patch the Gambit emitter for this constant-folding change: the
atomic objects are correct but the measured compiler cost is unchanged.
Do not lower GCC optimization to make an artificial build-time gain; emitted
program performance is part of the user's requirement. The next candidate
needs to reduce work common to many generated functions, prove equal or
better runtime behavior, and pass adjacent uninstrumented POO/MCP A/B before
promotion.
