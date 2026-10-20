# Public judge VM: prepare, run, verify

This is a **synthetic public demo**, not production banking. Target: a fresh **Ubuntu 24.04 amd64 or arm64** VM, systemd, a fixed DNS hostname, TCP 80/443 reachable. No Docker, cloud account automation or public deployment has been performed by this recipe's author. Hosting rationale: [owner's decision](hosting-options.md). The operator must configure DNS and cloud firewall rules and cap the API key at the provider.

## Install

Use an SSH key. Choose the hostname once: passkeys bind to it. Point its A/AAAA records at the VM; remove a stale AAAA record if IPv6 is not routed. Open TCP 80/443 in the cloud security rules. Allow your SSH port. Keep FISCO (8545–8548 and node/SDK ports), Watchman (8084/9094), API (8000), Next (3000) and Caddy admin off the public network.

```bash
sudo apt-get update && sudo apt-get install -y git make
sudo git clone --branch main https://github.com/thanhdvu/bursarbridge.git /opt/bursarbridge
sudo install -m 600 /opt/bursarbridge/infra/deploy/.env.example /root/bursarbridge.env
sudoedit /root/bursarbridge.env
# Set a dedicated OpenAI/Anthropic API key with a hard spend ceiling.
# Never put the owner's ChatGPT-login proxy/key on this VM.
cd /opt/bursarbridge
sudo bash infra/deploy/install.sh --hostname demo.example.org --env-file /root/bursarbridge.env --plan
sudo make deploy DEMO_HOST=demo.example.org DEPLOY_ENV=/root/bursarbridge.env
```

`--plan` validates arguments and describes the target without installation. The real recipe installs signed Caddy apt packages, Node 22.23.3 (official checksum manifest, architecture selected), uv 0.12.13 and pnpm 10.33.2; builds frozen Python/web dependencies and Solidity; configures native FISCO/Watchman; builds web **live** mode; installs systemd units and the Caddyfile. It enables UFW with TCP 22/80/443 (set `SSH_PORT` if yours differs). It never configures the cloud firewall or DNS. Do not run it on a machine hosting unrelated services.

The external env file is parsed as data, never shell-sourced. Only allowlisted settings enter `/etc/bursarbridge/api.env` (root-only 0600); no key goes into the Caddy config, web env, web build or Git. RP ID and exact origin are derived from the hostname, e.g. `demo.example.org` and `https://demo.example.org`. The API binds loopback and trusts forwarded headers **only from loopback**. Caddy overwrites client forwarding headers; adding another upstream proxy requires a new trust review.

## Several judges and a finite budget

Each browser receives a signed **Secure, HttpOnly, SameSite=Lax** cookie and its own SQLite ledger, issuer credentials, sessions, passkeys, audit log, clock and family. Cookie lifetime matches the idle window and is renewed on activity, avoiding a stale multi-day cookie after sandbox expiry. Reset/Freeze/tamper affect only that browser's sandbox. Different browsers/devices deliberately do not share a family; use the persona surfaces in one browser to demonstrate the family. This avoids surprising IP grouping on shared networks. Caddy bootstraps the cookie on the HTML request **before parallel persona logins**. Direct API clients should bootstrap and retain cookies before creating sessions.

HTML bootstrap only sets a signed browser cookie; only POST /session allocates a family sandbox. Defaults: 128 sandboxes; expire after 6 idle hours; creation limits 10/IP/minute, 120/IP/hour, 500 globally/hour and 2000 globally/day (PUBLIC_NEW_PER_IP_MINUTE, PUBLIC_NEW_PER_IP_HOUR, PUBLIC_NEW_GLOBAL_HOUR, PUBLIC_NEW_GLOBAL_DAY); 600 requests/IP/minute; 3 agent messages/visitor/minute and 30/hour, plus 30/IP/minute. All POSTs are bounded at 30/visitor/minute, 90/IP/minute and 300/global/minute; explicit reset/anchor control is three/visitor/minute. Public clock jumps are at most 31 combined simulated days per request to bound scheduled work. Live requests/streams and scenario runs are bounded (one runner globally, two runs/visitor/hour). State is capped per sandbox generation at 30 document attempts, 50 thread attempts, 200 message attempts and 500 POST attempts; Reset does not reset these counters. Admission and hosted-call counters survive restarts and resets. At capacity, retire the longest-idle sandbox, excluding in-flight requests and activity within at least five minutes (PUBLIC_SANDBOX_PROTECT_MINUTES can increase this). If all slots are protected, return 503 with Retry-After; rate limits return 429. API clients receive JSON and browsers accepting text/html receive a human retry page. Retired visitors start afresh at next login; existing live capacity/TTL overrides are preserved. This is abuse resistance, not DDoS protection or production IAM. The public judge persona controls only its own fictional sandbox. Public PDFs run outside the ledger/event loop in a Linux worker with 512 MiB address space, three CPU seconds, five-second timeout and two parser slots; it inherits no LLM key. Text uploads are limited to 12 KB. This mitigates parser resource abuse, not parser code-execution vulnerabilities: the worker still has the service UID, so only fictional documents belong here. Non-Linux public smoke mode allows trusted bundled PDFs only.

