# D1876: original best-line replay, startup recovered but full gate failed

The 9.628876-second startup of D1870 belongs to the rejected D1868 marker
candidate, not to a successful rollback. No marker candidate is admitted.

The retained D1513 B reference remains:

| Run | First compile seconds | Complete build seconds |
| --- | ---: | ---: |
| Historical B1 | 4.789153 | 51.737180 |
| Historical B2 | 4.933479 | 53.496910 |
| D1875 original-line replay | 5.177979 | 64.258463 |

D1875 uses the original D1510 binary (SHA256
`446fe0b905fd6e1186087a8dd27b52ecd3749e2f22b22cee7226e75c2d4282c3`),
original D1391 runtime home, GNU GCC and 12 physical-core workers. Identity
verification checked the selected binary, GSC, runtime archive, carrier and
42 native inputs. No new Gambit patch or consumer-source change was applied.

Unlike fresh-clone runs, this replay used the retained historical B1 project
path. The complete original project was copied before official clean. D1874
stopped before build because official clean retained 550 native images. Those
outputs were preserved, not counted as a cold build. D1875 isolated the
generated directory and reran official clean; zero native images remained.
The actual build exited zero, emitted `... compile util/compat` at 5.177979
seconds and produced the executable. The maximum real-output gap was
6.251434 seconds, within the unchanged ten-second gate. The complete-build
55-second gate failed and the controller exited one.

This is one startup observation at the requested approximately 5.2-second
level, not proof of stable restoration, an improvement ratio, or complete
performance qualification. The 51.737/53.497-second historical reference is
not replaced by 64.258 seconds. No cause for the remaining discrepancy is
asserted. Full-build restoration remains open.

After the replay, its generated output was moved into the new private
evidence directory, and the original historical generated directory was
restored from the pre-clean backup. The historical project's tracked diff
is empty. Original reports were not overwritten.

Private evidence: `.data/d1874-retained-best-line-replay/`,
`.data/d1874-historical-project-backup/`,
`.data/d1875-cold-retained-line-replay/` and
`.data/d1875-post-clean-historical-generated/`.
