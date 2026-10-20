# D1510 Unused Rest Priority Boundary

Decision: no runtime candidate is admitted from this audit. Do not change the
human-owned AOT configuration or CI. Keep the frozen D1510 carrier and the
5-second first-compile, 50-second cold-build and 112-second complete-test gates.

## Source Mechanism

The original generated runtime/expander C contains three exact constant-return
rest-only leaf bodies: `true`, `false` and `void` in runtime util. Each has
`IF_NARGS_EQ(0, SET_R1(NUL))`, `GET_REST(0,0,0,0)`, a constant result and
`JUMPRET(R0)`. This is distinct from immutable-rest forwarding: the body does
not read the constructed list at all.

The existing leaf-clone whitelist excludes `GET_REST`; bounded primitive
entries target length, reverse and structure predicates. Those transforms do
not already cover this exact entry shape.

Gambit's `_kernel.scm` rest handler, lines 501-601, pushes register arguments,
constructs pairs, handles a heap-limit transition with a GC-safe argument vector,
restores formal arguments and re-enters with negative argument count. The C
backend emits the handler dispatch in `gsc/_t-c-2.scm`, lines 724-773.
`IF_NARGS_EQ` has a trailing `else`; inserting an independent statement between
it and `GET_REST` is not a valid transformation. Any later optimization must
prove stack cleanup, internal negative-count re-entry and heap/debug contracts,
not merely delete the allocation macro.

## Reused Work Evidence

The retained D1334 preparation-corpus histogram records:

| Entry | Calls | Constructed pairs |
| --- | ---: | ---: |
| true | 6,803 | 6,803 |
| false | 34,931 | 34,931 |
| Total | 41,734 | 41,734 |

At the retained 24-byte raw pair allocation, this is 1,001,616 bytes. There is
no matching `void` row; absence is not proof of zero calls. Evidence:
`.data/d1334-rest-forward-executed-elision/mcp-counts.rest-callees.69956.tsv`.
This is an older instrumented preparation corpus, not the current frozen-host
first-window census, an exclusive CPU budget or an end-to-end speedup.

The recorded opportunity is substantially smaller than the previous
135,975,888-byte rest-forwarding elimination, which did not establish a major
matched startup win. This supports deprioritizing the narrow constant-leaf
route; it does not mathematically bound its possible CPU benefit. No candidate
was rendered, rebuilt, timed, committed or published from these counts.

## Mainline Boundary

Continue on shared dependency import and macro-expansion execution, not
package-name specialization. The earlier real native-phase initialization is
millisecond-scale after dependencies are loaded, so replacing that body is not
evidence of removing the dependency-import cost. Retain the existing negative
results rather than retrying them under a new name. A future candidate still
needs independent standard-library checks and all three whole-task gates.
