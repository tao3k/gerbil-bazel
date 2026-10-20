# D1510 GC Array Length Boundary

This is new reached-work evidence, not a performance candidate or delivery.
User-owned AOT/CI edits and all production patches remain unchanged.

## Current Unchanged Control

The original whitespace-reader binary was run once through the retained
controller with twelve hardware-derived workers and the unchanged 5/50/112
gates. Clean exits zero in 4.424413 seconds with zero native images remaining.
No actual compile line arrives by 5.007841 seconds; the gate denies the run,
kills/reaps the process group, and reports no cleanup errors. Complete build
and test times are unknown; tests are skipped. This is not a measured first-log
time or evidence of regression caused by a new candidate.

Evidence: `.data/d1510-retained-current-three-gates-v4/`. The v3 attempt fails
sandboxed hardware discovery before workload launch and is not a timing run.

Keep historical first logs 4.850866/4.573628/4.592897 seconds, cold builds
47.771713/47.824226/47.927094 seconds, and the complete 105.750982-second
39-file/965-case pass separate from this current denial. No gate is widened.

## Original Marker Census

Extend the existing `prepare_gc_mark_probe.py` observer with entry-length
buckets and total initial array cells. Preserve original copying, forwarding,
tail marking, weak handling, collection policy and Scheme roots. The existing
single-member framework compiles original and observed mem.o with the retained
GNU recipe, then links against the frozen carrier, providers and private reader.
Both original member and original linked control match their frozen bytes.
No global toolchain is replaced. This is single-VM/thread diagnostic evidence,
not qualification of the distinct multiple-VM/SMP production profile.

Lengths are bucketed as nonpositive, 1, 2, 3-4, 5-8, 9-32, 33-128, and >=129.
Initial array cells differ from marker visits: the latter include tail marking.
Four-ahead slots count `max(n - 4, 0)`, not cache misses or saved operations.

Four independent processes import the original std/make, std/test,
std/encoding/json and std/list/list concurrently. Hardware budget is twelve;
there are four actual jobs, not twelve replicas. All exit zero with final OK.
Each uses the isolated selected library HOME and no consumer-package imports.

| Root | Calls | Single-cell calls | Marker visits | Initial cells | Four-ahead slots |
| --- | ---: | ---: | ---: | ---: | ---: |
| std/make | 4,141,007 | 2,567,935 | 12,162,500 | 9,563,111 | 1,595,242 |
| std/test | 2,877,410 | 1,734,548 | 8,357,011 | 6,496,506 | 1,043,502 |
| std/encoding/json | 5,583,887 | 3,530,197 | 16,403,210 | 12,973,047 | 2,173,289 |
| std/list/list | 2,877,405 | 1,733,799 | 8,357,742 | 6,495,745 | 1,043,500 |

Arrays longer than 32 account for only 0.357-0.538% of these visits; four-ahead
slots account for 12.485-13.249%. These are counts, not cycle shares or upper
bounds on elapsed gains. They do not locate cache-miss latency or establish a
Darwin/Linux cause. The old D1611 marker cycle share belongs to a different,
instrumented composition and cannot be multiplied by these counts to predict
savings on the frozen host.

Evidence: `.data/d1510-gc-array-census-runtime-v2/`,
`.data/d1510-gc-array-census-native-v2/` and
`.data/d1510-gc-array-census-stdlib-v2/`. Observed binary SHA256:
`d132a110c9a515cb829b390850a0714b9f485cc19f180727c9069e7c0de6b2a2`.

## Invalid First Census And Validation

The v1 census mistakenly converts negative empty-scan lengths to unsigned
before counting. All four imports complete, but the >=129 bucket cells cannot
cover its reported calls. That distribution is invalid and retained, not
overwritten or promoted. Corrected counting records negative lengths separately
and assigns zero cells to all nonpositive scans, matching the original loop.
The corrected real imports observe 1,650-1,980 negative empty-scan calls.
This was an observer bug, not a discovered production-GC correctness bug.

The validator checks all eight bucket bounds, total entry count, single-cell
count, negative empty scans, visit coverage and the exact four-ahead total.
Six Python checks pass. A separate genuine GNU C control exercises -4, -1, 0,
1, 2, 3, 4, 5, 8, 9, 32, 33, 128 and 129; it matches all expected bucket counts
and cells, 354 initial cells and 316 eligible slots. Evidence is under
`.data/d1510-gc-array-counter-boundaries-v1/`.
The combined framework/probe pytest run passes all twenty checks. The relink
framework now propagates a replacement's diagnostic-only flag to future link
receipts; existing construction receipts are not rewritten.

## Decision

### Follow-Up: Existing Hardware And Tail-Scan Evidence

The original retained CPU-counter recording was exported again without running
another workload. Its CountingModeSamples table has 114 rows, all resolving to
the recorded target PID 75903 and the frozen binary receipt: 36 High Delivery
Bottleneck, 64 High Discarded and 14 High Processing Bottleneck remarks.
These threshold remarks do not measure cache misses or attribute exclusive
memory latency. The presence of `l1d_miss_sampling` among available modes in
trace metadata is not evidence that L1-miss sampling was active. Evidence:
`.data/d1510-stdlib-counter-profile-v1/counting-mode-samples-v2.xml`.
The initial export is blocked by sandboxed Instruments cache access; the
subsequent normal-cache export succeeds. No new profile or workload runs.

Original mem.c's `scan` default branch uses `body+1, words-1` for movable
pointer-bearing objects; `scan_and_advance` uses `(ptr)+2, PAIR_SIZE-1` for
pairs. Both skip the first field already tail-marked by mark_array. A proposed
duplicate-first-field elimination would remove work the original already
omits and is not a new optimization.

D999-D1003 already reorder pair traversal without CPU gain. D1004-D1006
already batch strong GC-table fields through a descending stride-two marker,
with about 2.48% preparation CPU improvement but no mainline admission. The
tested binary also predates a later index-conversion correction. Neither
prototype is rebuilt or revived from this census. The exclusion index now
names these older routes explicitly to avoid another duplicate investigation.

Do not implement a large-array batching/prefetch patch from an assumption that
large scans dominate this workload. The measured distribution contradicts that
premise. Nor does four-ahead eligibility establish enough latency to justify a
new prefetch candidate. GNU's documented prefetch primitive requires valid
address-expression evaluation; nonfaulting prefetch does not permit an unsafe
future-root read. See [GNU builtins documentation](https://gcc.gnu.org/onlinedocs/gcc-8.2.0/gcc/Other-Builtins.html).

Short-array and tail-mark work remain distinct research boundaries. Previously
denied single-cell bypass, chunk/barrier, heap-floor and copy-unrolling candidates
remain closed. No compiler flags, timeout policy, std/make/std/test implementation,
production patch, commit or push changes. No fresh complete build/test result
or speedup is claimed. All owned processes are terminal; the full goal is active.
