# D1701: retained full-build timeline and unsampled counter boundary

The D1513 historical B complete build is 51.737180 seconds; the identical
D1510 binary in D1678's new A control completes in 71.946552 seconds. The
20.209372-second difference remains unexplained. The historical B mean
52.617045 seconds and complete-build ceiling of 55 seconds are unchanged.

## Retained artifact timeline

D1698/D1699 read retained artifact mtimes and original build logs; no new
complete build is run. Differences measured between artifact writes do not
depend on the approximate process-start anchor:

| Artifact-write interval | Historical B seconds | Current control seconds |
| --- | ---: | ---: |
| First C to last SCM | 18.433282 | 29.148262 |
| First C to last C | 40.285220 | 57.506708 |
| First C to last static object | 41.676922 | 58.749882 |
| Last static object to executable | 3.397179 | 3.962292 |
| Embedded C to its static object | 26.034419 | 41.162324 |

These are overlapping write intervals, not additive CPU or task durations.
They include queueing, intermediate work and output buffering. Executable
mtime is not process-exit time. A retained file could have been rewritten;
no unsupported historical environment or scheduler reconstruction follows.
The retained timeline places most of the observed extra write interval before
the last static object, rather than in the executable-write tail alone.

The one job-name multiset difference is now explicit: historical compile-file
`tools/howto-run~1.scm` versus current `tools/resolve-imports~1.scm`. This is
not asserted to be a temporary link name, semantically equivalent work, or
the cause of the time difference. Both reports still record 740 jobs.

## Counter observation without stack attachment

The diagnostic controller now has a strict `--verify-child-only` mode. It
requires the actual build child, checks proc_pidpath and the binary digest,
and does not invoke either sample or xctrace. It rejects relaxed observation,
clean-only and sampling combinations. Existing sampling commands and output
gates remain unchanged. Seven focused controller tests pass.

D1700 uses a fresh unchanged MCP clone, the already constructed D1694 counter
binary, loader flag zero, twelve physical workers and the original ten-second
output gate. Actual builder PID 84549 is verified; no sampler is attached.
The observation still fails the output gate before its first compile line.
There is no admitted first-write snapshot, successful prefix measurement or
performance ratio. This failure rules out sampler attachment as necessary
for this particular failed diagnostic; it does not prove why the diagnostic
and uninstrumented builds differ. Exit counters are not substituted for a
first-write snapshot.

Canonical v0.19-staging is checked in this turn and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. No product std/make, std/test,
GXPkg, consumer sources, GCC flags or runtime archive are changed in this
investigation. No candidate is promoted to a production performance patch.

Evidence: `.data/d1698-retained-build-timeline/`,
`.data/d1699-retained-build-timeline-and-jobs/`,
`.data/d1700-context-burst-unsampled/`.
