# D1449: missed rest-dispatch coverage does not admit a larger accelerator

## Current Source Observation

D1444 uses the original GSC from the common current D1391 toolchain and the
current core, stx, mop and util SCM inputs. It retains the D1307 fixed-target,
exact-arity, immutability and dispatcher-shape checks, but observes what shapes
would pass without its bounded early-poll predicate. No candidate code is
emitted. Generated C is byte-identical to the current baseline in all four
units, and input hashes are unchanged. Twelve hardware-derived workers are
configured; only the four owned units are processed.

There are 55 additional dispatcher shapes: core 14, stx 7, mop 6 and util 28.
Examples include foldr/foldl, stx-map, the four-argument datum->syntax branch,
and later branches of core expansion dispatchers. These names are diagnostic
attribution, not a production allowlist. A shape count is not dynamic coverage,
an implemented optimization or a performance measurement.

The existing classifier stops at the first branch whose safety is unsupported.
Thus later otherwise-supported branches also belong to the missed suffix.
The new offline association preserves that order; it does not indiscriminately
count every branch in a partially supported dispatcher.

## Association With Retained Work Counts

D1448 reads the saved Scheme diagnostic forms with Gerbil's actual reader and
joins them to the retained D1334 rest-size histograms. It admits only plain
rest-only entry rows with subprocedure ID zero and exact observed arities below
eight. Bucket eight is overflow and is never treated as exact argc eight.

| Matched recorded entry | Potential pairs | Potential raw bytes |
| --- | ---: | ---: |
| foldr, arities 3 and 4 | 1,256,509 | 30,156,216 |
| stx-map, arities 2 and 3 | 69,542 | 1,669,008 |
| datum->syntax, arity 4 | 30,828 | 739,872 |
| core-deserialize-mark, arity 2 | 5,526 | 132,624 |
| All admitted matches | 1,362,729 | 32,705,496 |

These are potential removals in the **retained preparation corpus**, not an
exclusive current official-first-window allocation count. Unmatched shapes
remain explicitly listed in the private report; absence of a matched row is
not a general zero-work proof. No new allocations are eliminated and no CPU
or wall-time ratio follows from the byte counts. The result cannot be combined
arithmetically with D1439's startup reduction to manufacture a larger speedup.

## Safety And Priority

The existing early-poll restriction is a safety contract, not evidence that
Gambit cannot optimize any such function. Current gambit.h:8510-8536 checks
stack-trip state and, when configured, heartbeat countdown at the actual poll
boundary. A proposed fast arm would need to preserve requested polling,
argument/frame/GC maps and the original fallback; simply returning true from
the classifier does not prove those obligations. This turn changes the predicate
only inside a diagnostic observer and never in a production emitter.

Do not activate wider arity forwarding based on these shape counts. Its admitted
allocation opportunity is substantially smaller than the already measured
135,975,888-byte combined forwarding elimination, whose current matched startup
benefit is only modest. That comparison motivates priority, not a mathematical
CPU-speed bound. The requested major startup optimization remains unachieved.

## Evidence And Retained Failures

Observer: `.data/d1444-rest-poll-eligibility.py` and
`.data/d1444-rest-poll-eligibility.scm`; evidence is
`.data/d1444-rest-poll-eligibility/report.json` with original logs.
Association: `.data/d1445-rest-poll-potential.py` and
`.data/d1445-rest-poll-potential.ss`; authoritative output is
`.data/d1448-rest-poll-potential-json-writer/report.json`.

D1445 fails on an incorrect JSON module path, D1446 on an unavailable SRFI
import, and D1447 on an obsolete one-argument JSON writer call. Their raw logs
remain retained. The current staging JSON source supplies json->string; D1448
uses that API and finishes successfully. None of these reader-tool repairs is
a product optimization or a reason to alter Gerbil std libraries.

No production patch, compiler flag, consumer source or installed toolchain
changes. All owned diagnostic processes are terminal. The full goal remains
active, with major first-log cost and broader build/test qualification unresolved.
