# D1713: first-write context census and rejected local-type candidate

The startup/build/test goal is not achieved. Historical D1513 candidate mean
52.617045 seconds and the 55-second complete-build gate remain authoritative.
No production performance patch or full-toolchain qualification follows.

## Admitted execution counts

D1700's unsampled all-site counter diagnostic fails the original output gate.
D1703 instead leaves all host trace counters disabled, counts native helper
calls, and accumulates completed iterations once at helper return. It reuses
the D1694 fragmented-write observer/counter objects, hashes every linked object,
and changes neither product logic nor compiler flags. D1702's initial sandbox
host-discovery failure is retained; it does not count as a compiler failure.

D1704 passes the existing 36 actual compiled context/GC/rebinding/exception/
continuation/parent-change cases across twelve concurrent original/diagnostic
processes: 432 CASE-OK results. This is not whole-suite or forced-poll coverage.

D1705 verifies actual builder PID 53712, binary digest and loader flag zero on
a fresh unchanged MCP clone, without attaching a sampler. Its first compile
line arrives at 6.237559 seconds, under the unchanged ten-second output gate.
D1706 admits only the owning PID's frozen first-write snapshot:

- 4,618,900 context helper calls.
- 25,793,782 successful logical parent-walk iterations.
- 5.584399 iterations per helper call.
- No counters enabled at the other fourteen host trace sites.

Snapshot SHA256:
`aadebd7ce4f32d79b5755db044fb16ef42c62c96e33b4d7b13607b43092cf3d7`.
Diagnostic binary SHA256:
`3edd745a82df2a8e9847bd28051d55beb1e33ef5bbe3c278219b815574a15f64`.

These establish actual execution volume, not matched CPU savings, fallback
coverage or full-build speed. D1064-D1066 already established the limited
empty-table opportunity; that experiment is not repeated or implemented here.

## Invocation-local type candidate

D1707/D1708 retain the fourteen original trace sites and the bounded 32-step
Darwin/GNU helper. Exact validated table/context type metadata is reused only
inside one helper invocation without allocation, Scheme callback, handled poll
or live-frame write. Each iteration still checks actual structure type and
reads current table, method, parent, key and raw-table flags. Global binding,
moved-key and outer/post-lookup stack-trip guards remain. No lookup result,
table contents, parent pointer or cross-invocation metadata is cached. Original
type-chain validation is used when the type differs. Native construction and
framework imports pass; this is not an integrated compiler/toolchain patch.

D1709 passes 432 actual contract cases across twelve concurrent processes.
Candidate binary SHA256:
`9a11f92cdda8c473449a9df3921810a6640557ce744971860c9b83e19d80f885`.

D1710 fails before product launch because an explicit source argument requires
a nonexistent home-level receipt. The corrected invocation uses the default
common home and explicit candidate binary; the failed directory is not reused.

D1711 runs official clean and a complete unchanged MCP build with twelve
workers, GNU GCC, loader flag zero, captured current configuration and both
original output/performance gates:

| Measurement | Seconds |
| --- | ---: |
| Separate clean, exit zero, zero retained native images | 4.884920 |
| First compile line | 6.163012 |
| Complete build, exit zero | 66.481738 |

The complete-build ceiling fails. Controller exit is one, performanceQualified
and performanceCeilingQualified are false. Source inputs remain unchanged;
the executable is produced. No cross-run speed ratio against D1513, D1692 or
other differently timed observations is admitted.

## Concurrent framework test boundary

D1712 passes twelve native starts, twelve framework imports and the genuine
std/make/std/test fixture under the unchanged five-second output gate. Its
three exact CASE-OK lines, SUITE-OK, D885-OK and exit zero are verified.
Fixture wall time is 16.805435 seconds; measured cold/no-op/incremental phases
are 13.084323/0.073764/2.052616 seconds. Maximum observed output gap is 3.223247
seconds. Configured workers are twelve and peak observed GCC frontends are
eleven: native concurrency is proved, fullHardwareConcurrencyObserved is false.
This is fixture correctness/concurrency, not a matched speedup or MCP test-suite
qualification. Together with D1711's failed ceiling it does not close the goal.

Evidence: `.data/d1703-local-context-census-native/`,
`.data/d1704-local-context-contract/`, `.data/d1705-local-context-prefix/`,
`.data/d1706-local-context-summary/`, `.data/d1707-context-local-type-preflight/`,
`.data/d1708-context-local-type-native/`, `.data/d1709-context-local-type-contract/`,
`.data/d1711-context-local-type-real-mcp/`, `.data/d1712-context-local-type-concurrent/`.
