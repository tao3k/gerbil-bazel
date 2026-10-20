# Reader Extension Source Boundaries

This investigation follows the frozen reader candidate and the live 5/50 guard
DENY. It does not admit a new optimization or replace that failed result.

## Actual Remaining Test Stops

The retained 39-file wave has eight denied files:

- balance, cookbook, json-store, loadpath, verify: no first test output before
  the five-second real-output-gap watchdog. These are pre-output stalls, not
  established assertion failures or established macro-expansion attribution.
- chunk-03: last real case started `gerbil_bisect_crash keeps preamble forms`.
- chunk-07: last real case started `gerbil_howto_verify checks built-in recipes`.
- chunk-12: last real case started `scans a real binary (gxi)`.

The three latter files already emitted real CASE-OK output. They must not be
combined with the five pre-output failures as one generic startup problem.

## Source Findings

Gambit `_io.scm` `##build-escaped-string-up-to` reads its ordinary string
characters one at a time via `macro-read-next-char-or-eof`. `_io#.scm` maps
that macro to `##read-char1`; `gambit.h.in` `___READCHAR1P` performs primitive
trylock/unlock around each buffered character. The frozen token optimization
only replaces `##build-delimited-string`, not this string-literal path.

The MCP `util/json-store.ss` imports `data/embedded`, whose source contains large
quoted data strings. This establishes an uncovered parser path, not its measured
share of total startup time and not the cause of every pre-output stall.

Any future string-span candidate must retain the original escape decoder,
readtable-specific escapes, octal and hexadecimal rules, Unicode behavior,
backslash-newline handling, delimiter consumption, EOF diagnostics, buffer
identity, cursor concurrency checks, GC rooting, and line/column accounting.
It must fall back without consuming on unsupported input. The original reader
candidate and its recorded hashes must remain unchanged.

The binary audit calls `strings`, then `file`, then classifies each captured
string with Scheme regular expressions. MCP `proc.ss` captures subprocess output
using `read-substring`, not `read-line`. Gambit `##read-substring` already holds
the port lock across buffered transfers and uses `##substring-move!`. Therefore
batching `read-line` is not justified as an optimization for that capture path.
No MCP business code or std/test code was changed during this source audit.

## Cold Regression Boundary

The live 5/50 run's first compile log was 4.793609375 seconds. Its build was
stopped at 50.037967500 seconds and reaped. The last log was still in executable
object compilation; there is no completed build time to report.

Structured configuration comparison against the first 46.652867625-second run
found equal driver SHA, GCC version, captured file hashes, and all environment
values except the isolated project's `GERBIL_LOADPATH`. This does not establish
the cause of the wall-clock regression. No resource-contention explanation is
claimed, no configuration tuning is admitted, and no failed run is discarded.

Hard admission remains first compile log <= 5 seconds and complete cold build
<= 50 seconds. A failed candidate stops immediately and cannot become the next
performance baseline.
