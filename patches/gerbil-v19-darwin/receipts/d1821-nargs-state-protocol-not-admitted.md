# D1821: dense arity traffic, register protocol validated but not admitted

The original D1513 B / D1510 best line stays selected. The <=55-second full
build ceiling is unchanged. Canonical remote v0.19-staging was rechecked this
turn and remains `1cfb032c7a1612637da6205f5f8a15683eba3ba0`.

## Source and actual first-output census

Existing D1009 records GC at approximately 20.5% of the separate 187-module
preparation's user CPU. D999/D1004 and the heap-size experiments are already
negative. No collector/traversal/heap-policy experiment is repeated here.

Gambit's original SET_NARGS writes processor `na`; IF_NARGS_EQ reads it.
D1813's first generator check assumes one MD_ALL definition and fails before
compilation. The actual coalesced carrier has one host body and 23 state macro
definitions. D1814 corrects that diagnostic shape check, without changing the
original state writes or branch decisions: a host-local shadow remembers the
last set value, while actual decisions still read the processor field.

The original carrier/native objects/runtime are retained. Only diagnostic
hooks and the existing first-output I/O observer are added. D1814 compilation,
link and framework imports pass; original hashes remain unchanged. Diagnostic
binary SHA-256:
`8a1109c8fa2ab2115b3bb5c783f64e1b81da85810788f899bc716a29ec1cdf4e`.

D1815 official clean/build uses original library paths and a fresh unchanged
MCP fixture at `9a5c35e275e5d6847ff421151bb224f2eae177c1`. The actual builder
child PID 24414 is verified. At literal first compile, its side-channel snapshot
records 143,653,062 SET_NARGS operations, 103,595,710 IF_NARGS_EQ operations,
and zero observed shadow mismatches. First output is 5.797 seconds in this
instrumented run. It is deliberately stopped there, not a full build, speed
result, exclusive CPU attribution or proof of all foreign-call boundaries.

## Independent candidate

D1816/D1817 derive a fresh uninstrumented candidate from original D1508, not
from the rejected hash-inline or macro-home candidates. Under the Darwin/GNU,
single-host/single-VM guard, `na` uses the existing GVM D/R/W state protocol:
declare local state, read it on state reload, write it on state export. The six
arity macros and 14 existing caller reads use that local state. All 23 module
state definitions retain their original entries with the arity protocol added.
Other platforms retain original processor access. No object layout, argument
count interpretation, consumer source, RTS archive or GSC is changed.

Four focused generator tests pass. Native compile/link and real framework
imports pass. ARM64 object disassembly confirms `na` loaded from processor
offset 0x68 into x24 and used directly at entry checks; it is not merely a
new stack slot at the inspected entry. This is emission evidence, not a
global no-spill claim or runtime saving. Candidate binary SHA-256:
`2cf95fa2eefceded376bf08cb3e0573d94320b3170ff0db08814d8fa10a7ed4f`.

## Real tests and build

D1818 runs actual unchanged MCP regex gerbil-test CLI in two sequential
12-process waves, original D1510 then candidate. All 24 exit zero, preserve
source, return exactly 19 CASE-OK lines and final OK: 456 cases. Original
five-second real-output gates remain. Wave wall times are 3.179949/2.659832
seconds, but user CPU totals are 11.994785/11.884874 seconds (under 1% lower).
One AB batch is not a stable test acceleration or broad arity/FFI proof.

D1819 performs real cold MCP clean/build with 12 physical cores, GNU GCC,
original home and original preprocessing/object-reuse configuration. Clean
exits zero in 4.390130 seconds and leaves zero native images. Literal first
compile is 5.575560 seconds; complete build is 70.788101 seconds, exit zero,
maximum output gap 5.575560 seconds. Inputs remain unchanged. Correctness
passes; the <=55-second performance gate fails. Do not attribute comparisons
with other differently timed candidates to this change or redefine the best
line using this run.

D1820 independently runs unchanged concurrent std/make/std/test after the
MCP build terminates. Twelve runtime starts and twelve framework imports pass.
Cold/no-op/incremental contracts return all three CASE-OK markers, SUITE-OK,
D885-OK and controller exit zero. Parallel wall time is 16.781821 seconds,
maximum real-output gap 3.259266 seconds; 12 cores are configured but only 10
simultaneous GCC frontends are observed. No matched performance gain is proved.

Decision: no admission, no product/backend patch or full-toolchain acceleration
claim. Keep original D1510 selected. Large dynamic operation counts alone have
not established the major execution cost or its removal. The goal remains
active and incomplete. This prototype's bounded controls do not authorize
automatic caching across arbitrary C/FFI bodies or unsupported configurations.

Evidence: `.data/d1814-nargs-census/report.json`,
`.data/d1815-nargs-prefix/report.json` / `count.first.24414.tsv`,
`.data/d1816-nargs-register-preflight/report.json`,
`.data/d1817-nargs-register-native/report.json`,
`.data/d1818-nargs-register-mcp-tests/report.json`,
`.data/d1819-nargs-register-mcp/report.json` and
`.data/d1820-nargs-register-concurrent/report.json` / `parallel-make.log`.
