# ASCENT Static Link Regeneration Boundary

## Scope And Review

MCP remains the primary admission consumer. ASCENT is an additional real AOT
consumer at source HEAD `21e3638687d42ecfc36acebb28991987435ebc60`.
Its active checkout, installed tools and shared dependencies are read only
for this investigation. No ASCENT build/test was launched or supervised here.

Before production candidate edits:

1. Aligned: yes, actual static-closure compilation, not empty CLI startup.
2. Explored: patch 0007 already reuses runtime C produced in the same process.
   This audit checks the different boundary of a fresh entry compiler process.
3. Worth optimizing: the existing real cache-miss log records 74 actual gsc
   -obj invocations, not merely scheduled job messages.
4. Expected benefit: unknown wall time. Some dependency object invocations
   may be removable; 74 calls are not 74 proven redundant compilations.

## Existing Real Evidence

ASCENT direct-warm.out contains 76 scheduled compile-job messages, one GSC
-link call, 74 GSC -obj calls and one GCC link call. Of the actual object
calls, 55 target the project native-library static directory and 19 target
the locked dependency prefix. There are 30 CASE-OK markers and final OK;
recorded whole wall time is 55.69 seconds. direct-warm-confirmed.out records
library and entry cache hits, 30 CASE-OK markers, final OK and 7.84 seconds.
These are different cache states, not a measured compiler candidate speedup.

compile-entry.ss first calls compile-module with invoke-gsc false, then
compile-exe with static/parallel enabled, then drains compile jobs.
Darwin prepare-link consults current-compile-output-produced? for each
runtime C. That predicate is membership in the current executor's producer
table, not persistent artifact validation. Unregistered dependencies become
Scheme inputs. compile-obj invokes gsc when Scheme or C is newer than the
object, among its other conditions.

## Isolated Real-Module Link Control

check_gsc_link_regeneration.sh copies core__types.scm and its existing C
from the locked ASCENT prefix to a fresh private directory. It uses only
the retained private GSC and home, whose compiler SHA is recorded. This
compiler differs from ASCENT's installed compiler, so this is a behavior
control, not a matched installed-toolchain performance result.

Completed output: .data/ascent-link-regeneration-v3.

- Scheme input generates C, including the first regeneration from the copied
  installed-compiler artifact; that first content change is not a reuse test.
- C input leaves C SHA and nanosecond modification time unchanged.
- Repeated Scheme input with the same compiler/options leaves C SHA unchanged
  but changes its modification time.
- All three link files are byte-identical after the first generation.
- Copied Scheme remains byte-identical to the original source at completion.
- No object compilation or executable link occurs in this control.

v1 stopped before linking because PATH selected GNU stat with BSD arguments;
it is retained. v2 demonstrated basic C-input preservation. v3 explicitly
uses Darwin /usr/bin/stat and adds the identical-content rewrite assertion.
No timestamps are modified with touch and no cache receipt is manufactured.

## Candidate Boundary

There is now a demonstrated identical-content C rewrite that can invalidate
Gerbil's timestamp-based object reuse. A prospective Darwin-only Gambit
emission change could preserve an existing target only after generating and
comparing exact bytes, rather than admitting old C merely by file existence.
That would still pay Scheme-to-C cost and has no measured runtime benefit yet.

Before implementation, emission failure cleanup, concurrent writers, atomic
replacement, output permissions and option/source/toolchain invalidation
must be handled. Object reuse must also retain the source-freshness condition.
No production patch, cold-build improvement, peak-memory result or full
MCP/ASCENT admission is claimed. The requested six AOT invalidation scenarios
and both consumers' complete correctness/performance checks remain pending.

## Native Object Option Control

The fresh .data/ascent-link-regeneration-v4 control adds two actual GSC
object compilations of the same regenerated C, using the retained private
gambuild-C GNU gcc-16 path with explicit -O0 and -O2 respectively.
Both object compilations exit zero; Scheme and C hashes remain unchanged.
The native object hashes differ:

- -O0: `051ad10f203020d22167fdebf0f25818493c8d912f97a023276cffbb860c12e6`
- -O2: `1e7460fcbe022d8d45f7dc6eab8e85a986b811e0c4d71cbbae09e6bfd8dccb26`

The direct object commands intentionally compile twice. They do not demonstrate
that the actual Gerbil driver skipped either command. They prove that byte-equal
C alone cannot validate reuse under changed native compiler options. The current
driver's local skip predicate has no option comparison; gsc-link-options also
removes cc-options and ld-options from the Scheme-to-C link command.

Consequently, merely preserving C modification time must not be admitted as a
generic object-cache correctness fix. It needs an independently validated
object build-context invalidation rule, or a caller boundary that already
guarantees that rule. No such generic rule has yet been qualified in this
candidate. The existing 0014 capture reference validates image/object content
but does not record a native compile-context fingerprint; it is not evidence
that changed options, headers or compiler binaries are safe to reuse.

The long-task goal is active. Production compiler changes and both consumers'
six-scenario/complete-suite admission remain unfinished; no new speedup is
published from these local behavior controls.
