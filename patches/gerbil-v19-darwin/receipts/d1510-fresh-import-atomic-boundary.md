# Fresh Candidate Import And Atomic Boundary

## Review

The complete MCP wave remains DENY at 97.060801 seconds. Its interruption inside
an import-related trace case does not identify that case as a hang or attribute
the accumulated duration to interpreter startup. Before changing initialization
or process handling, compare actual execution under one selected home.
These are bounded diagnosis controls, not new consumer performance admission.
No production patch, source assertion or timeout is changed.

## Standard-Library Import Control

Receipt: `.data/d1510-fresh-native-import-abba-v1`.
A is the frozen native Gerbil; B is the fresh candidate native Gerbil. Both use
`.data/d1510-fresh-produced-frozen-test-home-v1`, the same package prefix, load
path and experimental environment switches. The command is native Gerbil
`interactive -e`, importing `:std/make` and `:std/test` and printing `IMPORT-OK`.
Four sequential ABBA launches exit zero with that marker.

| Launch | Real / user / system seconds |
| --- | --- |
| A1 | 0.47 / 0.34 / 0.09 |
| B1 | 0.40 / 0.33 / 0.06 |
| B2 | 0.40 / 0.33 / 0.06 |
| A2 | 0.40 / 0.33 / 0.06 |

This does not show a candidate import/startup regression. It is not a disk-cold
startup experiment, a speedup claim or a profile of every child in chunk-07.
The GSC backend is not invoked by this command; no inference about its cost
follows from these durations.

## Original Atomic Case

The existing native `mcp_atomic_case.ss` executes only the original
`gerbil_trace_eval works with imports` case. It uses the same candidate-cold-built
MCP executable for both controls, changing the selected native test interpreter
and child gxi. Assertions, import expression and subprocess timeout remain
unchanged. After matching the fixture's explicit MCP executable path, A and B
run sequentially, directly through Scheme, without Python test supervision.

| Control | Case body seconds | Entire native command seconds | Result |
| --- | --- | --- | --- |
| A2-atomic | 1.573071 | 3.54 | CASE-OK, final OK, exit 0 |
| B2-atomic | 1.583800 | 3.57 | CASE-OK, final OK, exit 0 |

The first two atomic setup attempts omit `GERBIL_MCP_BIN` while running outside
the package working directory. Both fail to open `.gerbil/bin/gerbil-mcp` and
exit 42 before selecting a case. They are not executed-case timing evidence.

| Raw file relative to receipt | SHA256 |
| --- | --- |
| `A1.time` | `318ef85afb90b1304a5732ddc18b8726a7ccdc2a0d145c063a0115b349b38d03` |
| `B1.time`, `B2.time`, `A2.time` | `73b9ca52ecad883c1147b5830480d6551f575e67f971ae21b9ef0d2231fb5101` |
| `A2-atomic.log` | `c362b675f900b2e40b6bc12fec95ef84c203888746fdc4c5dc26980a6cc2fd6b` |
| `B2-atomic.log` | `345ce18420ceaa806674f29117b23fcf7cdea8e37c98ff9dc085bf7fd51bcac0` |

## Consequence

Neither control reproduces a material startup regression or abnormal wait in
the interrupted case. Do not rewrite initialization or process handling based
on the last complete-wave log line. Chunk-07's accumulated work still needs
attribution; no resource-contention explanation or end-to-end gain is proved.

Separately, the 0037 current-queue branch checks selected C content, but its
fresh-object bypass needs a direct production-to-consumption options/toolchain
change control. Existing backend invalidation controls cover objects sent
through that backend, not objects bypassing it. The mode-sensitive control used
unchanged options and cannot close this requirement. Test this boundary before
further producer-proof changes or promotion. The frozen six-patch bundle and
4.5 / 42 / 97-second gates are unchanged; complete admission remains pending.
