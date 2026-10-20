# Whole Member Link Request Guard

## Root Cause And Decision

0041's group-local validation was insufficient. A real native CLI request with
two Scheme directories admitted an earlier include changed during the second
group: `.data/d1510-member-cli-cross-group-v1` records compiler exit 0 and a
published binding. The regression harness exits 42. Standalone 0041 is DENIED
for promotion; successful static-input Cases did not cover this interleaving.
Do not repeat or promote that unsafe configuration.

0042 adds full-request input, dependency-journal, tool and environment validation
before the complete binding is published. Every member journal must match its
logical output and immutable pin digest and include its main source. Before a
later group starts, tool/environment drift is rejected so a different context
cannot silently publish another group under a new identity.

Only member mode receives these checks. Both member switches must be enabled;
one switch alone takes the original group path. This closes the accidentally
selectable naive per-member-hashing configuration. Default/Linux dispatch and
the frozen six-patch MCP bundle are not changed. Expected direct speed benefit
of this safety patch is zero; its cost must still pass whole-consumer gates.

## Native Evidence

- `.data/d1510-member-cli-cross-group-v3`: external include mutation after the
  first group is rejected with exit 70 and no binding. Fresh retry has one MISS
  and one HIT, exact ordinary C parity on both members, complete flat-link parity,
  and no remaining member locks.
- `.data/d1510-member-cli-cross-tool-v1`: a valid GNU GCC-built SHA tool with
  identical SHA output but different executable bytes atomically replaces only
  a private copied tool while a subsequent existing-C pin is active. The request
  rejects tool drift with exit 70 and no binding. Retry invalidates the one Scheme
  member, preserves ordinary C/full-link parity, and leaves no locks. The original
  compiler/toolchain is not modified. A 32 MiB trailing C comment only provides
  a real pinning interval; it is a correctness fixture, not a performance sample.
- `.data/d1510-member-cli-guard-consumer-v1`: all 55 real alternating-directory
  inputs retain C/full-link parity, complete ordered bindings and member proofs.
  Mixed Scheme/C/preload, disabled reuse and unsupported-option controls pass.
  Population/HIT process times are 5.59/1.66 seconds; these are component results,
  not MCP first-log/build/test measurements or attributed speedups.
- `.data/d1510-member-cli-half-flag-consumer-v1`: member-proof-only mode follows
  the ordinary group path, creates no member proofs, and passes those same 55-module
  semantic controls.
- `.data/d1510-member-cli-tools-half-control-v1`: the reciprocal tools-only
  combination passes 28 real modules with C/full-link parity, mixed inputs,
  default-off and unsupported-option controls, and creates no member proofs.
  Population/HIT component times are 3.82/0.94 seconds. The harness now writes
  its mode receipt inside the selected output, not at the repository root.

Complete 0041/0042 reverse/forward source replay and frozen-contract/summary
validation pass 12 focused checks. These checks do not replace consumer tests.
The previous 114.46-second ASCENT cold 30-Case run used 0041 without this guard;
it remains historical evidence, not qualification of 0042.

## Guarded Consumer Evidence And Next Eligibility Boundary

The actual guarded ASCENT cold run at
`.data/d1510-member-guard-ascent-receipt-v1` completed in **121.26 seconds**
(301.50 user / 94.85 system), exit 0, **30/30 Cases** and final `OK`. Its own
`just`/Scheme runner used 12 host build cores and a 135-second component ceiling;
Python only read the terminal receipt afterward. This is not all 94 Suites or
a matched speedup. The log has **0 generated-C HIT / 73 MISS**, **0 object HIT /
74 MISS**, one 224-input closed-link selection and an entry cache MISS. The
terminal parser observed zero printable GSC object-command lines; that field is
not evidence that no object compiler ran. It must not override the 74 backend
MISS events.

