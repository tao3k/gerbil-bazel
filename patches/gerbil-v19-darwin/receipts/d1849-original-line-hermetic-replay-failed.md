# D1849: original line replay does not restore the performance gate

Human direction: restore D1513 B / original D1510 complete-build performance
before developing another optimization. Historical complete builds remain
51.737180 and 53.496910 seconds, mean 52.617045. The ceiling stays 55 seconds.

D1848 executes the retained original binary, SHA256
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`,
with the original D1391 home. The parent environment is cleared, retaining
only HOME, PATH and TMPDIR, before the existing Bazel host configuration is
resolved. GNU GCC is 16.2.0; physical concurrency is twelve; CFLAGS, CPPFLAGS,
CXXFLAGS and GERBIL_CC_OPTIONS are absent. Embedded-native mode remains zero.
No product code, toolchain artifact or candidate carrier is changed.

The fresh MCP clone retains head
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. Official clean succeeds in
6.872024 seconds and leaves zero project native images. Official build's
first literal compile line appears at 8.337594 seconds; complete build takes
77.506420 seconds and exits zero. Sources remain unchanged and the executable
exists. The unchanged ten-second real-output gate passes, but the 55-second
complete-build gate fails and the controller exits one.

This is a failed restoration, not a new baseline or an admitted optimization.
Clearing inherited environment did not restore the historical timing. It does
not establish a cause for the discrepancy or prove exact historical environment
identity: the historical complete driver/environment snapshot is unavailable.
New candidate development stays suspended until the original performance line
is actually reproduced. Repeating unchanged full builds is not a recovery plan.
The next bounded configuration audit is the original dynamically loaded library
image closure; the existing 42 native-C input checks do not cover that closure.

Private evidence: `.data/d1848-original-line-clean-environment/`.
The owned controller and child processes are terminal. No commit or push occurs.
