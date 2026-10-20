# D1462: sparse GVM budget needs iteration fuel and gives no major startup win

## Source Contract And Observer Correction

Current Gambit still guards common-code removal with historical next-label
number greater than 300, as identified in D881. This turn validates actual
coverage on eleven current native hotspot inputs, not another synthetic-only
claim. The common baseline is D1391; staging/Gambit source identities remain
`1cfb032c7a1612637da6205f5f8a15683eba3ba0` and
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.

D1455 initially replaces the common-code procedure binding and reports zero
over-budget events. Its displayed qualification is **not admitted**: it did
not prove that native internal calls reached the replaced binding. Zero events
must not be consumed as zero optimization opportunities.

D1457 introduces an explicit call-site observer in the unchanged five-step
GVM purification pipeline, but fails on an introduced missing parenthesis.
D1458 repairs syntax, requires actual common-hook calls and disabled C byte
identity, and exposes real eligible sparse graphs. The explicit pipeline
avoids assuming a binding replacement interposes native compiler calls.

## Actual Iterative Failure

The unlimited live-block substitution does not converge within the unchanged
90-second generation gate for two actual procedures:

- core-resolve-path: live count remains 43 while historical label span grows
  past 44,953, increasing by two in consecutive recorded iterations.
- eqv-hash: live count remains 21 while span grows past 44,662, likewise
  increasing by two in consecutive iterations.

Both owned compiler tasks are stopped/reaped on timeout. The retained repeated
growth is evidence that a live-block threshold alone is insufficient to bound
this existing common-tail transformation. It is not a formal proof of infinite
execution, a Darwin/Linux root cause or the cause of the official first-log
delay. D881's synthetic merging controls do not admit unlimited integration.

## Bounded Integration Probe

D1459 keeps every legacy dense-graph decision and permits at most **one added
sparse common-code pass per procedure**. Later sparse iterations retain the
original skip, preventing the newly introduced repeated-tail extraction. The
existing equality, polling, frame, GC metadata and dead-code machinery is
unchanged. Activation requires Darwin plus an explicit marker supplied only
after genuine GNU GCC 16 verification. No production compiler is altered.

All eleven current inputs regenerate successfully. Disabled output is
byte-identical to baseline C in every unit; checked SCM inputs stay unchanged.
The observer records 2,839 actual common-code calls and four added sparse
passes. Two units have changed C:

| Procedure | Historical span | Live blocks before | Live blocks after |
| --- | ---: | ---: | ---: |
| core-expand-import% | 301 | 211 | 204 |
| macro-expand-syntax | 372 | 299 | 272 |

Core and table also execute one added sparse pass each, but their final C is
byte-identical to baseline. This separates a pass being executed from emitted
work actually changing. No dynamic CPU frequency or eliminated allocation
claim follows from these static graph counts.

## Native Candidate And Actual First Log

D1460 compiles only the changed module/stxcase C objects with original GNU O1,
links them with all other original objects and RTS, and passes std/make,
std/test and std/build-script imports. GSC remains the original executable.
Existing process creation and object-reuse configuration is retained. Native
candidate SHA-256 is
`821b7fdc7c556f015f939d073c5f30132fa8b2de6c6eb6916375944c7cb32552`.

D1461 runs fresh independent official MCP clean/build first-log ABBA:

| Role | First `... compile util/compat`, seconds |
| --- | ---: |
| Baseline | 5.871778 |
| Candidate | 6.095925 |
| Candidate | 5.964095 |
| Baseline | 6.252580 |

Means are 6.062179 versus 6.030010 seconds, approximately 0.53% lower with
overlapping ranges. This is no demonstrated acceleration. Each clean exits
zero with zero project native images afterward; source checks pass. Each build
is deliberately stopped after the first actual line, terminal exit 70, under
the unchanged ten-second output gate. No complete build or concurrent test
claim is admitted for this candidate.

## Decision And Evidence

Do not activate the unlimited live-count prototype or freeze the bounded
variant as a performance patch. The real-source experiment corrects missing
coverage and exposes an iteration-fuel requirement, but does not solve startup.
No production patch, consumer/std library, installed toolchain or Linux path
changes. Twelve hardware-derived workers remain configured.

Retained evidence is under `.data/d1455-live-block-coverage`,
`.data/d1457-live-block-coverage-admitted`, `.data/d1458-live-block-coverage-fixed`,
`.data/d1459-live-block-one-pass-coverage`, `.data/d1460-live-block-native`, and
`.data/d1461-live-block-first`. The private probe is
`.data/d1455-live-block-coverage.py` with its Scheme observer; native linking is
`.data/d1460-live-block-native.py`.

All owned compiler/build processes are terminal. The full first-log and real
build/test objective remains active and unachieved.
