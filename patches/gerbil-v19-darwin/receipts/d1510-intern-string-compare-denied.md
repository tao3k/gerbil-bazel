# D1510 Fixed-Width Intern String Comparison: Denied

The retained reader-whitespace runtime remains unchanged. Historical heavy
cold builds are 47.771713 / 47.824226 / 47.927094 seconds, not measurements
of this candidate. Acceptance remains first real compile <=5 seconds,
complete cold build <=50 seconds and complete tests <=112 seconds.

## Distinct Source Mechanism

The original `___find_symkey_from_scheme_string` compares equal-length
Scheme strings character by character. Gambit uses the compile-time `___CS`
character width; `___STRINGREF` reads that fixed-width body. A private
Darwin/GNU/non-Clang, single-VM/single-threaded/one-processor candidate replaces
only that equality loop with `memcmp` over `n * ___CS` bytes. Linux and other
profiles retain the exact original loop.

This changes neither query hashing nor bucket/probe order, unlike the closed
hash-filter and SIMD probe candidates. It introduces no cached result,
intern-table representation change, UTF-8 decoder change or assumptions about
cached symbol hashes. Both strings' original equal-length condition remains.
The early mismatch position is not exposed by this function. Reading the full
existing string bodies is nevertheless not a demonstrated performance gain.

The adjacent GC-hash-table operation already selects multiply-high hashing,
not the alternative modulo macro. No capacity/division specialization is
constructed on that false premise.

## Native Construction And Correctness

Private GNU compilation reproduces original mem.o byte for byte:
`284504db424c05a2584759cf9f74abd1c576d79f95f6f3ad074514086710f553`.
Control linkage reproduces the retained runtime byte for byte:
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
Original sources, archive, native objects and providers remain unchanged.
Candidate runtime:
`414c075d9c3e4e233c945cbe095518e180264878a133b28ff420cf881a013e0f`.

Original and candidate each pass eight real named cases, final
`OK intern-string-semantics`, exit zero: empty, ASCII, Unicode, embedded NUL,
long same-prefix/tail-different names, mutable input, keyword identity, and
20,000 retained interned symbols across table growth and explicit GC.
These are focused controls, not complete language/collector conformance.
Their ordered process times are 1.296209 and 2.677852 seconds respectively;
these are not isolated body timings or evidence of acceleration. Eleven
source-transform and existing process/hash admission checks also pass.

## Actual Independent Standard-Library Gate

The unified stdlib workflow uses the candidate, unchanged common GSC and
12 discovered physical workers. Official clean exits zero in 7.314611 seconds.
The subsequent real build has no qualifying compile line by 5.007450 seconds
and is **DENY** against the unchanged five-second first-log gate. This number
is the deadline observation, not an observed first compilation latency.
The owned group is killed and reaped, terminal exit -9, no cleanup errors.

Complete build time and test time are unavailable. Tests and the downstream
heavy MCP run are skipped; there is no complete build/test qualification or
performance-admitted patch. A deadline failure alone does not prove that this
source change caused the observed latency. No retuning or repeated run is
used to turn the failure into a pass.

Decision: close this fixed-width memcmp deployment. Do not expand it into the
UTF-8 interner or use semantic success to promote it. Keep the frozen runtime.

Evidence:

- `.data/d1510-intern-string-runtime-v1/report.json`
- `.data/d1510-intern-string-native-v1/report.json`
- `.data/d1510-intern-string-controls-v1/report.json`
- `.data/d1510-intern-string-stdlib-v1/report.json`

All owned sessions are terminal. No production patch, AOT configuration,
consumer source, global installation, commit or push is changed in this run.
