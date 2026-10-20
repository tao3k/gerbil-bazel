# Real ASCENT Static Reuse Qualification

## Scope and Setup

Isolated consumer head: 21e3638687d42ecfc36acebb28991987435ebc60.
Workspace: .data/d1510-static-reuse-ascent-v1.
The original checkout, installed toolchain and dependency prefix were not edited.
No Python process launched or supervised native Scheme tests. The repository's
existing just test-native and native qualification code owned the real work.

The copied-profile load was previously rejected. Rather than retry that setup,
the isolated profile now references only byte-identical original dynamic .o1
images; C, Scheme, headers, static objects and test outputs stay independently
owned. A qualification-only native driver guard refuses output symlinks.
The guard was exercised: attempted dynamic-image output exited 2 with
ISOLATION-OUTPUT-SYMLINK-DENY, without compiling through the reference.
Post-run digests verified all 1,992 toolchain and 2,809 dependency dynamic images.
This reference mechanism is not a production optimization or validation bypass.

## Typed Setup Failures

- Readonly control v1 reached compilation but the default GSC pathname retained
  an unavailable CI location. The supported GERBIL_GSC override selects the
  isolated compiler explicitly.
- Control v2 was terminated after discovering default gcc would resolve to
  Apple Clang. It is not a GNU-qualified result.
- Control v3 explicitly used GNU GCC but the inherited Nix linker environment
  failed the final link with unresolved system symbols. It exited 70 after
  242.92 seconds. No Cases ran; this is not an accepted timing.
- Control v4 places the native system tool path before inherited Nix tools,
  selects GNU GCC explicitly and sets the existing build-core environment from
  getconf NPROCESSORS_ONLN: 12. It completes correctly.

No failed configuration was admitted. The partial library from cancelled v2
was removed before v3. The successful v4, candidate population and candidate
reuse scenarios have warm compiled libraries and a missing entry receipt.
They are not complete from-zero library builds.

## Actual Same-Consumer Results

| Scenario | Whole Time | User CPU | Native Cases | Object Reuse |
| --- | --- | --- | --- | --- |
| Control, entry miss | 43.08 s | 81.36 s | 30/30, final OK, exit 0 | 0 hits |
| v3, proof population | 51.71 s | 145.24 s | 30/30, final OK, exit 0 | 72 misses |
| v3, repeated entry miss | 43.40 s | 98.47 s | 30/30, final OK, exit 0 | 71 hits / 1 miss |

All three logs contain 74 actual GSC object invocations and an entry-cache MISS.
The second candidate run therefore proves real object reuse, not an AOT entry
cache hit. Calls without an eligible existing object use the original compiler
path; invocation counts are not individual-object counts because an invocation
can compile multiple inputs. Cases include all 512 directed three-node graphs and independent
reachability comparisons. The whole times include library currentness analysis,
entry compilation, linking, and execution of all 30 Cases.

The repeated candidate does not beat the 43.08-second matched control.
Its population cost is also higher. This v3 implementation is denied general
performance admission despite preserving correctness. Its separately frozen
MCP observations remain valid observations but do not prove cache causation.
Do not repeat unchanged v3 performance runs seeking a lucky result.

Canonical offline summary: .data/d1510-static-reuse-ascent-native-summary-v2.json.
The initial summary incorrectly anchored concurrent compile events to line
starts and undercounted interleaved output. The corrected parser counts event
tokens, preserves the original raw logs, and requires exact Cases, final OK and
exit status. It never launches native tests.

## Next Cost Candidate

The implementation hashes its tool set before and after preprocessing and again
at reuse admission. The new native CommonCrypto SHA-256 prototype targets that
new repeated work without weakening content identity or skipping source/options
checks. It is GNU/Darwin-only, uses public SDK CommonDigest APIs and rejects file
read/digest errors. No Scheme/compiler behavior is changed by this prototype.

Same-toolset component observation in .data/d1510-native-file-sha256-v1:
shasum wall 0.22 s / user 0.20 s; native wall 0.03 s / user 0.02 s.
Digest output is byte-identical. Empty/binary/space/backslash/newline filenames,
raw digest, symlink-to-file, missing file and directory failure controls pass.
Compilation uses GNU GCC with warnings as errors. This is a single component
measurement, not yet an integrated build/test performance claim. The native
backend is not connected to production or to the frozen helper in this turn.

The full ASCENT cold/invalidation/concurrency scenario set and integrated native
hash backend admission remain open. Goal completion and GitHub delivery are not
claimed.
