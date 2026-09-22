# D878 Darwin HTTP runtime closure

## Scope

This receipt qualifies two Darwin runtime gaps against the pinned V19 staging
plus PR 1493 composition recorded in D877. It does not modify ASP source. The
real consumer is the existing `agent-semantic-protocols` Gerbil provider.

## Typed root causes

1. Darwin `sockaddr` carries `sa_len`, but the V19 FFI initialized only
   `sa_family` and passed the max union size as `socklen_t`. `bind` therefore
   failed with `EINVAL` before the HTTP request path.
2. A nonblocking non-Linux `accept` returned the admitted negative EAGAIN
   sentinel, but accepted-fd setup ran before the sentinel check and attempted
   `close(-35)`. The server accept thread terminated, so a TCP handshake could
   complete while HTTP returned no bytes.
3. `std/make --release` injected fully static executable linkage on Darwin,
   where GCC failed for lack of `crt0.o`. Darwin release executables require
   ordinary dynamic native linkage.

## Implementation boundary

- Darwin sockaddr ABI changes are under `cond-expand (darwin ...)`.
- Linux retains the official `accept4` path and existing sockaddr length
  behavior.
- Non-Darwin release executables retain the existing static linkage contract.
- The accept control-flow correction changes only the existing non-Linux
  branch and does not alter the scheduler or HTTP server.

## Local evidence

- Focused upstream `src/std/os/socket-test.ss`: `MODULE-OK`, `HARNESS-OK`,
  `OK`. The added port-0 case starts accept before the client connects, proving
  the EAGAIN pending path survives.
- Release AOT sockaddr probe: first bytes changed from invalid `#u8(0 2 ...)`
  to Darwin-native `#u8(16 2 ...)` after rebuilding the static libgerbil
  closure.
- The ASP provider linked as an arm64 Mach-O executable with dynamic system,
  OpenSSL, zlib, and sqlite dependencies; no `-static`/`crt0.o` failure.
- Real ASP HTTP JSON acceptance: `MODULE-OK`, `HARNESS-OK`, `OK`.
  It covered bootstrap, health, runtime requests, concurrent connections,
  shutdown, and negative contracts. The 128 loopback samples reported P95
  2631 microseconds; the 16-connection sample reported P95 10536 microseconds.

## Separate integration gap

The ASP root Just recipe currently expects the provider under
`build/workspace-provider/bin`, while the official package build materializes
`.gerbil/bin/asp-gerbil-scheme`. That artifact-path ownership mismatch is not
an HTTP runtime failure and is intentionally not hidden by these upstream
patches.
