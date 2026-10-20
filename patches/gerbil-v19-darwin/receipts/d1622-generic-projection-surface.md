# D1622: generic projection discovery expands the executed opportunity

## Implementation and controls

D1619 adds a private structural discovery prototype using the existing Gambit
generated-procedure and macro parsers. It selects no Gerbil names. It recognizes
a directly installed return label followed immediately by SET_R1(CAR(R1)) or
SET_R1(CDR(R1)). The returned pair is overwritten before any other generated
instruction can retain it. This is only a consumer projection fact, not a
producer purity proof or authorization to delete evaluation.

The prototype refuses a pair copied before projection, an intervening global
write between return installation and call, and unknown generic calls. Local
and global calls plus a direct frame adjustment have focused controls. All five
controls pass. No product code, consumer Scheme, installed toolchain or Linux
behavior changes. No new MCP timing run is performed.

## Current source surface

D1620 finds 382 immediate projection sites in 16 current generated static
modules. Of these, 97 call syntax-e: 18 CAR and 79 CDR. The analyzer does not use
that callee name to select sites; these counts are a post-discovery summary.
Most other sites call stx-e, which is not evidence of two discarded fold paths.
Do not transfer the syntax-e opportunity to those procedures.

The previous two high-frequency CAR sites are recovered structurally:
core-expand1 continuation 15 and core-expand-head continuation 5. The frame
adjustment before the latter call is represented explicitly rather than silently
assumed absent. These facts can supply a future generic return-continuation
specialization pass; they do not emit a replacement ABI or accelerator.

## Reuse of the existing executed census

D1621 joins the original D1344 pair-return census by procedure name and relative
continuation ID only after confirming a unique projection site and byte-identical
entire generated consumer body between the historical D935 and current D1391
sources. File hashes differ, so whole-file identity is not claimed. The report
retains current source hashes, consumer-body hashes and the census receipt hash.

| Historical executed projected returns | Sites | Calls |
| --- | ---: | ---: |
| CAR | 2 | 1,370,219 |
| CDR | 14 | 416,024 |
| Total | 16 | 1,786,243 |

Largest newly attributed CDR-only consumer:
rename-macro-expander::apply-macro-expander continuation 4, 308,302 pair returns.
Next is macro-expand-let-values__% continuation 13, 51,081 returns. The two
macro-expand-if continuations each contribute 11,694 returns.

This expands the historically executed candidate surface beyond the previously
prioritized two CAR consumers without repeating counters. A CDR-only consumer
would require proving the first fold dispensable, whereas a CAR-only consumer
would require proving the second fold dispensable. Evaluation order, global
binding changes and escapes established in D1617 remain requirements in both
directions. Counts are historical input ownership, not current CPU shares,
removed wrapper counts, seconds saved or a performance result.

## Decision

Proceed with generic producer effect/termination summaries and projected-return
eligibility; do not implement a procedure-name allowlist. Consumer projection
alone is insufficient, and all report rows remain effectElisionQualified=false.
The 55-second full-build ceiling and actual first-log/concurrent std/make/std/test
acceptance remain unchanged and unmet. No optimization is promoted by this audit.

Private evidence: .data/d1619-projected-call-sites.py,
.data/d1620-projected-call-sites/report.json,
.data/d1621-projected-call-sites/report.json, and the unchanged
.data/d1344-syntax-pair-consumers/report.json.
