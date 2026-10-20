# D1510 Language Image Research

Research and source review only; no production change, benchmark rerun or
new speedup. Historical retained cold builds remain 47.771713 / 47.824226 /
47.927094 seconds. Gates remain first output 5, cold build 50 and full test
112 seconds. Complete-test qualification remains open.

## Search Selected By Existing Evidence

The expensive recorded Scheme expansion/import phase is the starting point.
Do not repeat the Linux comparison or reinterpret that phase label as proof
that dynamic relocation owns its time. Read the existing
[architecture transfer](d1510-interface-architecture-transfer.md),
[binding contract](d1510-import-binding-construction-contract.md) and
[Darwin sharing review](d1510-darwin-sharing-research.md) first.

## GNU Emacs: Initialization Is A Separate Artifact

[Bringing GNU Emacs to Native Code](https://arxiv.org/abs/2004.02504)
(ELS 2020, sections 4.1-4.4) separates native code, object relocation data,
environment initialization and saved-image restoration. A native library
alone does not eliminate initialization. Image dumping was extended to
restore native compilation units. This paper is not a Darwin-specific
benchmark and supplies no Gambit speedup prediction.

[Current pdumper source](https://github.com/emacs-mirror/emacs/blob/master/src/pdumper.c)
provides concrete constraints: binary fingerprints, offset-based relocation,
hot/discardable/cold regions and private writable file mappings. Its POSIX
backend explicitly accommodates macOS's older MAP_ANON naming. Even the
cold region is writable/private; cold is not a language immutability proof.
Native handles are cleared when dumping, then reopened and function addresses
resolved on restoration. Hash tables are thawed through load hooks. Neither
process pointers nor arbitrary foreign handles are blindly reused.

These details constrain, rather than admit, a Gambit image proposal. A generic
portable dumper is not intrinsically a Darwin fix. It must save substantial
reached initialization work after restoration overhead, and cannot resurrect
the rejected raw-AST or whole-context memo routes under a new name.

## Swift: Representation Before Linker Flags

[RelativePointer.h](https://github.com/swiftlang/swift/blob/main/include/swift/Basic/RelativePointer.h)
explicitly motivates relative references by startup cost and avoiding
unnecessary dynamic relocation. Direct references require linker-resolvable
offsets within the linkage unit; indirect references still need initialized
absolute slots, but can share them and improve locality. Near references also
have range and access-cost constraints.

[The type metadata ABI](https://github.com/swiftlang/swift/blob/main/docs/ABI/TypeMetadata.rst)
uses 32-bit field-relative offsets in protocol conformance records, while
retaining runtime creation for generic metadata. This is a representation
contract, not a switch that removes all initialization. These moving upstream
sources were reviewed for mechanism, not treated as the retained toolchain's
implementation or as measured Darwin/Gambit gains.

## Actual Transfer Boundary And Decision

Retained Gerbil `expander/module.ss:139` constructs a module context, expands
the interface body, retains context-bearing code and delays evaluation.
Gambit `lib/setup.c:1522` mutates registration flags and object tables.
Existing binding controls require live initialization and fresh mutable state.
There is no eligible shared initialized context established by this review.

The evidence favors investigating avoidable preparation inside actual Scheme
execution, not adding more native providers or retuning fixup flags. Existing
loader budgets do not support seconds-scale relocation savings; the binary
already uses chained fixups. Swift relative references do not reopen the
previously rejected relative-label/GOT candidates. Emacs image restoration
does not reopen phase serialization, which already lost to native execution.

A distinct candidate needs an explicit boundary: preparation moved out of
each launch versus required live imports, initializers and context creation.
It must preserve phase/order, reload and dependency invalidation, lexical
identity, mutation isolation, errors, GC roots and foreign/native lifetimes.
Darwin-only activation and a real GNU GCC implementation are mandatory;
copying Swift's C++ accessors does not establish correct GCC object emission.
Use independent standard libraries before the original clean/build/test gates.
No candidate is yet admitted: the existing residual import intervals include
observer overhead and are not a pure eligible preparation budget.

Only this research receipt was added. No sources, installed binaries, flags,
test assertions, deadlines or baseline artifacts were changed.
