# D1510 Terminal Driver Exec: Not Admitted

Decision: retain the original 0015 driver. No production runtime/driver patch,
AOT/CI change, MCP speedup, commit or publication is admitted. This is a new
terminal-process mechanism, not a retry of metadata omission or filename quoting.

## Reached Native Parent Control

The original `gambuild-C` finishes object, dynamic and executable cases through
shell `eval`. A GNU GCC 16 native PID/PPID probe replaces only the compiler in
an isolated invocation. The original compiler is a child of the retained driver
shell. In the private terminal-exec object prototype, the compiler replaces the
driver PID and its parent is the controller. The probe checks these relationships,
rather than inferring a fork from source text alone.

Original and object prototype receive the same ten compiler arguments. Both
propagate compiler exit status 7. A compound command in compiler options takes
the original eval fallback and executes its following printf. Shell syntax
checks pass. These narrow controls do not prove arbitrary quoting, all compiler
overrides, wrappers, signals, dynamic/executable variants or full runtime semantics.

GNU compilation uses the system compiler-tool path and selected macOS SDK.
Earlier probe links through the inherited non-system linker fail before any
probe runs; they are not runtime failures or candidate timings. No Clang
compilation is used.

The isolated candidate retains all 0015 metadata processing, substitution and
flags. It selects terminal exec only under the existing Darwin/GNU selector,
an executable leading compiler word and a conservative single-command filter.
Shell metacharacters or unsupported shapes fall back unchanged. This guard is
a private experiment, not a reviewed production shell parser.

## Independent Standard Library Clean/Build/Test

The existing runner now accepts an explicit `.data` Gambit driver and records
its relative path and SHA256. GSC remains original, and `GAMBOPT` selects the
isolated bin directory. No new Python runner is introduced. Both runs use
12 physical-core-derived workers and unchanged whole-task 5/50/112-second gates.

| Metric | Original 0015 control | Terminal-exec candidate |
| --- | ---: | ---: |
| Clean | 5.754870 s | 3.898471 s |
| First real compile | 4.964795 s | 3.603313 s |
| Complete standard-library build | 12.282235 s | 11.551909 s |
| Complete standard-library test wave | 10.184959 s | unknown / incomplete |
| Verified test cases | 65/65, two files | none verified; completeness unknown |

These are standard-library list/JSON fixtures, **not MCP complete builds/tests**.
The control checks source, binary and driver identity unchanged. The candidate
has two empty test logs, and the old runner raises while verifying completeness.
It consequently loses the per-process results; the cause and exact test
duration cannot be reconstructed from that receipt. Do not assert a first-log
timeout, crash, runtime correctness failure or a duration from this missing data.
Overall candidate command exit is 1. No end-to-end candidate admission follows.

In particular, terminal compiler exec occurs after the first compile message.
The observed first-log decrease cannot be attributed to this mechanism. One
sequential pair does not establish a stable build speedup, even before the
incomplete tests are considered. Do not rerun or retune this deployment merely
because its build observation is lower.

The test runner now retains process DENY/exit/timing fields even when complete
case verification fails, leaves cases null, and cannot promote process failure
because some case lines exist. Missing final/case evidence also rejects exit 0.
Selected standard-library and three-gate framework tests: 20 passed. This
repairs future evidence preservation; it does not recover the lost candidate
results or retrospectively pass its tests.

## Identity And Evidence

- Frozen binary: `1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
- Original driver: `65aba56445c2b165b667922603873aec9e58ad3edb733c6d040651eecf6d8d15`.
- Candidate driver: `68fa34863567707300f480e03f91532fa3c3585cf2c8fc8f1281d4cf2203935a`.
- Parent probe/private source: `.data/d1510-driver-exec-parent-v1/`.
- Completed original control: `.data/d1510-driver-exec-stdlib-control-v1/report.json`.
- Incomplete candidate: `.data/d1510-driver-exec-stdlib-candidate-v1/report.json`.

The current MCP anchor is not replaced: historical cold builds remain
47.771713 / 47.824226 / 47.927094 seconds, with a complete historical
105.750982-second, 39-file/965-case test. Current acceptance remains <=5 seconds
first compile, <=50 seconds cold build and <=112 seconds complete tests. All
owned probe, build and test sessions are terminal. The mainline goal is active.
