# D861: reject Gambit-header PCH as a broad Darwin fix

Date: 2026-09-22. Atomic diagnostic on unchanged real MCP-generated C and
the isolated V19/GCC 16 toolchain. No source, release patch, or global
installation was changed.

`gsc -obj -verbose` confirmed `-O1 -pipe -march=native -fPIC` and the
already-admitted `-ftrack-macro-expansion=0`; it did not show an accidental
`-g` debug build. A GCC precompiled header of a wrapper including the
installed `gambit.h` built successfully (9.6 MiB). But the real generated
`howto-verify~0.c` did **not** use it: GCC `-H` marked the `.gch` with `x`,
and `-Winvalid-pch` reported `not used because '___GLOCOUNT' is defined`.
The generated C defines `___VERSION`, `___MODULE_NAME`, symbol/global/
label counts, and other per-module macros before including `gambit.h`.

This is not a flag-order accident that a Justfile tweak should hide. A
shared PCH would require splitting Gambit's header into genuinely invariant
and per-module portions, an upstream C-header architecture change. The
representative small module's GCC time report attributed only 0.06 of
0.39 compiler seconds to preprocessing; even a hypothetical complete
removal of that work is too small to explain the package tail. The attempted
PCH path took 0.85 s versus the ordinary ~0.34–0.54 s atomic range, but
because GCC rejected the PCH, those timings do not constitute a valid
performance A/B.

Decision: do not add PCH setup, a local header split, or another cache layer.
Keep the optimization target on code generation and native work common to
many modules, with equivalent runtime and adjacent uninstrumented dual-
consumer gates. Preserve the D851 release hold and the package silence gate.
