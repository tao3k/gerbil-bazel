# D1368-D1369: linked GOT cost admission

## Decision

Do not implement symbol visibility or GOT-elimination changes as the next
major-cost Darwin patch for the expander core/stx hosts. The original
executable already removes the hypothesized GOT dereferences. This is
machine-code evidence from the current original toolchain, not a new
workload benchmark or qualified speedup. The seven-to-eight-second
first-log objective remains unresolved.

## Identity and method

The diagnostic source is retained under
`.data/d1368-linked-entry-code-admission/`; the paired-instruction result
is under `.data/d1369-linked-got-pairs/`. The first D1368 run joins sampled
PCs. D1369 additionally checks every paired GOT page/page-offset relocation
inside the two host functions, including instructions not sampled.

Original objects are checked against the D1365 object SHA-256 values.
Original executable SHA-256/UUID are checked against the existing D1102
profile. Each retained sampled PC is mapped using actual native function
starts and checked against both original-object and final-linked
disassembly. No compilation flags, runtime or generated C are changed.

Executable SHA-256:
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.

## Ordinary entry loads are not GOT loads

The expander core entry uses object offsets 0x1998/0x19b0 to load `____lp`.
The stx entry uses 0xc48/0xc60 for the same role. Both pairs use ordinary
ARM64_RELOC_PAGE21/PAGEOFF12 records, not GOT_LOAD relocations. Both still
execute an adrp/ldr in the linked image: this reads Gambit's module-local
link-data pointer, not an extra Mach-O GOT pointer. The sampled-PC weights
at these instructions do not establish exclusive load latency or a
Darwin-specific cost.

## Actual linker relaxation

| Host | Paired GOT references in original host text | Final shape | Unpaired GOT page references |
| --- | ---: | --- | ---: |
| expander core | 2,155 | adrp/ldr -> adrp/add | 0 |
| expander stx | 227 | adrp/ldr -> adrp/add | 0 |

Every checked pair is relaxed in the final executable. A proposed
visibility change cannot remove a GOT pointer load that no longer exists
in these host functions. This does not prove that every other runtime or
dynamic image is GOT-free, nor that address generation is free.

The sampled-PC opcode census from D1365 is also checked against final code:
all retained core/stx sampled PCs keep the same opcode. Some sampled adrp
instructions had GOT relocation records in the object, but their paired
unsampled ldr instructions were replaced by add. Thus neither a relocation
record nor a sampled instruction name alone identifies the executed
indirection or its cost. The existing load/store census remains diagnostic,
not a memory-stall attribution or justification for a cache rewrite.

No full toolchain rebuild or clean/build/test baseline is repeated for this
rejected mechanism. No Gambit, std/make, std/test or consumer source is
edited; the next candidate still needs a Darwin platform mechanism with
relevant major-cost coverage before a production experiment.
