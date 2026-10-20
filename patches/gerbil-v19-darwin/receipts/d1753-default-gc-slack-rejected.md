# D1753: default GC heap slack does not pass the performance gate

The selected original D1513 B / D1510 binary and carrier are unchanged.
Its historical 51.737180/53.496910-second complete builds and the <=55-second
acceptance gate are not replaced by this experiment. No timing discrepancy
investigation or production patch follows.

D1749 changes only isolated Gambit mem.c. For Apple/Mach, GNU non-Clang,
64-bit compilation, adjust_heap applies a 64 MiB target floor only when
there is no adjustment hook and live_percent equals the original default.
Other proportions/hooks retain their original path; the enclosing resize
code still clamps to max_heap. Explicitly selecting the default proportion
also selects this experimental policy. The experiment trades memory budget
for fewer collections; no measured memory saving or general safety is claimed.
All original B module objects, carrier and runtime archive remain unchanged.

Actual GNU compilation confirms that this candidate's platform branch is
active. Native linking, framework imports and an actual GC succeed. D1750
passes twelve hardware-derived concurrent original/candidate single-VM graph
tests with shared identities, cycles, still-to-movable edges and hash-table
lookups across forced collections. This is not SMP validation, a full suite,
or performance evidence. The earlier D1746 transition failures remain intact.

D1751 runs fresh unchanged MCP clones in A/B/B/A order, using original B as A
and the single-change candidate as B, GNU GCC, twelve build workers, original
ten-second build output gate and 55-second complete-build ceiling:

| Role | First compile, seconds | Complete build, seconds | Result |
| --- | ---: | ---: | --- |
| A | not observed within gate | incomplete | original output gate failed |
| B | 6.406232 | 80.481634 | exit zero; 55-second ceiling failed |
| B | 7.687043 | 93.301379 | exit zero; 55-second ceiling failed |
| A | not observed within gate | incomplete | original output gate failed |

All separate cleans exit zero and leave zero project native images. Both B
builds produce executables with unchanged consumer inputs. The controller
exits one. Since neither A run finishes, no paired speedup ratio is admitted.
These B results neither eliminate the startup cost nor guard the best line.

D1752 uses the unchanged std/make/std/test concurrent fixture with the flat
candidate and original GSC. Twelve starts and twelve framework imports pass.
The actual parallel-make phase then fails the original five-second real-output
gate. Its failure is retained; no SUITE-OK, complete concurrent fixture pass,
hardware GCC peak, or test acceleration is claimed.

The 64 MiB floor is rejected as a performance patch. Native construction and
partial correctness must not be promoted to acceptance. All owned processes
are terminal. Full staging toolchain integration and the requested startup,
complete-build and concurrent test acceleration remain unproved.

Evidence: `.data/d1749-gc-slack-native/`, `.data/d1750-gc-slack-contract/`,
`.data/d1751-gc-slack-real-mcp/`, `.data/d1752-gc-slack-concurrent/`.
