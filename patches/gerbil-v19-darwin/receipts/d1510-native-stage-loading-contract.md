# D1510 Native Stage Loading Contract

Original-runtime architecture qualification only. No optimization candidate,
new cold build, full-test wave or speedup is admitted. Historical cold results
47.771713 / 47.824226 / 47.927094 seconds and whole-task 5 / 50 / 112-second
gates remain unchanged. Stable full-test performance qualification is open.

The official `git.cons.io/mighty-gerbils/gerbil.git` v0.19-staging head was
queried read-only on 2026-10-08 and remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`. No checkout or CI recipe was updated.

## Source Boundary

Retained Gambit `_eval.scm:5569` returns the result of `##os-load-object-file`
without registering or running its Scheme modules. The normal binary load
path at `:5465-5474` subsequently registers descriptors and calls
`##load-modules`. Gerbil `runtime/loader.ss:62` uses this normal `load` path,
not code-only preparation.

Native `setup.c:2068-2092` dynamically maps the object, fixes up modules and
marks its linker descriptor as already set up. Collection at `:1925-1958`
also invokes `setup_mod`; this is not a side-effect-free filesystem mapping.
`gambit.h.in:9391-9404` separates primitive registration (`setup_mod`) from
C/global initialization (`init_mod`). Compiler `_t-c-1.scm:2208-2232` emits
`c-initialize` code in the latter stage, not primitive registration.

`_kernel.scm:5274-5289` advances per-module stages: stage one calls the native
initializer, stage two calls the Scheme thunk. The state transition precedes
each initializer call. Error replay, stage state and dependency collection
must therefore be preserved by any future integration, not replaced by an
untracked direct thunk invocation.

Importantly, `setup.c:1512-1513` changes an unbound supplied global from UNB1
to UNB2 during mapping. Deferring initialization does not preserve every
global-cell value or make early mapping observationally pure. Mapping an
existing phase object also prevents a later second OS-level mapping; normal
Gerbil loading cannot simply be left unaware of the prepared descriptor.

## Actual Native Contracts

The existing `run_import_binding_contract.py` now has `--native-stages`, using
the same Git-owned process controller, shared lease, private package homes,
hardware concurrency and strict ordered-case/exit checks as its binding suite.
There is no new independent timing runner or package-specific branch.

A small Gambit source contains one observable C initializer and one observable
Scheme initializer. The original selected GSC and literal-substitution driver
compile it with GNU GCC 16 through the existing Bazel SDK environment. Each
fresh consumer has its own effect marker file and module registry.

All eleven ordered cases pass in twelve concurrent original native processes:
**132/132**. They check returned descriptors, delayed C/Scheme effects,
the supplied-but-uninitialized global transition, descriptor/thunk survival
across GC, stage-zero behavior, C-only stage one, still-uninitialized Scheme
value, C-before-Scheme ordering, final live value, idempotent stage-two identity
and effects, and refusal of duplicate native mapping. These are separate
checks, not just a final success marker.

Final receipt: `.data/d1510-native-stages-contract-v4/report.json`.
V3 also passes 132 cases; V4 additionally validates both original/private source
hashes after execution. Runtime, fixture, compiled module and source remain
unchanged. The module SHA256 is
`72ab404b92b0b5ee0973a058cdd755448907ed8e97a68b2eec5437d7434efbff`;
source SHA256 is
`f9fbef91e87d88abea1d20a2a6a1a27a2198b4d350faf9d0b3f4a4ffd86007fe`.
No runtime archive, installed library or MCP source was changed.

The modified shared runner's original binding mode also passes all **408/408**
cases, with unchanged binary and fixture:
`.data/d1510-binding-contract-shared-runner-v3/report.json`.
Neither result is whole-toolchain or full-library correctness qualification.

## Negative Fixture Evidence

