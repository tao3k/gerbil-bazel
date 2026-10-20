# D1760: whole-producer snapshots reach native execution, not performance acceptance

The original D1513 B / D1510 line remains unchanged and selected. Historical
complete-build timings and the 55-second gate are not replaced. No production
performance patch or full staging toolchain qualification is admitted.

D1754 regenerates actual syntax-e states from the original stx/util/mop C
inputs, using the retained carrier's real module prefixes and label offsets.
Of 198 completed states, 122 pass the selective normal-return ownership
lowering; 76 are refused as not completed normal returns. Each accepted path
removes one three-word temporary pair from normal execution, preserving its
original poll snapshots by cold materialization. Static paths are not dynamic
frequencies, bytes saved in MCP, or a measured major-cost reduction.

The accepted paths form four existing-budget trees (32/32/32/26 paths,
63/63/63/51 nodes). No 32-path, 256-node, guard, work or visit budget is relaxed.
D1755 attaches them at the original syntax-e entry. Each tree reserves the
original complete 16-word bound and restores the heap checkpoint on a guard
miss before falling back to the original procedure. Returned objects and
original poll handler/resume exports are retained. All fourteen original
guarded trace sites are unchanged. This is supplemental code, not a claim
that the entire carrier's trace shape is identical to the original.

D1756 compiles this carrier with real GNU GCC/O1, links the original module
objects/runtime archive and passes framework imports. Original native inputs
remain byte-identical. Candidate SHA256:
`b47e28d2d3660f6b8df12cede69aec0ca325f7ec904155cfe818e9a15a76a979`.

D1757 passes twelve concurrent original/candidate runs of 42 exact cases:
504 CASE-OK results, including 252 from the candidate. Cases cover ordinary
and dotted data, mark streams, shared inputs, vectors/boxes, post-return GC,
fold rebinding with GC and restoration. Exact final status and exit zero are
required. This does not prove every native tree hits, forced poll exits,
all partially allocated rollback states, exception/continuation recovery or
whole-suite semantic equivalence.

D1758 performs actual unchanged MCP clean/build with twelve GNU workers:
clean succeeds in 5.573308 seconds and leaves zero native images. Build has
no first compile within the original ten-second output gate and is terminated.
The controller exits one; no complete build or performance pass is claimed.
No failed original baseline is rerun or used to fabricate a speedup ratio.

D1759 passes twelve native starts and twelve framework imports. Its unchanged
std/make/std/test parallel fixture then fails the original five-second genuine
output gate. No final suite success, full concurrent fixture pass or speedup
is inferred from the preliminary starts/imports.

Normal-return source/native feasibility now has stronger evidence, but the
candidate fails actual startup acceptance. Four sequential trees can replay
common guards after misses; dynamic coverage and cost are unmeasured. Do not
promote this three-word elimination as a major win or stack it onto the best
line. All owned sessions are terminal. The requested objective remains open.

Evidence: `.data/d1754-whole-producer-tree-preflight/`,
`.data/d1755-whole-producer-carrier/`, `.data/d1756-whole-producer-native/`,
`.data/d1757-whole-producer-contract/`, `.data/d1758-whole-producer-real-mcp/`,
`.data/d1759-whole-producer-concurrent/`.
