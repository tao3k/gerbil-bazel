# D1510 Driver Extension: Hard Denial

## Selected Line

Keep the retained original D1510 binary, GSC, runtime home, GNU GCC options,
runtime-object reuse and admitted 0015 driver. Its recorded complete cold
builds are 52.498548, 47.211369 and 48.705787 seconds. This investigation does
not replace those measurements with a slower baseline or add Multiple VM.

Every candidate complete cold build must be at most 55 seconds. Product
success, command parity, fewer subprocesses and averages cannot override
this ceiling. Startup and native-test acceleration require separate evidence.

## Source Hypothesis and Checks

After 0015, gambuild-C still scans each metadata input separately for five
metadata classes. A private Darwin/GNU candidate probes all five patterns
with one grep and skips those scans only when every file has no metadata.
Metadata-bearing or unreadable inputs retain the original parser. A second
private candidate also uses literal shell substitution for filename quote
encoding, retaining newline fallback and the portable branch.

Both candidates pass 60 object/dynamic/executable command cases, including
empty metadata, metadata-bearing files, mixed files, missing files, quotes,
backslashes and newline inputs. Driver names in diagnostic prefixes are
normalized for comparison; messages, command stdout and exit codes agree.
Both compile the actual MCP compat C input to the same GNU object as 0015:
`3c6c615e9608420772b45457b00d0448a9ccab36e502b4fa1a7282e6dfea7ffb`.

The empty-metadata shell trace changes from five grep/seven sed calls to
one grep/two sed calls. Adding builtin filename quoting leaves one grep
and zero sed calls. Actual identical GSC execution selects the first private
driver and reduces sed calls from seven to two. These are mechanism checks,
not complete-build speedup claims.

## Complete Cold Builds

All runs use MCP head `9a5c35e275e5d6847ff421151bb224f2eae177c1`, official
gerbil clean/build, 12 hardware-derived physical workers, GNU GCC 16,
unchanged compiler configuration and embedded-native reuse disabled.
Clean/build exit zero, clean leaves zero project native images and checked
consumer sources remain unchanged. The original 10-second real-output
watchdog and 180-second total build budget remain unchanged.

| Driver | First compile (s) | Complete build (s) | Decision |
| --- | ---: | ---: | --- |
| Retained 0015 observation | 5.731621 | 56.689304 | DENY |
| Empty-metadata probe | 5.396441 | 55.962595 | DENY |
| Probe plus builtin filename quoting | 5.331589 | 57.918305 | DENY |

The first row is a failed current observation, not a new admitted baseline.
No candidate is retained, published or installed. No end-to-end gain is
claimed. The original performance gate causes each controller to exit 1.
The original build reports' `qualified` field denotes product execution;
the separate admission receipts explicitly record `admitted:false` and
`decision:DENY`, with exit 1. Never consume product qualification alone as
performance admission.

A small GSC selection proof ran during the empty-metadata build. No second
full build ran concurrently. Do not infer a reliable sub-second difference
from these sequential observations or relax the ceiling to admit them.

## Executable Gate and Private Evidence

`tests/admit_d1510_cold_build.py` enforces the fixed ceiling, selected driver
hash, official clean/build success, zero post-clean native images and unchanged
sources. It rejects invalid durations, missing candidates and any over-ceiling
candidate instead of averaging it away. Five focused tests pass. Private
extension runners now write this fail-closed admission in their finalization.

All paths below are project-relative; private binaries and logs stay in .data:

- `.data/d1510-driver-extension-anchor-v2/`: failed retained-driver observation.
- `.data/d1510-driver-empty-meta/`: first private driver and semantic proofs.
- `.data/d1510-driver-empty-meta-cold/`: first cold build and DENY receipt.
- `.data/d1510-driver-builtins/`: second private driver and semantic proofs.
- `.data/d1510-driver-builtins-cold/`: second cold build and DENY receipt.

The earlier object-reuse audit already closes the hypothesis of 186 redundant
whole-runtime C compilations, and the real process census sees zero Gambit
fork calls in this workload. Keep those existing conclusions; do not repeat
them or remove freshness/dependency checks to manufacture a large gain.
