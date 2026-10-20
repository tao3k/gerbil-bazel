# D1510 Darwin FD Cleanup: Runtime DENY

No production admission or new complete-build/test acceleration. The frozen
47.771713 / 47.824226 / 47.927094 s cold anchor and whole-task 5/50/112 s
gates remain unchanged. The AOT-list task is separate and is not continued.

## Distinct Mechanism

Unlike the rejected PATH resolver/spawn substitution, this private candidate
keeps original process selection, fork, PATH search, child environment, pipe
and errno reporting. It changes only os_setup.c's descriptor-scan fallback:
Darwin/GNU uses a stack inventory of actual descriptors, then the existing
close-no-EINTR operation. Failure, malformed inventory, negative descriptors,
or a full 4096-entry buffer leaves the original upper-limit scan selected.
No allocation, directory traversal, FD cache or consumer-specific rule is added.
The noinline helper keeps its large inventory outside the ordinary caller frame.

[GLib's implementation](https://github.com/GNOME/glib/blob/main/glib/glib-unix.c)
uses Darwin proc_pidinfo for FD walking and explicitly notes that its
async-signal-safety is inferred from implementation, not API documentation.
[Apple's published wrapper](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)
delegates proc_pidinfo to proc_info and translates syscall failure to zero.
Published main branches do not prove the installed host's precise library
implementation or arbitrary signal/concurrency safety. Limited process controls
cannot substitute for that proof. No production patch is generated here.

## Construction And Actual Controls

The shared runtime-io/relink framework uses original GNU GCC commands.
Control os_setup.o matches the archived original byte for byte; the control
linked binary matches the frozen host byte for byte. Original inputs remain
unchanged. Candidate binary SHA256:
`6dade5061764413752ad8ee176821b68831d565c79433174b10eae946a5ec050`.

Both original and candidate pass 13 process-path/status/environment controls,
then six FD controls. The latter duplicate non-CLOEXEC descriptors and check
actual child closure plus unchanged parent descriptors for ordinary FDs,+sparse FDs >=65536, and 4100 descriptors forcing inventory overflow fallback.
All four invocations exit zero with exact terminal OK and named-case counts.
Twelve source/framework regression tests pass. These are not a complete suite.
The process controls' 7.177167 / 1.941664 s and FD controls' 4.953513 / 4.042008 s
are single ordered observations, not a stable speedup or admission result.

Evidence: `.data/d1510-darwin-closefrom-runtime-v1/`,
`.data/d1510-darwin-closefrom-native-v1/`,
`.data/d1510-darwin-closefrom-process-controls-v1/`,
`.data/d1510-darwin-closefrom-fd-controls-v1/`.

## Real Cold Gate

Official MCP clean succeeds in 5.419979 s and leaves zero native images.
Build has no qualifying first compilation log before 5.049419 s: DENY against
the unchanged 5 s ceiling. The owned group is killed/reaped, terminal exit -9,
with no cleanup errors. This is the deadline observation, not first-log latency.
Complete build time is unavailable; full tests are SKIP, not zero or passing.
Evidence: `.data/d1510-darwin-closefrom-acceptance-v1/`.

Do not retune/repeat this denied deployment or promote its component observations.
The denial does not prove that FD enumeration caused the first-log failure;
the earlier ordinary-build census has zero forks. It also does not establish
complete-suite savings from this separate test-process path. Keep the retained
host, not this candidate, as the mainline selection. All owned processes are
terminal; no commit, publication or goal completion follows.
