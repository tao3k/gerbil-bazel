# In-Process Digest Qualification

## Direction Review

The v8 generated-C producer component takes 10.07 seconds versus 6.27 seconds
for the original producer. Its later linking saving does not recover that cost.
This candidate addresses repeated digest subprocess creation, not dynamic/static
alias compatibility. The prior batched external helper still launches processes;
this bridge calls the unchanged file-digest routine inside the Scheme process.
It is not another retry of the denied whole-consumer wrapper.

Potential benefit is bounded by the producer's measured 3.80-second added cost;
there is no established whole-build saving or assumption that all of that cost
is removable. The bridge must pass digest equivalence and the existing proof
protocol before native integration. Consumer adoption remains a separate gate.

## Executed Evidence

`.data/d1510-generated-c-native-digest-v4` compiles a private native Scheme module
with the frozen GNU-GCC driver and matching runtime. It includes the unchanged
tracked `gambit-file-sha256.c` implementation. No shell hash tool is invoked by
`generation-native-file-sha`; it returns the same 64 lowercase hexadecimal bytes.

Passed controls: ordinary content, empty file, compiled module bytes, a filename
with spaces/backslash/newline, missing-file failure, directory failure, changed
file invalidation and repeated parity.

100 small-file calls in this component-only observation:

| Backend | Seconds |
| --- | --- |
| External helper per call | 0.245212078 |
| In-process bridge | 0.001174927 |

Do not extrapolate this small-file ratio to hashing large toolchain binaries or
end-to-end compilation. This is one observation, not a stable performance gate.

`.data/d1510-generated-c-native-digest-contract-v2` loads the bridge through an
explicit contract-only adapter. All 15 existing generation contracts and both
concurrent producer controls pass, including source/options/tool/environment
invalidation, changed sources during publication/hit validation, corrupt pins,
failed compilation preserving prior publication, macro fallback and diagnostic
parity. Final contract output SHA matches the retained external-backend contract.

The adapter selects only the explicitly named fixture helper; other tool paths
retain the original external behavior. It does not change frozen patch bytes.
It is not installed in the native GSC or admitted for a package run. Native
integration must bind the compiled bridge into GSC's content identity; a loaded
fixture module is not sufficient production toolchain provenance.

## Failed Setup Attempts

v1 fails before compilation because the driver bin is not a complete runtime
prefix. v2/v3 fail during bundle linking with unresolved C-library imports.
v4 supplies the matching runtime, explicit SDK and Darwin bundle dynamic lookup;
all runtime parity/failure tests then pass. These failures are retained; they
are not performance samples and do not justify changing the frozen driver.
The separate native-GSC static executable link must also qualify this bridge.

## Identities And Boundary

- Bridge source: `ff16a2e76f1a5009ffeacdd6aa0cc11f978a9e7993cb5a5e381f14f86d0a45ec`.
- Adapter source: `285e7daff4b72d5b4e8cb9bf5fabaf145e1ff1022d2f73beee91dfc1f1ab569a`.
- Digest controls: `7e61419a92b08320c23f55756408c4fd0c776760d749736f2d5d58e0596b58c2`.
- Generation contracts: `9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`.

Shell syntax checks pass, and the frozen patch-lock unit suite still passes all
11 tests. The 4.5/42/97 MCP ceilings and best receipts are unchanged. No new MCP
or complete ASCENT performance admission is claimed; the thread goal remains open.
