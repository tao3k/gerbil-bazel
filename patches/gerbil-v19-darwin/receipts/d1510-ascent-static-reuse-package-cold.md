# ASCENT Package-Cold Admission

## Review

- Direction: qualify the generic v4 object-reuse path on a real independent
  consumer, including library construction rather than only entry relinking.
- Prior coverage: successful repeated-entry runs retained compiled libraries;
  they do not prove package-cold performance.
- Worth testing: a default-enabled optimization must not hide cold-path cost
  behind gains available only after proof population.
- Expected benefit: no cold speedup assumed. The candidate may reuse unchanged
  dependency objects, but freshly constructed package outputs are not hits.

## Matched Setup

Both runs use the same isolated project, head
21e3638687d42ecfc36acebb28991987435ebc60, GNU GCC 16, compiler-aligned PATH,
private toolchain, dependencies and original Justfile/Scheme native qualifier.
Hardware-derived build capacity remains 12, with the original 1 GiB heap and
native deadlines. Python only reads terminal receipts; it never launches or
supervises native tests.

Before each run, the owned .cache/ascent/native-library directory is moved aside.
The qualifier reconstructs 85 production modules, 87 support modules and the
one requested Suite, then compiles/links the AOT entry and executes its Cases.
This is package-cold, not a from-zero build of the toolchain and dependencies.
The isolated dependency objects and previous object-reuse proofs remain present;
the control ignores those proofs and the candidate can use them. The control
executes first. No repeated matched series or statistical admission is claimed.

## Actual Complete Results

| Metric | Original Command | v4 Candidate |
| --- | --- | --- |
| Whole native task | 98.66 s | 101.90 s |
| User CPU | 281.73 s | 325.07 s |
| System CPU | 69.92 s | 79.56 s |
| Cases / final marker / exit | 30/30 / OK / 0 | 30/30 / OK / 0 |
| GSC object invocations | 74 | 74 |
| Object reuse events | none | 17 hits / 0 misses |
| Upper entry cache | MISS | MISS |

Candidate wall time regresses by 3.24 seconds (3.28%); user CPU increases by
43.34 seconds (15.38%). Seventeen object hits are not complete performance
admission. Default-enabled/general cold acceleration is DENIED by this pair.
The passing repeated-entry scenario remains separate evidence; do not erase it,
but do not substitute it for package-cold qualification. Do not repeat the same
candidate unchanged seeking a favorable wall-clock sample.

The receipt does not establish which stage caused the extra CPU. The next
investigation must isolate costs before changing the implementation. In
particular, missing-output fallback currently still acquires a cache lock and
invalidates a proof before the original compiler command. That is a concrete
source path to inspect, not proof that it explains the measured regression.

## Provenance And Isolation

Raw receipts:
.data/d1510-static-reuse-ascent-package-cold-control-v1 and
.data/d1510-static-reuse-ascent-package-cold-candidate-v1.
The offline summary .data/d1510-static-reuse-ascent-package-cold-summary-v1.json
binds exact raw output SHA-256 values:

- Control: 2a56d84aceb13b27ecd678eb06f3c46bdc129bca5ca9dfbf36a4ad109bcda3d0
- Candidate: 3fdd9d53d72a6c43093e42554a0be476beb0f53ed99c66103f9573986ce4044f

Post-run checks verified all 1,992 toolchain and 2,809 dependency read-only dynamic
images. The launcher confirms the isolated tracked checkout stays clean. The
active ASCENT checkout and shared dependencies were not modified. Saved cache
directories are owned snapshots, not new shared dependency locations.

MCP qualification is unchanged: three first logs below 5 seconds, three complete
cold builds below 50 seconds and 965/965 complete tests below 112 seconds. Those
MCP observations cannot overturn the independent ASCENT cold regression.
