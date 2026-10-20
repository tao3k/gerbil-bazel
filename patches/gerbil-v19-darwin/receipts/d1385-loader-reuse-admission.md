# D1385: loader reuse is not an admitted major-cost fix

## Source boundary

Read-only inspection uses `.data/d935-staging-source`, canonical staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, with Gambit `ea114fc3`.
No product source or consumer/std/make/std/test source changes are made.

Gerbil `src/gerbil/runtime/loader.ss`, `load-module`, already serializes the
module table. A builtin or loaded-path entry returns immediately; a loading
entry waits; failures retain the exception. Only a missing entry calls `load`.
This does not establish absence of every path alias or every duplicate native
image load, but contradicts a premise of unrestricted repeated module loading.
That loader is inspected for context, not changed.

Gambit `lib/os_dyn.c`, `dynamic_load_module`, calls `dlopen(RTLD_NOW)` and then
`dlsym` for each load request. Successful handles stay in `dl_list` until
`cleanup_dynamic_load`; there is no per-request successful `dlclose`.
Adding another handle cache has no evidence of removing repeated validation
of the same still-loaded image. Published
[Apple Loader.cpp](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/Loader.cpp)
also checks already-loaded paths and file identities before creating a disk
loader. This published source is not the installed dyld identity and is not
used to claim that every installed-loader alias check has been verified.

An exit-only unload change cannot remove the first-load `F_CHECK_LV` wait.
The existing `___DONT_UNLOAD_DYN_CODE` option is justified in source for gcov
cleanup; it is not an admitted Darwin optimization. Changing unload behavior
would require a separate destructor/embedding/reinitialization contract and
ordinary-exit evidence, not just samples of diagnostic termination.

## Actual original build-only diagnostic

The previous two strict original clean lanes failed before build. D1385
therefore explicitly sets `buildOnlyDiagnostic=true` and
`officialCleanPassed=false`. It asserts zero MCP native `.o1` images, then
invokes the actual original `gerbil build` with the original home, GNU GCC16,
Bazel environment and 12 physical cores. It is not cold clean/build admission.

This build also reaches the unchanged 10-second no-output failure gate with
a zero-byte log. No first compile or counter snapshot at that event exists;
no time or ratio is manufactured. `qualified=false`,
`performanceQualified=false` and `buildCompleted=false` remain explicit.
Original binary SHA256 remains
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.
Mach-time self-calibration passes at 0.194583542 versus 0.194584 seconds.
The process group is terminated/reaped; its original build PID is verified
absent. A process inventory before launch found no live xctrace, Instruments
or sample observer. This rules out those live command names, not every possible
system notification or policy participant.

Raw evidence: `.data/d1385-original-build-prefix-rusage/`.
Private observer: `.data/d1383-original-prefix-rusage.py`; syntax check passes.
No full-build or test qualification follows. The missing successful-prefix
CPU/wait partition is still missing, rather than replaced with failed-clean
or build-only evidence. No repeated ABBA campaign, image repacking, product
cache, security bypass or complete toolchain rebuild is admitted by this audit.
