# D874: candidate output-dependency contract

Patch `0007` is still an investigation candidate, not part of the four-patch
release. This pass changes only its compiler output-dependency executor and
adds `tests/compiler-output-dependency-contract.ss`.

## Reproduction and correction

The previously built D866 binary, with `GERBIL_HOME` set to its isolated build
root, ran the new test and failed in 0.46 seconds: an unregistered output was
silently treated as ready and its dependent ran. Source inspection also found
that an output producer raising `#f` published the same value as success, so
its dependents could run despite failure. The existing executor test already
establishes that `#f` is a valid raised object.

Patch `0007` now validates every dependency under the executor lock before
registering callbacks. It tracks output failure with an explicit Boolean,
separate from the raised object; the unused stored error was removed. The
test covers early and late subscribers, a two-output barrier, duplicate
producer rejection, unknown dependency rejection, and `#f` failure
propagation without executing the dependent.

## Local gates

- The revised `0007` passed `git apply --check` and applied cleanly after
  `0002` and `0003` on staging `d801e7a1c7f77df421f638e62aaebe370f193c97`.
  `0008` then applied cleanly in the same replay worktree.
- The edited compiler base compiled to a separate overlay with isolated D866
  `gxc -d`; the installed/global toolchain was not changed.
- Because the existing AOT `gxi` embeds its old compiler module, the overlay
  test explicitly loaded `gerbil/compiler/base~0.o1` before the test file.
  Both the new contract and the existing `compiler-executor-contract.ss`
  passed with `GERBIL_BUILD_CORES=2` and `12`.
- A direct build from the fresh replay worktree did not run: that checkout has
  no generated `src/gerbil/runtime/version.ss`. This is a setup distinction,
  not a compiler-test failure; the patch itself replayed cleanly.

These are source and atomic functional gates only. No full AOT rebuild or
adjacent real-consumer POO/MCP A/B was run for this revised patch. D873's
qualified timing applies to the prior candidate binary, not this revision;
the strict 10-second silence, POO anti-drift, and dual-consumer performance
admission remain open.
