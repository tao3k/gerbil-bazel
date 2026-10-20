# Fresh Producer Handoff: MCP Denied

## Admission Review

Correct direction to test: preserve original Darwin scheduling only for objects
successfully produced by the current executor queue, with exact static-C/link
binding validation. Older objects still require the full bound proof backend.
Unlike rejected eager-proof configurations, this does not capture every producer
or force every fresh object through another compiler invocation. Expected benefit
was removal of experimental overhead, not an assumed gain over the frozen line.
The opt-in is Darwin-only. Patch 0037 follows the 0028/0031 compiler composition,
not 0034; it remains outside both frozen patch bundles.

## Actual MCP Result

Profile: `d1510-fresh-produced-mcp-v1.json`.
Native binary SHA256:
`e18eb11e437897ca49e12bf5c7375ce78a297a958e21d8291b9065ff8b9c5fa8`.

| Round | First compile log (s) | Complete cold build (s) |
| --- | --- | --- |
| 1 | 3.882220 | 36.188334 |
| 2 | 3.896391 | 35.808262 |
| 3 | 3.883373 | 35.796654 |

All three real clean/build rounds pass, use 12 host cores, and preserve package
source identity. Complete testing takes **81.999996 seconds**; all 39 files run,
but only **38 files / 963 of 965 cases pass**. Overall admission is **DENY**,
despite duration gates passing. Ceilings remain **4.5 / 42 / 97 seconds**.

Both failures are in `test/chunk-05-test.ss`, lines 40 and 52: source-definition
lookup does not return a path containing `/src/`. The current selected test home
has no `src` directory. This is an observation, not yet proof of the complete
root cause: no assertion was deleted, no business behavior changed, and no
identical qualification was repeated to select a passing outcome. Test process
exit zero alone is insufficient; final `OK` and exact case inventory correctly
reject this file.

The initial v1 attempt fails host-memory discovery under the sandbox before
native building. It is not a speed sample. The actual terminal qualification is
`.data/d1510-fresh-produced-mcp-qualification-v2`.

| Raw receipt | SHA256 |
| --- | --- |
| `report.json` | `fdc353bb0ab3cd70d82359f127188de88c59ec1e23ecfe4a433730d0606658a0` |
| `tests/report.json` | `717263e6699bc833254e0a8e727501628ae06d2adcf5ce91cf75f591bb127e76` |
| `progressive-admission.json` | `783953177c52694dda6fa24d254547ddd1a1027ab8ca4205e9d3c06d985d1d33` |

## Evidence Boundary

The actual producer-handoff control preserves the produced object exactly,
executes the native result, and requires only one original object compilation.
The mismatch control mutates static C before the dependent link, rejects the
source binding, retains the object and creates no executable. Patch forward /
reverse replay matches the compiled donor source. The focused native-profile,
producer, native-source and progressive tests pass **51 checks**; Bash syntax
passes. These do not override the failed complete MCP correctness gate.

Minimal ad hoc interpreter queries additionally exit 139 for both this candidate
and the frozen reference with the selected home. Those queries do not reproduce
the framework's full launch environment and are not evidence of a new candidate
regression or a diagnosed root cause.

The frozen six-patch bundle is unchanged and remains the MCP anchor. This result
does not qualify complete ASCENT, establish a causal end-to-end speedup, or admit
general release. Next action is source-lookup fixture diagnosis, not another
unchanged eager-proof or timed qualification attempt.

The [fixture follow-up](d1510-fresh-produced-fixture-diagnosis.md) records the
resolved interpreter-query type error, independently copied source-aware homes,
both subsequent strict test denials, and ASCENT launcher admission controls.
It does not rewrite this original DENY or replace frozen measurements.
