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

## Explicit limitation

The local HTTP server suite could not provide an Issue 2 A/B result because
the Darwin host rejected listener setup with `Invalid argument` at `__bind`.
The test harness can still print success markers after those errors, so the
workflow intentionally does not treat that run as green. The HTTP-specific
patch must remain pending until the original Issue 2 reproducer can be run
with and without it on a valid listener host.
