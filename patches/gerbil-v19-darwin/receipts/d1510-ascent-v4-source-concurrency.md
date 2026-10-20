# V4 Real Source Invalidation And Concurrent Entry Calls

Status: source identity and concurrent consumer entry safety PASS; no new
performance admission. All work is in the owned tool-upgrade fixture, not the
active ASCENT checkout or frozen original workspace.

## Review Before Execution

Correct route: complete V4's missing real-consumer source/concurrency checks.
Prior native controls exercised these properties in object fixtures, and the
actual tool upgrade passed 90 Cases, but neither proved two simultaneous
consumer calls after a real source change. This safety check is required before
extending reuse. Expected speed benefit is zero; the source change must invalidate
the entry. No rejected cold candidate or unchanged speed experiment is reopened.

The only tracked consumer change is one appended comment in
`t/qualification/ascent-positive-plan-test.ss`. Every assertion and Suite remains
unchanged. Original source SHA256:
`ff5e7f164b2adf817486191604174e349d934a0e18345ba2cd9791824bf5f451`.
It matches the previous admitted executable receipt's source input. Modified
source SHA256:
`96157b87887b496be7655bbf83a92998f04459ed524b9930ed1273ae2793fe6c`.

The direct launcher retains clean tracked-source requirements by default. An
explicit eighth argument permits only an exactly hashed fixture diff, checked
before and after execution. This fixture's `git diff --binary HEAD` digest is
`19078bbc7f7979ac24c16c5b275fc47d3e5d2ed95f790edfe8ad557a04400dda`.
There is no generic dirty-source bypass. A wrong digest is rejected before
native launch (`.data/d1510-ascent-v4-source-diff-denied-v1`, exit 1, no output log).

## Direct Native Results

`.data/d1510-ascent-v4-source-concurrency-v1` launches two Bash/just/Scheme native
qualification tasks concurrently in the same owned workspace. Both process
handles are waited and both exit statuses retained, including on failure.
The existing consumer advisory lane lock owns compilation and Case execution;
this does not claim simultaneous compilation inside that lane or a new
parallel-speed improvement. Original 135-second whole-task and 120-second
lane-lock bounds are unchanged. No Python supervises the native tasks.

| Call | Wall Seconds | User / System Seconds | Entry | Cases |
| --- | --- | --- | --- | --- |
| 2, lane owner | 68.81 | 112.67 / 35.17 | MISS, rebuild | 30/30 |
| 1, waiter | 74.81 | 6.68 / 2.25 | HIT after owner | 30/30 |

Both exit zero and contain the final `OK`. Exactly one entry MISS and one HIT
occur, without deleting receipts. The HIT task has no static object events,
but still executes every Case. The newly admitted executable receipt binds the
modified source SHA256 above. The waiter wall time includes waiting and must not
be reported as an intrinsic test-body or cache-hit duration.

The rebuilding task has 72 static object MISS events and no HIT. This does not
reproduce V4's earlier 71 object HIT observation and does not justify claiming
object-reuse savings in this configuration. Which key component changed remains
unresolved; source invalidation at the consumer entry is proven, but attributing
all object misses to the single comment is not. Preserve exact context/tool/env
checks while investigating; do not remove them to manufacture cache hits.

Raw output SHA256:

- Call 1: `b3e62dd4558aad8649de6e12a470365ba160dca183565c4d4d96f9a0145c1545`
- Call 2: `7495bf0df23f38e0ede2c0f951a77a0396fdb353385f2c97fc563517d49c5047`

Post-run checks verify 1,992 immutable toolchain and 2,809 dependency images.
The frozen original consumer's tracked diff is empty. MCP's five patches,
measured driver and runtime still pass their separate identity lock.

## Remaining Scope

This closes the tested source/comment and cooperating-caller concurrency
scenarios, not all source mutation shapes, options, failures or proof races.
Primitive object concurrency remains separate evidence. Complete package-cold
and complete dual-consumer build/test performance still require qualification.
No MCP timed run, stable object-cache gain, default enablement, latest-staging
rebuild, commit, push or goal completion is claimed.
