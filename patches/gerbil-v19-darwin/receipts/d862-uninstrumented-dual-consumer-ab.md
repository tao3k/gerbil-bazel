# D862: uninstrumented D851 dual-consumer A/B requalification

Date: 2026-09-22. This is an investigation record, not release admission.
Neither real consumer source nor the global Gerbil installation was changed.
The D851 source was rebuilt without temporary D855 instrumentation. The
resulting isolated toolchain completed stage1, stdlib, libgerbil, tools, and
the existing General AOT gxpkg/gxtags build. Reverse `git apply --check` for
patch 0007 and checkout-local syntax expansion passed before the rebuild.

Identities: staging V19 `d801e7a1c7f77df421f638e62aaebe370f193c97`;
four-patch original Gerbil SHA-256
`ef64f8bfd89fe3920717b4f7c54e00626ff53e16c7546e3920a4d4df8fea6411`;
isolated D851 Gerbil SHA-256
`d774b84692b839a3a11ac85290845ab5f9465ecd38a40e733e5eb4474940435d`.
The real gerbil-poo source was revision
`16edc0164cc4c00d81dd4d5e0fed0b24414d4a40`, and gerbil-mcp was
`9a5c35e275e5d6847ff421151bb224f2eae177c1`. All measurements used
real Homebrew GCC 16, `GERBIL_BUILD_CORES=12`, verbose package logs, clean
source clones, excluded first access, and the existing real-consumer runner.

| Consumer, state, order | Original | D851 | Result |
| --- | ---: | ---: | --- |
| POO native-warm, original then D851, pair 1 | 13.466 s | 14.176 s | +5.27%, failed zero-regression gate |
| POO native-warm, original then D851, pair 2 | 12.915 s | 13.063 s | +1.15%, failed zero-regression gate |
| POO native-warm, D851 then original | 14.399 s | 14.395 s | D851 faster by 0.004 s; the runner's positional admission reports failed |
| MCP cold, original then D851, diagnostic 30 s silence allowance | 84.557 s | 70.405 s | D851 faster by 16.74%; not strict admission |
| MCP cold, original then D851, strict 10 s silence | 91.218 s | 71.208 s | D851 faster by 21.94%; passed |
| MCP cold, D851 then original, strict 10 s silence | 89.126 s | 72.777 s | D851 faster by 18.35%; both builds passed, positional admission reports failed |

MCP's first executable object to link fell from 17.942 s to 0.063 s in the
diagnostic pair and from 17.629 s to 0.061 s in the strict reverse pair. The
strict reverse pair's longest output gaps were 6.813 s for D851 and 6.865 s
for original. These boundaries locate the large win in the executable-object
closure, not in generic module compilation or graph preparation.

There were two non-comparable MCP attempts: one candidate toolchain-import
preflight exceeded its 30 s total limit after the original build; another
candidate package build hit the hard 10 s silence gate after the
`std/net/request` deprecation warning and was interrupted at 16.608 s.
Neither interrupted time is a speed result. A subsequent standalone import
completed in about 6.5 s, and later strict full builds passed, so the
pre-build outlier remains intermittent and unresolved.

To calibrate POO timing noise, the original binary was measured against
itself under the same native-warm runner: 13.858 s then 13.950 s, a 0.67%
apparent regression that also failed the zero-regression gate. This does not
automatically excuse D851's two forward-order POO misses; it shows that a
single zero-margin pair is not a reliable causal estimator at this scale.
POO's pure module graph does not enable D851's executable-object reuse path.

Machine receipts are `/private/tmp/d862-poo-ab-1.json`,
`d862-poo-ab-2.json`, `d862-poo-ab-reverse.json`,
`d862-poo-self-ab.json`, `d862-mcp-ab-1.json`, `d862-mcp-ab-2.json`,
`d862-mcp-diagnostic-30s.json`, `d862-mcp-ab-3.json`, and
`d862-mcp-ab-reverse.json` (all under `/private/tmp`).

Decision: the MCP benefit is reproduced in both orders and is material,
but patch 0007 remains outside the release workflow. Resolve the intermittent
pre-build silence/qualification failures and establish a defensible POO
non-regression conclusion without relaxing the existing strict gate merely
to absorb a measured loss. Only then consider release admission.

## Rejected Darwin AOT dispatcher experiment

An isolated follow-up tried routing `gerbil build` to the already-built native
`gxpkg` executable on Darwin when it exists. This changed only `src/gerbil/main.ss`
in the isolated Gerbil source. Gerbil-MCP balance checks and checkout-local
syntax expansion passed before and after the edit. Official `stage1`, `stdlib`,
and `tools` builds completed. `gerbil pkg version` improved from 3.58 s to
1.10 s in a focused probe, and an invalid package command retained exit code 1
after correcting Gambit's encoded child status. Direct `gxpkg build` also
completed on a clean real MCP clone using the root Justfile's Darwin/OpenSSL
environment. These are startup and functional probes, not a package A/B win.

