# D1389: guarded original-prefix kernel capture

The preceding D1388 turn recovers CC policy and complete-build distinctions;
it does not deliver an optimization. Current noninteractive administrator
credential validation still exits 1 with a password-required response.

The private `.data/d1383-original-prefix-rusage.py` now accepts
`--kernel-sample`. Before creating the output directory or launching any
Gerbil workload it checks noninteractive administrator credentials. The
checked invocation with output `.data/d1389-original-kernel-prefix` exits
77, explicitly reporting that no workload was launched. Python compilation
passes. The privileged capture path has not run or been verified.

When locally authorized, that mode substitutes a two-second installed
`spindump -onlyTarget` capture for the prior clean user-stack sample and
adds a two-second capture at the real build's three-second boundary. It uses
only the owned Gerbil PID, omits binary output, keeps text in `.data`, and
runs asynchronously so product-output monitoring is not delayed by capture.
The sampler has its own five-second limit and a bounded owned-group cleanup.
Official clean remains limited to 30 seconds and product-output silence to
10 seconds. Captured timing is diagnostic, not speedup qualification.

No security setting, signature, product source or consumer source changed.
The missing evidence is the kernel-side wait behind the already identified
installed F_CHECK_LV call. User stacks do not identify the policy provider or
its exclusive latency. Do not launch repeated identical samples while local
administrator access remains unavailable. Full build, first-log improvement,
and concurrent build/test admission remain incomplete.
