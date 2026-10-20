# Windows named-tunnel test link

Public link: `https://bursarbridge.pages.dev`, a Cloudflare Pages Function
that proxies every request to the tunnel host `https://bursarbridge.noamofficial.vn`
(which also still works). The proxy adds the visitor's IP with a shared secret
(`PUBLIC_PROXY_SECRET`), and passkeys bind to whichever allowed origin the
visitor uses (`WEBAUTHN_ORIGIN`). Proxy source: `D:\BursarBridge-pages`. This explicitly
uses the owner's local CLIProxy on **8318**, with durable shared LLM caps and
labelled scripted fallback. The [Ubuntu VM recipe](ubuntu-vm.md) remains the
official-judge path with a dedicated capped API key; its proxy rejection is intact.

## Install and operate

Prerequisites: owner's Windows login, WSL2 Ubuntu (default distro, or pass
`-WslDistro Ubuntu-24.04`), Git, uv, Node and pnpm on PATH. No Docker. Merge the
Round 8 backend into **origin/main** first: deployment refuses a main release
without the explicit local-proxy guard. It never deploys a development overlay.

From `D:\BursarBridge-api` (the env path is read privately, never printed):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infra/windows/live.ps1 install -EnvFile services/api/.env
```

This clones main into `D:\BursarBridge-live`, builds Next with `live` at build time,
deploys separate real FISCO contracts, and starts Task Scheduler's
**BursarBridge-Live** supervisor. No LLM key enters Next's build environment.
The runtime Node executable is copied into private live tools, so switching the
development Node version cannot replace the running web's executable.
Use the frozen controller, which survives development changes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:/BursarBridge-live-state/tools/live.ps1 check
# Same command with: start | stop | update | enable-logon
```

`update` requires a clean live checkout, stops only this stack, fast-forwards main,
rebuilds and restarts. Failed build restores the previous code/build; sandbox
state and keys stay intact. Build backups are retained in the private state root.
Updates cause a short maintenance window. Logs: `D:\BursarBridge-live-state\logs\`
(`supervisor.log`, `api.log`, `web.log`, `caddy.log`). `api.env` and sandbox data
are ACL restricted to the owner and SYSTEM, outside Git. Live signer/deployment
files stay in the live checkout's ignored `services/api/runtime/`; never delete it.

## Owner's single tunnel step

In the Cloudflare dashboard, open the **existing named tunnel**, add public hostname
**bursarbridge.noamofficial.vn**, service type **HTTP**, URL **127.0.0.1:18780**.
Keep the original public Host header. No cloudflared service restart, local tunnel
configuration, DNS credential or port 8317 change is needed. The launcher never
reads or changes the cloudflared service/config, Hermes or the Zalo bridge.

## Isolation and edge behavior

All listeners bind loopback: Caddy **18780**, API **18000**, Next production
**13700**; dedicated WSL FISCO Web3 **18545-18548**, native RPC **18500-18503**,
P2P **30310-30313**; dedicated Watchman **18084**, admin **19094**. Linux state is
`~/.local/share/bursarbridge-live/`. No dev chain, signer, contract, ledger, service
port or Watchman process is shared. Only a verified Watchman build cache may be
copied at installation; the live executable/config/data are then independent.
Dev API stays on 8000. Dev tests/evals/evidence cannot reset this chain.

Caddy accepts HTTP only from loopback; Cloudflare terminates public TLS. It trusts
`Cf-Connecting-Ip` only from the local tunnel hop, overwrites X-Forwarded-For and
scheme (https), and discards visitor-supplied X-Real-IP/return headers. Uvicorn
trusts forwarded headers only from loopback Caddy. Local machine users/processes
remain trusted; this is not isolation from a hostile administrator on the owner PC.
Passkey RP/origin are the fixed public hostname / exact HTTPS URL. Secure HttpOnly
cookies establish a stateless browser identity on the HTML request before persona logins. Only a POST to `/session` allocates a sandbox, so link previews do not consume one. Capacity retires the longest-idle sandbox, never in-flight or active within five minutes. See the API `.env.example` for configurable creation caps; existing live overrides are retained.
No API/session/SSE caching, gzip or proxy buffering; `/bbapi` goes directly to the
API. Agent and event streams send one-second comments even when otherwise quiet.
Caddy's native SSE flushing is used; negative `flush_interval` is deliberately
absent so closing a browser also releases its upstream stream and capacity slot.

Keep Windows awake and the owner logged in: the supervisor is a passwordless
**interactive owner** scheduled task so WSL remains available. `enable-logon`
optionally starts it at that owner's next login (not before login). A locked
screen is fine; sleep, logout, reboot without login and local-proxy outage affect
availability. Proxy outage/exhaustion degrades conversation; money checks still
fail closed. No new boot task is enabled automatically.

Windows public PDF parsing retains the safe sample-only gate: use bundled synthetic
PDFs (or bounded synthetic UTF-8 text), never real personal documents. The Linux VM
supports the bounded arbitrary-PDF worker. Each browser is a separate family sandbox;
two phones cannot co-approve the same family unless they share the same browser
sandbox. This is a labelled persona demo, not a real family invitation system.

PO acceptance after the owner adds the route: real hostname over cellular, two
private browser contexts, live progress and quiet heartbeat, a real public-host
passkey, full payment/refund/attack journey and a restart without lost state.
Local simulated Cloudflare headers do not prove public routing or phone acceptance.

References: [Cloudflare client headers](https://developers.cloudflare.com/fundamentals/reference/http-headers/),
[origin hostname parameters](https://developers.cloudflare.com/tunnel/reference/origin-parameters/),
[Caddy proxy trust](https://caddyserver.com/docs/caddyfile/options),
[Task Scheduler settings](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset).
