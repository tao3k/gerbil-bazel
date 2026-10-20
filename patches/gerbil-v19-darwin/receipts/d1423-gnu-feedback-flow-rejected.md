# D1423: GNU execution-feedback candidate rejected before timing

## Question

After D1420 establishes predominantly user execution in the actual normal
first-log window, test whether feedback-directed optimization can reduce the
large Gambit-generated host functions' executed branch/code-layout cost.
This is a new local GNU feedback experiment, not a claim that PGO explains
the Darwin/Linux difference, nor a repeat of O2/O3 flag-only comparisons.

GCC documents both [instrumentation and training](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
and [feedback-directed optimizations](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
The experiment does not infer several-fold savings from these references.

## Source exclusions

The original Gambit header already tail-calls external label hosts through
`___EXIT_HOST` and `___TAIL_CALL_VOID`. D1012-D1015's private fixed-register
calling convention remains rejected with only approximately 2.96% CPU gain.
Neither is repeated or promoted here.

`___OPTIMIZED_MODULE_LIMIT` is 20000 in the actual current header and canonical
configure default. The core/stx label counts are below it. The corresponding
`no-expensive-optimizations` downgrade cannot be selected as their slowdown
cause on this source evidence.

## Build and actual training

Private builder: `.data/d1421-pgo-runtime.py`. Common toolchain remains
`.data/d1391-runtime-object-source/build` at canonical staging
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`, rechecked in D1420.
The real GNU GCC 16 frontend and 12 physical workers were verified.

Eleven original separate host C files were copied byte-exactly. No parameter
shortcut, coalescing, Scheme edit, object representation, package behavior,
GSC executable, installed library, or default patch profile changed. The
instrumented build uses original O1 plus execution-feedback instrumentation.
It links profiling support and passes imports of std/make, std/test and
std/build-script. Compiler/import logs contain no reported profiling error.

Instrumented binary SHA-256:
`f806c66043f23e13dffa5b059b77c93a486c1c0e1423ab7931127ba1056af955`.

A fresh MCP checkout then underwent actual `gerbil clean/build` with original
source and unchanged 30-second clean/10-second output gates. Clean returned
zero and left zero native images. The first literal compile line appeared at
7.671111 seconds; the build was deliberately stopped there with exit 70.
This is instrumented training, not an acceleration result or complete build.
Eleven nonempty feedback files remain, including counts from import/clean and
normal diagnostic shutdown, not exclusively prefix execution.

Training receipt: `.data/d1422-pgo-first-training/report.json`.
Instrumented build receipt: `.data/d1421-pgo-runtime/generate-report.json`.

## Typed failure

Feedback-use recompilation retained identical source/object paths and required
existing feedback. All eleven host units were rejected with:

```text
corrupted profile info: profile data is not flow-consistent
```

The core diagnostic includes inferred negative execution counts for multiple
CFG edges, including -108196429. This is not a missing-profile or source
checksum error. It is not evidence of a Gambit semantic failure or a proven
Darwin-specific compiler bug. The address-label/tail-call instrumentation
interaction is a hypothesis; no minimal causal reproducer is admitted.

Do not add `-fprofile-correction`, downgrade errors, fabricate edge counts, or
activate this profile. No feedback-optimized binary was linked or timed. The
preserved instrumented binary is not an optimized candidate, and the current
private `report.json` is `qualified=false` to prevent accidental admission.

Failed receipt: `.data/d1421-pgo-runtime/use-report.json`; all eleven
`use-gerbil__*.log` diagnostics and original feedback files are retained.

## Admission

No major first-log improvement, complete build result, concurrent test result,
or new performance patch is qualified. Existing 0001/0007 advantages retain
their prior evidence boundaries. The main goal remains active and unachieved.
Any further feedback experiment must first demonstrate flow-consistent
training for Gambit's actual host control flow; compiler-error suppression is
not the next action.
