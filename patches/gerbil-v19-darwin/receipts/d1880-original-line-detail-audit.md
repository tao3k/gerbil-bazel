# D1880: retained best-line detail audit and second cold replay

No new compiler candidate or product edit was introduced. D1510 remains the
selected original binary; GNU GCC, twelve physical workers, macro tracking
disabled, original GSC/runtime and embedded-native disabled remain selected.

| Original-line observation | First compile seconds | Complete build seconds |
| --- | ---: | ---: |
| Historical B1 | 4.789153 | 51.737180 |
| Historical B2 | 4.933479 | 53.496910 |
| D1875, retained B1 path | 5.177979 | 64.258463 |
| D1878, retained B2 path | 5.053081 | 56.255963 |

Both replays isolate generated outputs, execute official clean with zero
remaining native images, then execute a complete official build. D1878 build
exit is zero; maximum real-output gap is 5.053081 seconds. Its controller
exits one because the unchanged 55-second complete-build gate fails.
The 64-to-56-second difference is not attributed to a code/configuration fix
or admitted as a causal speedup. The historical reference remains unchanged.

## Object-reuse checks

D1877/D1879 compare each preserved historical generated directory with the
corresponding new replay output. Each contains 187 package static objects,
186 corresponding runtime bundles and 373 generated C files. For every
corresponding bundle, runtime C equals static C, the object is not older than
static C, and the object is not newer than the bundle. No normalized C changes
remain after masking only explicit module timestamp literals. Project paths
are identical within each comparison.

These checks show no artifact evidence of late executable-stage object
replacement or a different generated C workload. They do not count actual GCC
invocations. Log prefix counts must not be treated as execution counts:
parallel output contains incomplete/interleaved records. B2 historical and
replay logs each have 740 extractable complete job records; one compile-file
name differs (`resolve-imports~1` versus `repl-session~1`). Neither this
record discrepancy nor equal total counts explains wall-time variation.

## Real-output stage boundaries

D1878 timestamps existing real output, without sampling, counter hooks,
synthetic progress or a product change:

| Observed job-entry boundary | Seconds from build start |
| --- | ---: |
| First module compile line | 5.053081 |
| First compile-file job line | 6.072328 |
| Prepare-executable-link job line | 51.606115 |
| First compile-executable-object job line | 51.606115 |
| Link-executable job line | 55.341088 |
| Complete process exit | 56.255963 |

These are output-observation boundaries, not exclusive CPU measurements or
per-job completion timings. Most elapsed build time precedes executable-link
preparation. No missing effective optimization switch was established in this
audit. Startup is near the requested 5.2-second target in two original-line
replays; complete historical performance is not yet restored.

All historical projects were backed up before clean, original generated
directories restored afterward, and tracked diffs remain empty. New generated
outputs and reports are preserved separately. No installation or admission
of a rejected candidate occurred.

Private evidence: `.data/d1877-retained-reuse-audit/`,
`.data/d1878-second-best-line-replay/`,
`.data/d1878-historical-project-backup/`, and
`.data/d1879-second-retained-reuse-audit/`.
