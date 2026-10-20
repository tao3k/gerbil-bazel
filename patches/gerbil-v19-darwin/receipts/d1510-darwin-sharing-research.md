# D1510 Darwin Sharing Research

Source research only. No production patch, benchmark rerun, speedup admission
or new baseline. Historical cold builds remain 47.771713, 47.824226 and
47.927094 seconds. Whole-task gates remain first log 5 seconds, cold build
50 seconds and complete test 112 seconds. The later strict test waves remain
DENY, not complete-suite passes.

## Existing Evidence Selects The Search

Use the existing interface, loader CPU and process-budget receipts. Do not
repeat the Linux comparison, reader census or failed flag/packing experiments.
Macro expansion is the recorded expensive phase; attributing that phase to
Mach-O fixups alone would still require evidence of the actual executed path.
The phase label and the operating-system mechanism are different claims.

## Platform Mechanism Verified In Another Runtime

[V8's Darwin platform implementation](https://github.com/v8/v8/blob/main/src/base/platform/platform-darwin.cc)
implements `OS::RemapPages` using `mach_vm_remap`, with page-aligned ranges,
fixed destination overwrite, `copy=FALSE`, failure reporting and destination
verification. It remaps rather than copying data. This is a concrete Darwin
backend, not an assertion that Gambit's current loader performs a removable
copy. These references are moving upstream sources, not the installed host's
exact revisions.

[V8 embedded builtins](https://v8.dev/blog/embedded-builtins) explains the
representation prerequisite: generated code must avoid embedded isolate and
heap addresses before executable pages can be shared across processes.
Existing Gambit native providers already reuse native code; embedding it
again is not a new candidate.

[V8 static roots](https://v8.dev/blog/static-roots) describes compile-time
construction of immovable, immutable roots, using addresses relative to a
reserved heap base. This requires a dedicated representation and address
contract, not merely marking arbitrary Scheme values `const`.

[The current read-only deserializer](https://github.com/v8/v8/blob/main/src/snapshot/read-only-deserializer.cc)
still copies raw segments, decodes tagged references when static roots are
disabled and resolves external references. A snapshot is not automatically
zero-copy or zero-initialization. Its runtime contracts must be transferred
explicitly, not inferred from the name.

## Actual Gambit Constraints

The retained `src/gambit/lib/setup.c:1522` `setup_module_fixup` mutates module
flags and tables. It interns global/symbol/keyword names, aligns object tables
and rewrites pair/subtyped references through `fixrefs`. The generated table
definitions in `include/gambit.h.in:8912` are writable arrays. Permanent GC
storage is not equivalent to proven language-level immutability.

Consequently, a shared-page candidate would first need a representation that
separates immutable payload from process/VM-specific symbol, global, label and
binding state. Remapping the current writable tables with `copy=FALSE` would
share mutations and is not acceptable. Nor may module setup, identity checks,
GC-root registration, lazy evaluation or errors be skipped.

Existing loader CPU measurements constrain this proposal: native registration
is a measured sub-boundary, not the entire Scheme expansion budget. Existing
import-binding evidence requires fresh contexts and mutable binding state.
Neither shared initialized contexts nor the rejected raw-AST restoration is
rehabilitated by the V8 references. No shared-heap implementation is admitted
without a substantial reached budget and those contracts.

## Two Attractive But Inapplicable Shortcuts

This review ran `otool -l` on the retained
`.data/d1510-reader-whitespace-native-v2/gerbil`. It already contains
`LC_DYLD_CHAINED_FIXUPS` (8,608 bytes). Merely enabling chained fixups cannot be
claimed as new work. Its `__text` is 22.826 MiB and writable `__data` is
46.053 MiB; section size is not resident size, dirty-page count, macro time or
an optimization budget.

[Current dyld Loader source](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/Loader.cpp)
also distinguishes kernel page-in linking from its in-process fallback and
restricts page-in linking after libSystem initialization. It cannot remove
Gambit's later Scheme execution or registration by changing a linker flag.
The already recorded page-in-linking investigation stays closed.

[The BOLT paper](https://arxiv.org/abs/1807.06735) reports substantial
profile-driven layout gains for other compiler binaries. However,
[BOLT's supported input contract](https://github.com/llvm/llvm-project/blob/main/bolt/README.md)
specifies X86-64/AArch64 ELF binaries. It is not a drop-in optimizer for this
Mach-O executable, and its reported ratios are not Gambit predictions.
Previously rejected layout/packing routes remain rejected.

## Mainline Decision

The reusable architectural lesson is to avoid reconstructing demonstrably
immutable runtime material while retaining fresh mutable instances. The
Darwin remapping implementation shows a platform backend, not a demonstrated
Gambit opportunity. First establish the exact eligible payload and its cost
inside existing reached expansion/evaluation boundaries. Only a distinct,
large-budget mechanism should proceed to a Darwin-only GNU GCC candidate.
No additional unchanged cold/full-test campaign was run for this research.
