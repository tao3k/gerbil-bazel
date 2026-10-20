# D1853: retained library identity and source coverage boundaries

The original D1510 configuration remains the development input. D1513 B's
52.617045-second full-build reference and the 55-second ceiling are unchanged.
D1848's 77.506420-second replay is a failed restoration, not a new baseline.

## Retained Loaded Images

D1851 compares every image hash in D1547's real MCP pre-first-compile load
record against the current D1391 home: all 277 match. Its current inventory
contains 5,785 native-image/SCM/SSI/SSXI files, with none modified after the
D1513 report's filesystem modification time. These observations do not
support subsequent library overwrite as the discrepancy explanation.

D1547 used the original D1391 binary, not the D1510 binary, and occurred
after D1513. Its load set is not an exact historical D1513 closure manifest.
File modification times do not independently prove historical byte identity.
No exact full historical environment restoration or timing cause is claimed.
Current GNU GCC is 16.2.0, matching the version recorded in D1370. The current
gambuild-C hash matches the retained D1394 baseline hash; object reuse and
macro-tracking-zero settings remain selected. Version equality alone does
not establish an exact historical compiler executable hash.

## Type-Chain Source Audit

D1852 verifies the 42 original native input hashes and original D1508 carrier
hash, then uses the existing type-chain recognizer in readonly audit mode.
It recognizes 158 exact control-flow loop shapes across twenty input modules.
This audit uses expression stubs: it establishes shape counts only, not
production-lowering eligibility, runtime execution frequency or CPU benefit.
No carrier is transformed and no native build or workload is launched.

Existing D946 evidence remains decisive against assuming a broad type-predicate
replacement is a win: its 174 native primitive jump sites were about 2.1%
slower in the recorded bounded CPU comparison. D952 then observed zero deep
fallbacks among 115,153,945 checks, ruling out simply increasing that walk's
bound as a remedy. Those primitive jump sites are not identical to D1852's
inlined loop shapes, but the negative result cannot be discarded based on
source coverage counts. No broad loop replacement is admitted or built.

The requested startup/full-build/test improvement and historical performance
restoration remain unachieved. Further development must target proven actual
execution cost in the original line, not repeat unchanged builds, compiler
flag sweeps or coverage-only candidate enlargement.

Private evidence: `.data/d1850-audit-original-library-closure.py`,
`.data/d1851-original-library-closure-audit/`,
`.data/d1852-type-chain-shape-audit.py` and
`.data/d1852-type-chain-shape-audit/`. D1850's initial missing optional report
field assertion failure is retained; corrected output is in D1851.
All owned processes are terminal. No product source or toolchain is changed,
and no commit or push occurs.
