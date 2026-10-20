# D1510 Darwin Heap Page Source Boundary

Read-only audit. No heap-size, collector, allocation, compiler or runtime
candidate is admitted. The retained 5/50/112-second acceptance gates remain.

## Actual System And Configured Source

The native `getconf PAGESIZE` query returns 16,384 bytes. The retained `mem.h`
defines MSECTION_SIZE as 131,072 words; with its eight-byte word profile this
is 1,048,576 bytes, exactly 64 system pages. This is the configured payload
size, not a proof that malloc's container/base is page-aligned or that there
are no page faults, TLB costs, allocator overheads or cache conflicts.

`alloc_mem_aligned_aux` preserves the original allocator container before the
aligned pointer and accepts a word-based multiplier/modulus. Normal msection
growth requests multiplier 1 and modulus 0. It does not encode a presumed
4-KiB system page or implement a custom Mach page allocator. Do not construct
a page-size mismatch candidate on that premise.

## Executed Allocation Object

The configured `include/config.h` leaves SUPPORT_LOWLEVEL_EXEC undefined.
The source consequently uses ordinary allocation for `alloc_mem_heap`, rather
than the separate code-memory mmap/mprotect branch.

This branch is independently verified in the actual original `os_base.o`:
`alloc_mem_heap` is a single AArch64 branch instruction at object text offset
0x100, and its BRANCH26 relocation targets malloc. Raw disassembly prints a
self-looking unresolved branch; the relocation is required to identify its
target correctly. The object is byte-identical to the os_base.o member of the
retained libgambit.a, verified by ar extraction and cmp.

- Object SHA256: `919af380aaab8ebafc9bd8cfe2748d39b1ad0d4dabc4f65529bb315c58f07167`.
- RTS archive SHA256: `fd3725c9cc68525efbd8c0385f242f72334de37d5c56a96fd7db8666bb873501`.

The presence of mmap/mprotect symbols elsewhere in the object does not make
that code-memory path the ordinary Scheme heap path. This does not prohibit
future allocator research; it excludes the alleged executable-heap penalty
from these configured inputs.

## Sorted Section Lookup

`find_msection` performs binary search. Its normal call site is heap-section
expansion; the other two source calls are in old-object consistency validation.
The marker's validation call is conditional on ENABLE_CONSISTENCY_CHECKS.
There is no unconditional per-object section search in the ordinary marker
body. Pointer-array shifts during section insertion still exist; no reached
address-order census or CPU budget has been established for them. Do not
assume Darwin malloc address order makes this a dominant runtime cost.

## Missing Hardware Evidence

The existing CPU Counters export contains bottleneck classifications, not
measured L1 miss counts. An attempt to inspect Instruments event configuration
through native app control times out twice without returning application state.
No event selection, template or new counter recording is verified. This is
an unavailable observation route, not a live-process wait, cache-miss result,
permission to use guessed CLI flags or evidence for a prefetch candidate.

Authoritative inputs: retained Gambit mem.c, mem.h, os_base.c, include/config.h,
original os_base.o and RTS archive under `.data/d1391-runtime-object-source/`.
No cold build or complete test was newly run for this source audit; historical
47-second MCP and complete-test anchors remain separate from current evidence.
