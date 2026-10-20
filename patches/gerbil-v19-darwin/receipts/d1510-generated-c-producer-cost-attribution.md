# Native Producer Cost Attribution

## Review And Scope

The V9 component producer regressed against original generation, although its
link phase saved time. Unchanged V9/V11 whole-consumer DENY routes remain closed.
This diagnostic measures the producer internals before choosing a new mechanism;
it is not another full MCP attempt or a package-specific optimization.

`tests/gambit-generated-c-cost-probe.scm` wraps mutable digest/compiler entry
procedures in the existing V9 image. `tests/run_generated_c_cost_probe.sh` runs
the 55 retained real generated Scheme files in one GSC process, then invokes
the matching original compiler at the identical output path/alias and compares
every complete C file. Bash owns launch and exit propagation; no Python native
test supervisor, frozen toolchain edits or shared dependency changes occur.

This intentionally removes per-module process startup from the diagnostic.
It cannot be compared with earlier 55-process timing as an end-to-end win.
Dynamic instrumentation adds overhead. Timings are inclusive, not additive.
Wrappers for environment, read-journal and pin-publication record zero calls:
compiled internal call sites bypass those replaced globals. Zero counts do not
mean those operations are free or absent. Compiler timing includes source reads,
copying and macro-context classification.

## Measurements

| Receipt suffix | Producer | Compiler | All batch digests | Tool batch digests | Data batch digests |
| --- | ---: | ---: | ---: | ---: | ---: |
| v2 | 5.412672 | 3.797050 | 1.359030 | not split | not split |
| v3 | 9.172307 | 6.531159 | 2.113321 | 2.061053 | 0.053038 |
| v4 | 8.042836 | 5.729020 | 1.906065 | 1.847519 | 0.059340 |

All units are seconds. Receipt roots are `.data/d1510-generated-c-cost-probe-*`.
Only v4 includes the completed 55-file original-compiler byte-parity phase.
The v1 attempt failed on an unqualified compiler-namespace symbol before doing
the workload; it is not counted. Changes v2 to v3 add diagnostic categorization;
v3 to v4 add post-run parity, not optimization code. No stable wall multiplier is
inferred from their timing variation.

In v3/v4 the digest call counts are exactly 165 tool batches and 275 data batches,
440 total. There are also 275 single digests. The V9 GSC is 16,036,896 bytes and
the helper 34,336 bytes. Three tool digest batches per module mean approximately
2.65 GB of executable/helper content is hashed across this 55-module batch.
Tool batches consume 97.5% / 96.9% of batch-digest time. V4 copying costs only
0.070947 seconds across 110 calls; it is not the main measured overhead.

V4 exit is zero, diagnostic wall 8.07 seconds, user 5.65/system 0.76; these fields
exclude the later original comparison phase. All 55 probed C files compare equal
to their own original GSC output. No complete package/test time is claimed.

## Next Mechanism Boundary

Repeated full executable validation is a concrete producer overhead. Existing
three checks occur before generation, after generation and before publication;
none is simply redundant under the current per-producer safety model. Removing
checks or replacing content identities with mtime/size alone is not admitted.

A prospective explicit closed batch could amortize tool hashes across modules,
but only if complete source/options/environment/tool revalidation surrounds that
batch and no partially validated proof becomes visible before admission. It also
needs failure rollback, concurrency controls and unchanged per-module aliases/C.
Compiler context isolation must be established before generic batch reuse.
The observed opportunity is bounded by 1.85-2.06 seconds in this component,
not the whole package build or pre-first-log macro expansion. No batch patch
or consumer performance qualification is claimed yet.

## Identities

- V9 GSC: `6493053bdc3c6f544e47642ba2de0888768010acad949351b6887d3b482d5d5c`.
- Probe Scheme: `8953f35db194449249d009ad4028447eb6eba33348efb4753865da22cc1dffce`.
- Probe runner: `69633578505157f3852cdc1497c884bbd81788c8f7ff62b78cb5c326a4339a57`.
- V4 output: `af97ef511eca84055c7061d7e6ce5d06242dda9fd14a26fba1ec618aeb8db2f5`.
- V4 time: `7b9f315cfb8d27edebd70c15d93f4802d1af0a4db14f210ff761b0ed9ecfd76e`.

The frozen five-patch MCP series, runtime and 4.5 / 42 / 97-second gates remain
unchanged. Independent complete ASCENT and repeated complete MCP performance
admission are still outstanding; the goal remains active.
