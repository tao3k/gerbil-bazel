# D873: strict dual-consumer requalification and POO control

Date: 2026-09-22. This round changes no patch, toolchain, consumer source, or
global installation. The four-patch original Gerbil SHA-256 is
`ef64f8bfd89fe3920717b4f7c54e00626ff53e16c7546e3920a4d4df8fea6411`;
the D866 0007+0008 candidate is
`f064c994fe1caaac0f3e70b7aaacf320fbae3d255df44fd625717572b34835ad`.
Real POO is `16edc0164cc4c00d81dd4d5e0fed0b24414d4a40`; real MCP is
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. The existing Python
consumer A/B runner's 23 unit tests passed before use. Its root Justfile
commands used GCC 16, 12 build workers, excluded first access, and the
unchanged 10-second measured-package silence gate. Source repositories were
clean before and after all runs.

| Consumer and order | Four-patch original | D866 | Measured result |
| --- | ---: | ---: | --- |
| POO native-warm, original then D866 | 13.688 s | 14.315 s | D866 +4.59%; strict relative and 13.13 s absolute gates failed |
| POO native-warm, D866 then original | 14.495 s | 14.212 s | D866 -1.95%; runner status is positional, with original as its candidate |
| MCP cold, original then D866 | 87.234 s | 73.258 s | D866 -16.02%; strict gate passed |
| MCP cold, D866 then original | 86.935 s | 66.024 s | D866 -24.05%; runner status is positional, with original as its candidate |

All eight real package builds succeeded, and their measured maximum output
gaps were below 10 seconds. MCP's first executable-object to final-link
interval repeated the expected mechanism: 17.212 s versus 0.046 s in the
forward pair, and 15.657 s versus 0.044 s in the reverse pair. The material
MCP benefit therefore survives both orders without changing the GCC
optimization flags or the output watchdog. The reverse runner's `failed`
status is **not** a D866 failure: the original toolchain occupied its
positional candidate slot and was slower.

POO cannot be admitted from these samples. Both POO orders completed, but the
first one failed the unchanged zero-regression and 13.13-second anti-drift
gates. A same-binary, same-source, same-state original-versus-original control
then took **12.788 s and 21.393 s** (+67.30%); both completed and remained
below the 10-second silence limit. The first compile moved from 2.199 s to
4.359 s and the final native-job announcement from 8.594 s to 15.882 s.
Thus a host/measurement-state drift much larger than the D866 POO difference
is present even with no code change. This control does not prove D866 has zero
POO overhead; it proves that the current single-pair timing gate cannot
attribute POO's observed difference to D866 on this host. Do not replace that
failure with an average, loosen the gate, or call the candidate release-ready.

Machine receipts, retaining every run and exact toolchain identity, are
`/private/tmp/d873-poo-ab-forward.json`, `d873-poo-ab-reverse.json`,
`d873-poo-self-control.json`, `d873-mcp-ab-forward.json`, and
`d873-mcp-ab-reverse.json`. Decision: preserve 0007/0008 as investigation
candidates; do not activate them in the release workflow. The next admission
attempt must first qualify a stable POO control and retain both orders with
the same strict correctness, absolute-time, and silence gates. No new native
performance hypothesis is justified by this measurement round.
