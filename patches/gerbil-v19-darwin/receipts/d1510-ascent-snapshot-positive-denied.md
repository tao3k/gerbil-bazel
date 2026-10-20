# Snapshot Reader: Real ASCENT AOT Attempt Denied

## Exact Candidate And Isolation

The candidate is `.data/d1510-native-generated-c-ascent-gsc-v4`, compiled with
planned producer admission, native digests and actual snapshot-reader patch 0025.
GSC SHA is `c9caaea9e777122e011fdd925f87fee578b94ff7eeac9031dce804fa8209f2e9`.
The explicit `d1510-ascent-native-snapshot-v4-identity.json` binds its binary,
helper, compiled entry/journal/header/config, other helper sources, original
journal input, patch 0025 and matching runtime archives. Identity verification
is not performance admission. Existing V8/V9/V11 consumer profile selection is
unchanged and cannot silently accept this binary.

The owned preparer verifies this identity before creating
`.data/d1510-native-generated-c-ascent-snapshot-v1`. It COW-copies the frozen
ASCENT project at `21e3638687d42ecfc36acebb28991987435ebc60`, its own MULTIPLE_VM
toolchain and dependencies, clears only the fresh copied static cache, installs
the candidate GSC and nine owned files from the previously verified planned
std/make overlay. No active checkout or shared dependency is edited.

## Real Whole-Task Gate

Command shape (all paths supplied from owned `.data`):

```sh
bash patches/gerbil-v19-darwin/tests/run_isolated_ascent_static_reuse.sh \
  <workspace> <receipt> native positive-plan native-digests 135
```

The repository's native Scheme qualifier owns compilation and Cases. Bash/just
and GNU timeout launch it directly; no Python native test supervision, per-file
silence timeout or fake progress output is introduced. The whole-task cap remains
135 seconds, the existing independent positive-plan ceiling, not an MCP budget.

Receipt `.data/d1510-native-generated-c-ascent-snapshot-positive-v1` is terminal
**DENY**. The task is still compiling library modules when the 135-second cap
terminates it. There are 80 producer-index records, demonstrating the new producer
executed, but no completed Suite/Case results, layer completion markers or native
static-link adoption. These records alone are not a reuse gain.

The runner exits 1. BSD time reports real 136.02 seconds including the termination
grace and abnormal signal handling; its zero CPU fields are invalid measurements.
This is not a completed AOT/test duration. No correctness pass or acceleration
ratio is claimed. The same time-file hash as the earlier timed-out attempt does
not make this a duplicate run: the output identity and owned candidate are new.

## Post-Run Checks

- Isolated project `git diff --exit-code --quiet`: passes.
- Toolchain: 1,989 remaining read-only dynamic images and nine owned std/make
  overlay files verify against their recorded content identities.
- Dependencies: all 2,809 read-only images verify.
- Exact owned-workspace `/usr/bin/pgrep` inspection: exit 1 with no matches;
  no remaining process for this task. The PATH-selected pgrep first failed to
  access sysmon; that failure was not treated as proof of process absence.
- Profile/runtime/input/patch drift rejection and isolation regression tests:
  33 pass. Defaults retain prior profile selection and source bytes.

Raw SHA256 identities:

- Output `862b7bcd138c1a5979b648079c31fe2638304ac9cf185ff2a1e9bdf10d78e654`.
- Time `e3659a6236cfa7f03abf3f1f123be950dfa431ee5abc4cb0dab9b56a50347a92`.
- Exit status `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`.

## Decision

Close this unchanged candidate/configuration as DENY. Snapshot binding fixes a
real source-proof race, but does not remove cold producer work or establish
consumer performance. Do not retry hoping to select a passing wall time, widen
the deadline, count partial records as Cases or add it to the fastest MCP series.
Producer tool-validation amortization still requires a new mechanism preserving
publication and concurrency safety. A new whole-task attempt requires such a
material change, not merely another identity label.

The frozen MCP measurements remain first log 4.004-4.049 seconds, cold builds
36.467-37.406 seconds and a complete 87.409-second/965-case pass. Active ceilings
remain 4.5/42/97 seconds. No new MCP task ran this turn. Both consumer performance
requirements remain incomplete; no goal completion, release or GitHub push is
claimed.
