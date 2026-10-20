# Retained Entry Objects: Real ASCENT Candidate

## Decision

Keep this cleanup experiment outside the frozen six-patch bundle and PR 49.
It demonstrates two additional existing-object HITs during a real source-change
rebuild, but does not qualify stable or substantial whole-consumer performance.
The complete 94-Suite ASCENT requirement remains open. No MCP package logic,
assertions, heap limit or worker count was changed.

## Actual Native Runs

All successful runs use the isolated project at commit
`21e3638687d42ecfc36acebb28991987435ebc60`, its Multiple-VM toolchain, GNU GCC,
12 hardware cores and the original 1-GiB heap setting. A comment-only change
forces the real entry rebuild. Bash launches the project's own native qualifier;
Python only parses completed receipts or tests utility argument handling.

| Owned receipt suffix | Wall | User | System | HIT | MISS | Cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| retained-entry-ascent-populate-v2 | 67.55 s | 112.58 s | 38.75 s | 0 | 72 | 30/30 |
| retained-entry-ascent-source-change-v1 | 68.64 s | 76.23 s | 34.34 s | 70 | 4 | 30/30 |
| retained-entry-ascent-proof-reuse-v1 | 57.07 s | 72.22 s | 33.91 s | 72 | 2 | 30/30 |
| retained-entry-ascent-cleanup-control-one-v1 | 67.19 s | 116.43 s | 38.66 s | 0 | 74 | 30/30 |
| retained-entry-ascent-cleanup-control-two-v1 | 59.65 s | 72.70 s | 35.03 s | 70 | 2 | 30/30 |

Each receipt is under `.data/d1510-`, with `time.txt`, `exit-status.txt`,
`output.log` and offline `qualification.json`. All listed runs exit zero and
have final OK. The executable-entry cache reports MISS throughout: these are
actual rebuilds, not skipped native executions.

The cleanup control uses the same compiler overlay but sets retention to zero.
The existing helper includes the entire sorted environment in its proof key;
changing this flag necessarily invalidates all old proofs. Therefore control
one is configuration population, not a performance comparator. Control two
uses the established control environment. Missing retained entry objects take
ordinary compilation and do not necessarily emit a helper MISS event; HIT/MISS
counts must not be mistaken for a complete GCC-call census.

The established candidate and control differ by 2.58 seconds (approximately
4.3 percent). There is one sample per established configuration, differing
comment fixtures and no matched repeated order. This is exploratory evidence,
not an admitted general gain. Do not repeat the invalid all-MISS comparison or
weaken environment invalidation to manufacture cache hits.

## Safety And Identity

The overlay changes exactly one successful cleanup site: on Darwin GNU GCC,
with both reuse and retention explicitly enabled, delete the regenerated C
files but retain the two entry objects. Default and non-Darwin cleanup are
unchanged. Failed compilation is not altered. Existing proofs remain mandatory.

Transformed source SHA256:
`fa5dfbb3a7691d69e6a8c5cd941c80f62dbb6125a93377a68319ce30fea920d3`.
Multiple-VM image SHA256:
`d53663f78c0071ec0d9008db33f982219060e09e9cf9b25d0d9a05e440149c4c`.
Transformer SHA256:
`7f27e33fc1ad785575f3aea7ceb6ac7831ca9fc503e83f1cdb18e8e87c4c8622`.
Runner SHA256:
`8a778c51b27b0bdff35d8332b0af365aedffb1b1f0937f3c6304f21fbd846e6b`.
Wrapper SHA256:
`4cf1656a63989416d1072088058465bd06e6c00d73e281295d2f7f6e951c141a`.

The proof-reuse run's before/after overlay identities compare equal. Its output
SHA256 is `065159a8623f8a3e5544bc69b508c27e7cd339fee096d87f041869482a53126d`.
The control-two output SHA256 is
`a50d69dd248df560d8054e4f470f903724b517f9b78a5630891735cd770e55d4`.

Population v1 is excluded: the initial wrapper injected an expression before
the runtime heap option and exited 70 with an unknown-option error. The corrected
wrapper preserves leading runtime options; four utility-only controls and the
native successful runs cover that correction. The combined wrapper, selected
home and receipt tests pass 23 tests; Bash syntax checks pass.

After testing, remove only the owned comment fixture and verify the isolated
project has no tracked diff. Verify the 1,992 toolchain and 2,809 dependency
dynamic images still reference their original read-only targets. The active
ASCENT checkout and shared dependencies are not modified.

The original frozen MCP lock independently verifies tools, patch bytes, raw
evidence and retained performance: first 3.950-4.038 s, cold 35.552-37.770 s,
complete tests 86.924 s with 965/965 passing. Its gates stay 4.5/42/97 s.
