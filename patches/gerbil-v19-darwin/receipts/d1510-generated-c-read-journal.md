# Native Generated C Read Journal

## Review

- Direction: collect actual compiler source reads for a generated-C producer,
  including includes emitted by macro expansion rather than guessed text paths.
- Prior work: include/prelude changes can alter C without changing the primary
  Scheme file; failed generation can leave old C in place.
- Worth implementing: a producer cannot safely reuse C without dependency
  evidence and successful private generation.
- Expected benefit: enable admission of the measured repeated generation cost;
  journal overhead must not consume that benefit. No cache gain is claimed here.

## Implemented Component

gambit-generated-c-reads.scm wraps the actual GSC runtime source-read operation,
copies each resolved source before reading it, invokes the original reader, and
restores the original operation with dynamic-wind. The private manifest is
written only after compile-file-to-target returns success. It records primary
input, options, output, ordered source/snapshot pairs and a compiler macro-context
marker using Scheme's structured writer. It does not publish a cache proof.

A live probe first replaced c#read-source. It observed the main read but missed
internal include reads. This hook is rejected as incomplete. The lower
##read-all-as-a-begin-expr-from-path hook observes both the main input and
resolved transitive includes, including a macro-emitted include. No installed
compiler binary or source was changed; hooks live only in the private GSC process.

The source-read result is a three-field vector: script line, source expression,
port name. This is confirmed by lib/_eval.scm and a native probe. The recorder
requires that shape and scans the actual source expression, not the whole vector.
The compiler macro marker detects definitions/syntax definitions/namespace and
macro scopes, ignoring quoted data. This is a conservative exclusion signal,
not a proof of arbitrary compiler/macro purity.

## Actual Native Controls

check_generated_c_reads.sh, passing output .data/d1510-generated-c-reads-v4:

1. Direct include: exact main, middle and leaf read inventory and byte-equal
   before-read snapshots.
2. Macro-generated include: the same exact transitive inventory and snapshots.
3. Macro context: the direct source is false and macro-defining source is true;
   quoted macro definitions are not misclassified as executable definitions.
4. Malformed dependency: generation fails and no manifest is published, even
   when an older C file exists.

Final marker: GENERATED-C-READS-CONTRACT-OK 4. The earlier v3 marker test failed
because it inspected the source-read result vector instead of its expression;
that failing receipt is retained. It was never used to admit a cache hit.

## Real Consumer Source Parity And Cost

check_real_generated_c_reads.sh uses the same 55 paired ASCENT module sources,
copied into an independent directory. Original GSC -c generation is compared
with public compiler-API private generation plus the read journal. Every C file
and every primary snapshot matches byte-for-byte; all 55 manifests exist.
No ASCENT tests are supervised with Python or replaced by this component probe.

Current output: .data/d1510-real-generated-c-reads-v3:

| Path | Whole Time | User CPU | System CPU |
| --- | --- | --- | --- |
| Original generation | 3.69 s | 3.53 s | 0.12 s |
| Private generation + journal | 3.56 s | 3.42 s | 0.13 s |

Markers: REAL-GENERATED-C-READS-PARITY-OK modules=55 and independent structured
manifest verification REAL-GENERATED-C-MACRO-CONTEXT-OK 55. All 55 report no
observed source macro context. This one ordered pair does not demonstrate a
speedup; it shows no large observed journal penalty for the tested source set.
Earlier recorder-only samples are retained and do not supersede the corrected
marker contract.

## Remaining Admission Work

The read journal is not a complete dependency/purity contract. Arbitrary macros
can perform I/O or nondeterministic operations outside compiler source reads;
custom reader/context behavior can also affect compilation. Such cases must
fall back or be covered by stronger compiler contracts, not silently cached.
Compiler/runtime/helper image content, effective options, environment, source
and dependency snapshot stability, generated C content, output identity and
concurrent atomic publication remain requirements of the eventual producer.
The existing native object proof cannot substitute for these checks.

No generated-C cache is enabled. The earlier ASCENT package-cold regression
remains denied. MCP's accepted whole-task gates remain historical receipts
against the existing candidate, not results for a new producer implementation.
The active ASCENT checkout and shared dependencies were not modified.
