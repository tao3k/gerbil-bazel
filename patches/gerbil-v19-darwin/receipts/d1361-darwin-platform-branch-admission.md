# D1360-D1362: Admit Platform Hypotheses Against Actual Branches

## Scope

The user requires Darwin-platform mechanisms, not generic optimization with
a Darwin enable guard. This audit uses original GNU GCC 16.2, the existing
Bazel-discovered SDK environment, original installed Gambit headers and
original source. It preprocesses six inputs; it neither generates candidate
machine code nor repeats MCP timing or the Native loader experiments.
No production Gambit, consumer, std/make or std/test source is changed.

## Source Identity

The canonical source remains https://git.cons.io/mighty-gerbils/gerbil.git.
A fresh read-only remote query confirms v0.19-staging at
1cfb032c7a1612637da6205f5f8a15683eba3ba0, matching D935. Its Gambit pin remains
ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f.

An initially mistaken query of the GitHub mirror returned
0c276b3b12c5f277ab5697c711c370cf377c6a21. Its July quasiquote commit precedes
the canonical checkout's later commits. The statement that official staging
had updated was withdrawn before any toolchain replacement. The fresh clone
in .data/d1362-latest-staging-source is a stale-mirror diagnostic, despite its
directory name; it is not admitted as the latest source or a build input.
Do not silently switch the canonical remote to that GitHub mirror.

## Actual Preprocessor Results

D1360 fails before preprocessing because sandboxed sysctl memory discovery is
denied. D1361 reruns only this read-only audit with host discovery permitted.
All six preprocessing commands exit zero. The GCC macro is 16 and __clang__
is absent. The generated stx input is inspected with both original object and
dynamic definitions; os_base, os_time, mem and setup use HAVE_CONFIG_H and the
original configured headers. These are branch-admission checks, not a claim
that all runtime compile commands or execution frequencies were remeasured.

| Proposed platform mechanism | Actual original branch | Decision |
| --- | --- | --- |
| TLS lookup or emutls at every processor-state access | SINGLE_THREADED_VMS; GET_REAL_PSTATE directly addresses the pstate; getter/setter branch absent | Reject this mechanism for current configuration |
| BSD libc setjmp signal-mask cost | SETJMP expands to __builtin_setjmp in all six inputs | Reject libc setjmp substitution as the fix |
| Executable heap allocation and cache invalidation for ordinary Scheme wrappers | SUPPORT_LOWLEVEL_EXEC absent; alloc_mem_heap delegates to ordinary allocation | Reject treating every Scheme allocation as a JIT mprotect/cache-flush operation |
| Monotonic-time fallback through expensive wall-clock conversion | os_time selects mach_absolute_time directly | Reject that fallback hypothesis |

Source links within the pinned tree: include/gambit.h.in lines 1641-1655 and
8622-8627; lib/os_base.c lines 445-475; lib/os_time.c lines 300-355; lib/setup.c
lines 1613-1627. USE_mmap is present in runtime OS headers, but its presence
alone does not imply that ordinary movable-object allocation takes that path.
The unsupported execution branch is the necessary additional condition.

The existing D1102 self-cycle table contains mach_absolute_time at 0.006426%
and its dyld stub at 0.006354%. No matching emutls, icache, mprotect,
sigprocmask or timebase self-symbol row is present in this selected summary.
Missing rows are not proof of zero calls, and these self-cycle percentages
are not a new whole-startup or OS-only attribution. They do not support
promoting a clock-frequency cache as the major solution.

## Platform References and Remaining Work

[GCC's TLS internals](https://gcc.gnu.org/onlinedocs/gccint/Emulated-TLS.html)
describes control-object lookup for emulated TLS; the current pstate branch
does not use it. [Linux setjmp documentation](https://man7.org/linux/man-pages/man3/longjmp.3.html)
explains BSD/System-V signal-mask differences; current compiler builtins make
that libc distinction irrelevant to these SETJMP expansions.

[Apple's dynamic-linking presentation](https://developer.apple.com/videos/play/wwdc2022/110362/)
describes startup page-in linking versus fixups performed inside later dlopen.
It remains a valid platform research input, but applicability to the installed
OS must not be assumed solely from a 2022 presentation. D1194-D1195 already
provide Native loader evidence and D1207/D1267-D1270 already delimit the
remaining MCP execution problem. No repetition or promotion of failed packing
or RTLD_LOCAL experiments follows from this audit.

Next platform research must resolve an actually executed Darwin boundary or
a Darwin GCC code-generation difference in the recorded macro workload.
The CI comparison uses Darwin AArch64 and Linux x86-64 releases, so its timing
ratio alone cannot assign the entire difference to the kernel, libc or CPU.
No generic PEA, TLS, setjmp or JIT-memory patch is admitted here. Actual MCP
first-log/full-build and complete concurrent tests remain unqualified; the
full objective is active. All owned commands are terminal.

Private source hashes, macro outputs and terminal report:
.data/d1361-darwin-platform-branches. Failed initial report:
.data/d1360-darwin-platform-branches. Existing CPU evidence:
.data/d1102-original-mcp-cpu-profiler/cpu-summary.json.
