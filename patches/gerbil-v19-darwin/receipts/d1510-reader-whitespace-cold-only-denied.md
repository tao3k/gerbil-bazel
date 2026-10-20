# Whitespace Reader: Cold Gate Passed, Full Admission Denied

This isolated candidate extends the frozen Darwin/GNU token reader with a
no-allocation whitespace skip. It contains neither the rejected string-span
candidate nor the fork-FD candidate. The original HOME, RTS archive, compiler,
program carrier and frozen reader artifacts remain unchanged.

The helper takes one primitive port lock, checks the actual readtable handler
for each buffered ASCII character, and updates the original cursor and newline
fields. Custom handlers, Unicode, comments and empty buffers keep their
original boundaries. Normal reading still dispatches the next datum through
the original reader.

## Semantic Controls

`.data/d1510-reader-whitespace-controls-v4/report.json`: 45 controls passed,
exit zero, final OK, 0.737086875 seconds. These include custom readtables,
Unicode fallback, actual datum reads, exact line/column positions, long inputs,
and 129 successive buffer chunks with GC between chunks.

Earlier controls assumed a 4096-character batch, then incorrectly assumed a
512-character string-port buffer. The original source distinguishes 32-character
u8vector-kind character buffers from ordinary 512-character buffers; the actual
string port returns 32. The failed v1/v2/v3 controls remain recorded. The final
control checks the first 32-character batch and exactly 4100 consumed spaces in
129 chunks. No candidate implementation was changed to satisfy this fixture.

## Real MCP Cold Builds

`.data/d1510-reader-whitespace-progressive-v1/report.json`:

| Round | First actual compile | Complete cold build | Decision |
| --- | ---: | ---: | --- |
| 0 | 4.850865875 s | 47.771712542 s | ALLOW |
| 1 | 4.573628042 s | 47.824226292 s | ALLOW |
| 2 | 4.592897458 s | 47.927093625 s | ALLOW |

All three clean operations exit zero, leave zero native images, retain the same
MCP source hashes, and complete with exit zero under the first-log 5-second and
complete-build 50-second gates. These results demonstrate gate retention, not
improvement over the frozen reader's historical 46.65--47.83-second runs.

Candidate binary SHA256:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.

## Full Test Wave: DENY

`.data/d1510-reader-whitespace-progressive-v1/tests/report.json` records the
unchanged 39-file/965-case inventory, 12 workers, 49.983260167-second wave,
22 files passed and 17 denied by the existing real-output-gap watchdog.
This is not 965 successful tests and not a complete test pass. No assertions
were removed and no timeout was widened. Denied processes are stopped/reaped
by the existing runner. The progressive pipeline's final decision is DENY.

This candidate cannot replace the anchor or be submitted as an admitted
performance patch. No suite acceleration or causal explanation for the
additional denied files is established by this single wave. Further tuning of
this implementation is not justified by these results; preserve it as a
negative investigation, not a new mainline.
