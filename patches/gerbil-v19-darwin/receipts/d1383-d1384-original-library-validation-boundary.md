# D1383-D1384: original Darwin library-validation wait

## Identity and scope

Canonical `v0.19-staging` was rechecked at
`1cfb032c7a1612637da6205f5f8a15683eba3ba0`.
Original source/home: `.data/d935-staging-source`, with its original `build`.
Original gerbil SHA256:
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`.
MCP fixture: `.data/d1374-original-mcp`, unchanged source.
GNU GCC 16, Bazel-discovered SDK/environment, physical-core budget 12.
No copied library home, product modification, signing change, attribute removal,
validation bypass, consumer change or full-build claim.

## Observation

D1383's unprofiled original `gerbil clean` failed the existing 30-second gate,
with a zero-byte log. There was consequently no admitted first-build window.
D1384 reads counters and a short stack in the same original clean workload;
it also fails at 30 seconds with a zero-byte log. The second run includes a
two-second sample, so it is not an uninstrumented timing comparison.

| Observation | Elapsed seconds | User CPU | System CPU | Page-ins | Read bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| First snapshot | 3.011883 | 0.767770 | 0.313521 | 2850 | 47476736 |
| Second snapshot | 25.038264 | 1.110629 | 0.437650 | 3078 | 51978240 |

Each snapshot reports only the original process, with zero reaped-child CPU.
CPU counters are cumulative, not exclusive syscall durations. Between snapshots
about 0.467 seconds of CPU accrue over about 22 seconds of wall time. This
establishes a low-CPU slow window, not its entire exclusive waiting cause.
The live 3-5 second sample has 183 main-thread samples; 167 are at:
`___dynamic_load -> dlopen -> Loader::mapSegments -> SyscallDelegate::fcntl -> __fcntl`.
The observed original failure therefore also reaches the loading boundary;
it is not limited to the copied-home lanes of D1381-D1382.

## Installed command identity

Installed macOS is 26.6.1 (25G76), dyld version 1387. Both the sample and the
arm64e slice of `/usr/lib/dyld` report UUID
`DF42DD9D-AD11-33A7-8849-9AD5DF30A274`.
The sampled return address is `0x18865b21c`; dyld base is `0x188614000`,
giving unslid address `0x4721c`. Installed `mapSegments` starts at `0x470e4`.
The matching instructions are:

```asm
47210: mov x1, x23
47214: mov w2, #0x62
47218: bl  SyscallDelegate::fcntl
4721c: cmn w0, #0x1
```

The installed delegate moves argument x2 into x1 before calling libc `fcntl`.
The SDK defines `F_CHECK_LV` as 98 (`0x62`). This identifies this particular
observed call as library validation, rather than merely guessing from public
source or confusing it with code-signature registration.
[Published XNU](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_descrip.c)
routes `F_CHECK_LV` to `mac_file_check_library_validation`. That source is not
matched to the installed kernel/security-policy implementation and does not
identify the policy provider, cache key, blocked file or exact wait duration.

## Counter correctness and reproduction

The GNU-C helper uses SDK `rusage_info_v2` and `proc_listchildpids` APIs.
The child-list API returns a PID count, not a byte count; this was corrected
before D1384. D1383 had no counter snapshot and is not used as family evidence.
CPU ticks are scaled by `mach_timebase_info`: this host reports 125/3.
Self-calibration against `getrusage` passes: D1384 user CPU 0.095911375 versus
0.095912 seconds. Published XNU `fill_task_rusage` and
`task_power_info_locked` retain Mach time units; direct nanosecond labeling
would undercount by about 41.7 times on this host.

Private reproducibility inputs: `.data/d1383-prefix-rusage.c` and
`.data/d1383-original-prefix-rusage.py`. Raw reports/logs remain in
`.data/d1383-original-prefix-rusage` and `.data/d1384-original-prefix-rusage`.
Python syntax check passes; the D1384 helper builds with GNU GCC without
warnings and passes unit calibration. Both measurement processes are terminal;
the owned original clean PID is verified absent after timeout.

## Admission boundary

This is new Darwin-specific waiting evidence, not an optimization receipt.
It strengthens the concrete library-validation branch while leaving the
ordinary successful 6-8 second build prefix unresolved. Do not infer that all
macro execution, historical Linux/macOS disparity, or total build/test time
is this syscall. No production patch or full toolchain rebuild is admitted.
Future mitigation must preserve library validation and Scheme/module semantics;
neither disabling security checks nor retrying rejected blind image packing
is justified by this result.
