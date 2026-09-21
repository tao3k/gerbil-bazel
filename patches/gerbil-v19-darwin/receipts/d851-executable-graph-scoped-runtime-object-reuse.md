# D851: executable-graph-scoped Darwin runtime object reuse

Date: 2026-09-22. This is an isolated staging-V19 experiment, **not an admitted
release patch**. It changed neither consumer source nor the global Gerbil
installation.

The measured implementation is frozen as
`../0007-gerbil-darwin-executable-runtime-object-reuse.patch`. This is a
source-control investigation artifact, not part of `publish-v19.yml` or a
Homebrew installation. Patch `0007` applies after the existing `0002` and
`0003` Gerbil patches on the staging revision specified below; its three changed
files replay byte-identically to the tested isolated source. Gerbil-MCP
delimiter balance, checkout-local syntax expansion, and `git diff --check`
passed after replay.

## Source and build qualification

The isolated source `/private/tmp/gerbil-d846-full.qHfGgo/source` starts from
staging V19 `d801e7a1c7f77df421f638e62aaebe370f193c97`, the four existing
Darwin/Gambit patches, and the D848/D849 compiler work. D850 reused one
Darwin PIC object for a package module's dynamic bundle and executable closure
through configured `gambuild-C dyn` and a canonical linker alias. D851 passes
Gerbil's existing `static:` compiler context only when the normalized
`std/make` build graph contains `exe:` or `static-exe:`. A pure module graph
keeps the ordinary dynamic compiler path. Gerbil's own `lib/static` remains
on the official static-object path. The graph decision is automatic; neither
consumer needs an opt-in environment variable or source modification.

Gerbil-MCP's balance checker passed on `driver.ss` (62 forms) and `std/make.ss`
(67 forms) before and immediately after the edits. Checkout-local `gxc -S`
for both files and `git diff --check` passed. The isolated toolchain completed
`make stage1`, `make stdlib`, `make libgerbil`, `make tools`, and the existing
General AOT `gxpkg`/`gxtags` build. All source builds used the POO Flow root
`just --evaluate gerbil_darwin_env` fragment, `GERBIL_BUILD_CORES=12`, and
`GERBIL_BUILD_VERBOSE=3`; no bespoke OpenSSL or SDK flags were added.

The required `libgerbil` stage is important: after backing up old generated
stdlib objects, `stdlib` alone regenerated `.scm` and dynamic modules but not
the static `.o` closure. The first MCP link consequently failed for missing
objects. After `make libgerbil`, the isolated static closure was 347 `.o`
files / 30,482,496 bytes, versus 348 / 113,568,160 bytes in the prior
overbroad PIC experiment. The final MCP executable was 35,840,232 bytes,
versus 35,586,792 bytes with the original toolchain, not the prior oversized
57.7 MB executable. The incomplete-toolchain failure is **not** a speed result.

Toolchain binary SHA-256:

- Original four-patch AOT: `ef64f8bfd89fe3920717b4f7c54e00626ff53e16c7546e3920a4d4df8fea6411`
- D851 isolated candidate: `e47797d92839f3298654a9e13e44683ad139758f9aa8fba8a09ed3b8f923129a`

## Real consumer results

The existing real-consumer runner cloned clean, revision-stable sources:
gerbil-poo `16edc0164cc4c00d81dd4d5e0fed0b24414d4a40` in native-warm
state and gerbil-mcp `9a5c35e275e5d6847ff421151bb224f2eae177c1` in
cold state. Builds used real GCC 16, 12 Gerbil build cores, and a **10-second
package-build silence gate**. First-access qualification was excluded from
timing. The A/B order was reversed to check order effects.

| Consumer and order | Original | D851 | Result |
| --- | ---: | ---: | --- |
| POO original then D851, pair 1 | 13.074 s | 13.099 s | Both built; D851 +0.19%; strict zero-regression admission failed |
| POO original then D851, pair 2 | 12.076 s | 12.258 s | Both built; D851 +1.51%; strict admission failed |
| POO D851 then original | 13.215 s | 14.308 s | Both built; first-run/order variation, still no POO gain |
| MCP D851 then original, strict | 72.130 s | 60.690 s | Both built; D851 faster by 15.9% versus original |
| MCP original then D851, strict | 74.727 s | 59.555 s | Both built; D851 faster by 20.3%; runner admission passed |

The final MCP strict pair had maximum output gaps of 6.172 s (original) and
5.792 s (D851). Its first-executable-object-to-link interval fell from
14.113 s to 0.053 s. The D851 executable exited 0 under a bounded `--help`
smoke invocation; it printed the server-start message, so this is only a
process smoke check, not MCP protocol acceptance. The POO clone had zero
static `.o` objects: its pure module graph did not enter the PIC reuse path.

One earlier D851 MCP strict run was **interrupted by the 10-second silence
gate** 10.08 s after a deprecation warning, before a first compile event;
its interrupted 16.07 s is not a build time or speedup. A separate diagnostic
run with a 30-second silence allowance built D851 in 65.004 s and original in
80.417 s; D851's warning-to-`... build in current directory` interval was
0.66 s and its following pre-first-compile gap was 6.59 s. That diagnostic
does not erase the failed strict run. The gap varies enough to remain an
unresolved graph/import observability and latency issue.

Machine receipts and logs are under `/private/tmp/d851-*`, especially
`d851-mcp-ab.json` (strict silence failure), `d851-mcp-diagnostic.json`,
`d851-mcp-reverse-strict.json`, `d851-mcp-forward-strict-repeat.json`,
`d851-poo-ab.json`, `d851-poo-ab-repeat.json`, and `d851-poo-reverse.json`.
The reverse receipts label the D851 toolchain `baseline` and original
toolchain `candidate`; the table uses actual toolchain identities.

## Decision

Do **not** add D850/D851 to the release patch series or install it globally
yet. The MCP improvement is material and survives reversed order, but POO has
no demonstrated zero-regression result and one MCP cold attempt failed the
hard 10-second silence gate. Next isolate the intermittent pre-graph/import
gap and the remaining POO difference with phase timestamps, retain the
automatic executable-graph boundary, and re-run both real consumers. If the
code is eventually proposed upstream, keep the optimization Darwin-only and
review the build-graph scope for mixed library/executable packages.
