# D1370: GNU Darwin native tuning admission

## Question and decision

Check whether the installed GNU Darwin compiler lacks native CPU detection,
or whether enabling native selects a different optimization cost model that
could explain the remaining major-cost window. Do not promote restoring
native as a proven several-fold optimization or rebuild the whole toolchain
on that premise. No workload timing or acceleration is claimed.

## Current source and installed compiler

The original isolated gambuild-C has no march/mcpu/mtune flag. The existing
source-build harness explicitly configures --enable-march=; this is already
visible in prior receipts and is not a newly discovered Darwin backend bug.
The GNU compiler is version 16.2.0, target aarch64-apple-darwin25.

The driver resolves default CPU selection to apple-m1 and -march=native
to apple-m2 on this machine. Thus native CPU detection does work on this
installed Darwin compiler. No sysctl detection workaround is warranted.

## Installed model output

The durable diagnostic under `.data/d1370-darwin-gnu-tuning-admission/`
uses -Q --help=target and -fdump-tuning-model with an empty C translation
unit. It compiles no Scheme or application source, links no workload and
does not change Gambit. All four commands exit zero and retain stdout,
stderr, compiler identity and the compiler-generated JSON model dumps.

| Driver options | Resolved CPU | Tuning dump bytes | SHA-256 |
| --- | --- | ---: | --- |
| default | apple-m1 | 10,872 | 5bc3575748b749e556e8b181930351249517ddd8eff60898a44a9cacc9d3349c |
| -march=native | apple-m2 | 10,872 | 5bc3575748b749e556e8b181930351249517ddd8eff60898a44a9cacc9d3349c |
| -mcpu=apple-m1 | apple-m1 | 10,872 | 5bc3575748b749e556e8b181930351249517ddd8eff60898a44a9cacc9d3349c |
| -mcpu=apple-m2 | apple-m2 | 10,872 | 5bc3575748b749e556e8b181930351249517ddd8eff60898a44a9cacc9d3349c |

The dumps are byte-identical, including issue_rate=3. This is installed
compiler metadata, not a measured hardware issue rate. The driver selections
can still change available ISA features. Identical tuning dumps do not
establish identical application code or exclude every possible flag effect.

## Primary reference and boundary

[GNU's Apple core implementation proposal, PR113257](https://gcc.gnu.org/pipermail/gcc-patches/2025-March/678884.html)
explicitly describes initial Apple entries with placeholder schedulers and
generic costs. That historical proposal is not assumed to describe the
installed compiler; the local dumps above are the current evidence.

This concerns compiler support for Apple CPUs, not proof of an XNU/macOS
runtime penalty. Apple CPU microarchitecture also exists under Linux. A
Darwin-only activation gate would not turn arbitrary cost-model tuning into
an OS-specific solution. No alternate-core proxy, scheduling override or
general flag sweep is admitted by this diagnostic. The original first-log
and full build/test objective remains open.