Hosted calls: **500/day, 100/hour, two concurrent** by default, counted per provider invocation (normally two per conversation turn). Exhaustion, timeout, 429, malformed output or provider outage uses `scripted_fallback` for that turn; it does **not** freeze the family. A 60-second shared provider cooldown avoids hammering an exhausted service. The deterministic engine, consent, cap, provenance, sanctions and bank checks still decide; chain failures, user Freeze and attack circuit breakers retain their money protections. The provider's own prepaid/spend cap is still essential: request counts are not a dollar guarantee. Do not auto-reload credit.

`GET /bbapi/health` reports configured provider, effective provider/degraded state, safe `llm.lastError` and `screeningMode`. SSE tokens include `source` and optional `fallback {provider,phase,code,httpStatus,at}` for a small badge. Logs use safe codes, never raw provider bodies/keys. Web consumers must display the source; an `openai` health configuration alone is not a hosted success. Re-evaluate any cheaper public model: only the locally recorded model has live conversation evidence.

## Validate before publishing the link

```bash
sudo systemctl status bursarbridge-{infra,api,web} caddy --no-pager
curl -fsS https://demo.example.org/bbapi/health
sudo journalctl -u bursarbridge-api -n 30 --no-pager
sudo ss -lntp
cd /opt/bursarbridge/services/api
sudo .venv/bin/python ../../infra/deploy/check.py hosted
```

The check helper reads root-only `/etc/bursarbridge/api.env` as data, drops to the service user and executes the eval; keys never enter command arguments or a shell. A keyless run is explicitly not hosted validation. For CLI judging, stop API first, then run the helper with `judge` instead of `hosted`; restart API afterward. Public `/scenarios/run` shares the API's serialized signer and is admission-limited.

Acceptance gates: two separate browsers concurrently complete requests; resetting A leaves B signed in; four persona surfaces in A share one journey; fake invoice denied, clean refusal still works; real passkey on the fixed HTTPS hostname; force a provider 429/zero local hosted budget and see labelled scripted continuation; verified receipt/root anchors; `curl -N` shows progress immediately; reboot VM and repeat. Also test from a mainland network and a phone over cellular. **A cloud deployment, public certificate, reboot, native arm64 VM and human passkey must be verified on the actual VM before the link is called accepted.**

## Operations and fallback

`systemctl restart bursarbridge-api` preserves sandboxes and budgets. The installer updates in place and stops API/web before rebuilding: use a maintenance window, retain the input env and state backup, and do not blindly pull while serving. Back up `/var/lib/bursarbridge` and `services/api/runtime` as private operator data; never publish keys/cookies/credentials. Do not run `make evidence` on the serving VM: it resets the team's chain and invalidates active registrations. Use a separate verification environment.

Caddy routes `/bbapi/*` straight to `/api/*`, with `flush_interval -1`, no encoding directive and no upstream Accept-Encoding. API SSE bypasses Next entirely. The API is single-worker by design; adding workers would defeat in-memory concurrency/cooldown coordination and needs a different architecture.

Mock-only fallback: in a separate web build use `NEXT_PUBLIC_API_MODE=mock` and `pnpm build` with `apps/web` as project root, then publish through the owner's chosen web host. No backend key or chain endpoint belongs in that build. Keep it a separate clearly MOCK link; this recipe does not create a hosting account or claim automatic live-to-mock UI failover.

Optional local proxy drill (no cloud, hosted calls or system CA installation): from `services/api`, run `uv run --frozen python scripts/public_proxy_smoke.py`. It downloads checksum-verified Caddy 2.11.7 and uses isolated ports 8016/8017/19443; those ports must be free. The report is written under ignored `runtime/`.

Primary configuration references: [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [body limits](https://caddyserver.com/docs/caddyfile/directives/request_body), [official installation](https://caddyserver.com/docs/install), [Uvicorn proxy trust](https://www.uvicorn.org/deployment/), [Node release manifests](https://nodejs.org/download/release/v22.23.3/).

