# D1748: original B already has sequential GC forwarding

The historical D1513 B / D1510 line remains selected. No production change
or new acceleration is admitted.

D1745 constructs an isolated native binary using the original B carrier,
module objects and runtime archive, with a separately compiled mem.o linked
ahead of the archive. It proposes a Darwin/GNU-only single-processor bypass
at the two GC forwarding CAS sites. GNU compilation, native linking,
framework imports and an actual GC complete. The original inputs are unchanged.
Construction success does not establish that the proposed branch is active.

D1746 launches twelve hardware-derived concurrent original/candidate graph
tests. All twelve fail the requested 1-2-1 processor transition: the first
single-processor graph phase passes, but the request for two processors stays
at one. These failures are retained, not converted to passes or omitted.
No multi-processor fallback or full graph-suite qualification is established.

D1747 preprocesses the actual mem.c compilation command from the retained
makefile, with its real includes and defines. It confirms GNU GCC 16,
Apple/Mach, SINGLE_THREADED_VMS and MAX_PROCESSORS=1. The proposed bypass is
therefore inactive: the original marker already uses non-atomic forwarding.
The configured command's historical enable-smp text is not evidence that SMP
is active. No performance benchmark is run for this inactive candidate.

The D1745 controller now checks the actual preprocessing path before native
construction and refuses an inactive proposal. Its retained first receipt
records construction only; D1747 controls algorithm eligibility. No existing
receipt is rewritten. There is no new startup, complete-build or test speedup.

This excludes GC forwarding synchronization as the selected B line's major
cost. The existing marker copying/scanning and allocation costs remain, and
must not be conflated with eliminated CAS work. Existing stride/traversal
negative results remain applicable. Full toolchain integration and real
performance acceptance are still open.

Evidence: `.data/d1745-single-processor-gc-native/`,
`.data/d1746-gc-contract/`, `.data/d1747-active-gc-macros/`.
