# D1510 Independent Stdlib And Host Distance

No new optimization or production admission. The historical heavy cold-build
anchor remains 47.771713 / 47.824226 / 47.927094 seconds. Whole-task gates
remain first log 5 seconds, build 50 seconds and complete test 112 seconds.
The independent fixture below does not replace the heavy regression sample
or qualify its complete test suite.

## Real Independent Standard Library

`tests/run_stdlib_rebuild.py` copies original staging list and JSON library
sources without changing their contents. Its build script uses the actual
`:std/build-script` / `std/make` path. Private command symlinks select the
retained runtime and original GSC; sources, output library and package home
are isolated under `.data`. The runtime home remains the canonical retained
home, preserving native-provider identity checks.

Successful receipt: `.data/d1510-stdlib-rebuild-v3/report.json`, SHA256
`48a0909c524c3a04bbf7365743168116a3932dc0da09fd0679e992ae84598e13`.

| Measurement | Seconds | Result |
| --- | ---: | --- |
| Real gerbil clean | 3.306560 | exit 0 |
| First real compile log | 4.028814 | under 5 |
| Complete eight-target gerbil build | 16.558582 | exit 0, under 50 |
| Whole concurrent test wave first output | 3.120097 | under 5 |
| Whole concurrent test wave completion | 10.821341 | under 112 |

Both original files complete with final OK: list 32 cases and JSON 33 cases,
65 total, no failed cases. Test processes run concurrently. Only the shared
whole-wave gates apply; there is no per-file silence deadline. Original and
copied source digests and retained binary identity remain unchanged.

`artifact-verification-v2.json` in that directory verifies that list, JSON
reader and JSON writer runtime images actually load from the new output
library. Loading original sources is not assumed from an environment variable.

Failures are preserved, not converted to successful measurements:

- v1: private build script lacked executable permission; fixture failure.
- v2: a new runtime-home alias did not match the retained provider's exact
  path checks, so the fixture selected fallback loading. First compile log
  was absent at 5.015004 seconds; DENY, child killed and reaped.
- First artifact verifier expected `json/api~0`; API only reexports and has
  no runtime body. The process exited 0; the verifier rejected the missing
  expected key. The corrected second receipt checks actual reader/writer
  runtime images. Both attempts remain available.

Three focused controller tests pass, including rejection of successful builds
without a compile log and protection against per-file silence cancellation.
These are fixture checks, not performance improvements.

## A Concrete Apple CPU Mechanism And Its Boundary

[V8 short builtin calls](https://v8.dev/blog/short-builtin-calls) reports that
Apple M1 indirect-call prediction suffered when code and targets were more
than 4 GiB apart. V8 placed builtins closer to JIT code. This is a specific
CPU/address-layout mechanism, not proof that all macOS macro expansion suffers
from it, and not an attribution to Mach-O fixup time.

`tests/audit_embedded_host_distance.py` reuses the existing structured Mach-O
parser and validates actual function-start symbols. On the retained binary,
`__text` spans 23,934,760 bytes (22.83 MiB). Expander core, stx and runtime mop
hosts reside in that same executable section. Their common ASLR slide cannot
change their relative distances. The V8 greater-than-4-GiB condition therefore
does not hold for calls between these embedded hosts.

This closes only that specific same-image hypothesis. It does not measure
branch misses, every dynamic image, external C calls or every GVM label path.
No code relocation, linker flag, jump-mode change or benchmark rerun is
admitted from this reference.
