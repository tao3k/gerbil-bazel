# D1510 Native Text and Stdlib Closure

The original D1510 remains selected. This readonly investigation extends the
core 42-input identity checks; it does not reconstruct historical timing or
select either the memo or grouped-emitter candidate.

## Object Machine Code

Follow the 186 normalized-equal MCP runtime C modules from
[the reuse audit](d1510-reuse-audit-grouped-native.md) into their actual static
Mach-O objects. Parse each text section with the existing native-object parser.

All 186 pairs have equal text lengths. Exactly 372 instruction words differ:
two per module. Each is the same AArch64 move-wide instruction except its
immediate, and both old/new immediates equal the corresponding generated module
timestamp's tagged-value chunk. The source timestamp pair was independently
checked by the C audit. No other text word differs. Each pair's bundle linkage
inventory also agrees: architecture/flags, paths, initialization hooks, external
definitions and undefined symbol ordinals as covered by the existing parser.

This is stronger than C size or source equality. It is not byte-identical whole
objects, symbolic relocation equivalence, identical SDK/linker internals, runtime
performance equality or proof of why a historical build was faster. No timestamp
is changed in any executable or source by the audit.

Evidence: `.data/d1510-mcp-text-audit-v2/report.json`.

## Full Runtime Home

The private best-line entry checks the Gerbil binary, GSC, RTS, carrier and 42
core C inputs, not every dynamically loaded standard-library module. The new
audit closes this current-state gap against the retained D1543 inventory.

For each of 1,100 module bases, enumerate consecutive `.o1`, `.o2`, and later
versions until the first gap, matching the actual loader rule. Compare the
selected path, selected native image SHA256 and generated Scheme SHA256 to
D1543. All 1,100 paths and both hash categories match; there are zero changed
selections, images or generated Scheme inputs. This includes actual higher
versions rather than incorrectly validating only old `.o1` files.

D1543 is later than D1513. These matches establish no subsequent drift from that
retained snapshot, not a newly discovered full D1513-era manifest or a fresh
D1394 rebuild. Current library timestamps or matching hashes are not a speedup
measurement. No library is replaced, rebuilt or repacked.

Evidence: `.data/d1510-stdlib-closure-audit/report.json`, reference
`.data/d1543-current-active-native-images/report.json` SHA256
`e0536a0900536f130040cf4f6892ec3d67d68da17577713ff123f13d13aa43c8`.

## Source Priority Correction

The existing wider D1613 hardware capture attributes 4.39% of captured active
cycles to context helper 11, versus 28.66% to mark_array and its clone. Therefore
41.23% repeated helper iterations from the completed-result census cannot be
presented as 41.23% removable CPU or first-log time. The capture is perturbed,
not a current uninstrumented time split. Already rejected marker, heap-slack,
return/entry and allocation candidates are not repeated based on these shares.

The next original-only cold run attaches this extended library closure rather
than consuming later candidates. Its timing must independently satisfy the
unchanged 55-second gate; original artifact identity alone is not performance
restoration. No PR or release is admitted by these checks.

## Original-Only Cold Build

With the original D1510 binary and original GSC, not either rejected candidate,
the new independent MCP clone completes official clean/build using twelve
workers. Clean exits zero and leaves zero native images. First compile is
5.352851 seconds; full build is 56.869967 seconds, exit zero. Source hashes
remain unchanged. The 55-second performance controller exits one.

This is the latest original-line observation, not the grouped GSC's 60.991300
seconds. It does not overwrite the D1878 fallback anchor of 56.255963 seconds,
the historical D1513 B1/B2 times or the 55-second upgrade gate. Its complete
time is 0.614004 seconds above D1878; no acceleration or historical restoration
is claimed. The original GSC, RTS, carrier and selected binary remain unchanged.

Private evidence: `.data/d1510-full-closure-original-cold/report.json`. A separate
post-build SDK audit rechecks the D1543 snapshot rather than assuming that
consumer compilation preserved all 1,100 library artifacts.
