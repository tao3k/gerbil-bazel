# Experiment Framework

Shared contracts for current isolated Gerbil experiments. Historical frozen
generators and receipts are not migrated or rewritten by this change.

## Modules

- `context.py`: persistent paths, toolchain identity, canonical runtime home,
  hardware-derived concurrency and a clean experiment environment.
- `process.py`: owned subprocesses, original real-output gates, immediate
  performance DENY cleanup, and separate bounded recorder finalization.
- `xml_evidence.py`: exact export schemas, references and complete rows.
- `compiler.py`: original GNU driver diagnostics in private outputs, with
  unchanged-source/reference-object hashes and no runtime admission.
- `link.py`: one-object substitution only after an exact-byte retained control
  relink, with frozen provider and native-input validation.
- `runtime_io.py`: one private RTS archive-member compilation, requiring the
  original compiler command and byte-identical original member before changes.
- `spawn.py`: original/candidate generic process semantics, exact named case
  inventory and real assertion flushing; never whole-test admission.
- Existing `progressive_performance_gate.py` remains the gate implementation;
  the framework reuses it instead of introducing another policy.

The five migrated workflows retain their standalone commands. New usage has
one entrypoint from the repository root:

```sh
python3 patches/gerbil-v19-darwin/tests/experiment.py stdlib --output .data/stdlib-round
python3 patches/gerbil-v19-darwin/tests/experiment.py artifacts --output .data/stdlib-round
python3 patches/gerbil-v19-darwin/tests/experiment.py counters --output .data/counter-round
python3 patches/gerbil-v19-darwin/tests/experiment.py counter-summary --profile .data/counter-round
python3 patches/gerbil-v19-darwin/tests/experiment.py counter-stacks --profile .data/counter-round
python3 patches/gerbil-v19-darwin/tests/experiment.py counter-stacks --profile .data/counter-round --context
```

Counter summaries require exported metric and time tables in the recording
directory. They never rerun the target. Evidence files are immutable by
default: use a fresh output directory or a fresh artifact-verification attempt.
The optional context report separates P/E sample coverage and stack depths;
process-bucket metric proxies are not per-core hardware cycle attribution.
`counter-stacks --layout` reuses the same immutable export to validate native
image page alignment and sample geometry by actual Mach-O function extent.
It cannot substitute timer samples for function-entry traces, page faults or
instruction costs. Its whole-function translation lower bound is geometric,
not an orderfile or executable optimization proposal.

`compiler-frame` accepts isolated `--source`, `--reference-object`, `--home`
and fresh `--output` paths. Its diagnostic finalization deadline is distinct
from product timing. `--shared-parameter-result` creates a private guarded
source candidate; compilation is not semantic or performance acceptance.

`register-branch --existing-preprocessor .data/d1510-gvm-register-layout-v1
--output .data/fresh-branch-audit` reuses qualified transcripts and validates
source/input identities without invoking GCC or the target. It distinguishes
the selected host-exit branch from runtime frequency and performance gains.
`native-layout --control-transfer --output .data/fresh-native-audit` reuses
Mach-O function metadata and checks contiguous original-binary disassembly.
Its ordinary BR/BLR site counts are static topology, not prediction misses,
dynamic transfers or a reason to repeat the denied distributed-exit candidate.

`runtime-io` accepts original isolated `--source` and `--archive` plus fresh
`--output`. `relink` also accepts its identity-checked replacement archive;
the retained providers, private reader objects and original control are kept.
`compiler-frame --allocation-sites` extends the constructor census to an
original generated carrier. It first requires a byte-identical uninstrumented
control object, then builds only a private diagnostic object without large RTL
dumps. The counter preserves original source line numbers and heap advancement;
it does not qualify runtime performance. `run_stdlib_import_cost.py` accepts
`--native-allocation-report` and an optional `--native-allocation-source` only
when composition identity, original source hashes and diagnostic binary hashes
agree. `gambit_allocation_sites.py` can reparse retained raw counters against a
matched successful source control without repeating the workload. Its lexical
procedure attribution is restricted to original procedure switch bodies.
`spawn-semantics --binary ... --output ...` validates child-PATH and original
shell-fallback contracts with both runtimes. Only successful assertions emit
and flush CASE-OK; no heartbeat is added. Component passage or its durations
cannot admit production. The child-PATH archive candidate failed the actual
first-compile gate and is excluded from further repetition.
`runtime-io --candidate hash-cold-tail` reuses the same original-member/control
contract for mem.o; `spawn-semantics --contract hash-cold-tail` uses the exact
GC-hash inventory instead of process cases. This private cold-rehash candidate
also failed the actual stdlib first-compile gate and is closed. Neither a
leaf instruction shape nor primitive semantic passage is speed admission.

`retained` dispatches the existing original D1510 cold-build/full-test pipeline,
without changing its recipe or gates. `three-lines` summarizes its cold report
and optional complete test report, always exposing all three measurements.
An unfinished phase has no complete time; performance stops remain visible.
The CLI defaults to the current 5/50/112 policy, and exits nonzero on DENY.
The summary function's historical 52-second default is retained for older
callers; current callers select 112 explicitly. An old receipt remains an old
measurement, even if its values fit today's thresholds.

## Evidence Boundaries

Standard-library correctness is not MCP correctness. Diagnostics, hardware
recording time, partial phases and whole-build timing stay separate. The
stdlib workflow retains first-log 5, complete-build 50 and whole-test 112
second limits, with concurrent test processes and no per-file silence gate.
Recorder shutdown grace never extends a product performance deadline.

No runtime patch, baseline binary, compiler flags, library assertion, case
inventory or historical result is changed by framework migration. Tests check
deadline cleanup, path isolation, canonical provider paths, schema integrity,
CLI dispatch and exact statistical parity against available original traces.
