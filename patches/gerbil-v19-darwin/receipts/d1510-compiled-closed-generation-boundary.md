# Compiled Closed-Set Generation And Link Boundary

## Admission Review

- Correct direction: skip demonstrated identical Scheme-to-C regeneration,
  not merely its later C object compilation.
- Prior work: singleton producers/std/make overlays remain DENY. The existing
  55-file closed-set API lacked compiled snapshot-reader timing and original
  complete Scheme-link parity. This is not naive multi-input CLI batching.
- Worthwhile: retain three tool checks around one closed set instead of three
  per module. Preserve source/include snapshots, full context, output digests,
  immutable pins and the closure lock.
- Expected benefit: the recorded 55-file generation opportunity is about
  3.69 seconds. No whole-package multiplier or cold speed improvement is assumed.

## Reuse-Off Compiler Control

`check_static_closure_generation_cost.sh` now optionally accepts a fourth
compiler bin. That mode uses original/native/native/original ordering with
proof flags disabled. Its existing Scheme/C/C/Scheme mode is preserved.
Header parity is checked before creating output; all 55 C files and complete
link outputs must match, and input/compiler identities remain unchanged.

Receipt `.data/d1510-closure-compiler-off-cost-v1`:

| Compiler | Real | User | System |
|---|---:|---:|---:|
| Original Multiple VM GSC | 3.96 s | 3.71 s | 0.15 s |
| Snapshot GSC, reuse off | 3.91 s | 3.70 s | 0.14 s |
| Snapshot GSC, reuse off | 3.95 s | 3.76 s | 0.15 s |
| Original Multiple VM GSC | 3.89 s | 3.72 s | 0.14 s |

Original GSC SHA256 is
`dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e`;
snapshot GSC is
`c9caaea9e777122e011fdd925f87fee578b94ff7eeac9031dce804fa8209f2e9`.
Headers are byte-identical; no Single/Multiple VM substitution occurs.
These data do not support a general reuse-off compiler slowdown or attribute
the earlier deployment's 135-second DENY to compiler code size alone.

## Actual Compiled Closed Set

`gambit-generated-c-closed-cost.scm` and `run_closed_generation_cost.sh` call
the existing compiled `c#reuse-generated-c-closure!` on 55 real Scheme files.
Ordinary and closed generation share paths, common `(target C)` options and
basenames in one process. Environment is unchanged across phases. All C bytes
are checked after every phase; a real closure proof and MISS/HIT are required.
Bash/GSC own execution; Python does not supervise native work.

| Private receipt suffix | Ordinary before | Population | Closed HIT | Ordinary after |
|---|---:|---:|---:|---:|
| `d1510-closed-generated-cost-v3` | 3.598140 s | 3.325875 s | 0.074964 s | 3.350764 s |
| `d1510-closed-generated-cost-v4` | 3.815579 s | 3.594996 s | 0.082897 s | 3.484128 s |
| `d1510-closed-generated-cost-v5` | 3.615736 s | 3.597891 s | 0.077661 s | 3.575524 s |

These are within-process component times, not cold package/test measurements.
Population has no established speed win; v5 is effectively equal to ordinary
generation. The roughly 46-fold HIT component ratio is NOT a complete-build gain.
v1 has a delimiter error and v2 a compiler namespace error; neither generates
successfully. Both negative receipts remain. Assertions were not removed.

v4 adds original Scheme versus returned immutable-C whole-link parity. v5 also
requires the original GSC CLI's 55 per-module C outputs to match the native API,
before comparing the link: matching linker metadata alone is insufficient.
All checks pass. v5 diagnostic time is 10.93 real / 10.22 user / 0.51 system
seconds for four phases and C checks; subsequent link commands are excluded.
No native consumer Cases are claimed by this component.

v5 link C SHA256:
`f4d7bfedc6c2469989aedda451bc32fd28b37ae3d3fb7377b181ffa2150dc2e0`;
it also matches the independent reuse-off ABBA link. v5 stdout SHA256:
`7a41d3a2ab7d072f841fe8b13213556fa511aa23e313e16cdea9824dec69a9e6`.
Private receipts retain inventories, tool/probe identities, C digest lists,
whole-link identity, native logs and terminal status.
Two ABI mismatch controls reject before output creation or native launch.
Combined ABI/receipt/identity/progressive-gate regression checks pass 131 tests;
both shell scripts also pass Bash syntax checks.

## Integration Requirements

The next mechanism should consume a closed set at the actual Scheme-link
boundary, avoiding speculative singleton proofs and a std/make overlay.
This integration is not implemented/admitted here. Preserve mixed C/SCM order,
aliases/options and the later executable-object source paths: immutable pins
alone do not prove those jobs compile the same C. Multiple directories, changed
membership, original diagnostics, failure publication and concurrent callers
need controls. Partitioning additionally needs context isolation and link parity;
filename heuristics/shared-state memoization are not authorized by these data.

No frozen toolchain, active ASCENT checkout or shared dependency is modified.
Outputs are owned `.data` files. Singleton 0023–0025 deployment DENYs stay closed.
MCP patch/driver/runtime/raw-report identity passes; its 4.004–4.049-second first
log, 36.467–37.406-second cold builds and 87.409-second/965-case pass remain
unchanged, with 4.5 / 42 / 97 ceilings. Full consumer admission and goal
completion remain unproved.
