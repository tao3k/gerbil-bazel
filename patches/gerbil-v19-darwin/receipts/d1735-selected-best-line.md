# D1735: return to the historical best B line

User direction: stop investigating the later twenty-second discrepancy.
Develop further Gambit optimizations from D1513's original B line instead.

Selected baseline:

- Native binary: `.data/d1510-outline-current-native/gerbil`.
- Original carrier: `.data/d1508-outline-current-preflight/gerbil-link.c`.
- Original GSC/runtime/library home: `.data/d1391-runtime-object-source/build`.
- Historical complete builds: 51.737180 and 53.496910 seconds.
- Historical mean: 52.617045 seconds; first compile: 4.789153 and 4.933479.
- Complete-build acceptance ceiling: 55 seconds; unchanged real-output gates.

D1734 revalidates the exact historical B binary, GSC, runtime archive,
carrier and all 42 original native inputs. All checks pass. It records the
selected line in `.data/d1734-best-line-selection/report.json`, using
project-relative artifact paths. This is an identity selection, not a fresh
performance reproduction or a claim that current wall time is already restored.

Do not layer the grouped-string GSC, expanded trace sites, local-context type
cache, native-object capture or proposed nargs cache into this baseline.
Retain those experimental artifacts without deleting or overwriting them.
Next candidates derive from the selected original carrier with one isolated
Gambit-side change. Original object-reuse and GNU GCC preprocessing advantages
remain part of the selected home. Use current physical CPU discovery, not a
fixed two-worker limit. No consumer or std/make/std/test source changes.

The goal remains actual Darwin startup/build/test acceleration, not explanation
of the later discrepancy. No new performance success or full-toolchain
qualification is claimed by this selection.
