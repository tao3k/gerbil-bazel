# Native Object Request Coordinator

**Follow-up blocker:** the [0045 environment contract](d1510-native-object-batch-environment.md)
reproduces a declared-versus-executed compiler-environment mismatch in unpaired
0044. The controls below remain historical scoped evidence, not generic admission.
Do not integrate the v1 protocol; the paired v2 correction requires new qualification.

## Review Before Implementation

Correct path: move a complete Darwin static-object request into one native
coordinator, rather than starting GSC/build-driver discovery separately for each
object. This is object compilation, not 0040's generated-C member adapter.
Already explored: unchanged eager-proof package configurations, simple producer
fusion and timestamp-based tool memoization are not retried. Worth implementing:
stage outputs before a request publication barrier, retain existing object proof
validation, and then qualify the common compiler boundary. Expected whole-package
gain remains unknown; the previous transport control cannot predict it.

## Experimental Patch

`0044-gambit-darwin-native-object-batch-coordinator.patch` applies after 0043 to
the experimental native capture backend. It adds an explicit `--batch` protocol,
enabled only by `GAMBIT_DARWIN_NATIVE_OBJECT_BATCH=1`. Normal digest/capture CLI
dispatch is unchanged. The backend's existing compile-time Darwin/GNU guard
remains in effect. No frozen series or release build selects the new protocol.

The bounded NUL-delimited manifest carries the existing 25-field capture records.
Targets are canonical, distinct, and cannot alias request inputs, tools or other
targets' proofs. Locks use the same names as the existing shell helper and are
acquired in sorted target order. Thread workers retain **all per-object before/
after full tool hashes**, source-pin binding, actual preprocessing input, compiler
recipe and object checks. Each worker has a 4 MiB stack because the retained
digest implementation has a 1 MiB stack buffer. Environment records are privately
copied and revalidated at the final barrier.

Objects and proofs are compiled or checked in private staging paths. No target
is published when compilation, source/request/environment validation or final
tool validation fails. The additional request-end tool snapshot is shared only
among identical ordered tool-path sets; it is freshly content-hashed for every
request and compared with every member's full precompile snapshot. This does not
remove a per-object compiler check or introduce cross-request memoization.

Publication uses the existing object/proof rename model after all checks. It is
not a filesystem transaction over all targets: an I/O error during the final
rename sequence can leave earlier individually valid members published. A failed
request must not create a consumer binding. Consumer binding and crash/signal
recovery are still integration requirements, not capabilities proved here.

## Real Patch-Built Controls

Receipt: `.data/d1510-native-object-batch-controls-v7`, exit 0. The actual binary
is compiled from the patch-composed source with GNU GCC 16, not just the prototype.
The sample is 1,092,831-byte real MCP registry generated C. Execution is Bash/
native C/GSC/GCC; Python does not supervise these semantic controls.

- 12 physical workers; cold objects match the ordinary dynamic/PIC reference.
- An actual GCC option error preserves all original object/proof hashes.
- Two concurrent requests with reverse manifest order both return 12 HITs;
  all original hashes remain identical after both complete.
- A changed tool-content record causes 12 MISSes with ordinary object parity.
- A real external process changes the tool record after a completed before-tool
  snapshot during compilation. The request rejects, does not COMMIT, and all
  original hashes remain unchanged. The trigger is recorded, not inferred.
- Changed compiler options retry successfully and match a separately compiled
  ordinary reference using those options.
- An actual exported context variable change causes 12 MISSes with byte parity.
- A source changed after binding is rejected before staging creation, preserving
  original objects and proofs.
- The final barrier reports one distinct freshly hashed tool set.

The single cold batch is **2.86 seconds**. This is not a matched performance
comparison, package timing or admission. Earlier prototype/patch compositions
were 3.14 / 3.25 seconds; they are not repeated stable qualification samples of
the final composition. No package acceleration is claimed from these values.

The first attempts are excluded: v1 failed configuration extraction, v2 crashed
with undersized Darwin thread stacks, and v4 failed to inject a tool change due
to a whitespace-sensitive counter comparison. The trigger was fixed and actually
observed in v5/v6/v7. LLDB observed corrupted thread stacks in the crashing binary;
no Gambit VM, linker or system-resource fault is asserted from that observation.

The patch applies/reverses with exact source parity. **27 focused checks pass**,
including nine patch/preflight checks, the 0043 protocol controls and frozen bundle
contract. Python here checks protocol rejection and patch bytes only.

## Qualification Still Required

Gerbil does not yet submit native object requests to this coordinator. The real
driver integration must derive flags and actual per-job child environment from
the configured driver, preserve producer proof identity, respect generated-C
metadata/options, retain unsupported-recipe fallback, and bind only a successful
complete request. Arbitrary supplied manifests are not a qualified replacement
for the existing validated build-driver preparation path.

Native include invalidation, mid-request source/environment mutations, signal/
publication failure, mixed tool sets, real MCP three cold builds/full tests and
isolated ASCENT AOT qualification remain outstanding. Neither the component
controls nor the new patch close the thread goal. Do not promote 0044 into either
frozen series or repeat the rejected 0043 package configuration unchanged.

The live frozen six-patch identity check still passes after these controls:
first logs 4.038 / 3.980 / 3.950 seconds; cold builds 36.414 / 35.552 / 37.770
seconds; complete tests 86.924 seconds, 39 files / 965 cases. These remain retained
measurements with unchanged **4.5 / 42 / 97 second** per-sample limits.

## Exact Identities

- 0044 patch: `734a895f8f28f33dbe3583c512585319a7def43398afb176334402b65e534052`
- Coordinator prototype: `94dd1f524d9c6b5b640722261b1514be35f38b1cb6ccc5a3a162e420783c3aab`
- Bash controls: `9e04a7a53ee72b3cfbd522f601da27a2cee9a53f091ff474cb16ef678377e35c`
- Patch-built binary: `0aeacb613fcfc1fdb1602caeed54bd4f09f860a4b2ad0e9a0261ffd100c946d6`
- Raw v7 receipt manifest: `74db4452e5a742a0b7a344ca7337cc974784fd8c986555730b8d282d4fde5ab0`

The raw manifest binds all semantic logs, before/after object-proof hash records,
the real mutation trigger, timer, selected tool/input identities and terminal
status. Personal absolute paths remain confined to local `.data` artifacts.
