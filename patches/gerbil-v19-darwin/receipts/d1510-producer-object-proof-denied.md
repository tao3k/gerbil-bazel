# Producer Object Proof: MCP Denied

## Review

Correct mechanism to investigate: the original Darwin producer already compiles
the object later used by native linking. A closed-link consumer must validate its
actual `-D___DYNAMIC -fPIC` recipe, not force a different static recipe merely
because C bytes match. This was not the missing-object-only 0032 path, nor the
0033 consumer-only capture path. Expected benefit was eliminating repeated
object compilation, contingent on affordable proof capture. No package-specific
business source was changed.

The resulting 0034 patch is **experimental and DENY**. It is not added to either
frozen measured series. Mechanism correctness in one real module does not admit
whole-consumer performance.

## Actual Results

The optimized donor was compiled with the matching isolated Multiple-VM toolchain;
only two compiler definitions were merged into the frozen MCP AOT source. The
matching native carrier was regenerated. Interface checks preserve all previous
global references and permit only the same eleven imported references required
by the prior closed-link driver. Native standard-library import smoke passes.
Private construction receipt: `.data/d1510-producer-proof-mcp-aot-v2`.

The real-module fixture uses Gerbil's output-dependent job queue, not a fabricated
producer marker. Its producer creates an object and full backend proof before
the executable is scheduled. The link handoff uses the matching dynamic options,
hits the proof, preserves exact object and proof bytes, and runs the native
program. The fixture now owns its Gerbil prefix rather than using a global prefix.
This is a one-module mechanism check, not ASCENT suite qualification or a package
benchmark.

Fresh MCP qualification: `.data/d1510-producer-proof-mcp-qualification-v2`.

| Metric | Result | Gate |
| --- | --- | --- |
| First compile log | 4.053162 s, pass | 4.5 s |
| Complete cold build | Unknown; stopped at 42.029597 s | 42 s |
| Complete tests | Skipped | 97 s |
| Further cold rounds | Skipped after first DENY | Three passing rounds required |

The process group was force-stopped and reaped, with no cleanup errors. Original
consumer source identities remain unchanged. The preceding v1 attempt lacked
the candidate binary's construction receipt and failed before any cold build;
it is not a timing sample. V2 is a terminal DENY, not a completed 42-second build.

At the stop, logs contain **183 single-pass producer captures, zero object HITs
and zero closed-link selection events**. Thus this implementation incurs proof
capture on initial library compilation before reaching its intended reuse stage.
That is materially different from assuming linkage misses caused this regression.
All-module eager proof capture in this form must not be rerun unchanged.

## Next Boundary

The proof helper fingerprints approximately 68.5 MB of compiler/backend tools at
each full tool check. One local batch measured about 0.03 s real / 0.02 s user;
this is an illustrative component observation, not wall-time attribution or an
end-to-end speedup. Every captured object performs repeated content checks, in
addition to source snapshots and subprocesses. A next candidate must reduce that
repeated acquisition work without removing source/options/toolchain invalidation
or accepting unproved objects. A filename/mtime-only bypass is not admitted.

The framework records and forwards the producer-proof switch, clears inherited
state, and requires cold/test policy equality. The focused identity, controller,
complete-test and producer patch-replay checks pass **47 tests**. Actual 0034
forward/reverse source replay passes exact donor parity. Raw evidence hashes and
the terminal decision are in [the denial receipt](d1510-producer-object-proof-denied.json).

The safe frozen line remains three cold builds **36.414 / 35.552 / 37.770 s**,
one complete test **86.924 s, 39 files / 965 cases**. Its patch/runtime/evidence
bytes and **4.5 / 42 / 97 s** gates are unchanged. No new ASCENT package test,
full latest-staging rebuild, general production admission or GitHub delivery is
claimed for this experiment. The dual-consumer goal remains incomplete.
