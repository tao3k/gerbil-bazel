# D1510 Scheme Loader Architecture References

## Retained Evidence

Historical cold builds remain 47.771713, 47.824226, 47.927094 seconds;
first compile logs remain 4.850866, 4.573628, 4.592897 seconds.
The complete 39-file/965-case test passed in 105.750982 seconds. The later
112-second strict run is DENY/incomplete, not a stable full-test qualification.
This source review introduces no production change or measured speedup.

## Comparative Implementations

[Guile's object-file documentation](https://www.gnu.org/software/guile/manual/html_node/Object-File-Format.html)
describes an ELF container on all platforms, handled by Guile's own loader,
not the platform ELF loader. Read-only mapping, a small writable region,
GC-root registration and separate initialization/entry thunks are explicit
parts of the format. This separates Scheme artifact loading from operating
system shared-library loading; it is not evidence of a Darwin speedup here.
Replacing Gambit's C backend with Guile bytecode is not an admitted candidate.

[Chez's implementation overview](https://github.com/cisco/ChezScheme/blob/main/IMPLEMENTATION.md)
describes compiled `.so` files as FASL, not OS shared libraries. Its vfasl
representation is near the loaded memory representation and streamlines
linking/interning; normal boot builds do not automatically select vfasl.
The thread context is held in a dedicated machine register during Scheme
execution, synchronized at relevant C boundaries. These are architectural
comparisons, not drop-in GNU GCC options for Gambit.

[Chez's FASL reader](https://github.com/cisco/ChezScheme/blob/main/c/fasl.c)
documents explicit format version/machine type, graph definitions/references,
code objects and relocation entries. This is substantially different from
serializing arbitrary expanded Gerbil ASTs. The rejected AST/symbol-evaluator
candidates remain rejected; this reference does not rehabilitate them.

[GCC's emulated TLS implementation](https://github.com/gcc-mirror/gcc/blob/master/libgcc/emutls.c)
contains per-thread lookup and first-use allocation/registration paths.
[GNU's Darwin libgcc change](https://gcc.gnu.org/pipermail/gcc-patches/2021-November/585066.html)
also documents DSO emutls exports and weak definitions. Neither establishes
that the retained Gambit VM access path calls that helper. D1361 found the
retained SINGLE_THREADED_VMS branch excludes its pstate TLS getter. Reopening
TLS requires evidence from the selected artifact's actual instructions and
configuration, including multiple-VM behavior, not a generic TLS assumption.
The referenced moving GCC sources are not the exact installed GCC 16 revision.

## Platform-Related Paper, With A Bounded Claim

[Optimizing Function Layout for Mobile Applications](https://arxiv.org/html/2211.09285v1)
evaluates real iOS binaries and startup page faults. Its production comparison
reports 4.2% average and 2.9% p99 cold-start improvement for SocialApp; the
authors acknowledge concurrent release changes and repeat alternations.
The pipeline uses LLVM 14 and linker function orders. It is neither a
GNU GCC implementation nor a macOS Scheme result. The paper notes that
multiple images add rebase/rebind page faults that function layout alone does
not remove. This supports distinguishing image loading from code locality,
not claiming a several-fold improvement. Layout is secondary, not the next
mainline experiment; existing rejected packing/GOT/relative-label routes stay
closed.

## Transfer To The Existing Successful Line

The useful common idea is separating artifact transport, runtime linking and
semantic initialization. Existing native providers already bypass the ordinary
OS dynamic-load backend on an admitted hit; blindly repeating image packing
is not a new architecture improvement.

The constructor in tests/build_embedded_provider_candidate.py currently emits
path/name/digest/entry rows. Its lookup scans rows and hashes the original
native image before accepting an entry. This preserves provenance but shows
that a provider hit is not zero-cost. No path-only acceptance, skipped digest,
mtime-only trust or package-specific lookup is proposed. The selected frozen
binary must be checked before attributing this constructor's costs to it.

Next admission should split the already reached native-load boundary into:

1. Path resolution and provider identity verification.
2. Actual OS mapping/binding on fallback, versus provider entry acquisition.
3. Gambit runtime registration, allocation and module initialization.

The standard-library observations in d1510-gambit-eval-platform-boundary.md
reach this boundary but do not split it yet. A replacement must preserve
demand order, phase identity, exceptions, cycles, GC roots and multiple VMs.
Instrumentation must first demonstrate that the retained artifact executes
the proposed expensive path. Do not optimize by import-call count or equate
load-module elapsed time with pure dyld time.

Only then is a Darwin/GNU GCC-only candidate on the retained line admissible.
Use independent standard-library build/test coverage plus the unchanged full
benchmark inventory; retain the first-log/build/full-test gates of 5/50/112
seconds. No compiler switch, MCP-specific provider selection, suppressed
initialization or relaxed correctness condition is permitted.
