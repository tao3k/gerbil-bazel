# D1510 Provider Extension Construction

Candidate preparation, not an admitted runtime optimization. Retain the frozen
47.771713 / 47.824226 / 47.927094-second cold anchor and 5/50/112 whole-task
gates. No original installation or provider binary was replaced.

## Existing Coverage Gap

Join the original standard-library loaded-module inventories in
`.data/d1510-loader-cpu-budget-v3/report.json` against the frozen provider
manifest. Make has 25 uncovered loaded modules, matching its 25 fallback
dlopen calls; JSON has 23, matching its 23 fallback calls. Test and list/list
have no uncovered loaded modules and no fallback calls.

Make's missing modules include eleven compiler phase modules and ordinary
make, plist, path, queue, barrier, channel and completion phase modules.
JSON's include parser and JSON phase modules; libcrypto remains a distinct
foreign-library boundary. Counts identify coverage, not a removable time
budget or several-fold startup forecast. Existing measured fallback intervals
must not be extrapolated to the entire expansion cost.

This gap exists because the retained 280-provider construction used an earlier
captured closure. It is not a new package-specific runtime branch. That
environment-bound construction is still not a universally qualified release;
see `d1510-package-specialization-audit.md`.

## Original Object Pilot

`tests/capture_provider_extension.py` accepts ordinary, uncovered modules from
the locked original toolchain inventory. It rejects duplicate, already-covered
and non-ordinary modules. The selected modules are a construction pilot, not
release-selection policy or universal coverage.

The runner verifies original binary/GSC/header/macro/archive/image/source
identities, actual Darwin GNU GCC 16 macros and host physical-core concurrency.
It uses original native-version linker names, original standard-library debug
flags and direct dependencies. Generation, object compilation and linking occur
only under a new persistent `.data` directory. The bounded construction tasks
are not consumer cold builds and do not redefine the 50-second consumer gate.

Three objects were generated and compiled successfully:

| Module | Original native text byte equality | Original dependency equality | Original inputs unchanged |
| --- | --- | --- | --- |
| gerbil/compiler/base~1 | PASS | PASS | PASS |
| std/make~0 | PASS | PASS | PASS |
| std/make~1 | PASS | PASS | PASS |

All original generation/object/link commands exit zero. Eight existing recipe
and native-capture regression tests pass. Native text and dependency equality
do not establish equality of all data, all FFI semantics, startup timings or
complete-library tests.

Evidence: `.data/d1510-provider-extension-objects-v1/report.json`, SHA256
`cad0bdb52985f2a251ef9c9b7deb9ab0782c05ac9bba0c26b8ca5972aa172487`.
Per-object C/object/image files and raw command logs are retained there.

## Remaining Admission

No extended host has been linked or executed yet. The next step is to add the
verified objects to a separate retained-line host, preserving exact image
digest verification and ordinary fallback. Verify actual new provider hits,
independent original standard-library build/test behavior and the unchanged
heavy complete inventory. A release must derive coverage from the toolchain,
not benchmark-specific names, and retain multiple-VM/initialization contracts.
No grouped-image packing, early initialization, skipped digest or directory
cache is proposed. Promote only after real end-to-end gain and correctness
under the unchanged gates; successful object construction alone is not gain.
