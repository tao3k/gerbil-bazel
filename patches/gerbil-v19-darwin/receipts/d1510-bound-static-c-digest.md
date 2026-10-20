# Bound Static C Digest Candidate

## Route Review

- Correct: bind the C selected during link preparation to the later object
  compiler, including cold objects. A snapshot alone does not connect those
  two consumers.
- Previously explored: 0026 protects GCC's actual input against a transient
  source mutation. It does not carry the link consumer's selected digest.
- Worthwhile: an actual Scheme/native fixture links a selected definition of
  17 but runs 29 after unbound recompilation of changed C. Rejecting that
  mismatch is a prerequisite for safe closed-set reuse.
- Expected gain: zero from this safety patch alone. Bulk generation reuse is
  a separate optimization; its component measurements are not package wins.

## Contract

Apply experimental 0027 after 0026. On Darwin, a per-object caller may set
`GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA` to the lowercase, 64-character SHA-256
of its selected C. Merely setting this variable activates the bound path; it
does not require the separate reuse flag. An empty or malformed value rejects.
Cold object creation cannot use the original mutable-input shortcut. A source
mismatch or unsupported snapshot invocation rejects without replacing the
existing object/proof. Concurrent bound creation retains the existing lock.

Both flags absent preserve the original default. Linux retains the original
platform branch. This is not a transitive-header snapshot or a caller
integration. Do not set the digest globally in a threaded build parent: it
must belong to the individual object invocation.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| 0027 patch | `fc5cf3192a13e387912c0ec99147a1640a4005ba6951f6494bd64a1bb4608ee8` |
| Patched helper | `86fc6b5610e59af38dfadb9e3853bd1fc694c5dedb1fd7d796b2157e77dd7c39` |
| Installed candidate driver | `78eeb8c4e9cec4e9ddfb612662d734d45b1a04ef345fb7c8917cf4f11fe85367` |

Preparation requires the exact 0026 helper identity. Actual source-template
replay applies 0026 then 0027 to the frozen five-patch source fixture and
reproduces the helper above. The configured driver's bytes differ from the
source template because configuration substitutes toolchain paths.

## Current Native Checks

Candidate: `.data/d1510-bound-static-c-candidate-v3/bin`. Matching isolated
ASCENT Multiple VM GSC/headers and genuine GNU GCC. All terminal exits are 0.

| `.data/` receipt | Result |
| --- | --- |
| `d1510-bound-static-c-controls-v4` | Binding alone activates cold MISS/HIT; existing/missing source mismatch, recovery, unsupported options, empty/malformed digest, concurrent one-MISS/one-HIT pass |
| `d1510-bound-static-c-cold-aba-v2` | Missing-object transient C mutation blocked; exact ordinary object and native return-value parity |
| `d1510-link-object-binding-v5` | Actual Scheme generation/link: ordinary 17, unbound changed C 29, bound rejection, restored bound 17; exact ordinary object/output |
| `d1510-bound-static-c-safety-v2` | Six unbound compiler/proof/warning/mid-flight mutation controls pass |
| `d1510-bound-static-c-semantics-v2` | Relative headers, filename macros, 2020 source timestamp, line/include levels, debug/prefix-map fallback parity |
| `d1510-bound-static-c-source-replay-v1` | Both actual source-template patch applications pass; helper digest matches |

Earlier candidate v2 failed preparation at the driver hunk; the attempted
control run exited 127. It is not a native or performance sample. The current
expanded hunk applies to both installed and unconfigured source forms.
Earlier standalone links resolved an ambient Nix linker and failed even for
an ordinary native C control. The current fixture uses the successful GNU GCC
build environment's explicit Homebrew/Apple PATH and SDK, not Clang.

## Admission Boundary

0027 is deliberately excluded from both measured patch series. It has not
received full MCP or full ASCENT qualification, and cannot inherit their times.
The six-patch MCP safety candidate remains separately frozen at three complete
cold builds of **36.414237 / 35.551924 / 37.770491 seconds**, first logs of
**4.038430 / 3.980393 / 3.950160 seconds**, and one complete test run of
**86.924285 seconds, 39/39 files, 965/965 cases**.
Ceilings remain **4.5 / 42 / 97 seconds**. Its patch/runtime/raw-evidence lock
still passes; 41 focused patch-lock tests pass. No new acceleration, full
toolchain rebuild, production admission, commit or GitHub delivery is claimed.
