# D1510 Two-Word GC Copy Specialization: Denied

The frozen reader-whitespace host remains selected, with historical complete
cold builds 47.771713 / 47.824226 / 47.927094 seconds. Active acceptance remains
first real compile <=5, complete cold build <=50 and complete tests <=112
seconds. No new optimization is admitted by this experiment.

## Different Source Mechanism

Existing D1008 counts record 18,067,589 exact two-word copied objects out of
43,237,938 copies; these are coverage counts, not CPU attribution or a speedup.
The old bulk-memcpy premise is unsupported because GCC already vectorizes
larger copies. Inspection of the actual original RTS mem.o nevertheless
confirms that two-word objects take the scalar counted copy loop: `_mark_array`
at object offset 0xcc0 selects the short-object branch to 0xe1c, whose loop at
0xe24 performs each load/store with decrement and conditional backedge.

A private Darwin/GNU/non-Clang, single-VM/single-threaded/one-processor,
eight-byte-word, no-handles branch performs exactly the two original sequential
assignments before advancing body/alloc by two and setting words to zero.
Other sizes and platforms retain the exact original loop. No restrict
assumption, changed heap size, barrier omission, marker-entry shortcut,
forwarding change, weak-table policy or traversal reordering is introduced.
Header publication, cell repair, tail marking and chunk handling are untouched.

Candidate mem.o contains the new `words == 2` branch and two sequential scalar
load/store pairs; static emission is not runtime-cost admission. This is not
the rejected no-copy single-cell marker entry, or a large-object memcpy retry.

## Construction And Controls

Original GNU compilation reproduces original mem.o exactly:
`284504db424c05a2584759cf9f74abd1c576d79f95f6f3ad074514086710f553`.
Independent control linkage reproduces frozen host SHA256 exactly:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Original input hashes remain unchanged. Candidate SHA256:
`bc2acc3c25b983c2e69632cde4a0236f8196f607e97f82c53bc21745562f57b3`.

Original/candidate each pass nine named cases, final
`OK two-word-copy-semantics` and exit zero: shared/cyclic pairs, two-word
vector/string, other-size fallback, closure roots, captured continuation roots,
weak live roots, and 24 explicit GCs retaining 10,000 mixed graphs per round.
These are focused moving-GC controls, not complete collector conformance.
Ordered whole-process times are 1.233970 / 2.569625 seconds; they are neither
isolated copy timings nor evidence of acceleration. Six source/hash checks pass.

## Actual Independent Standard-Library Gate

The real unified stdlib attempt uses twelve physical workers and unchanged
common GSC. Official clean exits zero in 7.667569 seconds. The subsequent
build produces no qualifying first compile line by 5.014730 seconds and is
DENY against the unchanged five-second gate. That number is the deadline
observation, not the actual first compile latency. The process group is killed
and reaped, exit -9, with no cleanup errors.

Complete build and test durations are unknown. Tests and the downstream heavy
cold campaign are skipped. A gate failure alone does not establish that this
source change caused the observed latency. No repeated run or deadline change
is used to promote it. Close this deployment; do not widen/unroll/retune the
same copy specialization as a new major-cost candidate.

Evidence:

- `.data/d1510-two-word-copy-runtime-v1/report.json`
- `.data/d1510-two-word-copy-native-v1/report.json`
- `.data/d1510-two-word-copy-controls-v1/report.json`
- `.data/d1510-two-word-copy-stdlib-v1/report.json`

All owned sessions are terminal. No production patch, std/make/std/test,
consumer business source, AOT configuration, installed toolchain, commit or
publication is changed. Full optimization objective remains unachieved.
