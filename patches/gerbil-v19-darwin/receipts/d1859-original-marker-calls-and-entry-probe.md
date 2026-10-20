# D1859: original native callers verified; joint probe not yet executed

D1857 disassembles the exact retained D1510 binary after verifying its SHA256
against construction evidence. Forty static direct marker call/branch sites
are recorded: eleven to the general marker, twenty-five to constprop.4 and
four to constprop.1. Callers are mark_frame, mark_captured_continuation, scan,
scan_movable_objs_to_scan and garbage_collect_pstate. Static sites are not
execution frequencies. The previous D1611-specific address is not reused as
an original D1510 address.

The original D1510 constprop.4 entry at 0x1003fe844 also establishes a 144-byte
frame and loads allocation pointer/limit before its first tag test. This
confirms the entry-overhead mechanism in the actual selected binary, rather
than transferring only the other composition's machine code. The absence of
a count loop is consistent with single-cell specialization; source/caller
correspondence still must not be replaced with inferred dynamic class counts.

D1858 implements a private diagnostic generator, not a fast-path optimizer.
Its hook occurs exactly once per original marker entry, before tail marking.
It counts single-cell immediate values and each of eight header kinds, retains
only integer counters, and uses a distinct opt-in output file. It excludes
non-Darwin, non-GNU/Clang, debug, multiple-VM/thread/processor and non-eight-byte
configurations. The disabled macro is a no-op.

Three Python tests pass: hook removal reconstructs the actual original mem.c
byte-for-byte; guard/fallback text remains present; joint-count validation
rejects wrong totals, malformed vectors and invalid counter types. These are
generator/parser tests, not native macro-activation or GC contract tests.
The generated diagnostic has not been compiled, linked, or run on MCP.
No hit count, CPU gain, startup improvement or performance qualification is
claimed. Original toolchain sources and artifacts remain untouched.

Next evidence is the joint distribution from an isolated original-carrier
observer, retaining literal product-output gates. Only after that can a
no-copy entry gate be evaluated against actual executed work. It remains a
bounded collector mechanism, not proof of the several-fold Darwin goal.
Historical mean 52.617045 seconds and the mandatory 55-second complete-build
ceiling remain unchanged; performance restoration remains incomplete.

Private files: `.data/d1857-marker-callsite-audit.py`,
`.data/d1857-marker-callsite-audit/`, `.data/d1858-marker-entry-probe.py` and
`.data/d1858-test-marker-entry-probe.py`. All owned processes are terminal.
No product source edit, commit or push occurs.
