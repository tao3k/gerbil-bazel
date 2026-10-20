# Static Reuse Cost Boundary

## Admission Review

- Direction: isolate actual costs within the generic native static closure path.
- Prior work: the package-cold pair regressed despite 17 object hits; the
  identical-C regeneration boundary was demonstrated previously on one module.
- Worth investigating: separate missing-object fallback overhead from the
  Scheme-to-C generation that object hits cannot eliminate.
- Expected benefit: unknown for fallback; generation reuse has a measurable
  upper bound, not an assumed end-to-end win.

## Missing-Object Native ABBA

check_static_reuse_cold_cost.sh uses the isolated installed-profile GSC/driver
and a copied real 290,216-byte core__types.c. Each invocation removes its own
object/proof, compiles with the actual GNU compiler, checks exact reference
object bytes and verifies no proof/lock remains. Four batches contain eight
compilations each; only the opt-in setting changes. No synthetic compiler,
Python supervision, source timestamp manipulation or shared output is used.

| Batch | Mode | Whole Time | User CPU | System CPU |
| --- | --- | --- | --- | --- |
| 1 | original | 4.54 s | 4.15 s | 0.53 s |
| 2 | candidate | 4.65 s | 4.19 s | 0.58 s |
| 3 | candidate | 4.67 s | 4.19 s | 0.58 s |
| 4 | original | 4.57 s | 4.18 s | 0.54 s |

All 32 native objects are byte-identical; there are no HIT/MISS events.
Observed average added wall time is 0.105 seconds per batch, about 13 milliseconds
per invocation. Multiplying this observation by the 74 actual object calls is
under one second, not an explanation of the package-cold pair's 43.34-second
extra user CPU. This extrapolation is a bound estimate, not a matched workload
measurement. A cold fast-path patch is not admitted on this evidence alone.
Raw receipt: .data/d1510-static-reuse-cold-cost-v1.

## Real Package Scheme-To-C Generation ABBA

check_static_closure_generation_cost.sh copies the saved, owned ASCENT package
static directory's 55 paired Scheme/C modules into a fresh probe directory.
The other 119 Scheme files have no corresponding C and are explicitly listed
in unpaired-scheme-inputs.txt. This benchmark covers the 55 paired modules, not
every source module, dependencies, complete tests or the complete toolchain.

First it regenerates C using the exact private compiler, so copied C is never
assumed compatible. It then links Scheme / C / C / Scheme, using identical
flat-link options and output path. Every measured output must match the first
link file byte-for-byte; every generated module C must retain its exact digest.
Both private and original Scheme sources must remain unchanged.

| Batch | Input | Whole Time | User CPU | System CPU |
| --- | --- | --- | --- | --- |
| 1 | Scheme | 3.72 s | 3.59 s | 0.11 s |
| 2 | C | 0.11 s | 0.10 s | 0.00 s |
| 3 | C | 0.12 s | 0.10 s | 0.00 s |
| 4 | Scheme | 3.89 s | 3.76 s | 0.11 s |

Final marker: STATIC-CLOSURE-GENERATION-COST-OK modules=55. All exact-content
controls pass. Mean observed generation/link difference is 3.69 seconds for
this set. This is meaningful avoided work, not a claimed 33-fold complete
build speedup. A persistent C-producer admission would have its own cost and
must bind source, transitive Scheme includes/macros, compiler/options/context
and generated C identity, plus failures and concurrent publication. Existing
object proofs do not establish these conditions.

Gambit _back.scm get-link-info reads target link information from supplied
target-language files; link-modules constructs a linker output from that
information. Gerbil's Darwin prepare-link currently chooses runtime C only
when its current executor producer table marks it ready. That table is not a
persistent compiler-context proof. No file-existence or timestamp-only
substitution is admitted; neither is a whole-expander memoization retry.

Raw passing receipt: .data/d1510-static-closure-generation-cost-v3. Initial v1
and v2 preflight attempts stopped on the first unpaired Scheme file before any
compiler invocation. The final explicit paired-input inventory corrects the
probe scope; it does not omit any native test Cases from consumer qualification.

## Decision

Keep v4 default-off and preserve the package-cold rejection. Do not spend the
next candidate on the small missing-object lock cost. The next high-value
mechanism to qualify is content/context-admitted generated C reuse across
compiler processes, rather than only skipping the subsequent C object compile.
The generation experiment justifies investigation, not production enablement
or completion of the active goal.
