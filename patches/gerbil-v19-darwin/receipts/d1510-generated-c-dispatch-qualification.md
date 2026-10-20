# Isolated GSC Producer Dispatch

## Direction Review

Previous controls invoked the cache API directly. This revision adds an opt-in
native GSC command-line adapter for the actual runtime producer argument shape,
without replacing the original Scheme-to-C generation on a miss with a second
generation. On a miss the journal observes the one compiler invocation; on a hit
the proof is validated in a fresh GSC process. Expected benefit is repeat producer
reuse, not yet an admitted cold-build speedup or eliminated static-link rewrite.

## Scope And Preparation

`prepare_static_reuse_driver.py --generated-c` prepares only an isolated profile.
It retains `gsc-original`, the existing object driver and native hash backend, and
copies the Scheme journal/cache/adapter beside the dispatcher. Preparation is
Python filesystem glue; execution and failure controls invoke native GSC directly.
Use the frozen v3 helper explicitly with `--native-sha`; the first preparation
attempt with the current default helper rejected an anchor drift before testing.

Dispatch is off unless `GAMBIT_DARWIN_GENERATED_C_REUSE=1` and uname is Darwin.
It intercepts only `-c`, one `-o`, matching `-module-ref` and `-linker-name`, optional
`-target C`, and one regular nonsymlink Scheme input. Input/output stems must match.
Unsupported flags, absent aliases and other commands exec the original GSC with
the original argument vector. There is no package-name condition.

The shell writes a private NUL-delimited data request. Native Scheme reads it
without evaluating data, removes the two adapter transport environment variables
before context binding, and supplies the exact producer alias options. Loaded
adapter and compiler bytes enter the proof's tool identity. Runtime-generated
paths are not interpolated into Scheme source. Temporary request/work directories
are removed on ordinary exit and catchable signals.

## Real Entrypoint Controls

Passing receipt: `.data/d1510-generated-c-dispatch-contract-v3` against isolated
`.data/d1510-generated-c-adapter-v4/bin`.

- First real `gsc -c` emits MISS and matches original generated C byte for byte.
- A second independent GSC process emits HIT.
- Alias change emits MISS and matches its corresponding original CLI control.
- Source change emits MISS and matches its corresponding original CLI control.
- Invalid Scheme exits nonzero while retaining both previous logical C and proof.
- A no-alias generation invokes original GSC without cache markers/proof.
- Lock, request and work directories are absent after completion.

Receipt v1 covered the initial cross-process path. v2 failed the cleanup gate:
GSC's uncaught top-level compiler error left a lock despite preserving outputs.
The adapter now catches exceptions outside the cache dynamic-wind scope, renders
the exception and exits 70 after unwinding. v3 verifies the formerly failing
case; no lock deletion heuristic or timeout relaxation was added.

## Identity

- Dispatcher: `5a65f369ca8285e584090738db09eefaa33be7a1009bdcbfc845eba43c60c7c1`
- Native adapter: `3f50f05ccfb588c3fa93a0fa5e378c4cd7d17d9da0861529ead3aefbdda2fc3e`
- First log: `32343ebeeaf34df4bcd31a598892cddab241bc00dafd7a9e12029269715f9cc0`
- Repeat log: `9d0cbee2b538e050b848c920828be342ce8a40a6fc7257f13a3b90c6876bedf8`
- Failure log: `1d909283584798f8c86383b9bfb74585aac721533efcbfffcb65f5345925aa29`

## Remaining Qualification

This entrypoint is not installed globally or promoted to a default product patch.
It has not run either consumer's complete workload. SIGKILL/crash lock recovery,
reader/default-diagnostic admission, loaded compiler image identity and object
source-path semantics remain open. Proof mismatch currently regenerates C, not
the default compiler's entire output/error presentation contract.

The static linker must still consume the admitted existing producer C instead
of rewriting Scheme; dispatch alone does not establish that integration. The
MCP first/cold/full-test gates and isolated ASCENT cold nonregression remain
required. Independent ASCENT scheduling changes are excluded from this compiler
evidence, and its active checkout/shared dependencies remain untouched.
