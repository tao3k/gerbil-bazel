# D1791: native emitter registration and actual macro source eligibility

The original D1513 B / D1510 remains selected and unchanged. The original
<=55-second full-build ceiling remains the admission gate. No new MCP timing,
startup speedup, Linux execution comparison or complete-toolchain qualification
is asserted in this receipt.

## Compiler integration

D1786 prepares isolated Gambit `_t-c-1.scm` and `_t-c-2.scm` changes. The C
emitter now registers all eight parameter helper dependencies through its
ordinary `targ-use-glo` mechanism while scanning eligible global calls, before
sorting/dumping the module global resources. It emits late-bound aliases using
resolved module indices, the guarded helper and cleanup of those aliases.
Module-local state resets at heap-begin. Caller frame/read/write resources are
registered instead of assuming a particular procedure already declares them.

The experiment is opt-in via `c#targ-darwin-parameter-entry?`, default false.
Helper activation still requires Darwin and genuine GNU/non-Clang, DYNAMIC,
single-host/label-value execution and the existing VM/ABI/poll restrictions.
This is not automatic performance-admitted activation or a frozen toolchain
patch. It changes no Gerbil, std or consumer source.

Only zero-argument NOTSAFE global calls are eligible. The standalone conversion
prototype is likewise tightened; its sixth unit test explicitly refuses a
SAFE-only module. Do not infer SAFE custom-getter qualification from the prior
NOTSAFE fixture. The ordinary original jump remains the miss fallback.

D1787 rebuilds the actual two backend modules, dependent generated linker
metadata, native compiler archive and GSC under GNU GCC with twelve hardware
workers in isolation. The native smoke prints the default false switch and
exact PARAMETER-GSC-OK. All recorded original compiler/source/object/bootstrap/
RTS inputs remain hash-identical.

New native GSC SHA256:
`d5a4bb7f8ac24ee1eb81f4ab68221a4cfd6ccab8c8b46bfd1318ef6a764d1764`.

## Actual generation and native execution

D1788 retains a failed controller invocation: placing -c after -e enters
evaluation mode, warns and produces no active C file. D1789 uses the real
`compile-file-to-target` API after setting the experimental switch.

Its fixture contains no artificial list of helper kernel dependencies. The
new emitter registers all eight dependencies itself and emits fifteen eligible
call sites. With the switch disabled, generated C is byte-identical to the
original retained GSC output (same module basename and same source).

Original and default-off generated C SHA256:
`111fc757e4aa13699e56bdfc5ee380503565ac564fe392b5ffe336a593d114df`.
Active C SHA256:
`8eef9608ec8ec99557a644939d39ddc643c941835595fbf00c2a625f22e3d260`.

Original, active and separate diagnostic modules compile with GNU GCC and
actually load/register/initialize on the unchanged selected Gerbil binary.
Each returns ten exact CASE-OK records, final DYNAMIC-PARAMETER-OK 10 and exit
zero. Only the separate diagnostic module has a hit marker; it proves actual
helper entry. The active artifact is uninstrumented. No timing is compared.
This adds compiler-emitted dependency/native execution evidence to the prior
D1784 twelve-way concurrent fixture; it is not a new concurrent framework or
MCP build qualification.

## Actual macro modules: eligibility, not execution coverage

D1790 runs the new native emitter on three unchanged generated Scheme modules
whose dynamic hosts occur in the retained first-window sample:

| Actual macro module | Emitted eligible calls |
| --- | ---: |
| gerbil/core/contract~6 | 2 |
| gerbil/core/sugar~1 | 0 |
| gerbil/core/mop~1 | 0 |

The two contract calls read its current-type-env parameter. These are emitted
source sites, not hit counts or CPU shares. The small fixture's fifteen sites
must not be extrapolated to macro-library-wide coverage. Source hashes are
unchanged and all three generation processes return zero. The absence of
eligible calls in two sampled macro modules narrows the expected scope of
this extension; it does not prove that the contract calls are cold or hot.
Do not claim major startup acceleration or blindly enable the feature over
every dynamic library from this source-only result.

Remaining gates include real contract/module execution coverage and binding/
poll edge cases, an unchanged MCP complete cold build with literal first-log
timing, genuine concurrent std/make/std/test, GNU/Darwin activation integration
and the original full-build ceiling. The goal remains active and incomplete.

Private evidence: `.data/d1786-parameter-emitter-source/`,
`.data/d1787-parameter-gsc-native/`, `.data/d1788-native-parameter-emitter-contract/`,
`.data/d1789-native-parameter-emitter-contract/`, `.data/d1790-native-macro-emission/`.
No live compiler or test process remains.
