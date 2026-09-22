# D876: real-consumer host-load preflight

Date: 2026-09-22. D875 stopped because the identical-binary POO control
failed while host load exceeded the 12 logical CPUs. A later attempt found
1-, 5-, and 15-minute load averages of 29.997, 23.626, and 19.930. Starting
another first-access and measured pair under that state would not create an
attributable comparison.

`tools/bench/run_real_consumer_ab.py` now accepts the opt-in
`--max-host-load-per-core` preflight. When supplied, it captures all three
load averages and requires both the 1- and 5-minute values to be no greater
than `build cores * ratio`. The 15-minute value is evidence only: gating it
would unnecessarily retain load that is no longer active. Omission preserves
the prior runner behavior.

The strict Darwin qualification command uses
`--max-host-load-per-core=1.0`. With 12 host-derived build workers, the limit
was therefore 12.0. The current host was rejected in 0.07 seconds before the
scenario clone, toolchain import, first access, or either measured arm. The
machine receipt is `/private/tmp/d876-poo-aa-load-preflight.json` and records
`status=qualification-failed`, `failedPhase=host-load-preflight`.

The runner's 25 unit tests pass, including acceptance at 11.5/12.0 load,
rejection at 12.1, and preservation of opt-in semantics. This gate is an
environment qualification, not a performance optimization and not evidence
for admitting candidate `0007+0008`. The next valid action remains the same:
rerun the identical-binary POO A/A in a host window that passes this preflight.
