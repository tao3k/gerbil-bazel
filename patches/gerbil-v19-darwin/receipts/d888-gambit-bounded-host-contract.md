# D888: bounded Gambit host implementation contract

Date: 2026-10-03. Source investigation only; no acceleration is admitted.

## Identity and Scope

A fresh remote query of `refs/heads/v0.19-staging` returned
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, matching D884.
Its Gambit gitlink is `ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
All source references below are relative to that checkout's `src/gambit/`.
The candidate must retain the D884 patches and real GNU GCC configuration.

D879/D880/D859/D860 are prior evidence, not benchmarks to rerun.
The descriptor sweep and GCC macro provenance policy already have patches.
The remaining ordinary-file optimization/code-generation work motivates a
bounded-host candidate. This is not a new Darwin/Linux causal attribution.
GXPkg, HTTP imports, package lifecycle, and std/make are outside this change.

Native compilation and dynamic-image startup are separate costs. Bounded C
hosts target the former; they do not reduce `.o1` image count and must not be
advertised as a solution to the recorded dyld startup cost.

## Additional Runtime Constraint

`lib/setup.c:1741-1808` initializes the module label table in order. When a
label's host differs from `current_host`, it invokes that host with the
special zero PC, receives its computed-goto label array, skips the first
INTRO entry, and advances the array for subsequent labels. INTRO records
also advance that pointer.

Consequently a host cannot be assigned disjoint label-table intervals without
changing this initialization protocol. A sequence A/B/A restarts A's array
on its second appearance. Merely mapping noncontiguous procedures to A can
associate later Scheme labels with earlier native goto addresses.

The first candidate should partition the existing procedure sequence into
contiguous groups and preserve every procedure's complete INTRO/value-label
interval. It should not reorder public labels or use arbitrary SCC grouping.
The runtime already enumerates multiple hosts; that does not establish that
an arbitrary grouping policy is correct.

## Coherent Source Boundary

- `gsc/_t-c-1.scm:1137`: construct group ownership once from `prc-list` after
  scanning. Preserve procedure identity, ordering, module supply/demand,
  constants, debug information, and global label indices.
- `gsc/_t-c-1.scm:1854`: emit each group's host and host-label array; compute
  its read/write resource union from each procedure's existing vectors.
- `gsc/_t-c-1.scm:2066`: use group label origin with each procedure's existing
  `PH_LBL0`. Keep procedure-local labels and frame descriptors intact.
- `gsc/_t-c-2.scm:1378,1385`: determine whether a known internal call crosses
  a group boundary. Only same-group calls may retain direct native goto.
- `include/gambit.h.in:6776-6805`: make host selection, label origin and
  resource selection agree. Do not globally disable single-host mode.
- `include/gambit.h.in:8099`: cross-group internal transfers must use the
  host-transition path with their existing argument setup.
- `include/gambit.h.in:11851,11860`: procedure AND return labels must identify
  their actual group host instead of all resolving to `MH_PROC`.

Changing just the configure limit, a code boundary, or `JUMPINT` is not a
complete implementation. The existing INLINE_JUMPS policy remains unchanged.
No fixed budget is justified yet: source operation counts, native compile
cost and cross-group runtime transitions require new-candidate evidence.

## Gates Before Promotion

First prove same-group and cross-group calls, checked/unchecked argument
paths, returned closures, multiple-value returns, exception unwinding,
continuations, GC/frame metadata and C-named entries against the unchanged
compiler. Include the computed-goto label initialization boundary explicitly.
An oversized single procedure remains an unsolved case, not permission to
split inside its frame/control-flow protocol.

Then use the unchanged PR #11 project and original tests, the D884 toolchain
as adjacent control, hardware-derived parallelism, separate fresh build
roots under `.data/`, identical flags and no artifact reuse. Record compiler
wall time, complete cold build/test time and produced-program behavior.
Keep startup measurements separate. The existing host-load admission gate
must pass before claiming a percentage; functional success is not speedup.

Status: source ownership and the additional contiguous-label constraint are
established. No grouping emitter patch, runtime qualification, matched A/B,
or accelerated complete toolchain is claimed by this receipt.
