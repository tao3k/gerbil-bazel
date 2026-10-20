# Explicit Producer Alias Qualification

## Direction Review

The real Darwin runtime producer in `compiler/driver.ss:gsc-compile-file`
passes both `-module-ref` and `-linker-name` using the same static module stem.
Removing those arguments would change the generated linker identity. Qualifying
them is a prerequisite for integration, not a new timing route or package-specific
optimization. Expected benefit remains elimination of duplicate source generation;
this receipt does not establish a new consumer speedup.

## Admitted Options

The closed adapter now accepts optional `(target C)` and an optional paired
`(module-ref SYMBOL)` / `(linker-name STRING)`, only when the string is the
symbol's spelling. Keys must be unique and each form have exactly two elements.
Input option order and values remain in the context digest, without sorting or
discarding aliases. Empty options remain supported.

Missing pairs, mismatched aliases, duplicate target options and debug options
are rejected by the admission predicate. Arbitrary GSC CLI flags are not parsed
or admitted. Unsupported options still take the uncached compiler path and mark
the process unsuitable for later cache admission.

## Native CLI Control

`tests/check_real_generated_c_alias.sh` invokes original GSC with explicit
`-module-ref`, `-linker-name` and `-target C`, then compares entire output bytes
with the prototype API. Output basename and input path are matched.

Receipt `.data/d1510-real-generated-c-alias-v2` passes:

- original CLI/API generated-C parity;
- repeat HIT with empty generation work directory;
- changed alias MISS with changed proof and pinned output identity;
- earlier pinned reader retaining original bytes;
- admission rejection of the five unsupported option shapes above.

v1 was rejected: the control wrote `alias-first.c` while the candidate wrote
`module.c`. Its sole C difference was the generated file-name comment. v2 fixes
the mismatched control basename; no compiler output is filtered or normalized.
The alias control uses a small deterministic Scheme fixture, not a complete
ASCENT production build.

## Regression Qualification

`.data/d1510-generated-c-closure-contract-v17` passes all 15 existing native
controls plus two concurrent native writers. `.data/d1510-real-generated-c-closure-v15`
passes the 55 real paired ASCENT module C comparisons and whole default incremental
link C byte comparison. These are component tests against the frozen owned
source inventory, not the independently updated active ASCENT checkout.

Original generation process wall time: 3.53 seconds. API first generation and
proof population: 4.571812 seconds. API validated HIT: 0.698918 seconds. API
timings exclude process startup. First population remains a cost, not an accepted
cold-build optimization. The next adapter must use the existing runtime C producer
and must not add a second cold generation.

## Exact Identity

- Producer: `8f0d27d37a24579086032fef74c5bde9598d2019294e71bf3c96da548c4b9ac4`
- Alias control: `fec8553ace0e1a4b20b2eb04d11afaa0eb3825f2ba9355f63d8bee20ade7f3d3`
- Alias output: `641bbb6edba43c2ec5e21cd950f6631e56c7e0c27040404930de6e253e65ef74`
- Contract output: `9c4716e3f75e012c60420c86cade5e28a3b8343fc4e069852092d38e739019e5`
- Real-source output: `ebdc43af8fa9e4da4dcc506b84e7a67433c261874c667099c8893dab890794d2`

No product/default enablement, consumer integration, cold-build admission or
complete-test admission follows from these controls. Native objects' original
include/debug/source-path semantics and actual production alias combinations
still require integrated qualification. MCP and ASCENT whole-task gates remain
open; unrelated ASCENT scheduling/cache changes are not compiler evidence.
