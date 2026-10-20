# D881: historical label budget can suppress useful GVM code merging

This is new source-level work, not a repeat of package timing experiments.
It identifies a missed optimization opportunity, not a measured speedup or
a root cause of the Darwin/Linux difference. No release patch is admitted.

## Exact source and executable boundary

Source: Gerbil staging `1cfb032c7a1612637da6205f5f8a15683eba3ba0`,
Gambit `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`, in
`.data/gerbil-gambit-bootstrap-audit` relative to the project root.

Probe executable: the installed Gerbil toolchain's `bin/gsc`,
the GNU GCC 16-built `dcd677c` compiler, NOT a newly built staging
compiler. `git diff --exit-code dcd677cd3e40860bdd27dfbdbf5e3ce46ab03813 HEAD
-- gsc/_gvm.scm gsc/_gvmadt.scm gsc/_utils.scm` passes in the staged Gambit
checkout. Thus the exercised GVM implementation has matching source, but this
does not qualify the latest staging runtime or an integrated compiler build.

## The missed opportunity

In `src/gambit/gsc/_gvm.scm`:

* Line 324: `bbs-new-lbl!` monotonically increments the next label number.
* Line 1086: dead-block cleanup copies that historical next label number into
  the new BBS. It does not renumber surviving blocks.
* Line 1105: common-code cleanup skips when that number exceeds 300. The guard
  does not inspect the number of live candidate blocks.
* Line 1465: the actual common-code comparison iterates nonempty blocks through
  `bbs-for-each-bb`, so holes do not become comparison candidates.

Consequently a function can have very few live blocks after earlier cleanup
and still lose duplicate-block/common-tail merging because of past allocation.
Macro-heavy code can plausibly reach this situation; its frequency in actual
library/test builds has NOT been established by this probe. The guard is a
per-procedure GVM guard, not a module-wide C label limit.

## Narrow prototype

`tests/gambit-common-code-live-blocks.scm` keeps the old cheap path for next
label numbers <= 300. Otherwise it counts nonempty blocks, stops at 301, and
only invokes the EXISTING common-code implementation when the live count is
at most 300. It preserves label identities and does not alter equivalence,
GC metadata, operand comparisons, polling checks or native optimization flags.

The scan has a cost proportional to the sparse label span until its early
exit. Existing comparison/tail-extraction costs are still present; bounding
live blocks is not proof of a wall-time improvement. Enabling the pass for
sparse functions may increase Scheme compiler work while decreasing emitted
C work. Do not raise the guard to admit truly large live graphs.

The existing common-code pass redirects references but can leave the replaced
block temporarily in the BBS. The next dead-block cleanup removes it; the
probe follows that behavior rather than expecting immediate vector deletion.

## Executable receipt

From the gerbil-bazel root:

```sh
"$GERBIL_TOOLCHAIN/bin/gsc" -e \
  '(load "patches/gerbil-v19-darwin/tests/gambit-common-code-live-blocks.scm")'
```

The synthetic reachable graph has three blocks at labels 1, 401 and 402.
Both branch arms return through the same register. Baseline guard skips;
prototype plus existing dead cleanup leaves two blocks, both arms referencing
one survivor, with the same return operand and historical next label 403.
Small dense graphs retain their existing optimization. Different return
operands and polling requirements remain distinct. Exactly 300 live blocks
are eligible; 301 are skipped. Final marker: `GVM-LIVE-BLOCK-GUARD-OK`.
No timing or GNU GCC native compilation is needed for this control-flow probe.

## Deeper host-grouping boundary

`src/gambit/lib/setup.c:1750-1808` walks the public label table in order. On a
host change it calls that host with `pc=FIX(0)`, gets its host-label array,
skips the introductory slot and walks forward. Therefore arbitrary noncontiguous
SCC grouping is not compatible with simply reusing this loader: returning to
a previously seen host restarts that host's array cursor. Consecutive groups
are the conservative starting point; noncontiguous grouping requires explicit
indexing or coordinated label reordering.

`gsc/_t-c-2.scm:1376` can bypass argument checks via direct internal gotos.
Across host groups, the ordinary procedure entry must set nargs and use the
existing host transition, or an explicit unchecked entry descriptor is needed.
The current per-procedure scan already retains read/write resource vectors
(lines 82-83), so group resource unions are feasible without rescanning GVM.

## Decision

The live-block guard is a smaller and more concrete candidate than introducing
host groups. This probe is a regression demonstration of the guard decision
and existing merge semantics, not a fully patched staging compiler or a full
semantic conformance test. Before integration, check source syntax in its
compiler context and use a built-in Gerbil library/test scenario to determine
whether sparse over-budget procedures actually occur. That is new candidate
validation, not a request to repeat prior package benchmarks. The host-group
architecture remains exploratory and has no established runtime equivalence.
