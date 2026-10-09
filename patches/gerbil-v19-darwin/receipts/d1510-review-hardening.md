# Static Snapshot Review Hardening

## Decision

PR 49 review thread `PRRT_kwDOTcq_2s6qowK5` identifies a correctness boundary,
not a new performance route: multiline source paths must use the original
compiler command instead of snapshot preprocessing. Existing fallback for quote
and backslash paths remains. GNU GCC's diagnostics, failure status and existing
output are preserved. No package identity or MCP-specific behavior is added.

`static-snapshot-path-fallback.patch` applies after the locked six patches.
Their bytes, order, measured driver and retained performance lock remain intact;
the follow-up implementation is not misrepresented as the historical benchmark.
The source CI patchset identity includes this additional patch automatically.

`static-reuse-helper-install.patch` fixes a separate demonstrated installation
failure. CI run `37880098407` built both helpers at 03:39:55 UTC, then completed
the Gerbil installation and failed its installed-helper check at 05:03:28 UTC.
Gerbil `src/build.sh` copies a fixed list of Gambit tools, omitting these helpers.
The Darwin-only follow-up copies them into the normal build prefix, so the
unchanged installer carries them into the final installation. Missing helpers
remain a hard failure. Linux's tool-copy path is unchanged.

Expected benefit: correctness for exceptional source paths and a usable
source-built Darwin installation. No additional speedup is claimed. The ordinary
reuse path has only one added shell-builtin carriage-return construction and a
pathname case check; no extra compiler probe, digest or preprocessing pass.

## Verification

Private outputs: `.data/d1510-review-hardening-v1` in the delivery worktree.

- `check_static_snapshot_path_fallback.sh`: genuine GNU GCC compilation through
  the helper, four LF/CR/CRLF/directory-path cases; object and diagnostics match
  uncached GCC, then invalid C preserves failure status, diagnostics and old
  output. Final marker `STATIC-SNAPSHOT-PATH-FALLBACK-OK 8`, exit zero.
- `check_static_object_reuse.sh`: real selected GSC and GNU compiler path;
  final marker `STATIC-OBJECT-REUSE-OK 8`, exit zero. Includes ordinary hits,
  options/header/tamper invalidation, concurrent calls and failed compilation.
- Frozen safety/performance and source CI unit contracts: 31 passing tests.
  Installer tests exercise Darwin copy, missing-helper failure and Linux no-op.
- Both follow-up patches applied to owned real-source fixtures. Shell syntax
  and tracked diff whitespace checks passed.
- Frozen lock SHA-256 remains
  `a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2`.

The multiline path test intentionally exercises the helper/compiler boundary:
the selected GSC's filename discovery already rejects newline filenames before
that boundary. It does not claim that this patch fixes GSC's pathname parsing.
The full source-built CI and post-polish whole-package timings remain separate
verification gates; these local native checks do not claim either is complete.
