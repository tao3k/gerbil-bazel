# D880: staging C emitter ownership, without repeated benchmarks

Source-only audit. No package build, timing comparison, performance admission,
or upstream compiler change was performed for this receipt.

## Snapshot

Gerbil v0.19-staging: `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
Gambit gerbil-patches gitlink: `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
Checkout: `.data/gerbil-gambit-bootstrap-audit` relative to the project root.
The intended native compiler remains real GNU GCC, not Clang.

Existing D857/D858/D859/D860/D871 results are inputs, not experiments to repeat.
In particular, string lowering and ordinary native-code compilation have
different critical-path implications. A larger preprocessed file alone does
not establish the owner of the ordinary-function tail or the Darwin/Linux gap.

## Confirmed generation chain

Paths below are relative to `src/gambit/` in the pinned checkout.

* `gsc/_front.scm:757`: `compile-parsed-program` constructs module main and
  top-level constant procedure definitions. At line 940 it keeps procedures
  with code, then calls `purify-procs`.
* `gsc/_gvm.scm:736`: `bbs-purify` already removes unreachable blocks, jump
  cascades and useless jumps, and conditionally merges common code. The latter
  skips when `bbs-next-lbl-num > 300` (line 1105); D881 isolates a missed case
  where historical label allocation exceeds the live-block count. Adding a
  generic dead-block pass would duplicate existing work.
* `gsc/_front.scm:436`: the remaining module procedures enter `target.dump`.
* `gsc/_t-c-1.scm:353`: module main is registered; at line 356, with
  `targ-tree-shake?` false, every remaining procedure is registered as supplied.
  Lines 395-396 both initialize and explicitly set this switch to false.
* `gsc/_t-c-1.scm:764`: `targ-use-prc` deduplicates by procedure identity and
  enqueues unscanned procedure objects. Primitive procedures also register
  global supply/demand information. This is not simply a list of disposable
  private functions.
* `gsc/_t-c-1.scm:1854`: `targ-dump-prc` emits module-wide resources and host
  labels, then each procedure's code and resources, then the module label
  table. The C header determines which host arrangement survives expansion.

## Structural gap: no intermediate host grouping

`include/gambit.h.in:6776` chooses module host or procedure host via `___SM`.
At lines 6779-6799 the module and procedure code/label/switch boundaries are
selected correspondingly. `___BEGIN_COD` at line 6805 constructs the actual C
function; `___D_ALL`, `___R_ALL`, and `___W_ALL` select its resource sets.

`configure.ac:489` explicitly documents the tradeoff: one C function per
module improves execution but makes compilation longer and more memory hungry.
`include/gambit.h.in:1244` does not split a large module: exceeding a positive
single-host limit switches the whole module to per-procedure hosts. Limit zero
disables this fallback. There is no bounded multi-procedure host-group layer in
this emitter/header path.

This makes bounded host grouping a distinct architectural candidate, not a
retry of scheduler tuning, string packing, or disabling GCC optimization.
It is NOT a measured speedup, nor proof of a Darwin-specific GCC pathology.
It also does not directly solve the large constant-string preprocessing cost.

A correct implementation would need one coherent ownership change:

* Assign procedures to groups, with a host and label origin for each group.
* Compute declaration/read/write resource unions per group instead of using
  only module-wide or individual-procedure sets.
* Emit group-local host-label arrays and preserve the module's public label
  table, module initialization and GC/frame metadata.
* Keep direct gotos only for same-group targets. `___JUMPINT` at header line
  8099 currently assumes every internal target is local in single-host mode.
  Cross-group targets must use the existing host transition machinery.
* Update `___HOST_LBL0`, `___LBL`, `___PRC` and label-table host ownership
  together. Changing only `BEGIN_M_COD` or the configure limit is insufficient.

Group construction should not be prescribed as SCC-only: a large recursive
SCC can itself exceed a budget, and hot cross-group transitions can cost runtime
performance. Grouping policy and runtime equivalence remain research gates.

## Do not enable tree shaking blindly

The disabled emitter switch is a source fact, not evidence of useful dead
procedures in the actual workloads. The front end already performs binding
reachability cleanup (`gsc/_ptree2.scm:1326`) and the GVM already purifies blocks.
Top-level procedure supply, C-named entry points and module metadata must remain
roots. Moreover `targ-dump` scans its procedure queue before registering
`module-descr` and `c-objs` through `targ-use-obj` (lines 383-390). A reachability
change must audit root ordering and the fixed point before pruning anything.

## Decision

No performance patch is admitted from this source inspection. Do not rerun the
recorded package experiments to rediscover their outcomes. The new source-level
question is whether bounded host groups can reduce ordinary-function GCC work
without losing the execution benefit of local control transfers. The initial
correctness fixture can use Gerbil's own libraries and `defbuild-script`; no
external package is needed. Such a fixture would test new group/label semantics,
not repeat existing byte-size or wall-time baselines.
