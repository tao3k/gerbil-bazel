# D1510 Mach-O Hot Page Layout Boundary

## No Baseline Or Runtime Change

Historical cold builds remain 47.771713 / 47.824226 / 47.927094 seconds,
with first compile 4.850866 / 4.573628 / 4.592897. Historical complete tests
remain 105.750982 seconds with 39 files / 965 cases passed; subsequent strict
112-second attempts remain DENY. Current hard gates stay 5/50/112. No new
clean, build, test or profiler recording was run for this layout audit.

## Reference Mechanism And Its Limits

[LLVM's function-order presentation](https://llvm.org/devmtg/2024-04/slides/TechnicalTalks/Hoag-TemporalProfiling-and-OrderfileOptimization-forMobileApps.pdf)
uses function-entry traces to reduce text-page faults in iOS applications.
[LLVM's order command](https://llvm.org/docs/CommandGuide/llvm-profdata.html)
supports a Mach-O linker orderfile.
[Apple ld64's manual](https://github.com/apple-oss-distributions/ld64/blob/main/doc/man/man1/ld-classic.1)
orders symbols/functions within sections; its source describes follow-on
constraints when objects lack subsections-via-symbols. These references do
not establish instruction-fetch pressure or page-fault cost in this Scheme
workload. The earlier iOS paper was already recorded as secondary research;
this audit does not reinterpret it as a several-fold macOS result.

The actual retained carrier, original mem.o and first renamed provider
object all have Mach-O flags 0x2000 (subsections-via-symbols). This is three
checked objects, not proof that every input is independently reorderable.
No LLVM/clang compilation or PGO collection is introduced; the runtime is
the unchanged GNU-built artifact.

## Existing Export Reanalysis

The unified counter-stacks workflow now accepts --layout. It reuses the
completed original standard-library CPU-counter recording and its time
sample export, validates exact binary SHA256/UUID/native function identity,
checks actual ASLR page alignment, and masks exported PC low bits only to
the four-byte instruction boundary. All original 513 matched-sample leaf
statistics remain exactly unchanged. It records timer-sample geometry, not
hardware cycle attribution, function-entry order or page faults.

Evidence: `.data/d1510-stdlib-counter-profile-v1/stack-layout.json`.
Page size from the host is 16384 bytes. The 335 validated native running
samples touch 68 distinct sampled native pages. The named common host is
unique in the exact image, at 0x1002f3f64; names are not used to merge
different functions into a single layout unit.

| Function | Native extent bytes | Distinct sampled PCs | Observed sampled pages | Whole-function translation lower bound |
| --- | ---: | ---: | ---: | ---: |
| gb_coalesced_host | 1059016 | 71 | 28 | 27 |
| mark_array | 1096 | 16 | 1 | 1 |
| setup_module_fixup | 2584 | 9 | 1 | 1 |
| mark_array.constprop.4 | 1060 | 12 | 1 | 1 |
| gc_hash_table_set | 428 | 6 | 1 | 1 |
| gc_hash_table_ref | 160 | 6 | 1 | 1 |

The lower bound tries every four-byte whole-function translation within a
page while preserving internal instruction offsets. It is deliberately more
permissive than actual linker placement and is not a linker recipe. Moving
the common host intact can reduce its sampled page count by at most one in
this model. It cannot compact that function's internal sampled instructions
to a few pages. This does not exclude cross-function page sharing, unsampled
code, different workloads or internal code transformations, and does not
translate a page-count difference into seconds or a speedup percentage.

An independent reanalysis with the strengthened alignment validation
reproduces the saved geometry and original correlation exactly. Layout
tests cover same-name/different-function separation, page-boundary effects,
invalid alignment/page sizes, empty native evidence and extent overflow.

## Provider Identity Check

Both retained canonical HOME and original source HOME were also checked
against all 280 original provider image hashes in the frozen manifest.
Each HOME has zero mismatches or missing images. This rules out that specific
image-drift explanation in those two directories; it does not validate all
interfaces, every fallback image or package artifacts. No file is repaired,
rehydrated or overwritten by this read-only check.

## Decision

Do not spend another cold campaign on the premise that an orderfile can
compact the common host internally. Native layout remains secondary research
without a demonstrated large removable startup budget. No orderfile, runtime
candidate or performance patch is admitted. Existing packing, GOT, relative
label, branch-layout and host-splitting denials stay closed.
