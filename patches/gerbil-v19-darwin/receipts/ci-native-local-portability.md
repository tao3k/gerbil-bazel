# Native CI Local Portability Verification

The failed macOS job in run `37906506489` reached the first static-object
assertion and exited 127 because `rg` was unavailable. Ubuntu passed. The
Darwin release in run `37908843142` succeeded at main commit
`7f7a1b9877ceb49134a2942dceea492811538741`.

Local verification reused that exact released GNU GCC 16, Multiple-VM artifact:

`gerbil-v0.19-1cfb032c7a1612637da6205f5f8a15683eba3ba0-darwin-aarch64-gcc16-arm64-aot-tools-single-host-unlimited-multiple-vms-patch618d76f9eb72`

The downloaded archive passed its published SHA-256 check. The test ran the
native contract step extracted from the workflow YAML, without `GERBIL_GCC`,
and with an `rg` executable that would exit 99 if called. No toolchain rebuild
or global installation was performed.

| Local check | Result |
| --- | --- |
| Source-toolchain regression tests | 15 passed |
| Frozen patch contracts | 100 passed, 1 skipped |
| Static-object reuse contracts | 8 passed |
| Multiline snapshot path fallback contracts | 8 passed |
| Combined native workflow step | 17.78 seconds |
| Multiple-VM globals, GC and concurrent workers | Passed, 2.75 seconds |

The workflow now passes the persisted `CC` value to the path fallback test.
`GERBIL_GCC` was exported only inside the source-build child process and is
not inherited by subsequent workflow steps. Marker-count rejection still
covers zero and duplicate HIT/MISS records.

Raw local evidence is under
`.data/released-toolchain-verification/local-ci.log` in the portability
worktree. These are post-build contract timings, not MCP cold-build or test
performance claims. They do not establish complete Bazel CI success.
