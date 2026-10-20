# D1510 Original Test Prefix Boundary

This tests the original D1510 binary against the project produced by the
56.869967-second original-only cold build. It does not select a candidate or
change the 55-second build ceiling. The binary remains SHA256
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.

## Uninstrumented Official Test Wave

Run official `gerbil test -v 5` for each of the thirteen unchanged MCP unit
files, using twelve physical workers and the original runtime home. Keep the
existing five-second real-output silence gate and ninety-second per-invocation
wall gate. Do not precompile the tests or substitute a custom Scheme harness.

Only regex passes: all nineteen cases, final `OK`, exit zero, unchanged source;
its first output is 3.055198 seconds and full invocation is 3.306918 seconds.
The other twelve invocations exceed the silence gate before any captured output
and are terminated/reaped. The entire scheduling wave is 9.118132 seconds,
including cancellation and the thirteenth queued file. This is not the full
test-suite completion time or a slowdown ratio. The controller exits one.

Private evidence: `.data/d1510-full-closure-original-unit-wave-v2/report.json`.
The initial attempt is rejected before workload execution because the sandbox
denies hardware memory discovery; it is not counted as a test measurement.

## Native Observer Boundary

A separate diagnostic wave attaches macOS `sample` for two seconds to the
original `parse-test.ss` process. Sampling succeeds. The main-thread graph
contains 1,651 samples, including 1,266 under Gambit `___dynamic_load` and
781 under dyld `RemoteNotificationResponder::blockOnSynchronousEvent`.

These are sampled stack observations, not active-cycle attribution. The
attached observer can induce debugger image notifications. Therefore this
capture does not establish that dyld dominates uninstrumented tests, cannot
be used to subtract loader time from a test result, and does not justify a
Darwin loader patch. The recorded Scheme/GC leaves also do not establish that
test startup has the same distribution as the prior builder CPU capture.

Private evidence: `.data/d1510-original-test-prefix-sample/report.json` and
`baseline-4/prefix.sample.txt` beneath that directory. The diagnostic report is
explicitly unqualified regardless of individual passing files.

## Decision

The private runner now permits an original-only wave and propagates failure
through its exit code; previous reports are preserved. No toolchain, consumer,
std/make or std/test source changes. Both owned waves are terminal and all
supervised children are reaped. The original baseline and historical fallback
remain selected. Neither complete-build restoration nor test acceleration is
proved, so no performance admission or PR follows from this receipt.
