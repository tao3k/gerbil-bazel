# Native GSC Consumer Admission Gap

## Actual Isolated Consumer

Receipt: `.data/d1510-native-generated-c-ascent-positive-v1`.
Frozen consumer revision: `21e3638687d42ecfc36acebb28991987435ebc60`.
The ordinary repository `just test-native` qualifier was launched directly by
Bash, not supervised by Python. Source and assertions were not edited.

- End-to-end wall time: **196.73 seconds** (user 303.45, system 76.36).
- Exit status: 0; 30 `CASE-OK` lines; final `HARNESS-OK` and `OK`.
- Independent directed-graph reachability corpus: 512/512.
- The final consumer-reported 4 seconds covers execution only, not preparation.
- Compilation layers contain 85, 87 and 1 modules; this is not a whole-suite run.
- No producer index records or generated-C producer/link-hit markers were found.
- After execution, all 1,992 toolchain and 2,809 dependency read-only dynamic
  image references still pass their original digest checks.

This is isolated correctness evidence, **not performance admission**. No matched
complete-cold control exists for this new workspace, and historical cache/workload
measurements cannot substitute for one. Do not rerun the unchanged native
candidate hoping for admission.

Raw evidence digests:

| File | SHA256 |
| --- | --- |
| output.log | `f479dcafca8b563c39d73fce935b0b0de17119e145c6c80902f876c01ab78a4a` |
| time.txt | `9c996194b723f0b306b264458083ee865b21028898ba94368b130af0205520b9` |
| toolchain.sha256 | `1c16c620f18fec62c227825af3e9c85bab9476a83a03e683e939bace46eb602a` |

## Why The Producer Hook Does Not Cover This Lane

The consumer's library compiler calls ordinary `std/make make`. In the frozen
toolchain, `std/make#gxc-compile__0` defaults
`compile-static-runtime-objects?` to false. The compiler therefore takes ordinary
dynamic `compile-file`, not the explicit `-c -o` native-capture branch. Its C
generation occurs in `_gsclib.scm` through `c#cf`, then the intermediate target
is deleted unless `keep-temp` is requested. The prototype only patches the CLI's
`do-compile-file-to-target` explicit-output call. Consequently its producer
registration is not on this actual library path. This is a coverage gap, not a
reason to weaken proof validation or change package options.

There is also a semantic blocker to copying ordinary dynamic C into static
linking. `.data/d1510-ascent-actual-dynamic-static-alias-v1` compiles the actual
generated binary-relation input with the original matching ASCENT compiler.
With the same module reference and all other options held constant, only the
linker name changes. The C files differ:

- Input SHA256: `7ea3b8fd93f13a9fcd2fd1412d6d925442ed2c9d14d5d891e48f8c89cbc5288c`.
- Dynamic C: `8cc9a8ef893372302e7c92eefc359eb2ec141ae0b9cf9647e5b2665d38197ebc`.
- Static C: `634f013b674c9ebc63b6a6375fa11afc7514f54df0e92c3c57f403fbdfd5cc29`.
- `___LINKER_ID` is the dynamic `.o1` name versus the static module alias.

This control is deliberately stronger for isolating the linker-name difference
than the ordinary dynamic command, which also infers its module reference. It
does not certify every inferred option on that command. The observed mismatch
is enough to reject unconditional dynamic-to-static C adoption.

## Next-Change Review

1. Is the unchanged explicit-output hook the right route? No: it misses this
   consumer's ordinary producer and has no adoption evidence here.
2. Has it been explored? Yes: retain the explicit-output parity and invalidation
   contracts, but close unchanged full-consumer reruns.
3. Is a lower-level producer extension worthwhile? Only if it preserves dynamic
   loader identity while producing a proven static-compatible artifact. Copying
   C or broadening admitted options alone is incorrect.
4. Expected benefit? Unproven. The rebuilt v8 55-module component produced C in
   10.07 seconds versus 6.27 seconds, then linked in 0.96 versus 4.07 seconds:
   serial total **11.03 versus 10.34 seconds**, a regression. A new implementation
   must eliminate producer overhead as well as cover the real path before
   another whole-consumer performance attempt is justified.

The fastest frozen five-patch stack and its 4.5/42/97 MCP ceilings remain intact.
The new native GSC prototype remains default-off and outside that patch series.
