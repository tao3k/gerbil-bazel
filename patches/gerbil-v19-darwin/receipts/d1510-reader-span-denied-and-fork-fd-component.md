# Reader Span Denial And Fork FD Investigation

All candidates retain the original D1510 objects, GNU GCC16 environment,
0015 driver, 0018 loader driver, original program carrier, and frozen token
reader anchor. Work remains in isolated `.data/`; no consumer business,
std/make, std/test, package transport, or resource-limit changes are made.

## Closed String-Span Candidate

A private Darwin/GNU extension batches ordinary ASCII runs inside quoted
strings, stopping before escapes, Unicode, newline, or the closing character.
It keeps the original escape decoder and a 512-character chunk limit, and
revalidates the port buffer/cursor under its primitive lock after Scheme
allocation. Other platforms retain the original reader.

Actual reader controls: **53 passed**, including all 24 frozen token controls,
quoted identifiers, octal/hex escapes, Unicode, 511/512/513 and 16384 character
strings, EOF, line/column accounting, and GC. The stronger EOF control unwraps
Gerbil's `RuntimeException` before checking the underlying parsing exception.
The intermediate direct `read-error?` check failed on both reference and
candidate because the exception is wrapped; that failed diagnostic is retained.

Binary SHA256:
`e6ac0c28d144275aedbde055bd26127858a843b4405de003d5f1cd5cd95251ac`.

Real cold clean exits zero and leaves zero native images. First compile output
is **4.587851708 seconds**. Complete-build watchdog fires at **50.004316416
seconds**: **DENY**, SIGKILL, reaped, exit -9. No completed build time is claimed.
The campaign stops after one failed round and skips full tests. This implementation
is **NO / IGNORE for further extension**; it is not a new anchor.

Private evidence:

- `.data/d1510-reader-span-runtime-v1/`
- `.data/d1510-reader-span-native-v1/`
- `.data/d1510-reader-span-controls-v3/report.json`
- `.data/d1510-reader-span-progressive-v1/report.json`

The embedded data source's 1.85 MB size does not establish import parser cost:
its actual `.ssi` is only 554 bytes. No claim is made that every import parses
the large data source.

## Different Fork Mechanism

The prior same-PATH spawn extension remains DENY; its 6.58x component ratio does
not admit that implementation. The existing executable object audit also rules
out treating 189 logged freshness checks as 189 duplicate C compilations.
Neither hypothesis is rerun here.

The new fork candidate does **not** broaden spawn/PATH eligibility. It changes
only FD cleanup in an already-selected Darwin/GNU fork child, after interrupt
cleanup. The original `execvp`, environment, cwd, redirection and error-pipe
handling remain in place.

It binds libproc before fork but never uses the parent's FD snapshot. In the
child, it masks signals, queries its own descriptors into a fixed 256-entry
stack buffer, and closes only listed descriptors at or above the original
threshold. The original signal mask is restored; restoration failure is
reported through the existing child error path. No user-space allocation,
descriptor-limit change, PATH cache, or executable-search change is introduced.

Zero/error, non-integral, or full/truncated results retain the original full
scan. The strict less-than-buffer-size condition is required: Apple's public
[kernel FD listing implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c)
can truncate to the supplied capacity. The public
[libproc wrapper](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)
for `proc_pidinfo` directly calls `__proc_info`; this source inspection is not
a general POSIX async-safety guarantee or proof of the installed kernel revision.

## Component And Native Controls

12 physical-core workers run eight actual fork/FD controls each: **96 passed**,
wave **1.857014208 seconds**. Controls cover sparse descriptors, descriptor 4096,
dense/truncated lists, query error, malformed response, preservation below the
threshold, all actual descriptors above it closed, and the signal mask restored.

One recorded worker:

| Case | close attempts | FD cleanup seconds |
| --- | ---: | ---: |
| Original sparse | 1048570 | 0.155571000 |
| Candidate sparse | 2 | 0.000044000 |
| Original high FD | 1048570 | 0.435706000 |
| Candidate high FD | 3 | 0.000010000 |

Full-buffer and error cases still perform the original 1048570 attempts. These
are component observations, not a whole-fork, startup, cold-build, or suite ratio.

Actual Gambit process controls match frozen binary output and statuses for shell
execution with explicit environment, changed child PATH, no-shebang executable
text, and missing command. Both exit zero. One four-command observation takes
**0.569791500 seconds** frozen and **0.117580500 seconds** candidate; this is not
matched repeated suite evidence or admission. An earlier malformed control
expression failed parsing in both roles; the repaired v2 preserves all assertions.

Private evidence:

- `.data/d1510-fork-fd-controls-v2/report.json`
- `.data/d1510-fork-fd-runtime-v1/report.json`
- `.data/d1510-fork-fd-native-v1/report.json`
- `.data/d1510-fork-fd-native-controls-v2/report.json`

Candidate SHA256:
`ccaaf8ede8a42fdae594dd943c063a5505769d72f914c5c56e7a5022a2dca21a`.

The token reader object and its Gambit runtime linker object are byte-identical
to the frozen anchor. The new C `os_io` object is combined with that reader
using relocatable linking; the original RTS archive and program carrier remain
untouched. This candidate contains none of the rejected string-span code.

Real cold-build admission remains **first compile <= 5 seconds, complete <=
50 seconds**. Full tests require unchanged case inventory, exit status, final
OK, and existing real-output watchdogs. Component/native-control qualification
cannot replace either gate. No new performance patch is admitted in this note.

## Host Candidate Cold Gate: DENY

`.data/d1510-fork-fd-progressive-v1/report.json` records:

| Round | First actual compile | Complete cold build | Decision |
| --- | ---: | ---: | --- |
| 0 | 4.494367041 s | 47.229114791 s | ALLOW |
| 1 | No compile by 5.023185208 s | Interrupted | DENY |

Both cleans exit zero with zero native images remaining. Sources remain
unchanged. Round 1 is killed and reaped with terminal exit -9; round 2 and the
full test wave are skipped. The successful first round does not override the
failed first-log gate. This host candidate is not promoted to the anchor.

The construction changes only the CLI's linked runtime object. The retained
MCP build still uses the original HOME's `libgambit.a` for its final executable.
Consequently its compiled server subprocess path does not contain this new
FD cleanup. Component and CLI controls do not establish consumer deployment
or real MCP test acceleration.

Source inspection identifies an existing compiler contract, not an implemented
optimization: `GERBIL_BUILD_PREFIX` selects the executable link library directory
while runtime HOME remains separate. Any future private C-only archive test
must prove the selected member and consumer executable identity, retain source
and frozen input hashes, and keep the same hard gates. No consumer result is
claimed here.