The strict MCP A/B with the dispatcher binary SHA-256
`766b5550497b513554de5627e1ab0629ebf4313ae5989c270ddc8a9cb86787d4`
failed: the original completed in 91.139 s, but the candidate was interrupted
by the 10 s silence gate after printing the `gerbil build` command and before
any package build log. The interrupted 14.519 s is **not** a speed result.
Machine receipt: `/private/tmp/d863-mcp-ab-1.json`. The dispatcher edit was
removed from the isolated source and its restored form rechecked for balance
and syntax; the last built binary remains an experimental, source-mismatched
artifact and must not be used for subsequent D851 A/B. No dispatcher patch was
added to the release or investigation series.

## D866: keep pure module graphs on their original output path

D866 adds `../0008-gerbil-darwin-pure-module-original-path.patch` after 0007.
The compiler now uses D851's early static-Scheme copy only when its existing
`current-compile-static` context is true; a pure module graph uses the same
post-compile `.scm` copy order as the four-patch original. The isolated source
passed Gerbil-MCP balance (62 forms), checkout-local `gxc -S`, and
`git diff --check`. Reverse `git apply --check` for 0008 passed against the
built source. The complete isolated toolchain passed stage1, stdlib,
libgerbil (347 static objects), tools, and the repository's General AOT
gxpkg/gxtags build. All three executable tools are arm64 Mach-O files.
The D866 `gerbil` SHA-256 is
`f064c994fe1caaac0f3e70b7aaacf320fbae3d255df44fd625717572b34835ad`.

The same real source revisions, GCC 16, 12 build cores, excluded first access,
and 10 s **measured package** silence gate were retained. The following are
complete builds, with actual identities shown regardless of the runner's
positional `baseline`/`candidate` labels:

| Consumer, state, order | Four-patch original | D866 | D866 difference |
| --- | ---: | ---: | ---: |
| POO native-warm, original then D866, pair 1 | 15.862 s | 15.887 s | +0.16% |
| POO native-warm, D866 then original, pair 2 | 15.768 s | 14.075 s | -10.74% |
| POO native-warm, original then D866, pair 3 | 13.999 s | 12.816 s | -8.46% |
| POO native-warm, D866 then original, pair 4 | 15.174 s | 14.057 s | -7.36% |
| MCP cold, D866 then original | 87.306 s | 83.865 s | -3.94% |
| MCP cold, original then D866 | 95.955 s | 71.905 s | -25.06% |

The order-balanced POO arithmetic means are 15.201 s original and 14.209 s
D866 (-6.53%). This is **non-regression evidence**, not an attributed POO
optimization: the pure module path is restored and the 1.8 s spread between
D866 runs shows material host/order variation. The one +0.16% pair failed the
runner's single-pair zero-regression admission; the earlier original-vs-itself
control also failed it with a +0.67% apparent regression. Do not claim every
single-pair gate green. All eight POO builds and their 10 s silence gates
passed.

The two complete MCP pairs average 91.631 s original versus 77.885 s D866,
a 15.00% reduction with both orders represented. In those same receipts,
the first executable object to link fell from 17.246/19.154 s to
0.060/0.058 s. Thus the large executable-closure improvement survived the
POO-path correction, while pre-`main` times still fluctuate. All four MCP
builds and their 10 s silence gates passed; the slowest candidate gap in
these pairs was 9.979 s, close to the boundary.

There are separate **non-comparable** qualification/measurement attempts.
One original-first MCP run completed its 94.649 s original build, then the
D866 import-only qualification exceeded its 30 s total limit; no candidate
build started (`/private/tmp/d866-mcp-ab-1.json`). To remove this order effect
without relaxing either timeout, the existing A/B runner now qualifies both
toolchains before either measured cold build. Its 23 unit tests pass, including
an explicit preflight-before-build ordering test. In the first real replay of
that runner change, both imports passed in 1.98/2.73 s, but the **original**
package build was interrupted by the unchanged 10 s silence gate after
`... build in current directory` and before the first compile log
(`/private/tmp/d866-mcp-preflight-order-ab.json`). Its 16.898 s is not a build
time, and D866 was not run in that attempt. The intermittent pre-compile gap
therefore affects the original as well as candidates; neither its root cause
nor reliable silence behavior is closed by D866.

Complete machine receipts: `/private/tmp/d866-poo-ab-1.json`,
`d866-poo-ab-reverse.json`, `d866-poo-ab-2.json`,
`d866-poo-ab-reverse-2.json`, `d866-mcp-ab-reverse.json`, and
`d866-mcp-ab-2.json` (all under `/private/tmp`).

Decision: D866 has a reproduced, order-balanced dual-consumer performance
conclusion and is a source-controlled **candidate** patch. Do not represent
the intermittent 10 s pre-compile silence or the single-pair POO zero-margin
failure as closed. Keep release activation and global installation separate
until the admission policy for noisy paired timing and the common pre-compile
silence issue are resolved explicitly.
