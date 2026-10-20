# Generated C Member Independence

## Review Before Code

Correct target: reduce repeated Scheme-to-C generation at the actual static-link
consumer, without making every ordinary library compiler produce extra proofs.
0039's queue metadata does not cross ASCENT's library-only compiler processes.

Already explored: ordinary multi-input GSC batching is denied by D859. Persistent
consumer-side generation is already implemented by 0029/0030. Neither is a new
proposal here. The uncovered question is whether a changed member must invalidate
the generated C of every other member in its directory group.

Worthwhile: existing group proofs bind all member source digests, so one changed
member regenerates unchanged C too. The original Gambit implementation calls
`reset-options`, establishes a new compilation context, and creates a new global
environment for each file (`gsc/_front.scm` and `gsc/_gsclib.scm`). This is a source
reason to test file-level generation independence, not proof that arbitrary
macro/evaluation contexts can be cached separately.

Expected benefit: avoid generation of unchanged members after a member changes.
Cold proof-acquisition overhead and whole-consumer benefit are unknown. The
existing 55-module generation opportunity is about 3.6 seconds, not a predicted
MCP percentage or seconds-scale first-log improvement. No cache implementation
or production patch is admitted by this control.

## Actual Native Control

`tests/check_generated_c_member_independence.sh` copies the 55 real paired
ASCENT Scheme inputs into a fresh owned receipt directory. It uses the ordinary
native GSC APIs, with closed-link / producer caching disabled, and unchanged
matching Multiple-VM headers/runtime. It never edits the original paired-input
directory, active ASCENT checkout or shared dependencies. There is no Python
native-test supervisor and no parallel-build policy change.

1. Ordinary `gsc -link -flat` establishes this exact compiler's C and link output.
   Saved historical C is not trusted as the reference.
2. `compile-file-to-target` recompiles all 55 members in reverse order with
   explicit target C and the same output basenames. Every module C and the full
   flat-link output remain byte-identical.
3. A new definition is appended only to the copied first member. Only that
   member is recompiled. Its C changes; all other 54 C files remain unchanged.
4. An ordinary complete Scheme link regenerates all 55 C files. Its complete C
   inventory and link output exactly match the partial-generation result. The
   other 54 files still match their original C bytes.
5. Compiler content and every original source remain unchanged. Nonmutated
   copied sources also remain exact. Errors propagate through the Bash receipt.

Both receipts terminate at exit zero:

| Receipt | Reverse all 55 | One changed member | Complete changed Scheme generation + link |
| --- | --- | --- | --- |
| `.data/d1510-member-independence-v1` | 3.58 s | 0.03 s | 3.83 s |
| `.data/d1510-member-independence-v2` | 3.60 s | 0.03 s | 4.07 s |

These columns cover different work; the one-member time excludes final linking,
cache validation and publication. Do not divide them into a whole-package gain.
v2 adds an explicit saved-source check for the original first member as well;
v1 did not check that member after mutating its private copy. No compiler behavior
changed between these receipts. v2 is the final source-preservation control.

Final marker: `GENERATED-C-MEMBER-INDEPENDENCE-OK modules=55 unchanged=54
C-and-flat-link-byte-parity`. Bash syntax validation passes.

## Exact Final Receipt Identities

| Artifact | SHA256 |
| --- | --- |
| Native GSC | `7f8423a0c1ab30313cd37b6482d1b931a076a6d91c5a9c2527664b3d897aeeff` |
| `tests/check_generated_c_member_independence.sh` | `82383a7f15e56715ec5c367a07683f1d0a9723634056ac9f245dc0d1118c2197` |
| `tests/generated_c_member_independence.scm` | `0c30075f330b5af1b21fcc6adf64fe8f8b0fe7afdc941211a3f34a38823efc05` |
| v2 original-source inventory | `6c1b40a9528a209b097d78b5e5ef0fc510b488bbc3563cda21ccdf6b4cd54854` |
| v2 partial / complete C inventories (equal) | `3ccd67dd9bdee5896b63f5594d96b81780d921cd791b7e19de297358d397015d` |
| v2 partial / complete link C (equal) | `c63ba70603e2afcd4b05da8eaccfc17252dbda32566d4d49970e6c8c3a0fc962` |
| v2 reverse log | `fa2857a10edf926ee3f36e1ffbd907429df64ffdcddfd5426c5b7c9f15a2841a` |
| v2 one-change log | `183d73c70fed1cc2df7e99926bc457a30ed8b8bc5967aab1242da9643ea18755` |

## Next Admission Boundary

The evidence supports a separate member-granularity generation experiment, not
removing complete-link validation. An implementation must still bind every
selected input in exact order, member source and transitive read snapshots,
compiler/options/environment identity and immutable C content. Unsupported macro
contexts must remain uncached. Failure, concurrent publication, dependency /
option / tool mutations and cold acquisition cost require native controls.
Do not rehash the full compiler separately for every member; any shared batch
snapshot needs actual complete before/after tool checks, not metadata trust.

No new whole MCP or full ASCENT results were produced. The frozen six-patch MCP
bundle stays unchanged: first 3.950--4.038 s, cold 36.414 / 35.552 / 37.770 s,
complete test 86.924 s with all 39 files / 965 Cases. Gates remain 4.5 / 42 / 97 s.
The dual-consumer goal remains incomplete. This is component generation evidence,
not a latest-staging rebuild, cache patch delivery or GitHub publication.
