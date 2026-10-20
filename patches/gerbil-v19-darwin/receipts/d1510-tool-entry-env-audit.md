# Interpreter Entry And Package Environment Audit

## Decision Review

- Aligned: yes, distinguish direct interpreter startup from package-environment entry using the same interpreter identity.
- Already explored: D862 tried native-tool handoff and failed real MCP admission. Do not recover that production patch from short-command timings.
- Worth investigating: yes as an entry-path correctness audit. The AOT tool list does not change `tool-main` dynamic dispatch.
- Expected benefit: unknown before measurement. These probes do not qualify a cold build or full test improvement.

## Matched Retained Control

The private framework command is `experiment.py tool-entry --output .data/d1510-tool-entry-env-v2 --rounds 2`.
All interpreter and package-tool aliases resolve to the retained binary SHA256
`1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21`.
The process environment uses the isolated retained home, fresh package path,
and explicit tool bin directory; no global executable is launched.
Rounds alternate entry order. Each child has a 15-second diagnostic bound,
not an MCP build/test performance gate. Durations include the framework's
bounded process-wait polling and are not fine-grained CPU measurements.

| Entry | Round 1 Seconds | Round 2 Seconds |
| --- | ---: | ---: |
| Direct gxi | 0.128 | 0.133 |
| gxpkg env, absolute gxi | 0.668 | 0.666 |
| gerbil env, absolute gxi | 0.673 | 0.734 |
| gerbil env, PATH gxi | 0.672 | 0.673 |

All eight commands exited zero with the exact final marker. A separate
`gerbil env` shell resolution check selected the expected private gxi.
The original binary hash remained unchanged. The deprecated std/net/request
warning is preserved in raw logs and counted explicitly, not treated as a
test result. The first v1 diagnostic rejected that known warning as a PATH
mismatch; its incomplete report remains preserved. v2 accepts only that
exact warning, rejecting other extra output.

## Source And Admission Boundary

Retained `src/gerbil/main.ss` maps env to gxpkg env. `tool-main` imports the
tool module and resolves/evaluates its main entry. It does not execute the
separate AOT gxpkg binary. `src/tools/gxpkg.ss` imports its package-manager
dependencies, including std/net/request; env-exec prepares the environment,
prepends the package bin to PATH, and invokes the child. AOT eliminates
neither module initialization nor the child's own startup automatically.

The retained gxpkg alias is not a standalone AOT executable. Therefore these
numbers establish environment-entry overhead in the retained control, not
the current installed AOT tool's overhead and not the causal breakdown of
all loading, initialization, or process costs. Inspection of the current
Homebrew installation found a real native gxpkg behind its shell wrapper,
but that global installation was not executed in this experiment.

No runtime dispatcher patch is admitted. No claim of cold-build or full-test
acceleration follows. Historical cold builds remain 47.772, 47.824 and
47.927 seconds; this audit did not rerun them. Stable full-test admission
under 112 seconds remains open.

## Real MCP Working Directory Correction

The earlier table used an empty diagnostic directory, not the MCP package.
It must not be described as an MCP-context measurement. The corrected command
adds `--project .data/gerbil-mcp`, with fresh output
`.data/d1510-tool-entry-mcp-env-v1`. MCP HEAD is
`05ed8728a4871e3483fe9792480ecee2d9653e4b`.

| Entry In MCP | Round 1 Seconds | Round 2 Seconds |
| --- | ---: | ---: |
| Direct gxi | 0.127 | 0.129 |
| gxpkg env, absolute gxi | 0.645 | 0.619 |
| gerbil env, absolute gxi | 0.621 | 0.672 |
| gerbil env, PATH gxi | 0.618 | 0.612 |

All eight commands passed with the exact marker. For env commands,
GERBIL_PATH is unset before launching so normal local package detection runs.
A child shell asserts that both PWD and GERBIL_PATH point to the MCP checkout
and its local .gerbil directory, then verifies PATH selects the expected
private interpreter. Direct gxi uses that same local package path explicitly.
The previously absent .gerbil directory is created by normal gxpkg env setup;
no dependency installation or package clean/build/test runs occurred.
The manifest and retained binary hashes remain unchanged, and MCP git status
is still clean. These are real MCP-directory startup probes, not application
module loads, full tests, cold builds, or standalone AOT gxpkg comparisons.
