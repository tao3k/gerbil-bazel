# Unified Source and Publication Validation

- Upstream `v0.19-staging`: `1c6c15385979f0092574fbc2b828f3fb656319b3`.
- Gambit gitlink: `7c490c3ab5b5a4238b26f4a59d8cd9fd4b085882`.
- All 21 selected Darwin/common patches applied in order to these real sources.
- Shared source provisioning contracts: 15 passed.
- Packaging, publication and workflow admission contracts: 12 passed.
- CI-selected frozen patch/performance/safety contracts: 100 passed, 1 skipped.
- Both workflow YAML files parsed; all run blocks and shared scripts passed Bash syntax checks.

Linux generated and verified its Bazel 9.2.0 lock in
[job 114162746558](https://github.com/tao3k/gerbil-bazel/actions/runs/38034746585/job/114162746558).
The remaining queued lock jobs were cancelled after downloading that seed.
Local Darwin `bazel mod deps --config=lock_update`, followed by
`bazel mod deps --lockfile_mode=error`, completed the merge without source compilation.
The resulting Linux entry is structurally identical to the verified Linux seed.

The full historical experiment-test directory is not a clean-checkout gate:
196 tests passed, 1 skipped, and 6 failed because retired `.data` fixtures are absent.
Those experimental fixtures and tests were not changed by this release work.

This receipt does not certify a new native toolchain build, downstream performance,
or completed release publication. Those require the exact-head source CI results.
Automatic publication admits only successful main push CI and distributes its
Linux and Darwin artifacts without another build. Manual source construction uses
the same profile and builder; it does not introduce another configure-flag list.
