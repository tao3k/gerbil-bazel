# D1381-D1382: copied-home failure has a Darwin loader boundary

## Cross the binary variable before blaming a candidate

D1378's restored-lowopt candidate failed copied-home clean at 30 seconds,
while D1379 passed clean with original library home. D1381 repeats only
that failed lane with the immutable original binary, not candidate code.
Original binary SHA-256:
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.
The existing MCP source head and original 30-second gate are unchanged.

Actual original-binary clean with copied library home also produces no
output and times out at 30 seconds. The two-second stack sample completes
while that process is live. Of 1,609 main-thread samples, 1,578 have top
frame __fcntl under Gambit dynamic_load, dyld dlopen and Loader::mapSegments.
That is approximately 98.07 percent of this short stack sample, not active
CPU cycles or a census of the whole failed command. It establishes a loader
syscall location during the failure, not a Scheme macro/codegen regression.
The supervisor receipt does not populate cleanSampleExitCode on its timeout
path; the retained completed sample artifact is separate diagnostic evidence.

## File identity control and its limits

The bounded inventory covers 1,992 original native .o1 images. Every copied
image is byte-identical and has a distinct inode. A separate hardlinked
diagnostic home has the same native-image bytes and original inodes at a
new path. These links are used only for runtime reads, never recompilation,
replacement, chmod or metadata editing; modifying them could modify the
original isolated baseline files.

D1382 original-binary clean with that hardlinked library home completes in
16.092 seconds, still much slower than the prior original-home observations.
Its two-second main-thread sample has 1,581 of 1,770 samples in __fcntl
(1,580 under the prominent mapping stack, plus one in another loader stack).
The observed new-path delay therefore is not explained solely by new native
image inodes. A single partial control does not isolate path policy, vnode
cache state, signing checks, storage behavior or temporal effects. Neither
the completed clean nor its elapsed time is an optimization qualification.

Read-only inspection of representative original/copied images confirms
matching embedded linker-generated ad-hoc signature bytes and the presence
of the provenance attribute on both. No quarantine or provenance attribute
is removed and nothing is re-signed. Attribute identifiers and personal
paths are not copied into this receipt.

## Published platform source, without over-identification

Apple's published
[dyld Loader.cpp](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/Loader.cpp)
has signature registration and an F_CHECK_LV library-validation fcntl before
segment mapping. This is a real Darwin-specific boundary. Published main is
not matched to the installed OS; stack names and offsets alone do not prove
which fcntl command, kernel policy or cache caused the observed delay.
No bypass of library validation or security policy is proposed.

## Relation to the goal

This corrects attribution of copied-home candidate failures and prevents
using them as evidence of macro optimization regressions. It does not turn
D1380's approximately 1.23 percent overlapping ABBA difference into a win,
nor establish the cause of the original seven-to-eight-second prefix.
Partial Running-cycle profiles also cannot bound syscall wait time in a
different library home.

The synchronization review reuses D968 rather than repeating its rejected
single-collector experiment. Original single-threaded allocation locks and
forwarding CAS are conditionally absent; chunk publication barriers are a
distinct existing D968 case, not a newly admitted main optimization.

No production source is changed, no full toolchain is built, no std/test
case or full-build speedup is claimed. All owned diagnostic processes are
terminal. The objective remains active and unresolved.
