# D877: pinned PR 1493 staging composition

Date: 2026-09-22

This receipt qualifies the Git composition used by the v0.19 release workflow.
It does not claim that the HTTP issue is closed.

## Exact source identity

- staging: `66542a3ca585af9b99a177927f4b4e940a1112ec`
- Ensemble PR head: `76968e6d3987a42d613f183317f98f4c024fb180`
- deterministic rebased head: `1ae1e5a3ffd4e895303b82399acc312b619de914`
- rebased tree: `00f004730ff67d106fea044aa3065c7f7d0e4b61`

Two independent repositories produced the same rebased head and tree when
`--committer-date-is-author-date` was combined with the workflow-owned
`gerbil-bazel` committer identity. The PR contains no changes below
`src/std/net/http`. The remaining
`gerbil-v19-bio-integer-growth-upstream.patch` applies cleanly to the rebased
tree; the older complete memory-writer patch is retained only for exact
`d801e7a1` replay.

## Local Darwin qualification

The rebased tree plus the remaining integer patch and the existing audited
Darwin release patches completed the full local build through `tools` with
Homebrew GCC 16 and `GERBIL_BUILD_CORES=12`. The following focused tests then
reported five `MODULE-OK` results, one `HARNESS-OK`, no `ERROR`, and final
`OK`:

- `std/io/bio/bio-test.ss`
- `std/encoding/json/json-test.ss`
- `std/ensemble/ucan/did-test.ss`
- `std/ensemble/ucan/context-test.ss`
- `std/ensemble/network/auth-test.ss`

The build also exposed a material Darwin cost: compiling
`ensemble/network/connection~1.c` spent more than two minutes in the GCC
frontend. This is performance evidence for later Darwin work, not a reason to
weaken the source qualification.

## Strict buffered-writer negative control

PR #1493 does not subsume the remaining integer/varuint repair. An APFS clone
of the same qualified build was made and only
`gerbil-v19-bio-integer-growth-upstream.patch` was reversed. With otherwise
identical binaries and load paths, the 100 KB `json->string` reproducer gave
the following hard result:

- PR #1493 plus the integer/varuint patch: `JSON-OK`, exit 0, approximately
  one second wall time;
- PR #1493 only: no completion before the ten-second timeout, exit 124.

The JSON writer reaches the fixed-width integer/varuint retry path, so this is
a downstream behavioral A/B rather than a source-shape inference. The small
patch remains required until its equivalent is present upstream.

## ASP Scheme downstream qualification

The ASP Scheme source is already expressed against the v0.19 HTTP API
(`:std/net/http/server`) and pins
`github.com/tao3k/gerbil-poo@1b384119f25552c7ed2868c961d10b0bc1ead442`.
After removing stale v0.18 package artifacts and rebuilding that dependency
with this receipt's isolated v0.19 toolchain, the repository's
`t/projection-batch-test.ss` completed with `MODULE-OK`, `HARNESS-OK`, and
`OK`.

The full HTTP test did reach the real provider executable, but failed before
any JSON request was accepted. On Darwin, `tcp-listen` passed a native
`sockaddr_in` whose bytes began `#u8(0 2 ...)`: `sa_family` was set to
`AF_INET`, while Darwin's leading `sin_len` remained zero. `bind(2)` therefore
returned `EINVAL`. Separately, the repository's release build selects
`std/make` static executable linkage, which adds `-Bstatic` and `-static`; real
GCC 16 then reports that Darwin has no `crt0.o`. These are downstream Darwin
HTTP/build blockers, not evidence against the buffered-writer A/B above.

## Explicit limitation

The local HTTP server suite does not close ASP HTTP acceptance because Darwin
listener setup fails before the request/response path. The test harness can
still print trailing markers after case errors, so the workflow intentionally
does not treat that run as green. The buffered-writer repair is qualified by
its strict JSON A/B; Darwin `sockaddr` initialization and release executable
linkage require separate fixes and receipts.