Project HEAD remains `21e3638687d42ecfc36acebb28991987435ebc60` with a clean
tracked checkout. After execution, all **1989 runtime / 2809 dependency** dynamic
references still verify. The active checkout and shared dependencies are not
used as writable fixtures. Summary SHA256 is
`10d2ecc870a8af2ad12d249d2cacc1373953777a886699a688a3a3081c6e6edf`;
output SHA256 is
`c4884953674ccd78ae4b900de144aef81ea1966b24df3688cf8d9a0aa72c8fbe`.

An ABI-matched private MCP GSC was also built successfully at
`.data/d1510-member-guard-mcp-gsc-v1`. Its SHA256 is
`aeef96bd0ff3fe0630eddf347b18ea97f5c16e27d5faf0b5a6696c183fbe83f7`.
The frozen MCP header defaults to Single VM; the ASCENT candidate uses Multiple
VMs. These images cannot be interchanged. This private ABI pairing does not
disable Multiple VMs for the required latest-staging release.

Its compiled member API passes 11 source/include/options/tool/environment,
failure/publication and malformed-input controls plus two-process concurrency
at `.data/d1510-member-guard-mcp-controls-v1`. External include/tool mutation
controls also reject during compilation with exit 70, then retry with exact C
parity at `.data/d1510-member-guard-mcp-external-v1`. Their identity-log SHA256s
are `1819cca5923dc75289895be987eff01a8b4f593f8aac24f5c3a0a6d65dcf310e`
and `f88b70157d4c9c4e05dcfb51a251fd4825f057e7a5dc454c79c2d6021207e5a8`.
These are native safety controls, not fresh complete MCP timings.

The actual frozen `build/lib/static/std__make.scm` confirms that `make-build`
sets `compile-static-runtime-objects?` when the normalized specification includes
`exe:` or `static-exe:`; ordinary library-only calls default to false. MCP's
real specification includes an executable, unlike ASCENT's independent library
layers. This makes successful same-executor producer recipe handoff eligible
for investigation on MCP, not automatically on ASCENT. Repeating forced static
object compilation from the denied 0033/0034 routes is not justified: it still
changes the dynamic producer recipe and has no demonstrated cold member-cache
benefit. The next integration must retain frozen AOT fast paths and transport
the actual successful worker recipe with 0039's failure/option guards before
any whole-MCP timed run. Expected metadata speed gain is zero; only observed
proof HITs avoiding a second GNU GCC pass can substantiate a performance gain.

## Exact Identities

| Artifact | SHA256 |
| --- | --- |
| 0042 | `81379aa10796f1a31bf06984b07e215062bd86a4b4fcf6c704d589b7a18b85f6` |
| Guarded native GSC | `7980d3b214da33a1e729402ce3fad4b6c26545e4b7b8974ebf64c751f4d7e954` |
| Reproduced unsafe output log | `43454c7eed15e8a70490d279bd2b1c40e314d2ef1e3ebd56d045ebbe7bec9fde` |
| Include-control identity log | `680351002b4753b3f246a7b979bcf75647d43fb18b7aa4292e65cfa21372d578` |
| Tool-control identity log | `661663686403eeed6f5f85c6506fdcb71b0294728530ddb459aba3013e99decd` |
| Original digest executable | `e0124f9b69561d6fc34b148aa57e1573aebb7f3adc0ef4470b657f895156f2df` |
| Replacement digest executable | `bdc835b4f7492c0a307848d95562f239f23e1b5e1df2497326749eda9ad6ad62` |
| Tool-mutation output log | `0c36c693619be67d3b3b5588a67fa1e58c1b8ec359d8cb71697f0c76b4cdff18` |
| Tool-retry output log | `c285c27e257a9979cdd1aab3a75dbf3ac095afc0faa19819a84e92d97a5b257f` |

The retained MCP lock still verifies actual driver/runtime/GSC, original raw
reports and all samples against **4.5/42/97 seconds**. Its preserved first logs
are 4.038/3.980/3.950 seconds, cold builds 36.414/35.552/37.770 seconds, and full
tests 86.924 seconds with 39 files/965 cases. No new MCP timing is claimed.
Guarded whole-consumer correctness/performance, complete ASCENT and general
release admission remain pending; neither 0041 nor 0042 enters the frozen series.
