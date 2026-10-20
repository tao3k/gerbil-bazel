# D1510 Runtime Profile Applicability

## Follow-Up: Current On-Disk Source Identity

A read-only content comparison covers every .scm, .ssi, .ssxi and .ss file
under the original cold-build HOME's lib directory and the retained test HOME's
lib directory. Both contain 2,327 files: 1,547 .scm, 388 .ssi and 392 .ss, with
no .ssxi files. There are zero missing paths and zero differing SHA256 values.
The SHA256 of the sorted relative-path-to-content-hash mapping, serialized as
compact JSON with sorted keys, is
`00a4ea6d30843ff40c39d053ca98306629f3cdfe4d4e1eec3f2732cb0891e882`.

This excludes a current source-text difference between these two retained
library copies. It does not prove equivalence to all historical inputs, cover
native images/headers or establish the cause of the current first-output denial.
No library file, configuration or source checkpoint hash is changed to force
parity. No build or test runs in this audit.

The existing complete-test receipt also confirms that chunk-07's 105.748693
seconds nearly spans the entire 105.750982-second wave; its 83 cases pass.
The older atomic investigation already identifies the long original all-recipes
case and repeated fresh-process imports. This is reused evidence, not a new
case benchmark, permission to modify MCP verification, or proof that all of
that time belongs to module loading. Continue pursuing general Gambit/Gerbil
execution, preserving the original consumer and complete-case inventory.

## Follow-Up: GC Root Source Boundary

The upstream `v0.19-staging` ref was read live again and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. The initially queried literal
`staging` name has no upstream ref; the release workflow and existing checkout
identify `v0.19-staging`. No revision, CI file or source checkout is changed.

Original Gambit `mem.c` already skips traversal for `___PERM` values in
`mark_array`; the procedure scanner explicitly states that nonclosure
procedures are permanent and scans only closure free variables. Therefore
the hypothetical repeated recursive scan of native permanent procedures or
static literal graphs is not a missing optimization in this source.

`mark_global_variables` has two materially different layouts. SINGLE_VM
walks each assigned global sublist and marks its individual value cell.
MULTIPLE_VMS partitions the logical global count and calls `mark_array` on
the current VM's contiguous global-value range. Current source CI selects
MULTIPLE_VMS, unlike the retained 47-second SINGLE_VM host. Merely adding a
dense traversal to the latter is not a general production improvement;
the former already has that representation. No new root packing/cache,
generational collector, VM-mode change or write barrier is proposed from
the old aggregate GC fraction alone.

The old D1611 hardware export was also read directly, validating target PID,
running state and cycle weights through the shared XML reader. Its 3,160
mark-array rows contain only leaf frames, not callers: 1,634,170,368 cycles
for `mark_array` and 1,250,063,466 for its constprop clone. Those rows cannot
attribute the clone's cost specifically to global roots, permanent objects
or a particular source-module constructor. D1612 already contains a wider
qualified source map; the later duplicate mapping is corrected in
`d1510-original-gnu-source-map.md` and its redundant implementation removed.

Eighteen focused framework/DWARF checks pass after that cleanup. The historical
5/50/112 gates and 47-second anchor are unchanged; no fresh full-build or test
time, admitted speedup or GitHub publication is claimed.

This is a source applicability audit, not a new optimization or timing run.
The user's AOT tool list and CI configuration are unchanged by this audit.

## Retained Evidence

The frozen whitespace-reader binary has historical complete cold builds of
47.771713, 47.824226 and 47.927094 seconds, with first compilation at
4.850866, 4.573628 and 4.592897 seconds. Its later complete test receipt is
105.750982 seconds, 39 files and 965 cases passing. Subsequent strict
112-second waves were denied; the historical pass is not stable current
test admission. The original partial 49.983260-second test wave is not a
complete-test result.

The active gates remain first output 5 seconds, cold build 50 seconds and
complete test 112 seconds. No profile change or deadline relaxation is
admitted here.

## Distinct Source Profiles

`tools/ci/build_source_toolchain.sh` currently requests multiple VMs, SMP and
`--enable-single-host=0`. Gambit `configure.ac` explicitly defines zero as
single-host mode without a control-point limit, not disabled single-host.
The earlier non-single-host interpretation was incorrect. Its source-toolchain
receipt explicitly does not claim D1510 performance admission.

The frozen carrier at `.data/d1510-source-loader-linked/gerbil-link.c`
contains native fast-path guards requiring SINGLE_HOST, SINGLE_VM,
SINGLE_THREADED_VMS and one processor, alongside Darwin/GNU/non-Clang and
other calling-contract conditions. Those helpers cannot simply be enabled
for the current multiple-VM/SMP profile by removing their guards. This is a
source precondition, not a measurement of multiple-VM overhead.

The current source-CI patch arrays do not apply the private carrier recipe
or `0018-gerbil-darwin-generated-source-loader.patch`. The latter explicitly
targets generated static driver output and excludes complete upstream-source
and release admission. Distinguish a helper absent from the build from a
helper present but disabled by its guard. Neither establishes a regression
in the frozen binary.

The whitespace reader helper itself is different: its C guard is Darwin/GNU,
and its buffer operation uses the port mutex, the actual readtable handler,
a bounded scan and original fallback. It does not require SINGLE_VM. That
source property is not proof of multiple-VM safety or end-to-end speedup;
the existing frozen-profile controls cannot certify a different runtime.

## Research Consequence

Keep the frozen profile as the comparison anchor and retain the requested
multiple-VM production configuration. Do not silently compare the two as
one performance line, disable multiple VMs to meet a gate, or delete native
helper guards to manufacture coverage. A generally distributable gain needs
an equivalent source transformation and actual correctness/performance
qualification on the profile where it will run.

No new candidate, complete build/test timing or GitHub performance claim
follows from this audit. Previously denied runtime and dispatcher routes
remain closed; the AOT list is a separate user-owned change.

## Current Checks

The retained binary and carrier still match their frozen SHA256 identities.
The focused reader/checkpoint checks give five passes and one failure:
portable historical verification rejects the current
`tests/summarize_three_time_gates.py` hash against the old checkpoint.
No historical hash is updated to hide this failure, and no existing script
change is reverted. This is a checkpoint-verifier mismatch, not a failed
reader semantic run or measured runtime regression. Full current checkpoint
verification therefore remains unconfirmed.

## Unchanged Current Cold Control

The frozen binary was subsequently exercised through the existing unified
`retained` command, without a new candidate, using the literal driver,
12 physical workers and the unchanged 5/50/112 gates. Output is persistent
at `.data/d1510-retained-current-three-gates-v1/`.

Clean exits zero in 10.353893 seconds and leaves zero native images. No real
compile line arrives by 5.032836 seconds after build launch. The hard gate
denies the run and reaps it with terminal exit -9 and no cleanup errors.
First-compile time, complete-build time and complete-test time are unknown;
tests are skipped. The deadline observation is not a measured first-log time
or a complete-build duration.

The captured compiler/runtime hashes, compiler version and controller digest
match the historical first 47-second round. Captured environment values also
match after excluding the per-project load path and package-home field. This
does not establish complete input equivalence or the cause of the denial.
Separately, every frozen provider image in the canonical test HOME passed
the manifest's SHA256 check; that check is not execution or a timing result.

This actual unchanged control also fails the current first-output gate.
Therefore candidate-only first-output denial is insufficient evidence that
an individual recent candidate caused a regression. Those candidates remain
not admitted; no rejected implementation is revived and no historical anchor
is replaced. The next performance claim needs a currently passing control as
well as the candidate's complete correctness and three timing results.
