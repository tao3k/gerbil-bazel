# D1387: target-only kernel observation needs local authorization

The prior turn is progress: D1386 identifies an original native FD, checks its
disk signature, and retains the failed actual build gate. It does not qualify
an optimization or identify the policy-provider implementation.

To avoid another copy of the existing user-stack samples, this turn checks
whether installed spindump can observe the kernel wait. Installed help states
that it gathers user/kernel stacks and that `-onlyTarget` limits sampling to
the target. A one-second capability probe targets only its own command process,
with no binary/file output, a five-second internal limit and automation mode.
No new Gerbil workload is launched for the capability probe.

The direct probe exits 77: live sampling must run as root. The same own-process
probe using `sudo -n` exits 1: a password is required. No password is requested
through chat or provided to a tool. No capture, privileged process, system-wide
trace, security change, policy restart or product modification is performed.
Both command handles are terminal. The check does not infer anything about
exclusive validation duration or first-log performance.

Current observation boundary: user-mode stacks identify the installed F_CHECK_LV
call, but target-only kernel observation is unavailable to the agent without
local administrator authorization. Published XNU policy dispatch and absent
matching logs do not replace that missing evidence. Local authorization for
a short, target-only capture is requested; unrestricted administrator access,
security disablement, certificate/signing changes and password disclosure are
not requested. The goal remains incomplete, with no admitted patch or complete
toolchain build. Do not keep rerunning unchanged user-stack captures while this
specific access condition is unresolved.
