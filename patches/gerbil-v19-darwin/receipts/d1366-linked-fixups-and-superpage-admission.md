# D1366-D1367: linked fixups and installed superpage admission

## Decision

Do not implement the relative host-label-table candidate or an explicit
Darwin superpage heap as the next major-cost patch. The former lacks
relevant major-cost coverage; the latter is rejected by the installed
arm64 kernel. This is new admission evidence, not another baseline campaign
and not an acceleration claim. The original first-log objective remains
unresolved; no toolchain completion or test-speed qualification is implied.

## D1366: final-image census, not object-file inference

The diagnostic under `.data/d1366-linked-label-admission/` uses Apple's
`dyld_info -symbolic_fixups` and `-fixup_chains` on the original executable.
It checks that the SHA-256 and UUID match the retained D1102 CPU profile and
D1365 object census before inspecting the image.

Executable SHA-256:
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.
UUID: `16EB1FE7-A2A7-3FE9-8EAF-9D677087B096`.

The linked core/stx host-label tables contain exactly 1,665/502 rebases.
Both are in the main executable, not dynamically loaded images, and are
not repeated dlopen work. The executable already has chained fixups in
DYLD_CHAINED_PTR_64_OFFSET format with 16 KiB chain pages. This proves file
format, not that kernel page-in linking was enabled for the profiled run.

Across all 52 main-executable label tables, 62,393 rebases are present.
The entire image has 163,509 rebases and 160 binds. The label-table share
of rebase count is 38.16 percent; it is not a time share or a speedup bound.

## Existing CPU stack reanalysis

D1366 reuses the existing loader-stack attribution helper on D1102's retained
XML, rather than collecting another profile. Its cycle total matches the
existing summary exactly. D1102 covers passive preparation of 187 real MCP
modules, not a timed complete gerbil clean/build first-log run.

| Running cycle category | Percent |
| --- | ---: |
| dyld image self | 9.866 |
| Atlas inclusive | 9.782 |
| dlopen inclusive | 4.897 |
| Atlas inside dlopen inclusive | 4.758 |

Categories overlap and must not be added. A supplementary spelling-based
match for fixup/rebase frames gives 0.0301 percent. That subset is not
complete fixup attribution, kernel time or wall time. Neither it nor the
label census supports promoting a relative-table rewrite to a several-fold
MCP first-log solution. Existing Native-loader wins are not withdrawn, but
are not transferred to this different workload.

## D1367: installed Darwin API probe with GNU GCC

[Apple's published XNU vm_map.c](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/vm/vm_map.c)
puts the explicit SUPERPAGE_SIZE_ANY/2MB cases behind __x86_64__ and otherwise
returns KERN_INVALID_ARGUMENT. Published main is not assumed to identify the
installed kernel, so a small allocation API probe checks the local boundary.

The probe under `.data/d1367-darwin-superpage-admission/` uses GNU GCC 16,
the existing Bazel SDK discovery and an arm64/Darwin compile-time guard.
It makes three sequential API requests, each for 2 MiB; it is not a workload
benchmark, concurrency trial or TLB measurement. The ordinary allocation
and release both return KERN_SUCCESS. SUPERPAGE_ANY and SUPERPAGE_2MB both
return 4, KERN_INVALID_ARGUMENT, on macOS 26.6.1 arm64. The probe exits zero
and retains compiler output, source/binary hashes and its structured report.

No allocator ownership is changed. Ordinary memory allocation still works;
this result only rejects the proposed explicit-superpage flags on this host.
It does not rule out every possible VM optimization or explain the observed
Darwin/Linux difference. No Gambit, consumer or std/make source is edited.
