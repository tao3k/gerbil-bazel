# Existing Producer Batch Revalidation

This is a default-off component experiment, not part of the frozen MCP patch
series. No MCP package-specific source or active ASCENT checkout was changed.
The measured MCP baseline and 4.5 / 42 / 97 second policy remain unchanged.

## Safety Boundary

The non-generating consumer now snapshots all static inputs, producer inputs
and proofs before any leaf lookup. It checks that entire snapshot, every
returned C pin, all tool bytes and the environment before returning any batch.
Later lookups therefore cannot hide changes to an earlier source. Any failure
returns false; the integration caller must retain original Scheme linking.
This is not an atomic filesystem snapshot or protection against arbitrary
hostile writes after the final check. Production integration is still absent.

`.data/d1510-produced-generated-c-contract-v6` passes adoption, static and
producer invalidation, absent-proof fallback, include rejection, post-leaf
tool/static/producer/proof/pin/environment mutation rejection, unchanged-batch
admission, no-generation checks and independent original-link C byte parity.
The v5 attempt failed because the fixture used getenv without an absent-value
default; v6 corrects that fixture and does not alter admission semantics.

`.data/d1510-generated-c-closure-contract-v19` passes all 15 existing
generation/failure/invalidation controls and two concurrent native writers.
Implementation SHA-256:
`c43296bda536f4f63d7f20c526cfc64bd644a5be2a3721eb841c5528ff32595f`.
Consumer contract source/log SHA-256 respectively:
`f432089178aa37444a9494a44e93eea35efab16f3526e0e10ca537c603b3adc2` /
`2bb6fc856b5359fd1856da301634a670653462eca14949f9abc567008873f826`.
Generation contract log SHA-256:
`9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`.
Concurrent writer logs respectively:
`32343ebeeaf34df4bcd31a598892cddab241bc00dafd7a9e12029269715f9cc0` /
`9d0cbee2b538e050b848c920828be342ce8a40a6fc7257f13a3b90c6876bedf8`.

## Real 55 Module Boundary

`.data/d1510-real-produced-generated-c-v3` uses copied paired static Scheme
modules from the isolated ASCENT fixture, preserves input order, and runs GSC
directly with its matching runtime. No Python supervises the native commands.

| Component | Seconds |
| --- | ---: |
| Cold proof population, separate and not amortized away | 18.474463 |
| Existing producer batch lookup | 4.395742 |
| Original Scheme metadata link | 8.63 |
| Proven C metadata link | 0.26 |
| Lookup plus proven C link | 4.655742 |

Both complete link C files have SHA-256
`f77f65622075bab58187de816e461aa1da7429db99afe189cbf57b89591c7e0b`.
Output log SHA-256:
`7fab033321e6c71f11a687e9d6f0ce0d7a73ae5fba413bca1e3ba71bfd678412`.
Original/pin link time receipts respectively:
`523120d893e08830a9d8b155d18ed45cff439225df313ad3535b183b61e1809e` /
`11acc22a9afdb760e97272c4b25ae2de95046685ca9b267e5ff4c8a9d18c3ff2`.

These are component measurements, not complete cold build/test times. The cold
proof population overhead prevents admission as a cold-build optimization.
Previous v2 lookup/link numbers cannot be inherited by the strengthened code.
Next integration must consume existing producers without duplicate generation
and reduce repeated digest-process costs without dropping final validation.
Both full consumer correctness and performance gates remain unproven.
