# Generated C Pinning And Default Link Parity

## Review

Direction: generic Darwin-only immutable generated-C identities, not a package
name special case. Retain old readers' bytes across later logical publication.
This advances concurrency safety before consumer integration. Expected repeat
benefit is avoiding the already-measured Scheme-to-C rewrite; no whole-build
benefit is admitted here. First proof population remains slower than generation.

## Current Native Evidence

Contract receipt: `.data/d1510-generated-c-closure-contract-v12`.
Twelve controls pass, including retained-reader bytes, corrupt-pin rejection
without damaging the logical publication/proof, source/tool/environment
invalidation, failure preservation, macro/option fallback and diagnostics.
Two concurrent native GSC writers pass. Proof is mode 0600 and does not retain
the injected environment secret. This is not a claim of arbitrary hostile-writer
or mid-publication failure coverage.

Real-source receipt: `.data/d1510-real-generated-c-closure-v11`.
All 55 paired owned ASCENT modules match original GSC generation byte for byte.
Both canonical and pinned C are passed to default incremental GSC linking in
the same declared order, with the same output name and matching base runtime.
The resulting entire link C files match byte for byte.

| Phase | Seconds | Scope |
| --- | --- | --- |
| Original generation | 3.53 | Native process wall time |
| Generation and proof population | 4.760703 | In-process API wall time |
| Validated repeat reuse | 0.508475 | In-process API wall time |

Timings have different startup boundaries and are not an end-to-end ratio.
Population overhead is not an accepted cold-build optimization.

## Rejected Or Corrected Probe Results

- v7: pin layout preflight rejected an incorrect parent directory.
- v8: canonical default linking failed before testing pins because the isolated
  bin-only profile pointed at a nonexistent runtime library. The harness now
  requires an explicit owned runtime and byte-compares its GSC with the selected
  compiler before using its base link file.
- v9: source-path preflight failed; no timing qualification.
- v10: link byte parity failed because the harness used shell-glob order for
  canonical inputs but filesystem enumeration order for pinned inputs. This was
  not evidence of GSC sorting by path. Both sides now consume one ordered roster;
  the producer's order is preserved, not silently normalized by the cache.

## Identity

- GSC: `9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`
- Producer: `f0c6cf172d1ee7459e2b29e509fe1f52aac71deebdb80686f1840b7484601130`
- Real-source fixture: `e546a6f5f2bb26fe936f0dcd539690339698c81ca662d16bf4b279c291a08f23`
- Contract output: `542a9e2c63fa645b71cd06256956223dc807fce95e1064f4dc0cea09852dec30`
- Real-source output: `a15742d48a9cf13fd14328fc8925f63bc0c7b6eb1a4dbe159fbaeaa39000129d`
- Equal incremental link C: `f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`

## Remaining Admission

Neither consumer calls this API yet. Native object compilation through pinned
paths is not qualified: quote includes, debug/source paths and object proof keys
must retain their semantics. Loaded compiler image identity, supported producer
aliases/options, cross-process invalidation and publication-failure controls
remain required. Integration must consume already-produced C rather than add a
second cold generation. The MCP three-task gates and isolated ASCENT cold
nonregression gate remain unmet; this receipt does not promote a default patch.

## Explicit Target And Context Revalidation

The next revision admits exactly empty options or `((target C))`, retaining
their distinct serialized context identities. It does not generalize to arbitrary
GSC options. A dedicated control proves original target-C byte parity, repeat
hit with no generation, and invalidation when returning to empty options.
Unsupported warning options and source macros retain uncached behavior.

On a hit, pinning now consumes the expected output digests in the admitted proof,
not freshly trusted output bytes. Source, output, tool and environment identities
are checked again before returning. The miss path rechecks source/tool/environment
after pinning and before logical publication. Native fault-injection controls
change an included source during pinning on both hit and miss: both requests are
rejected, the prior logical C/proof stay byte-identical and the lock is removed.
This does not make a multi-output logical publication transactional or prove
protection against a hostile writer changing files after the final check.

Current contract receipt `.data/d1510-generated-c-closure-contract-v16` passes
15 controls plus two concurrent native writers. Current real-source receipt
`.data/d1510-real-generated-c-closure-v14` uses explicit target C on both sides;
all 55 generated modules and the complete default incremental link C match.
Original process wall time is 3.67 seconds; API population is 4.696271 seconds;
API hit is 0.818897 seconds. Added safety validation has real cost. Earlier
0.508-second observations must not be advertised for this revision.

Current identities:

- Producer: `68719131b8e4afcd2217ef66b234778529a7cb01893f02534633544223670572`
- Contract: `0208488ba4684da7e2807d7555b64bfdd794118436926799e97336d36fa12280`
- Real fixture: `69981d29b847f219eaf859ce91fd7981562eb324719f73c362f4180ddd55d8ba`
- Contract output: `9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`
- Real output: `1ce893b34624185811e0bee6f0c4509d809dea926c0c0c06a956809ac9e69640`
- Link C remains `f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`.

The production adapter also needs the actual runtime producer's explicit
module-ref/linker-name identities (`gsc-compile-file` in compiler/driver.ss),
which are not admitted by this revision. Do not drop these aliases to make the
prototype fit the real path. The next integration must preserve these identities
and consume the runtime producer's already-generated C.
