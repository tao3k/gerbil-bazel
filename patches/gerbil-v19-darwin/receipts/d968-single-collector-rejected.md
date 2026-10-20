# D968 Single-Collector Batching Rejected

Objective remains reduction of MCP's first actual compilation latency, not
earlier artificial progress, changed consumer flags, or native C compilation.
The immutable D935 runtime and MCP inputs remain unchanged.

## Source Hypothesis

Gambit `mem.c` normally completes heap chunks at `___MSECTION_CHUNK`
(approximately 1 KiB in this build), queues completed chunks, and issues two
publication barriers and one dequeue barrier. These barriers remain present
in native ARM code even in the single-threaded VM configuration.

The isolated candidate requires Darwin, GNU/non-Clang and
`___SINGLE_THREADED_VMS`. It ends chunks at the existing allocation limit and
omits only these three inter-collector barriers. Original end markers, FIFO
links, scanning, forwarding and allocation boundaries remain. Other targets
and multi-threaded VM builds retain the original path. It does not change heap
size, collection frequency policy, or Gerbil sources.

## Result

Original and modified C syntax pass with actual GNU GCC 16. The selected RTS
object, archive and native Gerbil relink pass; the original GSC is unchanged.
All four runs prepare the same 187 real MCP modules and exit zero:

| Order | Runtime | User CPU (s) | Wall (s) |
| --- | --- | ---: | ---: |
| A | Original | 4.568239 | 5.041478 |
| B | Candidate | 4.698379 | 5.083283 |
| B | Candidate | 4.767894 | 5.181444 |
| A | Original | 4.698419 | 5.184757 |

Candidate mean user CPU is approximately 2.15% higher. The candidate is rejected,
not promoted or added to the patch stack. These are preparation diagnostics,
not official full build/test or first-compilation results. An expensive full
toolchain rebuild and further correctness qualification are not warranted for
a candidate that fails this execution-cost gate.

Evidence: `.data/d968-original-syntax/`, `.data/d968-single-collector-build/`,
`.data/d968-single-collector-cpu/`, `.data/d968-single-collector-source/`.

## Remaining Source Boundary

Read-only inspection of the original Gerbil source and generated GVM code shows:

- `expander/core.ss` `core-context-resolve` repeatedly calls `hash-get`, following
  parent contexts on a miss. Tables and contexts are mutable.
- Generated `runtime/hash.scm` `hash-get` calls `cast`, then `__hash-get` reads
  receiver slot 1 and method slot 8 and performs a generic procedure call.
- `runtime/interface.ss` `cast` calls `class-of`. An already matching interface
  returns the original object without a wrapper allocation; raw-object casts
  can copy a prototype and invoke different failure paths.
- `runtime/mop.ss` `class-of` reads a mutable procedure vector. The usual
  structure branch tests the class descriptor before returning it, while other
  branches can initialize class caches or call shadow-class logic.
- The existing native-address counts identify high-frequency edges, not their
  CPU share and not a guarantee of unique Scheme procedure identity.

Consequently, an unconditional resolution cache or direct interface bypass
would not preserve the original contracts. A larger Gambit-only candidate would
need generic guarded call-chain specialization: verify live bindings and actual
procedure identity, preserve method dispatch and original fallbacks, and retain
valid safepoints/GC roots. This is an investigation direction, not implemented
capability, proof of speedup, or qualification of the seven-to-eight-second gate.
