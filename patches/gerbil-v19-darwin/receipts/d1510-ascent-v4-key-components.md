# Real ASCENT Static-Proof Component Evidence

## Review Before Code

- Correct direction: explain real static-object invalidation without weakening
  source, command, environment, tool or output checks.
- Prior exploration: source/concurrent admission passed, but that receipt's
  72 MISS events did not retain individual proof components. Its cause remains
  unproven; a comment alone must not be blamed without component evidence.
- Worthwhile: distinguish changed generated C from unrelated context drift and
  identify actual reusable closure members before another optimization.
- Expected gain: diagnostic code has zero expected speed benefit and cannot be
  admitted as a performance candidate.

## Isolation And Method

Owned COW fixture `.data/d1510-ascent-v4-key-components-v1` is prepared from the
frozen ASCENT fixture using `tests/prepare_ascent_tool_upgrade.sh`. It retains
the pinned consumer HEAD `21e3638687d42ecfc36acebb28991987435ebc60`, Multiple VM
toolchain and genuine private GNU GCC. Neither the active consumer nor shared
dependencies are modified.

`tests/static_reuse_key_trace.patch` adds only component-hash observation to
the private copied V4 helper. It is NOT in `mcp-v4-driver.series` and is not an
optimization patch. The traced helper SHA256 is
`1a668927e38a5194ac52393014de15c6994484ffed57d4e7b0f69a4ab759ed46`.
Reverse dry-run validates the tracked diagnostic patch against that helper.

Both launches use the original just/Scheme native qualifier directly, with a
135-second diagnostic whole-task cap. Python performs only offline trace
comparison, not native test supervision. The second launch appends one comment
to `t/qualification/ascent-positive-plan-test.ss`, without changing assertions.
The exact tracked diff is bound before and after execution:
`19078bbc7f7979ac24c16c5b275fc47d3e5d2ed95f790edfe8ad557a04400dda`.

Traces retain only six SHA256 fields: source C, preprocessed C, sorted complete
environment, tool identities, command/current directory and final key. Raw
environment values are not retained. Traces are moved out of the owned output
paths before the next launch. The offline comparator rejects mismatched
inventories, missing/duplicate/invalid fields and symlinked files.

## Actual Results

| Diagnostic launch | Real | User | System | Object events | Native Cases |
|---|---:|---:|---:|---|---|
| Establish traced helper | 81.48 s | 101.12 s | 33.21 s | 72 MISS | 30/30, final OK, exit 0 |
| Comment-only source change | 58.63 s | 68.87 s | 31.40 s | 70 HIT / 2 MISS | 30/30, final OK, exit 0 |

These are NOT package-cold samples or full-suite qualification. Instrumentation,
population and filesystem warming prohibit a speedup claim from this pair.

All 72 object traces have identical environment, tool and command/directory
components. Exactly two have changed source C, preprocessed C and final keys:
the positive-plan test module and native single-test entry. The other 70 keys
are unchanged and all 70 objects HIT. The retained dependency-graph C compares
byte-for-byte equal after the second launch; its compiled timestamp did not
change. General timestamp regeneration is therefore not the cause in this pair.

This demonstrates unchanged closure reuse under a genuine source admission
change. It does not retrospectively explain the earlier all-MISS receipt.
Next analysis should target the remaining HIT execution cost, preserving all
proof checks; global environment stripping is not justified by these results.

## Receipts And Framework Checks

Private receipts:

- `.data/d1510-ascent-v4-key-components-receipt-v1`: stdout SHA256
  `7a78be407cc292e46244ab6918696cea4e7f6a85ee27755036c6881041475850`.
- `.data/d1510-ascent-v4-key-components-receipt-v2`: stdout SHA256
  `f8e2752aa57032022e18a1a8f2f8e66c0dcd727266d0d8e14bd253a932c515e6`.

Initial root-scoped collection honored ignore rules and omitted private
`.cache` traces. Comparison correctly returned `STATIC-TRACE-DENY Trace
inventories differ`. The retained missing files were collected without rerunning
native tests. The collector now uses `--hidden --no-ignore` and requires an
explicit expected inventory size; the final comparison includes all 72 objects.

```sh
python3 patches/gerbil-v19-darwin/tests/experiment_framework/static_reuse_trace.py \
  .data/d1510-ascent-v4-key-components-receipt-v1/traces \
  .data/d1510-ascent-v4-key-components-receipt-v2/traces
```

Seven offline comparison tests pass; combined trace/patch identity suite has
47 passing checks. Frozen MCP patch/driver/runtime/raw-report identity still
passes. Its 4.5 / 42 / 97-second admission ceilings and measured optimization
patch bytes remain unchanged. Both consumers' complete performance/correctness
admission remains incomplete; no goal completion or GitHub delivery is claimed.
