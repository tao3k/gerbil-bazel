# Gerbil v0.19 buffered memory writer

Base revision: `d801e7a1c7f77df421f638e62aaebe370f193c97`.

`gerbil-v19-bio-memory-writer.patch` is the complete historical patch for
this pinned revision. It refreshes `bio.buf` and its
length after a memory-output drain in the UTF-8, fixed-width integer, and
varuint retry loops. It adds boundary regressions in `bio-test.ss` and a
100 KB `json->string` round-trip in `json-test.ss`.

[Upstream PR #1493](https://git.cons.io/mighty-gerbils/gerbil/pulls/1493)
already fixes the UTF-8 retry loop and adds UTF-8 growth tests, but remains
unmerged. The release workflow now rebases the pinned PR head onto the pinned
staging revision with Git, then applies
`gerbil-v19-bio-integer-growth-upstream.patch` for only the remaining
fixed-width integer and varuint repairs plus their tests. This avoids
duplicating the PR's UTF-8 change while keeping this complete patch available
for exact `d801e7a1` replay.
The remaining integer-path defect is tracked in
[upstream GitHub issue #1435](https://github.com/mighty-gerbils/gerbil/issues/1435).

A strict local negative control confirms that this residual patch is not
redundant. On otherwise identical staging-plus-PR-1493 builds, a 100 KB
`json->string` reproducer completed with `JSON-OK` in approximately one second
when the integer/varuint patch was present. Reversing only that patch caused
the same command to exceed a ten-second hard timeout (exit 124). PR #1493
therefore fixes the UTF-8 retry, but does not close the large-JSON path by
itself.

On the pinned revision, both patches pass `git apply --cached --check` against
the clean index. With the complete patch compiled using `gxc -O`, the Gerbil
buffered-output and JSON suites pass, a 100 KB JSON string round-trips under a
128 MB Gambit heap limit, and the 94,439-byte ASP owner-facts packet (67 facts)
encodes and decodes under the same limit. This is a source and focused-runtime
qualification, not a full release-build receipt.
