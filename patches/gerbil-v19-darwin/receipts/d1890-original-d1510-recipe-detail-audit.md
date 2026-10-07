# D1890: original D1510 recipe detail audit only

No new candidate, binary construction, consumer performance run or source
profile substitution occurs in this audit. Original D1510 remains selected;
the unresolved complete-build references are 51.737180/53.496910 seconds,
with the unchanged 55-second admission gate. The latest original replay is
58.442762 seconds, not restored performance.

## Construction details recovered from the original records

D1510 consumes D1508's current D1391 object-reuse inputs, not an arbitrary
later carrier. The input module order comes from the retained D994 order
record. All 42 static C inputs remain protected by their original hashes.

The original recipe enables readonly identity-call traces, polls, restart and
coalesced polls, primitive boundaries, inline/outlined lookup, lookup return
branches, parameter entry/identity/environment paths and bounded primitives.
It does not enable later scalarization, result caches, epoch shortcuts,
supplementary traces or return-outlining experiments. The resulting selection
has 11 modules in one host and exactly 14 recorded trace shapes.

The original carrier is compiled at O1 through the original gambuild-C and
linked with the original ordered static objects, main and runtime archive.
The already generated lookup helpers have their existing bounded native
optimization settings. This is not a reason to change global optimization
flags. GSC remains the original compiler for consumer compilation; the
application executable does not automatically inherit the D1510 carrier.

Original carrier SHA256:
`e4a2ffde9b4dc329bf44db818f8241a30ef0c8ecaa7fc220c3fe6521936277e1`.
Original binary SHA256:
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`.

## Generator drift and bounded replay

D1508 records hashes for five generation helpers. Three current helpers differ:
gambit_guarded_trace.py, gambit_host_coalescing.py and gambit_trace_outlining.py.
This justified checking the original recipe, not assuming current helpers are
historical source snapshots and not replacing the original binary.

D1888 runs only the original D1508 preflight recipe in a fresh output directory.
All 42 input hashes and the GSC hash match; all 14 complete trace records match.
It does not compile a carrier object or link a replacement executable.

D1889 compares the original and replayed generated source. The carrier's raw
hash differs. The formatter creates alias dictionaries from a set of private
identifiers, so alias directive order is not deterministic across processes.
Its output-directory references also differ. The comparison sorts only unique,
contiguous, single-token module alias definitions and normalizes only the two
explicit output-directory prefixes. Both files contain 23 such blocks with
34,627 bindings. No instruction, statement, trace, literal or timestamp is
masked. After those two bounded normalizations, carrier text is identical.
All eleven module C files and the original link C also match after the explicit
output-directory normalization.

Thus this audit finds no additional generated behavior from the changed
helpers under the original recipe. It does not establish exact raw carrier or
native binary reproducibility from a new generation, and does not explain the
51/56/58-second execution variation of the unchanged original binary.

## Boundaries kept

Do not replace the retained original carrier with a newly generated raw-hash
variant, choose another candidate by its timing, or call source-shape parity
a performance restoration. No default release profile or GitHub PR changes.
Further execution investigation remains on D1510's original pre-executable
compilation stage, using the existing timing and artifact evidence.

Private evidence: `.data/d1508-outline-current-preflight/`,
`.data/d1510-outline-current-native/`,
`.data/d1888-original-d1510-recipe-preflight/`, and
`.data/d1889-original-recipe-source-audit/`.
