# D1365: Darwin mechanism research gate

## Scope correction

The requested research is Darwin-specific platform optimization, not a
general Scheme/compiler optimization enabled only on Darwin. Worker/wrapper,
partial escape analysis and continuation specialization do not satisfy that
criterion without a demonstrated platform mechanism. They are not the next
main experiment. Apple CPU behavior alone is also not an OS-specific cause.

No production source is changed, no new toolchain is built, and no speedup
is qualified by this receipt. Existing build/test and rejected-candidate
receipts remain authoritative; there is no new workload baseline campaign.

## Platform reference and its limit

[Apple's WWDC 2022 linking session](https://developer.apple.com/videos/play/wwdc2022/110362/)
distinguishes launch-time page-in linking from later dlopen fixups.
[Apple's published dyld Loader.cpp](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/Loader.cpp)
provides the source-level boundary: setUpPageInLinking gates kernel-assisted
linking on initialization/configuration/sandbox state and otherwise assigns
ranges to in-process processing. This published main-branch source is not
identity-matched to the installed OS. It corroborates a platform mechanism,
not the cost distribution of the current MCP first-log window.

These are platform technical references, not peer-reviewed papers. No
Darwin-specific paper establishing a several-fold fix for this workload has
been identified. A general allocator or compiler paper is not a substitute.

## Original-object evidence

The retained D1365 diagnostic joins original-object instructions to existing
D1102 sampled PCs via D1104 mappings and validates original text identity.
It does not collect new timings. Its report is under the durable local
`.data/d1365-darwin-label-relocations/` directory.

| Original unit | Host labels | Absolute object relocations in label table | Raw table bytes |
| --- | ---: | ---: | ---: |
| expander core | 1,665 | 1,665 | 14,632 |
| expander stx | 502 | 502 | 4,664 |

These are ARM64_RELOC_UNSIGNED records in relocatable objects, not a census
of final linked-image dynamic fixups or measured dyld time. The linker and
final image must be checked before asserting runtime fixup coverage.
GCC's [labels-as-values documentation](https://gcc.gnu.org/onlinedocs/gcc/Labels-as-Values.html)
describes relative label tables, but that technique itself is general.
It is only a candidate mitigation if linked Mach-O evidence and the existing
relevant-workload cost support the Darwin mechanism above.

D1363 and D1364 failed census assertions because the table-size calculation
initially omitted multiple INTRO zero slots. D1365 counts all INTRO slots
and the terminal zero; both units pass. These failures remain local records.

Sampled PCs frequently land on load/store instructions. That is not exclusive
instruction cost, memory-stall evidence, or proof of Darwin causality. It
does not authorize a cache/prefetch rewrite.

## Allocation admission boundary

Original Gambit mem.c documents small-object allocation by incrementing the
heap pointer inside retained msections. Therefore the large number of Scheme
temporary objects does not imply one Darwin malloc call per object.
The existing D1102 self-cycle rows matching malloc/calloc/bzero/madvise/
vm_allocate/munmap sum to approximately 0.0266 percent. This narrow symbol
selection is not inclusive allocator time, kernel fault time, or a complete
VM census; it cannot rule out all VM costs. It does not support admitting
malloc replacement as the major-cost optimization either.

## Required next gate

A candidate must name the Darwin mechanism, identify its relevant recorded
cost, state the Gambit-owned mitigation and explain why previous rejected
candidates do not already cover it. For label tables, final-image fixup
coverage and cost admission precede any compiler/runtime prototype.
No existing loader/packing result is promoted into a solution for the MCP
7-8 second first-log delay. Linux behavior, GNU GCC and consumer source
ownership remain unchanged.
