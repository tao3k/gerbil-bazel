# D1510 Original Compile Job Closure

Compare retained D1513 B1 artifacts with the latest original D1510 cold build,
not the rejected memo or grouped-emitter binaries. No new build is run.

## Producer Classification

Each log has 549 strictly parseable compile-file jobs: 186 runtime modules,
186 loader modules and 177 phi modules. Runtime `~0.scm`, loader `.scm` and
phi `~N.scm` have different producer contracts; their count cannot be presented
as hundreds of duplicate runtime C compilations.

Both logs contain interleaved compiler output around another job. Historical
output preserves its compile-file marker but breaks its pathname; current
output splits the marker itself. The current fragment names
`tools/explain-error~1.scm`. Preserve this uncertainty rather than comparing
549 versus 550 as a missing operation or silently repairing the log. These
are job-scheduling records, not a live GCC invocation profile.

All 186 runtime producers in both builds have byte-equal runtime/static C
copies, a static object and dynamic bundle. Each object is at least as new as
its static C and runtime SCM, and no newer than its bundle. This supports
intact producer reuse but does not prove no later identical rewrite occurred.

## Executable Jobs

Both logs have 189 executable-object jobs. Of these, 186 correspond to the
runtime producers above. The remaining three are:

- `static/gerbil-mcp__main.c`
- `bin/gerbil-mcp__exe.c`
- `bin/gerbil-mcp__exe_.c`

The original compiler's object job logs before checking freshness. Its actual
GSC `-obj` invocation is conditional on missing/stale output, including the C
input timestamp. Therefore 189 logged jobs are not evidence of 189 repeated C
compilations. The three unmatched files cannot be assumed to be equivalent
runtime objects simply because their filenames resemble other outputs.

## Decision

No uncovered whole-runtime second compilation is established. Do not modify
0007 or remove freshness checks based on this audit. The earlier admitted
process census already observes zero Gambit fork calls in the real build;
the simple producer-fusion experiment is also already recorded. Neither is
rerun or promoted to a new large performance opportunity.

The 51.737180/53.496910-second historical references, 56.255963-second fallback
and 55-second admission ceiling remain unchanged. Latest original full build
is still 56.869967 seconds. This closes a candidate hypothesis, not restoration,
test acceleration or performance admission.

Private evidence: `.data/d1510-compile-job-closure-v4/report.json`. Earlier
private attempts retain their failed count assumptions; they are not qualified
reports. Original source, runtime, GSC, carrier and selected binary are not
modified. See also [the real process census](d1469-real-process-census-and-extension-boundary.md).
