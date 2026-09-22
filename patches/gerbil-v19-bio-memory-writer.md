# Gerbil v0.19 buffered memory writer

Base revision: `d801e7a1c7f77df421f638e62aaebe370f193c97`.

`gerbil-v19-bio-memory-writer.patch` is the complete patch applied by
`publish-v19.yml` to this pinned revision. It refreshes `bio.buf` and its
length after a memory-output drain in the UTF-8, fixed-width integer, and
varuint retry loops. It adds boundary regressions in `bio-test.ss` and a
100 KB `json->string` round-trip in `json-test.ss`.

[Upstream PR #1493](https://git.cons.io/mighty-gerbils/gerbil/pulls/1493)
already fixes the UTF-8 retry loop and adds UTF-8 growth tests, but remains
unmerged. `gerbil-v19-bio-integer-growth-upstream.patch` contains only the
remaining fixed-width integer and varuint repairs plus their tests, so it
can be proposed upstream without duplicating PR #1493. It is not applied by
the release workflow because the complete pinned-revision patch includes it.
The remaining integer-path defect is tracked in
[upstream GitHub issue #1435](https://github.com/mighty-gerbils/gerbil/issues/1435).

On the pinned revision, both patches pass `git apply --cached --check` against
the clean index. With the complete patch compiled using `gxc -O`, the Gerbil
buffered-output and JSON suites pass, a 100 KB JSON string round-trips under a
128 MB Gambit heap limit, and the 94,439-byte ASP owner-facts packet (67 facts)
encodes and decodes under the same limit. This is a source and focused-runtime
qualification, not a full release-build receipt.
