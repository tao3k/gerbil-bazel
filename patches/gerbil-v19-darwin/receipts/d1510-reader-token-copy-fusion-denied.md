# Token Copy Fusion: Semantic Pass, First-Log DENY

Research starts from the published whitespace cold checkpoint, commit
`e3f349bab5a234c6ec2cd432faeb843d03c9c115`. The 47-second baseline and all
its hashes remain unchanged. This candidate contains no FD, private-archive,
string-span, HOME, compiler-flag or consumer-source change.

## Source Mechanism

The original token fast path scans the buffered token, allocates and initializes
its private destination string, reacquires the primitive port lock, validates
the complete token and delimiter, then traverses it again to copy characters.

The candidate preserves scan, allocation, prefix fill, locks, length bounds,
buffer/cursor identity checks and full revalidation. It combines revalidation
with writes to the still-private destination. It accumulates newline metadata
locally and commits port cursor/line fields only after complete token and final
delimiter validation. Failed validation returns false without committing port
state; the temporary string does not escape. No uninitialized allocation,
readtable cache, prefix specialization or early port consumption is introduced.

This removes a redundant traversal in source; it is not evidence of a measured
user-visible speedup. The runtime linker object is byte-identical to the
whitespace checkpoint, and no Scheme globals are added or removed.

## Actual Controls

`.data/d1510-reader-token-copy-controls-v1/report.json`: all **48** controls
pass, exit zero, final OK, 1.127502417 seconds. These retain all 45 parent
controls and add Unicode-prefix/multiple-newline contents, exact multi-line
position and unconsumed delimiter checks. Two focused Python source-boundary
tests also pass. These controls cannot substitute for performance admission.

Candidate binary SHA256:
`ebe974bf611f580416cc77cc1b375789f5a18b866aa529b52202fc0a62a55b14`.

## Real Cold Gate: DENY

`.data/d1510-reader-token-copy-progressive-v1/report.json` records:

- Clean: exit zero, zero native images.
- First actual compile log: none before deadline.
- First-log watchdog: DENY at **5.000896541 seconds**, ceiling 5 seconds.
- Process killed and reaped with terminal exit -9.
- Sources unchanged; no complete build duration exists.
- Remaining cold rounds and complete test wave: SKIP.

Do not report the deadline observation as first-log latency or complete build
time. Do not infer that this source change caused the deadline failure, or
claim a speedup from fewer source traversals. The candidate is not published
or promoted; this fusion route is closed for retuning/repetition under the
current evidence. The published parent remains the selected cold checkpoint.

Private construction evidence:

- `.data/d1510-reader-token-copy-runtime-v1/report.json`
- `.data/d1510-reader-token-copy-native-v1/report.json`
- `.data/d1510-reader-token-copy-controls-v1/report.json`
- `.data/d1510-reader-token-copy-progressive-v1/progressive-admission.json`
