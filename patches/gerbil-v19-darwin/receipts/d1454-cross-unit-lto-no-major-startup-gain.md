# D1454: actual GNU LTO does not demonstrate major first-log acceleration

## Candidate Scope

The common current toolchain is D1391, with existing object reuse retained.
Gerbil staging source identity remains
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`; Gambit is
`ea114fc3d2f120abbe20393c1f9aeafdd3f8c89f`.
Eleven original generated C units are copied byte-exact: core, module, compile,
stx, stxcase, hash, table, top, mop, interface and util. No Scheme algorithm,
host grouping, VM ABI, compiler front end, consumer source, library image or
production patch changes. Original objects outside these units are reused.

The isolated Darwin/genuine-GNU candidate retains O1 and debug information,
adding `-flto=12` at object compilation and final GNU linking. Original macro
tracking and host/jump definitions remain. This is a directed cross-unit
optimization experiment, not an O2/O3 sweep or a whole-RTS LTO toolchain.
Hardware-derived compilation concurrency is 12. No profile training or
flow-inconsistent GCC feedback is consumed.

## Actual LTO Admission

D1450 requests slim LTO objects and fails immediately: this installed Darwin
GNU compiler requires linker-plugin support for `-fno-fat-lto-objects`.
The failed logs/report remain retained. D1451 instead uses the supported
default fat-object format, compiling/linking all selected units and passing
original std/make, std/test and std/build-script imports.

Fat-object success alone might accidentally qualify native fallback. D1452
therefore relinks through the actual GNU driver with verbose logging and
requires real lto1 execution in the log, not a dry-run command. Both WPA with
12 requested workers and LTRANS invocations are present. The admitted binary
again imports the original frameworks successfully, exit zero.

Candidate SHA-256:
`5b75d2166855125e87396b80376f6960b26a4a0abe2ca56c0da7124b1d763e1b`.
Original GSC SHA-256:
`9a1b842156fe15bb0c9415b87aebad0e72707bd793fe00353e7b68956929ab00`.
The original baseline inputs remain unchanged.

## Real MCP First-Log ABBA

D1453 executes fresh independent official MCP clean/build fixtures with common
library/GSC home and the existing ten-second actual-output gate:

| Role | First actual compile line, seconds |
| --- | ---: |
| Baseline | 5.916445 |
| LTO candidate | 6.049008 |
| LTO candidate | 5.788805 |
| Baseline | 6.085018 |

Means are 6.000731 versus 5.918906 seconds, approximately 1.36% lower; ranges
overlap. This is not a demonstrated stable win or the requested major cost
reduction. All cleans exit zero with zero project native images afterward.
Builds are deliberately stopped after `... compile util/compat`, terminal
exit 70; no complete build, final executable or concurrent test claim follows.
Consumer inputs remain unchanged. This is project-cold, not OS-cache-cold.

## Decision And Evidence

Do not activate LTO as a successful performance patch or launch a complete
toolchain build based on this result. The actual cross-unit pass execution
is proved; substantial startup acceleration is not. This does not prove all
possible whole-toolchain LTO policies fail or establish the Darwin/Linux cause.
Original proven spawn, object-reuse and preprocessing benefits remain intact.

Evidence: `.data/d1450-cross-unit-lto-runtime/report.json`,
`.data/d1451-cross-unit-lto-fat-runtime/report.json`,
`.data/d1452-admitted-lto-runtime/report.json` with `verbose-link.log`, and
`.data/d1453-cross-unit-lto-first/report.json`. The private build harness is
`.data/d1421-pgo-runtime.py`, extended with a separate LTO mode that preserves
its original feedback modes; admission is `.data/d1452-admit-lto-link.py`.

All owned processes are terminal. The major first-log and broader real
build/test objective remains active and unachieved.
