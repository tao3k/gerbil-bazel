# Native Object Batch Environment Contract

## Admission Review

Correct direction: prove the real per-job compiler environment before connecting
the object coordinator to Gerbil. Already explored: 0044 stages objects and checks
records, but does not transfer their declared environments into GCC processes.
Worth fixing: accepting a proof for a context that was not executed is a correctness
defect, independent of timing. Expected speed gain is zero; no complete package
benchmark is admitted by passing this contract alone.

## Reproduced Defect

`.data/d1510-native-object-batch-environment-denied-v1` exits 42. A declared
`GCC_COMPARE_DEBUG=-fcompare-debug-not-overridden` environment makes the ordinary
GSC/GNU GCC object compilation fail (exit 70), while unpaired 0044 accepts the
same declared environment, compiles under the coordinator's ambient environment
and COMMITs (exit 0). No installed/shared toolchain or consumer checkout is changed.
The GCC option affects actual compilation rather than preprocessing, so unchanged
preprocessor input cannot detect this mismatch. This behavior is documented in
[GCC Developer Options](https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html).

The original 0044 controls were valid for their prepared environments, but do not
prove a generic per-job environment contract. Unpaired 0044 is **not admitted**;
do not use its v1 manifest protocol for driver integration.

## Correctness Patch

`0045-gambit-darwin-native-object-batch-environment.patch` follows 0044 and keeps
ordinary digest/single-capture behavior unchanged. The batch protocol becomes v2:
the existing 25 capture fields plus a NUL-delimited actual child-environment file.
The native dumper produces that file and its sorted proof record together. The
loader verifies that both encodings represent the same environment, rejects
duplicate names/truncation/multiline ambiguity, keeps a private immutable in-memory
copy, and checks the raw input digest again before publication.

Workers pass these arrays directly to `posix_spawn`; no parent `setenv` mutation
is used. The compiler-environment pointer is thread-local and reset after each
job. All existing per-object source, preprocessing, tool, option and object checks
remain. A v1 batch request returns 77 before staging rather than inventing missing
environment information. This is not a replacement for the driver's existing
unsupported-recipe fallback.

GCC `cc1`, assembler and Apple assembler discovery also uses the exact requested
environment and compiler prefix. Selected paths must equal the recorded tools,
both before compilation and at the final request barrier. Identical full
environment/tool/prefix contexts can share discovery within one phase/request;
there is no cross-request cache or metadata-only tool-content check.

## Actual Native Controls

Final receipt: `.data/d1510-native-object-batch-environment-controls-v8`, exit 0,
12 physical workers, real 1,092,831-byte MCP generated C, GNU GCC 16 and the
matching Single-VM GSC. Bash/C/GSC/GCC execute the semantic controls directly.

- A parent `GCC_COMPARE_DEBUG` poison does not leak into a declared normal request:
  all 12 members HIT and succeed.
- A request declaring that failing compiler environment rejects; object/proof
  hashes remain unchanged and no publication COMMIT is produced.
- A mixed request contains 11 normal environments and one failing environment.
  The 11 normal jobs genuinely compile under their own environments; the failing
  job rejects the whole request without changing original targets.
- Those 11 staged normal objects match a separately compiled ordinary GNU GCC
  reference using the same `-fno-inline` options, byte for byte.
- A private `GCC_EXEC_PREFIX` demonstrably selects a different owned `cc1` path.
  Retaining the original recorded tool path is rejected before object execution,
  and all original object/proof hashes remain unchanged.

V4's `COMPILER_PATH` injection did not override this GCC's installed `cc1`; the
test correctly failed its expected-DENY assertion. It is excluded, not attributed
to a coordinator defect. V6/v7/v8 explicitly verify that the selected path really
changes under the private execution prefix before counting the rejection.

The preceding v5 composition passes the existing source binding, environment
change, option retry, tool-content mutation, real mid-request tool mutation,
failure-no-publication and two reverse-order concurrent request controls. Final
source additionally factors discovery and performs the request-end path check.
Complete native regression and consumer integration still need qualification;
these preceding controls do not grant whole-consumer admission to the final source.

**32 focused checks pass** against the final source: exact 0044/0045 apply/reverse,
v2 protocol/encoding rejection, 0043 controls and frozen bundle contract. The
Python checks cover bytes and protocol rejection, not Scheme test supervision.
No new build/test performance result is claimed.

## Remaining Consumer Work

Gerbil does not yet route object requests here. Its real configured-driver
preparation must preserve generated-C metadata/options, construct each exact
requested environment, derive matching tool paths, retain producer proof identity,
and create a link binding only after a successful request. Mid-request environment
and tool-selection changes, native include invalidation, signal/publication I/O
failure and both full consumers remain required integration controls.

The live frozen checkpoint remains unchanged: first logs 4.038 / 3.980 / 3.950
seconds; cold builds 36.414 / 35.552 / 37.770 seconds; complete tests 86.924 seconds,
39 files / 965 cases. Limits remain 4.5 / 42 / 97 seconds per sample. 0044/0045
remain outside the frozen series and release build. The thread goal is not closed.

## Identities

- 0045: `069077c25c173ad7d7ae213fa34656b5abd54c0d4aa702d1dad70de860c65aa3`
- Final coordinator: `86c736a624e8902692a9b33e1cd24cda3fc72aa090a82fee5427162727a65542`
- Final patch-built binary: `7bc5898022ef3f9aedbf5e6d1093498feafadc3d1760ff4b4c069163f3b04fb9`
- V8 raw receipt manifest: `9f532d1965f2955a44f9e352876622feb7c315148b6d0aa3c999b248d6a8e11d`

The raw manifest binds logs, before/after object-proof records, the independent
mixed-object parity hashes, timer, input/tool identities and terminal status.
Personal absolute paths are confined to local `.data` evidence.
