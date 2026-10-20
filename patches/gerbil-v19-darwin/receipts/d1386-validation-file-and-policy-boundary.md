# D1386: native file identity and validation-policy boundary

## Original workload evidence

No product modification is made. The original D935 source/build home and
original binary SHA256
`cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928`
are used with GNU GCC16, Bazel environment and 12 physical cores.
The fixture is unchanged `.data/d1374-original-mcp`.
The actual `gerbil clean` exits zero in 21.507044 seconds, inside the unchanged
30-second limit. Zero MCP native `.o1` images are asserted after clean.
The subsequent actual `gerbil build` has a zero-byte output log and fails the
unchanged ten-second product-output limit. There is no first-compile timing.
`qualified=false`, `performanceQualified=false`, `buildCompleted=false`.
The clean lane includes a two-second sample and is not an unprofiled speed
comparison. No full-build or concurrent-test qualification follows.

At elapsed 3.018130 seconds, the own-process SDK FD inventory reports one
native-image file open at fd 5:
`.data/d935-staging-source/build/lib/std/net/uri~0.o1`.
Other vnode descriptors are `/dev/null` and the diagnostic clean log.
Inventory is not truncated. User CPU is 0.907282 seconds; system CPU is
0.233074 seconds; page-ins are 319; disk reads are 3895296 bytes.
The nearby live two-second sample has 185 main-thread samples, 181 at the
same mapSegments/__fcntl return address identified as `F_CHECK_LV` in D1384.
The FD inventory is a snapshot before sampling, not a captured syscall
argument. It narrows the loaded-file identity without proving the FD stayed
unchanged across every sample or measuring this file's exclusive delay.

## Read-only signature verification

`codesign --verify --strict --verbose=2` on that exact original image exits 0:
valid on disk, satisfying its Designated Requirement. Read-only display reports
an embedded SHA256, adhoc/linker-signed CodeDirectory, flags `0x20002`,
36 code hashes and no TeamIdentifier. CDHash:
`191bdc9cb4c3d7f5955d0e7a783fb814335ada83`.
This excludes failed disk-signature verification for this selected image;
it does not establish a trusted certificate chain or policy acceptance latency.
No signing, metadata change, attribute deletion or security bypass is performed.

## Policy implementation and log admission

Published XNU
[mac_file.c](https://github.com/apple-oss-distributions/xnu/blob/main/security/mac_file.c)
dispatches library validation through `MAC_CHECK(file_check_library_validation)`.
[mac_internal.h](https://github.com/apple-oss-distributions/xnu/blob/main/security/mac_internal.h)
iterates registered policy callbacks and combines their errors. That dispatch
does not identify the installed callback implementation, exclusive wait time,
policy provider or cache keys. It provides no Gambit-side switch to preserve
verification while merely bypassing the observed callback.

A recent log query restricted to syspolicyd/amfid initially matching the generic
word gerbil returns Homebrew/release and other Gerbil-related paths. Those
events are not assigned to the D935 workload. A second bounded query, restricted
to the exact D935 home token and owned D1384/D1385 PIDs, returns no events.
Absent logs are not proof of an absent policy call. No unmatched error about
an unknown/adhoc certificate chain is promoted to our workload's cause.

## Reproduction and decision

Raw report, logs and sample: `.data/d1386-original-validation-file-identity/`.
Private SDK/GNU helper: `.data/d1383-prefix-rusage.c`, now enumerating own
vnode descriptors with `PROC_PIDLISTFDS`/`PROC_PIDFDVNODEPATHINFO` and JSON
escaping. Private runner: `.data/d1383-original-prefix-rusage.py`.
GNU helper compilation and Mach-time/getrusage unit calibration pass.
Both owned original clean/build processes are terminal and verified absent.

The policy-provider cause remains unresolved. This result prevents a mistaken
signature-repair or unrelated Homebrew-log explanation; it is not acceleration
and does not replace the missing successful original first-window partition.
No new product cache, image packer, production patch or complete toolchain build
is admitted. The requested first-log and end-to-end gates remain open.
