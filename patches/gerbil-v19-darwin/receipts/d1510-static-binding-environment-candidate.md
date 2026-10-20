# Static Binding Environment Candidate

## Admission Review

Correct mechanism: a binding variable belongs to source validation, not GCC's
recipe. The actual prior boundary control found identical dynamic CPP and object
bytes but a different proof key solely from
`GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA`. This caused a needless MISS.

Already explored: dropping this field only from a key was explicitly unsafe,
because actual GCC still inherited it. The present change saves and validates
the expected digest, then unsets the variable in the helper process before both
environment acquisition and actual compiler execution. Source binding remains
an independent checked argument. Other environment fields and full source,
CPP, options, object and tool content checks remain unchanged.

Worthwhile: an identical verified recipe can avoid another GCC optimization /
generation pass. Expected benefit is that eliminated pass, not a quantified
whole-package gain. This does not retry the denied all-producer capture setup
or use metadata-only tool trust. It is a prerequisite for affordable full proof,
not a repair of 0037's unproved fresh-object bypass.

## Patch And Replay

Experimental patch:
`0038-gambit-darwin-static-binding-environment.patch`.
SHA256: `bcacf4529604f006e5b3f6af3267e9ae9834ba1878ceb42aba56525c5e89b282`.
It follows the experimental 0036 helper, not the frozen six-patch bundle.
It has no package names, package-specific shortcuts or new default enablement.
The helper's existing Darwin/GNU opt-in boundary remains intact; the non-Darwin
early return does not enter this changed function.

Actual replay: `.data/d1510-static-binding-patch-replay-v1`. Forward check/apply,
reverse check/apply, exact original helper parity, then reapply and exact
installed candidate parity all pass. Candidate helper SHA256:
`6b071f05f5e92bacba23c67b9825dbef2e89634a8d63580da9871ccb2ed82dd9`.
Installed controls use `.data/d1510-static-binding-native-v1/bin`; the original
selected ASCENT home and its dependencies are not modified.

## Actual Proof Controls

The copied real ASCENT binary-relation C has SHA256
`c32aaf784e326527c060312d3c2c7480218d19de058f584e763944b75f639e36`.
Selected Multiple-VM GSC has SHA256
`7f8423a0c1ab30313cd37b6482d1b931a076a6d91c5a9c2527664b3d897aeeff`.
GNU GCC is selected through the qualified Darwin path.

The original diagnostic helper is cloned privately and given the same two-line
change, retaining its environment/context audit output. Direct controls pass:

| Receipt | Actual result |
| --- | --- |
| `.data/d1510-static-proof-binding-sanitized-v1/receipt-v1` | Shell proof: same recipe HIT, identical object/proof/environment, changed mode MISS, wrong binding DENY with old object retained |
| `.data/d1510-static-proof-binding-sanitized-v1/native-receipt-v1` | Native proof-check marker required and present; same recipe HIT, changed mode MISS with different object, wrong binding DENY with old object retained |

The shell producer and bound-consumer proof SHA256 are both
`28a19bd869e0820e1db485d3e115b27d93679b7acaed808ad422918216dac8cd`.
Their environment SHA256 values are both
`1a8c5c6733b9535e9f3498f25ee069079c00ae156b9ed13dd627351a1483841b`.
This proves a genuine reuse decision without rekeying the old proof by hand.
Native producer/bound proof SHA256 is
`b994bd1c01b633f3fa6f43b4aac2876d9bc8d9b1171bc4a1dfa8a7013d9a84b8`.
Relative native raw log identities are:

| File | SHA256 |
| --- | --- |
| `bound-same-mode.log` | `66edc06abd55e572c5d036d691f07dff388d073e2da6483a9d7cac4e12df0976` |
| `static-mode.log` | `2d3412379a0658ab820ada7bcba983747223bc1ae689eac1ddcf8d62298eae30` |
| `wrong-binding.log` | `9956a45f1e921ec103f1d47ed24a4c7e8e32617122a69c9e61e707e04bd9308e` |

The uninstrumented patch-installed helper also passes all **22 existing native
contracts**, directly through Bash/GSC, against the selected Multiple-VM ABI:

| Owned receipt below `.data/d1510-static-binding-native-v1` | Contracts |
| --- | --- |
| `reuse-controls` | 8: actual C/object parity, options, header, object tamper, concurrency and compilation failure |
| `identity-controls` | 3: source/helper/driver content invalidation |
| `safety-controls` | 6: proof path/symlink, diagnostics and mid-flight mutation |
| `toolchain-controls` | 5: compiler/assembler/digest mutation, unavailable digest and mocked platform fallback |

All four commands exit zero. Mocked fallback is not actual Linux CI coverage.
Bash syntax validation of the extended boundary runner passes.
The focused selected-home, trace and frozen-lock suite passes 22 framework
tests; these are distinct from the 22 direct native contracts above.

## Remaining Gates

No new MCP cold build, complete MCP test or ASCENT AOT Cases result is claimed
for 0038. Both frozen series, original toolchain bytes and 4.5 / 42 / 97-second
ceilings remain untouched. The six-patch anchor retains three cold builds
36.414 / 35.552 / 37.770 seconds, first logs 4.038 / 3.980 / 3.950 seconds and
one complete 86.924-second test pass, 39 files / 965 cases.

0037's production-to-consumption options-change control still DENIES. A next
composition must route fresh objects through their actual bound producer recipe
rather than inherit timestamp-based acceptance. No all-producer or whole-wave
configuration is admitted by this component evidence; dual-consumer correctness
and performance qualification and general release remain incomplete.
