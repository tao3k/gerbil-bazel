# D1510 Platform Literature Transfer Gate

The active optimization goal retains the verified 47.771713/47.824226/
47.927094-second cold anchor and first-log/build/full-test limits of 5/50/112
seconds. No gain, new baseline or completed toolchain follows from this review.
Existing Scheme-expansion cost evidence is the starting point, not a request
for another Linux benchmark campaign. Scheme expansion execution and GCC C
preprocessing remain different stages.

## References Beyond Scheme Implementations

[LLD for Mach-O: The Journey](https://llvm.org/devmtg/2022-05/slides/2022EuroLLVM-LLD-for-Mach-O.pdf)
is a 2022 compiler-engineering presentation, not a peer-reviewed paper.
It explains Mach-O embedded relocation addends interfering with identical
code folding and describes selective section copying instead of indiscriminate
copy-on-write mapping. The reported linker comparison is not total compilation
or Scheme expansion. It cannot explain a first log before C compilation starts.
Using this reference does not authorize switching away from GNU GCC.

[Swift's relative metadata discussion](https://forums.swift.org/t/making-the-value-witness-table-reference-relative/1206)
and [relative pointer implementation](https://github.com/swiftlang/swift/blob/main/include/swift/Basic/RelativePointer.h)
show a concrete tradeoff: fewer absolute metadata pointers can allow read-only
representation, but ARM address reconstruction and cross-image references have
costs and limitations. The discussion is a design proposal, not proof every
proposed representation shipped or that it accelerates Gambit.

[Go 1.26's linker changes](https://go.dev/doc/go1.26)
remove the text-start pointer from pcHeader, eliminating relocations in that
metadata section. The release notes explicitly distinguish ELF and Mach-O
section naming. This is a real metadata representation change, not evidence
of a Darwin-specific several-fold startup win. Gambit has different label,
object, GC and module-layout contracts; Go metadata cannot be copied wholesale.

[From Dynamic Loading to Extensible Transformation](https://www.usenix.org/system/files/osdi22-ren.pdf)
is an OSDI 2022 paper on iFed. Its loader passes combine library placement and
relocation branch elimination. Evaluation runs on Linux/openEuler with glibc,
not Darwin. Its instruction rewriting and hugepage assumptions do not transfer
to signed Mach-O text or the installed arm64 superpage interface. It also
reports increased pre-main loading overhead: faster steady execution does not
automatically mean faster cold startup. A paper with positive runtime results
is not sufficient to admit a startup optimization.

[GCC's tail-call hook documentation](https://gcc.gnu.org/onlinedocs/gccint/Tail-Calls.html)
explains ABI/PIC restrictions on C sibling calls. That does not prove a hot
Gambit Scheme call becomes a C sibling call. The retained header maps
JUMPGLONOTSAFE through label entries and JUMP, whose label-value branches use
computed goto and a separate external-host exit. No missing Darwin sibling
optimization is established by reading the hook documentation. Published GCC
main is not the exact installed Darwin fork; no compiler flag or ABI rewrite
is admitted on that source alone.

## Apply To Executed Costs, Not File-Format Names

The admissible question is which platform cost survives in the selected
macro-expansion hot path, not whether Mach-O generally has overhead:

1. Cross-image branch indirection: D1369 already proves the inspected core/stx
   GOT pairs relax in the linked image. iFed does not reopen this rejected
   visibility/GOT route for those hosts.
2. Label-table relocation: D1366 already rejects rewriting those tables as
   the major startup fix. Swift/Go references do not change that cost coverage.
3. Native loading/registration: the new loader diagnostic separates digest,
   fallback dlopen and runtime registration. It does not establish a large
   removable budget, and its cold host fails the 5-second first-log gate.
4. Compiler/linker work: Mach-O linker improvements occur after expansion.
   They may matter to complete build, but cannot be labeled a cure for the
   initial Scheme macro-expansion interval.
5. Thread/VM access: actual selected branch evidence, not another runtime's
   TLS implementation, controls eligibility. D1361/D1748 exclude the retained
   TLS getter/GC CAS hypotheses; multiple VM configurations need their own
   artifact evidence.

A metadata candidate outside those closed routes would first need a distinct
executed table/operation, its actual time coverage, and a compatible GC,
registration and error contract. A high relocation count or large object file
alone does not qualify it. Architecture research continues under the active
goal; these references are not promoted into untested production patches.

## Additional Darwin Runtime Implementations

[Go's Darwin memory backend](https://github.com/golang/go/blob/master/src/runtime/mem_darwin.go)
uses anonymous mmap for allocation and paired MADV_FREE_REUSABLE /
MADV_FREE_REUSE operations for unused/reused pages. Its comments distinguish
kernel accounting from reclamation; needZeroAfterSysUnusedOS returns true.
The huge-page hooks in this implementation are empty. This is concrete
platform-specific memory lifecycle handling, not a published startup speedup
or evidence that a huge-page switch is available on the selected host.

[OpenJDK's BSD/Darwin memory backend](https://github.com/openjdk/jdk/blob/master/src/hotspot/os/bsd/os_bsd.cpp)
separates executable mappings from ordinary memory. On Apple, executable
commit preserves MAP_JIT mappings using mprotect rather than replacing them;
executable uncommit uses MADV_FREE and mprotect. Ordinary uncommit can replace
the region with a PROT_NONE mapping. These branches preserve runtime contracts;
their existence is not evidence of a several-fold compilation gain.

The retained Gambit source was checked at lib/os_base.c:188-238, 320-475 and
lib/mem.c:554-602. Ordinary aligned heap sections delegate through
___alloc_mem_heap to ___alloc_mem and malloc when SUPPORT_LOWLEVEL_EXEC is
absent. D1361 already verifies that absent branch with the selected GCC
preprocessor. USE_mmap alone does not put the macro-expansion heap on the JIT
path. Do not copy MAP_JIT protection or page-reuse operations onto malloc-owned
blocks, and do not reopen the rejected heap-floor or superpage experiments.
A separate section allocator would require matched allocation/free ownership,
alignment, failure and GC contracts plus actual cost coverage before a build.

[The Structure and Performance of Efficient Interpreters](https://jilp.org/vol5/v5paper12.pdf)
(Ertl and Gregg, 2003) studies indirect dispatch and branch prediction. Its
GNU C labels-as-values mechanism is relevant to reading Gambit's generated
control flow, but it is not a Darwin or Apple Silicon experiment. Its simulated
prediction comparisons cannot be used as a Gambit speedup forecast or a reason
to repeat the rejected jump/dispatch candidates. In particular, a CPU mechanism
must not be relabeled as a demonstrated Mach-O or Darwin kernel cause.

These additional references are research inputs only. No runtime source,
consumer, baseline binary, timing receipt or performance gate was changed.

## Darwin ABI And Compiler Transfer Audit

[GCC support for the Darwin AArch64 ABI](https://lpc.events/event/11/contributions/1011/contribution.pdf)
is the one-page abstract for a 2021 Linux Plumbers lightning talk, not a
performance paper. The associated
[GNU implementation proposal](https://gcc.gnu.org/pipermail/gcc-patches/2021-November/584338.html)
distinguishes naturally aligned named stack arguments from word-aligned
variadic arguments. The proposal explicitly says it was not ready for trunk;
it must not be treated as the selected compiler's current implementation or
as an optimization result.

The retained Gambit header's `___BEGIN_COD` defines a host function with one
fixed processor-state parameter. `___CALL_LABEL_HOST` passes that state;
`___JUMPGENNOTSAFE` and the label-value `___JUMPFAST` path select Scheme label
entries and computed gotos. Scheme rest arguments therefore cannot be
identified with C ABI variadic arguments from their source-level arity alone.
FFI/library calls remain separate boundaries. This audit does not measure
spill cost or exclude every ABI effect; it supplies no justification for a
varargs ABI rewrite of the macro-expansion path.

[GCC 12's optimization documentation](https://gcc.gnu.org/onlinedocs/gcc-12.1.0/gcc/Optimize-Options.html)
warns that computed-goto programs may execute faster without GCSE. It also
describes early factoring and late duplication of computed jumps, trading
compiler complexity against dispatch layout. These are GNU mechanisms, not
Darwin-specific performance results. D897 already investigated the explicit
optimization override losing `-fno-gcse`; D1380 already rejects the default
low-optimization restoration. Do not turn this documentation into another
flag sweep or reopen those experiments. Source-level inline jumps alone do
not prove the final compiler preserved every dispatch site.

[Reverse Engineering the Apple M1 Conditional Branch Predictor](https://arxiv.org/abs/2502.10719)
is platform-relevant research, but addresses conditional-branch predictor
aliasing and Spectre mistraining. It does not benchmark Gambit, optimize
Mach-O loading, or establish the cost of Gambit's indirect dispatch. An Apple
CPU result is also not automatically a Darwin kernel result. No branch-layout
candidate or speedup forecast follows from this paper's abstract.

The existing native fixup-detail controls place JSON symbol/keyword setup at
about 48-87 milliseconds and label/frame setup at about 2-4 milliseconds.
Those registration observations are distinct from Scheme interface execution
and dyld relocations. The UTF-8 interner's apparent missing hash filter is
exactly the previously rejected D1510 symbol-key candidate, not a new route.
See `d1510-symkey-hash-filter-rejected.md` and the fixup-detail follow-up in
`d1510-native-loader-boundaries-tested.md`.

This review adds no measurements. The historical cold anchor remains
47.771713 / 47.824226 / 47.927094 seconds; strict full-test DENY remains open.
The next useful literature transfer must reduce actual shared Scheme
execution/allocation or another independently demonstrated large cost, retain
fresh module-context semantics, and differ from the recorded rejected routes.
No production edit, toolchain rebuild, baseline replacement or publication
is admitted by this audit.
