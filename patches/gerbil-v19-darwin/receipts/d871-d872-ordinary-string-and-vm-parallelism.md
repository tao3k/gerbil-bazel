# D871–D872: ordinary strings and Gambit VM parallelism

Date: 2026-09-22. These are atomic diagnostics on staging Gerbil
`d801e7a1c7f77df421f638e62aaebe370f193c97`, not a performance A/B or
an admitted release patch. Neither real consumer nor the global installation
was changed.

## Ordinary generated-C string lowering

The D857 packed-`___STR8` experiment was repeated on two ordinary generated
MCP C files with the same GCC 16 flags. In `howto-verify~0.c` (152 strings),
the original and packed variants produced byte-identical Mach-O objects.
Alternating warm `gsc -obj` wall times were 0.76/0.35/0.36 s and
0.35/0.54/0.41 s respectively: no stable gain. In `lint~0.c` (617 strings),
the objects were also byte-identical; alternating original times were
3.63/2.98 s and packed times 3.38/3.23 s (both medians 3.305 s). The large
embedded-file result does not generalize to ordinary files, so no emitter or
header change is admitted. Raw experiment artifacts are under
`/private/tmp/d871-str8-ordinary.8PzpDI`.

## SMP is not OS-thread parallelism

The qualified D866 Gambit has `--enable-smp`, but
`##current-vm-processor-count` reports 1. In Gambit `configure.ac`,
`--enable-smp` selects the Scheme scheduler while the separate
`--enable-multiple-threaded-vms` option permits multiple OS threads per VM;
the latter defaults to off. This is a real architectural distinction, not
proof that the existing package build is under-parallelized: the 12 native GCC
workers remain independent OS processes.

An isolated, same-revision Gambit build with
`--enable-multiple-threaded-vms` and the same GCC/optimization flags reported
12 processors under `-:p12` (and 1 under `-:p1`). The default heap settings
overflowed even on a minimal expression at 12 processors; `-:m32M,p100%`
passed that atomic smoke test. Making `p100%` the default then failed the
Gerbil stage0 build: each of the 12 concurrent compiler subprocesses acquired
its own 12-processor VM and many reported heap overflow. Setting the default
back to `p1` removed that oversubscription, but one isolated `gsc` compile
still exited 139 while the unchanged D866 compiler passed the same input.
The isolated build reused same-revision generated Gambit C, so this failure
is **not** evidence that a correctly bootstrapped upstream multi-threaded VM
is broken. It does mean this candidate has not passed toolchain qualification
and must not enter the real-consumer A/B or release stack. The Gerbil stage0
wrapper also exited 0 after printing compiler failures; its exit status is
not a valid success receipt in this case.

`##set-parallelism-level!` only updates the setup parameter after VM startup;
it did not change the running VM processor count from 1. If this direction is
resumed, a correctly bootstrapped multi-threaded Gambit must first pass a
single real Gerbil compilation, then stage0 with explicit error checking.
Only the `std/make` coordinator should receive a host-derived parallelism
setting; compiler subprocesses should remain lightweight. Until those gates
pass, the qualified four-patch D866 toolchain remains the comparison baseline.
