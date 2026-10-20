# D1510 Original Binding Initializer Samples

Diagnostic observations only. No new candidate, improvement, cold-build
baseline or complete-test qualification. Retain the historical 47.771713 /
47.824226 / 47.927094-second cold anchor and 5 / 50 / 112-second gates.

## Source Choice

Patch 0017 reduces repeated accumulated resource merges during final GSC
link generation. Its comparison-count benefit does not cover initial Scheme
imports. Its unstable native wall observations and default-off status remain
unchanged; no similar runtime improvement is inferred merely from list folds.

Retained `expander/module.ss:541` creates import bindings and invokes their
live initializer; `expander/core.ss:111` initializes binding and import fields.
The prior contract requires these initializer calls even when an existing
binding is retained or a conflict follows. Do not skip them or share mutable
bindings. This diagnostic addresses the original initializer body, not another
count of prior-binding cache opportunities.

## Reached Original Execution

Four fresh standard-library processes run concurrently using the retained
host, selected runtime home, empty package home and 12 physical-worker budget.
The live initializer global is wrapped; every invocation delegates its original
seven arguments to the original native initializer and returns its value.
Every 128th invocation at offset 53 records process user/system CPU around
that original call. No return-value cache, changed initializer or alternate
binding construction is used. The global is restored before final diagnostic
output, with dynamic-wind restoration also covering exits.

| Root | Reached initializer calls | Sampled calls | Raw sampled CPU seconds |
| --- | ---: | ---: | ---: |
| std/make | 109,802 | 858 | 0.001593 |
| std/test | 80,330 | 628 | 0.001065 |
| std/encoding/json | 160,689 | 1,255 | 0.002107 |
| std/list/list | 79,141 | 618 | 0.000881 |

These counts include all reached calls through this initializer across the
observed phases, not just the earlier phase-zero import-binding census. The
intervals include measurement overhead and possible GC/scheduling within the
call. Deterministic sampling can be biased; counter resolution is material at
this scale. No multiplication by 128, whole-phase budget, percentage saving or
speedup is admitted. They establish a reached measurement boundary but not a
seconds-scale opportunity to inline or omit initialization.

All four exit zero with final OK, cached-context identity and restoration.
Their export and native-module inventories match the earlier original control.
These are import controls, not full library assertions or a full test suite.
The original frozen binary hash remains unchanged. Seven parser tests pass.

Private evidence: `.data/d1510-binding-initializer-samples-v2/report.json`
and per-library original logs. The v1 attempt passes a string instead of the
module-symbol argument required by the original import API; all four exit 70
before completing imports. Its logs are retained as a diagnostic fixture
failure, not a runtime regression or performance sample. The corrected v2
uses the same quoted-symbol convention as the existing import runner.

## Decision

Do not construct a canonical-initializer fast path from invocation counts or
extrapolated samples. Initialization semantics remain live. Further source work
must isolate actual binding/context construction and lookup execution from
required initializer behavior, or identify another large reached cost in the
admitted native reuse/reader/compiler paths. No unchanged cold/full-test
campaign, runtime patch admission or publication follows from this diagnostic.
