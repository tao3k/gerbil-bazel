# D1510 Bound-Symbol Native Candidate: DENY

## Scope and Construction

This experiment follows the symbol-root census and shadow comparison in
[the preceding validation](d1510-build-test-validation-and-symbol-eval.md).
It tests a native candidate, not an interpreted timing proxy. It does not
modify std/make, gxtest, MCP, the original runtime home or selected binaries.

The private candidate uses the original D1510 RTS and forty-one unchanged
native objects. One expander/init object is regenerated to select a guarded
Gambit global-reference evaluator; the original eleven-unit outline carrier
recipe is regenerated against these inputs. Source hashes of the original
forty-two modules remain unchanged. All artifacts are repository-local.

The generated helper checks Darwin/Mach/GNU and excludes Clang. It accepts only
the standard expander hook, normal Scheme-source mode, a disabled reference
step handler, a Gerbil noexpand-prefixed symbol, a fresh CTE not-found result
and a bound global value. Other paths delegate to ordinary ##eval. No old
lookup, value, compilation context or result is cached. This is a private
Gambit execution-entry prototype, not a published Gambit or Gerbil patch.

## First Revision: Inert Guard

The first binary is SHA256
`0cfbe341451120320417314264d2396b338d8d3a603b186643cea9eba75e127a`.
Twelve value/error controls initially pass, but a later eligibility control
fails: default ##current-stepper is not pointer-identical to ##no-stepper.
Those controls exercised fallback and are NOT proof that the fast path ran.
The thirty-nine-file wave passes twenty-six files, including all thirteen unit
files; it remains failed. This does not establish a performance regression or
win for an active fast path.

The cold controller is interrupted after this failure is established. Its
original run completes at first compile 6.673280 seconds and complete build
48.963521 seconds. The first candidate build is terminated after first compile
4.932819 seconds; it has no complete build time. All owned children are reaped.
Admission is DENY. Neither the truncated candidate nor the interrupted ABBA
sequence is a performance comparison.

Private evidence: `.data/d1510-bound-symbol-native/`,
`.data/d1510-bound-symbol-all-tests/`, and
`.data/d1510-bound-symbol-cold-abba/`.

## Second Revision: Actual Reference Handler Guard

Gambit `_eval#.scm` macro-reference-step! uses outer stepper slot six;
macro-step! checks that slot directly. The default stepper's handler template
contains procedures, while this active slot is false. Revision two therefore
checks the real reference-step slot rather than stepper object identity.

Native binary SHA256:
`14e3488a5b957f2a00a572edfe1dcaaa2e47aab6df5a86acba1507300dc5059c`.
Thirteen controls pass, including an explicit eligibility control. The active
reference-handler control observes two callbacks, one from ordinary eval and
one from candidate fallback, with equal values. Namespace resolution, macro
as variable, unbound variables, false/void/identity values, fresh mutation and
a custom source hook are also checked.

The actual thirty-nine-file CLI wave uses twelve hardware workers, the same
MCP project and original runtime home, admitted 0015 driver, unchanged inputs,
five-second actual-output watchdog and ninety-second invocation watchdog.
All child tool entrypoints select the candidate binary. All thirteen unit
files pass their 177 cases. Twenty-nine of thirty-nine files pass all gates.
The same ten integration files fail as the original full-file wave:
03, 05, 06, 07, 10, 12, 15, 18, 21 and 23. First output ranges from
1.549591 to 3.442660 seconds. The scheduling/observation wall is 43.144397
seconds and the controller exits one.

This time contains failed/terminated invocations, is not successful full-suite
completion, and is not a causal speedup versus the earlier 52.195490-second
original wave. The test project was built by the original compiler; this wave
does not qualify every newly compiled candidate consumer product.

Private evidence: `.data/d1510-bound-symbol-native-v2/` and
`.data/d1510-bound-symbol-v2-all-tests/`.

## Complete Matched Cold ABBA

All four runs use independent source-identical clones, original runtime home,
GNU GCC 16.2.0, twelve physical workers, original GSC, the same admitted 0015
driver and the original VM/outline recipe. Only the selected Gerbil binary
differs. The baseline driver is explicitly matched rather than accidentally
using the older home driver. Official clean leaves zero native images in every
run. Each clean/build exits zero, the executable exists and source hashes remain
unchanged. No debugger or synthetic progress is introduced.

| Run | Clean | First compile | Complete build | 55-second build gate |
| --- | ---: | ---: | ---: | --- |
| A1 original | 2.789290 s | 4.935083 s | 48.318466 s | PASS |
| B1 candidate | 2.769167 s | 5.174668 s | 47.323533 s | PASS |
| B2 candidate | 2.411445 s | 5.250318 s | 51.019967 s | PASS |
| A2 original | 2.869633 s | 5.126438 s | 49.420934 s | PASS |

Unchanged thresholds: clean wall 30 seconds, build actual-output gap
10 seconds, build wall watchdog 180 seconds, complete build performance ceiling
55 seconds. Clean is reported separately from historical build-only timing.
The two candidate clean-plus-build totals are 50.092700 and 53.431412 seconds.
The controller stops immediately if a candidate exceeds 55 seconds or is
incomplete. No average can override an individual failed gate.

The build-only controller returns ALLOW for two complete candidate runs. This
is only ceiling admission: the candidate is not consistently faster and both
candidate first logs are slower than the corresponding original rows. The
four receipts do not demonstrate the requested major build/startup advantage.

Private evidence: `.data/d1510-bound-symbol-v2-cold-abba/report.json`,
per-run configuration and logs, and `admission.json` in that directory.

## Additional Semantic Failure

A fourteenth control supplies a malformed noexpand wrapper whose cdr is a raw
bound symbol, not a Gambit source object. Ordinary eval raises an error, but
the candidate returns the value. The control fails. Recognizing a prefix alone
does not justify treating arbitrary input as validated compiler output.

This excludes revision two independently of the timing result. The latest
control log records that failure; the earlier thirteen-control positive result
must not be presented as complete semantic conformance. Do not publish the
candidate or silently weaken this control. A guard repair alone is not evidence
that the already unimproved timing will become a major gain.

## Decision and Next Boundary

Joint delivery: DENY. Retain the original D1510 plus 0015. No source patch,
CI profile, selected runtime, Git commit or PR push is changed by this experiment.
Do not widen this symbol-read fast path as the main solution: high callback
coverage did not produce a stable major first-log/build benefit, and it has a
semantic failure. No native revision three is built merely to retune that line.

The next major candidate must be selected by actual execution cost, not callback
counts. The remaining begin-form/module preparation work is not quantified by
these counts. The separately observed make-type-env constructor is a five-field
linked environment, not an established expensive table clone; no environment
cache or copy-removal experiment follows from assuming otherwise.

All owned native builds, controls, real test invocations and cold-build controllers
are terminal; supervised children are reaped. The admitted 55-second build gate
and five-second actual test-output gate remain unchanged.
