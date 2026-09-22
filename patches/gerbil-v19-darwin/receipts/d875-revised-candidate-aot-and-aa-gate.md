# D875: revised candidate AOT and POO A/A gate

Date: 2026-09-22. This round rebuilt the D874-corrected candidate before any
new performance comparison. It did not modify either real consumer or the
global Gerbil installation.

## Isolated candidate

The source is staging V19
`d801e7a1c7f77df421f638e62aaebe370f193c97` with the release support patches,
the four Darwin performance patches, and candidates `0007` plus `0008`.
Observation candidate `0009` was detected through its `module-index` events,
removed before the successful stdlib rebuild, and is not in this candidate.
The build used real GCC 16, host-derived 12-worker ordinary compilation, and
the existing General AOT path that closes only `gxpkg` and `gxtags`
sequentially.

The isolated installation is
`/private/tmp/d875-isolated/private/tmp/gerbil-d846-full.qHfGgo/install/current`.
It was not activated globally. All three tools are arm64 Mach-O executables:

| tool | SHA-256 |
| --- | --- |
| `gerbil` | `2e650f93a7bd4b063f43630e369d1acf2f5489367d5d56658483bc921b0632f9` |
| `gxpkg` | `2deb1161da65e986745ad631416814fcdee05916d0d8d7211128bf85af79ffc2` |
| `gxtags` | `0775c93e47cb0dc65f91de921606e4d34429b5db8e961083bb42730a0ecddb6e` |

Relocated `gxi -v`, AOT `gxpkg version`, and `gxtags --help` passed. The first
relocated `:std/make` import took approximately 18.8 seconds and was excluded;
the immediately following import completed in 0.55 seconds. Both compiler
executor contracts passed at 2 and 12 workers, including the new output
dependency cases.

The rebuild also exposed three toolchain-generation observability gaps:
`stage1` bach linking, `libgerbil` closure generation, and each General AOT
tool can remain silent for well over 10 seconds. They are not package-build
measurements and do not authorize adding observation Patch `0009` to this
performance candidate.

## POO same-binary control

Real POO remained at
`16edc0164cc4c00d81dd4d5e0fed0b24414d4a40`. Both A/A arms used the exact
`gerbil` hash above, GCC 16, 12 workers, native-warm state, the 10-second
measured-package silence gate, zero allowed relative regression, and the
13.13-second absolute candidate gate.

The first attempt did not reach a measured arm: its excluded first-access
qualification hit the separate 30-second silence timeout. One same-config
retry was allowed to determine whether this was first file access. It reached
the measured A/A pair:

| arm | wall | first compile | last native event | max silence |
| --- | ---: | ---: | ---: | ---: |
| identical binary A | 12.577 s | 2.318 s | 8.654 s | 3.922 s |
| identical binary A | 13.283 s | 2.447 s | 9.033 s | 4.250 s |

The second arm was 0.706 seconds (`+5.62%`) slower and exceeded the absolute
gate by 0.153 seconds. Both builds and the 10-second silence gate passed, but
the A/A admission failed. Immediately afterwards the host load averages were
17.37, 17.80, and 18.38 against 12 logical CPUs; free memory was 85 percent.
This is evidence that the qualification environment was loaded, not proof of
the precise cause of the drift.

Machine receipt: `/private/tmp/d875-poo-aa-2.json`. Decision: stop before the
POO/MCP candidate A/B. Do not weaken either performance gate, average this
failed control into a pass, or transfer D873's results to the revised binary.
Resume only when an identical-binary POO control passes in a stable host
window; then run both real consumers in both orders.