V1 compiles but all twelve consumers fail after two cases: assigning the
unbound sentinel to a top-level observer variable makes reading that variable
raise an unbound error. V2 boxes it but the identity-preservation assertion
fails. That second failure reflects the real UNB1-to-UNB2 setup transition,
not Scheme initialization. The final case explicitly checks both unboundness
and this identity change; it does not silently discard the observation.

Both failed reports/logs and exact `failed-fixture.scm` copies remain in
`.data/d1510-native-stages-contract-v1/` and `-v2/`. Their fixture hashes are
`5f95ef3544aab2c69f1419f8ed3461b5d473ac6b626ac6eb70ede7cf1ad9be0a` and
`b41bf0ae91032dd84bfae8ae5b5bec5bcdbc139081c7351a6ae970921942704a`.

## Four-Question Decision

| Question | Decision |
| --- | --- |
| Correct direction? | Code preparation and live instantiation can be staged, but mapping has registration/global effects. A future fresh-interface construction artifact must preserve those boundaries and all live callbacks. |
| Already explored? | Prior real-phase serialization restores executable code and was rejected against native phase cost. This test uses original native object descriptors and staged initializers instead; it is not another serialized phase replacement. |
| Worth implementing? | Protocol boundary established; ANALYZE ONLY for a construction-program deployment. NO to blindly preloading existing phase objects or bypassing Gerbil's loading/error/order state. |
| Expected benefit? | Not measured. Existing native phase initialization is already cheap. Potential savings must come from avoided generic interface preparation, with native artifact construction/loading charged to cold build and startup. |

Missing before a production candidate: reached removable interface-work budget,
fresh-context/record/mark/property equivalence, live handler and dependency
mutations, cycle/reload/error and concurrent-loading semantics, and real stdlib
plus MCP clean/build/full-test acceptance. This contract does not claim a
Darwin/Linux cause, a platform speedup or a license to skip phase execution.

## Failed Initializer And Public Loader Replay

The same compiled fixture now optionally raises `native-stage-failure` after
recording its Scheme effect, before assigning the supplied Scheme global.
The shared runner selects `normal`, `scheme-error` or `gerbil-error`; it does
not add another controller or change the original binding suite's default.

| Mode | Processes | Ordered cases per process | Passed |
| --- | ---: | ---: | ---: |
| Bottom-level failed Scheme initializer | 12 | 13 | 156/156 |
| Gerbil public loader error cache | 12 | 6 | 72/72 |
| Normal native-stage regression | 12 | 11 | 132/132 |

Private receipts are respectively
`.data/d1510-native-stage-error-contract-v1/report.json`,
`.data/d1510-native-stage-gerbil-error-v1/report.json` and
`.data/d1510-native-stage-normal-error-regression-v1/report.json`.
The updated source SHA256 is
`e73733f6d797d70e390ccd43f9b4685f9a4f9bcdd1756834db9938b53fb51c5e`;
the normal/public-loader runs' compiled module SHA256 is
`d64b2746d45e35a818f94d0583558309b368ace13be2f2ef0689794a24edee06`.
These are new fixture versions, not replacements for the historical hashes.
All three reports pass binary, fixture, module and source identity checks.
The updated runner's default binding mode separately passes **408/408** in
`.data/d1510-binding-contract-error-modes-regression-v1/report.json`, with
unchanged binary and fixture. The optional modes do not replace that suite.

On failure, Gambit has already advanced the descriptor to stage two. Its
next bottom-level initialization returns without repeating the thunk **or
replaying the exception**. The prior C/Scheme effects remain; the supplied
global is still uninitialized. Gerbil's public `load-module`, by contrast,
stores `(error exception)` in its registry and rethrows that same exception
on the next call, without repeating those effects. A staged construction
integration cannot substitute the bottom-level stage flag for this error
registry. Neither behavior permits restarting a partially executed thunk.

This extension closes a correctness question needed by any future deployment,
not a removable execution budget. Expected performance benefit remains
unmeasured; no first-log, cold-build or complete-test result is produced and
no production optimization is admitted.
