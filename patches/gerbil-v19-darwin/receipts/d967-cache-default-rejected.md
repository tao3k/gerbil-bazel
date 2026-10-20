# D967 Default Cache/Heap Candidate Rejected

Scope: Gambit `os_thread.c` only, Darwin/GNU only, unchanged consumer flags.
No release patch or baseline installation changed.

The generic Darwin L2 cache key reports 4 MiB on this heterogeneous Mac,
while `hw.perflevel0.l2cachesize` reports 16 MiB. Using the larger key changes
the existing default minimum heap from 2 MiB to 8 MiB. This hardware fact is
not proof that the default heap causes the startup delay.

The first implementation misread the 32-bit sysctl value as an 8-byte value;
its branch was inactive. Its timing observations cannot qualify the candidate.
The corrected implementation passes GNU syntax, runtime relinking and imports,
and a native query confirms the intended 16 MiB cache / 8 MiB minimum heap.

All four paired runs prepare the same 187 MCP modules and exit successfully:

| Order | Runtime | User CPU (s) | Wall (s) |
| --- | --- | ---: | ---: |
| A | Original | 4.608628 | 5.006488 |
| B | Candidate | 5.660729 | 9.565880 |
| B | Candidate | 5.734461 | 7.785426 |
| A | Original | 4.666294 | 5.138948 |

Candidate mean user CPU is approximately 22.9% higher. The candidate is rejected.
An official clean/build observation reaches the candidate's first actual compile
at 6.446 seconds; a fresh original observation takes 15.594 seconds and fails
the strict progress gate. These highly variable wall observations do not reverse
the paired CPU result. Both builds were deliberately stopped after observation,
so neither is a complete build/test result.

Evidence: `.data/d967-cache-width-build/`,
`.data/d967-cache-width-mcp-cpu/`, `.data/d967-cache-first-compile/`,
`.data/d967-current-control-first-compile/`.
