# D1604: complete diagnostic identifies tasks, not a speedup

The preceding goal turn made progress by collecting child CPU and reaps, but
could not identify the long C task. This turn records compiler mode and input/
output basenames without argument contents or personal paths. The observer is
only a dependency of isolated diagnostic binaries. No Gambit product behavior,
consumer source, installed toolchain or output deadline is changed.

Private evidence is `.data/d1603-composed-task-identity/`, with observer source
`.data/d1603-process-task.c` and driver `.data/d1600-process-lifetime.py`.
The fork/spawn/spawnp control matches three successful terminal reaps. Canonical
staging is freshly checked as 1cfb032c7a1612637da6205f5f8a15683eba3ba0.
The unchanged D1590 outline/family composition, original GSC inputs, Bazel GNU
GCC environment, original MCP head and twelve physical workers are retained.

## Actual Complete Construction

Official clean passes in 2.790944 seconds and leaves zero project native images.
The first literal compilation is 4.709145 seconds. Complete build exits zero in
71.716029 seconds, preserves the checked source hashes and produces the MCP
executable. It fails the user's 55-second ceiling by 16.716029 seconds. The
observer report is diagnostically qualified, with performanceQualified false.
This is not an uninstrumented comparison or a startup/whole-toolchain admission.

All 1,482 observed launches match successful terminal reaps: 740 GSC, 553
gambuild-C, 186 env, one GCC, one git and one build.ss. Both actual builder gxi
and GSC load the observer. No unmatched launch/reap remains within this observer
scope; arbitrary non-observed descendants' internal APIs remain out of scope.

## Long Task And Actual Tail

| Downstream task | Start | Reaped | Interval upper bound | CPU |
| --- | ---: | ---: | ---: | ---: |
| data/embedded object | 10.408566 s | 53.172251 s | 42.763685 s | 11.666184 s |
| tools/lint object | 42.318935 s | 54.944560 s | 12.625625 s | 3.156340 s |
| util/parse object | 8.973098 s | 18.068027 s | 9.094929 s | 3.064340 s |
| final exe_ closure object | 67.781540 s | 71.439414 s | 3.657874 s | 3.502297 s |

The long matched GSC task selects gerbil-mcp__data__embedded.c, with 11,425,281
generated C bytes. The caller's interval and CPU closely enclose its downstream
C-build task. Reap intervals remain exit-time upper bounds, not exact task
execution or scheduler attribution. CPU counters include descendants; do not
sum parent and child counters as independent work.

The embedded task finishes about 18.54 seconds before total completion. Later
GSC tasks include lib.scm ending at 66.675701 seconds, executable link generation
at 66.703239 through 67.670517, then the final executable closure object through
71.440316. Thus optimizing the single longest early task does not directly
remove the broad later tail. These observations do not explain the difference
between the historical D1513 and D1592 runs.

The completed GSC -obj records contain no repeated input basename. This is not
a semantic-equivalence census, nor a proof that basename-distinct work cannot
be reused. It rules out claiming a newly measured exact-name repeat in this
particular object subset.

## Do Not Repeat Established Negative Routes

The source emits large ordinary strings as ___DEF_SUB_STR plus numeric ___STR8
groups. D857 already measured packed-value object equivalence and approximately
3.1x atomic C-to-object improvement. D966 already saved and rebuilt the guarded
emitter candidate, with additional Scheme-emission work and no admitted complete
build. D858 already showed the header-only improvement did not materially
shorten a similar broad tail. Do not relabel this module identification as a
new discovery or rerun those atomic experiments without a new source hypothesis.

D1416 already limits simple producer fusion to about 4.16% on its measured
producer waves. This trace does not promote fusion or establish a broader
reuse contract. The next missing optimization evidence concerns actual late
work or in-process Scheme execution, not another generic compiler flag change.
First-log and real Scheme-test acceleration remain independent required gates.

All owned tool sessions are terminal. No release patch, full-toolchain rebuild,
commit, push or completion claim is admitted. The goal remains active.
