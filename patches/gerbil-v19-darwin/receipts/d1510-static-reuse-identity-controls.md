# Static Reuse Identity Controls

The exact frozen v2 driver/helper were copied into an owned isolated directory.
The original frozen candidate and all external consumer worktrees were untouched.

Native command: tests/check_static_reuse_identity.sh.
Output: .data/d1510-static-reuse-identity-v1.
Final marker: STATIC-OBJECT-IDENTITY-OK 3. Exit status: zero.

1. Changing a C function's returned value invalidated the proof, produced a
   different object, and matched an original non-reuse GNU GCC invocation.
2. Changing the helper bytes invalidated the proof without changing the source
   or native object semantics. The next identical invocation hit.
3. Changing the driver bytes invalidated the proof without changing the source
   or native object semantics. The next identical invocation hit.

This complements the earlier eight native option/header/tamper/failure/
concurrency controls. It does not establish live compiler replacement safety,
arbitrary wrapper/specs support, or consumer performance attribution. The
candidate remains experimental and default-off.

## Second Consumer Isolation

The real ASCENT checkout was reverified at
21e3638687d42ecfc36acebb28991987435ebc60 and cloned into
.data/d1510-static-reuse-ascent-v1/project at exactly that commit.
Its locked dependency prefix and corresponding installed toolchain were
APFS-cloned into the same isolated workspace, not linked for shared writes.
The copied gxi resolves to the copied gerbil. The only copied-toolchain change
is the opt-in object branch plus the exact tested v2 helper.

tests/run_isolated_ascent_static_reuse.sh invokes the existing
just test-native t/qualification/ascent-positive-plan-test.ss directly.
The existing Scheme qualification code owns compilation, tests and deadlines;
no Python process supervises the native test command. Output and process time
are recorded separately. No new performance or correctness claim is made here.

The first control is terminal, exit 70 after owned-process SIGTERM at 146.34
seconds. It produced no NATIVE compilation marker. A one-second live sample
contained 762 of 798 main-thread samples under dyld mapSegments -> fcntl
and 787 under Gambit's dynamic_load -> dlopen. Loaded paths were confirmed
inside the isolated copied toolchain/dependency prefix, not the active checkout.
This is an invalid comparison setup, not a candidate reuse performance result.
The copied-profile attempt must not be repeated as a speedup benchmark without
first resolving its admission boundary. Original source identity remains clean.
Raw diagnostic: .data/d1510-static-reuse-ascent-cold-control-v1.

## Remaining Admission

The compiler/assembler replacement and mid-flight replacement controls remain
unverified. Proof-file publication type checks, complete fail-closed digest
handling, compiler diagnostic preservation and unsupported auxiliary options
also remain required before enabling the helper by default. The complete
isolated ASCENT correctness/performance scenarios are still outstanding.
