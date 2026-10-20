# D1510 Gambit Evaluation And Darwin Platform Boundary

## Unchanged Anchor

Historical complete cold builds: 47.771713, 47.824226, 47.927094 seconds.
Corresponding first compile logs: 4.850866, 4.573628, 4.592897 seconds.
The full 39-file/965-case test baseline completes in 105.750982 seconds with
all assertions passing. The later strict 112-second wave is DENY/incomplete;
do not call the test duration stably qualified. Current gates remain first log
5 seconds, cold build 50 seconds, full MCP test 112 seconds.

No improved cold build or complete test result follows from this investigation.
The frozen binary remains unchanged. Standard-library diagnostic timings are
not comparable substitutes for any of these end-to-end results.

## Isolated Source-Mirrored Diagnosis

The diagnostic uses the supported ##eval-top-set! entry. It mirrors the
retained Gambit ##eval-top body: ##sourcify/##compile-top, followed by demand
module loading and code execution. The latter split follows
##setup-requirements-and-run and macro-code-run exactly: ##load-modules on the
compiled result's cdr, then its car code node's procedure with node and false
runtime environment. This is an isolated diagnostic replacement, not delegation
to the untouched evaluator body and not a production semantic proof.

A second observation binds load-module to a wrapper that always invokes the
original procedure. Compiled direct calls can bypass global rebinding; real
hits are required, and this is not claimed to cover every native load. All
four library probes complete, retain cached context identity and exit zero.
Original and split runs have identical exported name/phase inventories and
completed builtin/loaded module inventories. This does not prove equal export
values, load order, exceptions, continuations or full library behavior.

For begin forms in split-v2, summed observed own seconds are:

| Standard library | Gambit preparation | Demand-module handling | Code execution |
| --- | ---: | ---: | ---: |
| make | 0.004179 | 0.000072 | 0.129284 |
| test | 0.003445 | 0.000049 | 0.054290 |
| encoding/json | 0.011773 | 0.000219 | 0.853369 |
| list/list | 0.023353 | 0.000048 | 0.214627 |

In the later split-v3, reached load-module calls are 80/49/143/44 respectively;
their summed observed own times are 0.186465/0.014326/0.460823/0.009881 seconds.
Do not subtract timings across these different runs. load-module includes
search, native loading and module initialization; it is not pure dyld time.
Observer overhead and large wall variation preclude speedup claims.

Private reports: .data/d1510-stdlib-gambit-eval-split-v1/report.json through v3,
and .data/d1510-stdlib-gambit-eval-split-control-v1/report.json. Both v2 and v3
inventory comparisons against the original control pass for all four libraries.
The updated parsing/import-tree checks pass 18 Python tests. All child processes
are terminal and reaped. No production patch, full-build rerun or push occurs.

## Platform Architecture, Not Generic Optimization Relabeling

The user's direction is Darwin platform mitigation in the shared Gambit/Gerbil
toolchain. Generic object elimination or fewer Scheme callbacks activated
only on Darwin does not by itself explain or remedy a platform penalty.
The new observations select execution/native preparation as a boundary; they
do not prove that the whole remaining import cost comes from the operating
system or establish a Linux causal decomposition.

[Apple's WWDC 2022 linking presentation](https://developer.apple.com/videos/play/wwdc2022/110362/)
distinguishes launch page-in fixups from later dlopen work and identifies image
count as a loading cost. This is primary platform guidance, not a peer-reviewed
paper or new discovery here: REFLECTION already cites it. Current published
[dyld API source](https://github.com/apple-oss-distributions/dyld/blob/main/dyld/DyldAPIs.cpp)
still disables ordinary page-in linking before main and performs load
notifications/initializers for dlopen images. Its internal-install exception
and moving main branch are not claims about the installed host's exact dyld.
The source is corroboration of a mechanism, not measured workload attribution.

The existing image-reduction/native-provider results are the architectural
starting point. Do not repeat failed packing, RTLD visibility, relative-label,
superpage or symbol-evaluator candidates. A further architecture candidate
must identify the remaining executed Darwin loading/registration boundary,
preserve demand initialization/error/identity behavior, and work from the
toolchain's standard modules rather than benchmark-selected package modules.
No bypass of dyld safety checks, private page-in APIs or code-signing policy
is proposed.

D1361 already rejects TLS lookup for its retained SINGLE_THREADED_VMS branch,
libc setjmp substitution, JIT heap/cache-flush assumptions and a clock fallback.
These findings must not be generalized to a differently configured release;
any reconsideration requires proof that the selected artifact takes a different
branch, not another generic TLS paper. No new platform-specific research paper
establishing a several-fold win for this workload was found in this search.

The inspected expander/init.ss and runtime/init.ss files match the canonical
retained D935 files; the separately named D1362 mirror is not represented as
latest staging or promoted to a build input.
