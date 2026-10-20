# Public deployment for the judges: hosting options and decision

Status: decision memo, 17 Oct 2026. Nothing has been signed up for or deployed. Every price and limit below was read on the provider's own page on 17 Oct 2026 (see Sources).

## Recommendation

**Primary: one Oracle Cloud Always Free Arm VM runs everything.** VM.Standard.A1.Flex with 2 OCPU and 12 GB (the whole Always Free A1 allowance), Ubuntu arm64, home region Singapore (or Seoul). It runs the 4 FISCO nodes, Watchman, FastAPI and `next start`, with Caddy in front for automatic Let's Encrypt HTTPS on a free DuckDNS hostname (for example `bursarbridge.duckdns.org`). The VM never sleeps, so a judge's one click works, and the bonus-relevant chain is real FISCO.

**LLM: a separate, capped API key. Never the owner's ChatGPT login.** Use an OpenAI API key with US$10 prepaid and auto-reload turned off, on the same Responses code path that is already tested. Alternative: an Anthropic key with a US$10 workspace spend limit (Haiku 5.5). If the budget runs out, the app must fall back to scripted replies (needs a backend change, see Gotchas).

**Fallback that cannot break: Vercel Hobby, `apps/web` in mock mode.** The UI and journeys run in the browser and are labelled MOCK. No backend, free, no sleep. Put this as the second link in the README for when the VM is down.

**Total cost: US$0 hosting + US$5–10 one-off LLM credit.** Oracle needs a credit/debit card for identity verification. Optional own domain instead of DuckDNS (price not researched).

If Oracle rejects the card or has no A1 capacity: run the same VM recipe on AWS (US$100 credit, 6-month free plan) or on Azure for Students (US$100, no card, but the student product reviewer's student account). Pick a 2 vCPU / 4 GB+ instance and check its price against the credit first. **Last-resort stopgap for Mon–Tue only:** the owner's laptop behind a *named* Cloudflare Tunnel (needs a domain on Cloudflare). A quick tunnel (trycloudflare) does not support SSE.

## Measured footprint (laptop WSL, 17 Oct, idle)

FISCO: 4 nodes x ~56–60 MB RSS, **each ~25% of a core even when idle** (about 1 core in total). Watchman: 176 MB. API: ~70 MB. Total with Next.js is under 1 GB of RAM, but about 1 core is busy all the time.

That constant CPU rules out 0.1-vCPU free tiers and makes per-vCPU billing expensive. On Railway, 1 vCPU running continuously is ~US$20/month. It is fine on a 2-OCPU A1 and also keeps Oracle's idle-reclaim rule from triggering. FISCO v3.17.1 publishes `fisco-bcos-linux-aarch64` and `build_chain.sh` selects it on aarch64. `infra/watchman/install.py` hard-codes `linux-amd64` Go and needs a one-line arch fix (backend owner).

## Comparison

| Option | Cost now → later | Sleep / cold start | Fits FISCO + Watchman + API + web? | Persistence | HTTPS | Signup friction | Setup | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Oracle Always Free A1** (2 OCPU, 12 GB, 200 GB disk, 10 TB egress) | $0 → $0 (Always Free) | None. Idle VMs (p95 CPU, network and memory all <20% over 7 days) may be reclaimed; FISCO keeps CPU above that | Yes, all in one box | Block volume | Caddy + DuckDNS/own domain | Card for verification; home region fixed; "out of host capacity" possible | 5–8 h | **Primary** |
| Vercel Hobby (web only) | $0, non-commercial use only | No server to sleep | Web only; functions max 300 s | n/a | `*.vercel.app` | GitHub login | 0.5 h (mock) | **Fallback (mock)**; live mode would also need an API host |
| Owner laptop + named Cloudflare Tunnel | $0 + domain | Down whenever the laptop is | Yes (as today) | Local | Cloudflare (domain must be on Cloudflare); 125 s proxy read timeout, so heartbeats needed | Domain | 1–2 h | Stopgap only |
| Cloudflare quick tunnel | $0 | No uptime guarantee; URL changes on every restart | — | — | trycloudflare | none | 0.2 h | **No**: no SSE support |
| AWS free plan | $100 credit (up to $200), account closes after 6 months or when the credit is used up | None | Yes, on a 4 GB instance paid from the credit | EBS | Caddy | Card | 5–8 h | Backup VM |
| Azure for Students | $100 credit for 12 months, no card; B1s / B2pts v2 / B2ats v2 750 h | None | 1 GB burstable VMs are too tight for ~1 core of steady FISCO CPU; use the credit for a 4 GB VM | Disk | Caddy | Student email (the student product reviewer) | 5–8 h | Backup VM, card-free |
| GCP | $300 / 90-day trial; Always Free: e2-micro (US only), Cloud Run 180k vCPU-s | Cloud Run scales to zero (cold start) | e2-micro 1 GB: no. Cloud Run: API only, local chain, no disk state | Ephemeral on Cloud Run | `*.run.app` | Card | 3–4 h | No |
| Fly.io | No free tier (trial: 2 machine-hours or 7 days); 2 GB shared-cpu-1x ≈ $12.70/month | Optional | Possible in one machine, but a shared CPU vs FISCO's steady load is a risk | Volumes | `*.fly.dev` | Card after trial | 6–10 h | Paid backup |
| Railway | $5 trial / 30 days; Free = $1/month with 0.5 GB; Hobby $5/month + ~$20/vCPU-month | n/a | Free tier: no. Hobby: ~$25+/month with FISCO | Volumes | Yes (no custom domain on Free) | None for trial | 4–6 h | No |
| Render free | $0, 750 h | **Spins down after 15 min, ~1 min to wake** | No (no disk, small instance) | None | Yes | — | 2 h | No (fatal cold start) |
| Koyeb free | $0, 1 instance with 512 MB / 0.1 vCPU, Frankfurt or Washington | **Scales to zero after 1 h** | No | No volumes | Yes | — | 2 h | No |
| HF Spaces | Docker Spaces now **require PRO** to create; CPU Basic 2 vCPU / 16 GB | Sleeps after 48 h idle | Technically yes | **Not persistent** | `*.hf.space` | Paid plan | 6+ h | No |

Untested risk: the organiser and possibly the judges are in mainland China. Whether `*.vercel.app` and `duckdns.org` are reachable there is **not verified**. Before submission, ask someone on a mainland network to open both links. An own domain on the Singapore VM is the safest bet.

## LLM decision

- **Do not expose CLIProxyAPI or the ChatGPT login.** OpenAI's Terms of Use (effective 1 Jan 2026) say you "may not share your account credentials or make your account available to anyone else". They also forbid "Automatically or programmatically extract data or Output" and circumventing rate limits. A public link would let any visitor spend the owner's personal quota and risks a ban of his personal account. It also only works while his laptop is on (the code allows plain HTTP only to loopback). Keep the proxy for the recorded video and local demos only.
- **Public link: a dedicated API key with a hard budget.**
  - *OpenAI API* (lowest risk: same `/responses` + strict `json_schema` path). Prepaid, minimum US$5. Auto-reload is **on by default, so turn it off**. When the credit is gone, requests return `credit_balance_exhausted`. Small overruns can appear as a negative balance.
  - Price: `gpt-4.1-mini` $0.40/$1.60 per MTok, `gpt-5-mini` $0.25/$2.00. Assuming ~3K input + 0.4K output tokens per call and 2 calls per turn, one turn costs ≈ US$0.004, so US$10 ≈ 2,500 turns.
  - Re-run `conversation-eval --provider hosted` on the cheap model first: only gpt-6.1-sol was evaluated (median 7.2 s per case). If it fails, use a stronger model under the same cap.
  - *Anthropic* (already supported, `ANTHROPIC_API_KEY`, `output_config.format` is GA). Haiku 5.5 is $0.10/$0.50 per MTok and you can set a spend limit below your tier's cap. It has never been run live, so run the hosted eval before trusting it.
- **Free options exist but need backend work.** Groq has a free plan and a beta Responses API with strict schema on `openai/gpt-oss-120b`. But it lists `store` as unsupported (our request sends `store:false`) and caps that model at 8K TPM / 1K requests per day. Gemini's OpenAI-compatible endpoint documents only Chat Completions. Not worth it before Tuesday.
- **Scripted mode stays the floor.** If the key is missing or exhausted, the public link still works deterministically, provided the circuit-breaker change below is made.

## Gotchas (WebAuthn, HTTPS, SSE, shared demo)

1. **WebAuthn needs a domain name over HTTPS.** The spec allows an `https` origin, or `http` only on `localhost`. RP IDs must be a domain, so a bare IP or `http://` VM will fail. Set `WEBAUTHN_RP_ID=bursarbridge.duckdns.org` and `WEBAUTHN_ORIGIN=https://bursarbridge.duckdns.org` exactly (no port, no trailing slash). Passkeys are bound to the RP ID, so changing the hostname later invalidates every registered passkey. Pick the name once.
2. **Let's Encrypt and free hostnames.** Limit: 50 certificates per registered domain per week, where the registered domain is decided by the Public Suffix List. `duckdns.org` is on the PSL (you get your own bucket); `sslip.io`/`nip.io` are not (shared with everyone), so avoid them. Caddy needs ports 80/443 reachable and a persistent data dir. Open 80/443 in both the OCI security list and the VM firewall.
3. **SSE through proxies.**
   - Route `/bbapi/*` in Caddy straight to `127.0.0.1:8000/api/*` instead of through Next's rewrite. `next start` gzips responses by default, which can buffer streams, or set `compress:false`.
   - Caddy flushes `text/event-stream` immediately. Do not add `encode` on that route.
   - The API already sends `X-Accel-Buffering: no` and `Cache-Control: no-store`, and heartbeats on `/events`.
   - Behind Cloudflare, an idle stream dies after 125 s. Quick tunnels do not carry SSE at all.
4. **Rate limit becomes global behind a proxy.** `main.py` keys its 600 req/min bucket on `request.client.host`, which is `127.0.0.1` for every visitor behind Caddy. Run uvicorn with proxy headers trusted only from 127.0.0.1, and add a small per-IP cap on agent messages to protect the LLM budget.
5. **An LLM failure freezes the family.** `agent.py`/`main.py` set `frozen=True` with `llm_circuit_breaker` when planning fails. An exhausted key or a 429 would freeze the judge's demo. For the public deployment, degrade to the scripted planner without freezing; keep the freeze for chain outages. *(Backend brief.)*
6. **Shared state.** All visitors share one demo store, and `DEMO=1` exposes reset/clock to everyone. One judge's reset logs the others out. Add a README note ("press Reset demo first; shared sandbox"), and consider a nightly automatic reset.
7. `NEXT_PUBLIC_API_MODE` is inlined at **build** time. Build the VM web with `live` and the Vercel fallback with `mock`.

## Steps for the recommended path

1. Owner: create the Oracle Cloud Free Tier account (home region Singapore, which cannot be changed), with the card he chooses. Stay within 2 OCPU / 12 GB: exceeding the A1 allowance after the trial disables the A1 instances. Log in monthly, since accounts idle for 30+ days may be suspended.
2. Create the A1.Flex VM (2 OCPU, 12 GB, Ubuntu arm64, 100 GB boot) and a reserved public IP. Open TCP 80/443 in the security list and the instance firewall. SSH by key only.
3. Register `bursarbridge.duckdns.org` (or an own domain) pointing to the IP.
4. Backend brief (Codex):
   - arm64-aware Watchman install;
   - proxy headers + per-IP agent cap;
   - scripted fallback without freeze on provider error;
   - a `deploy/` folder with systemd units for API, web and Caddy, a Caddyfile and an env template (no secrets).
5. On the VM: install uv, Node 20 + pnpm, then clone the repo. Set `.env` on the VM only: `DEMO=1`, `WEBAUTHN_*`, `LLM_PROVIDER=auto`, `OPENAI_API_KEY`, `OPENAI_MODEL`. Run `cli dev` once to bootstrap FISCO, deploy contracts and build Watchman, then switch to the systemd units. Run `pnpm build` with `NEXT_PUBLIC_API_MODE=live`.
6. Create the LLM key: US$10, auto-reload off. Run `conversation-eval --provider hosted` on the VM.
7. Accept as a judge would, on a phone over 4G and a laptop: `/demo` reset, full Linh/Minh journey, a real passkey, Lan co-sign, trust-center tamper/verify, and a FISCO tx visible. Check that SSE events arrive live, reboot the VM and repeat.
8. Deploy the mock fallback to Vercel (root `apps/web`, `NEXT_PUBLIC_API_MODE=mock`). Put both links in the README, plus "shared sandbox, press Reset demo".
9. Until judging ends: an uptime check (any free pinger) on `/bbapi/health`, and a monthly look at the LLM balance.

## Sources (all opened 17 Oct 2026)

- Oracle Always Free resources (A1 = 1,500 OCPU-h + 9,000 GB-h = 2 OCPU/12 GB; idle reclaim; home region; capacity): https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Oracle Free Tier FAQ (card for verification; US$300/30-day trial; A1 over-allowance disabled after trial; 30-day idle accounts): https://www.oracle.com/cloud/free/faq/
- Render free: https://render.com/docs/free · Koyeb instances: https://www.koyeb.com/docs/reference/instances · Fly.io pricing: https://docs.fly.io/about/pricing · Railway pricing: https://railway.com/pricing
- GCP free features: https://docs.cloud.google.com/free/docs/free-cloud-features · AWS Free Tier: https://aws.amazon.com/free/ · Azure for Students: https://azure.microsoft.com/en-us/free/students
- Hugging Face Spaces overview and hardware/sleep: https://huggingface.co/docs/hub/spaces-overview , https://huggingface.co/docs/hub/spaces-gpus
- Vercel Hobby (updated 2026-09-14): https://vercel.com/docs/plans/hobby · Vercel rewrites: https://vercel.com/docs/rewrites
- Cloudflare quick tunnels: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/ · named tunnels: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/ · 524 timeout: https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/
- Let's Encrypt rate limits: https://letsencrypt.org/docs/rate-limits/ · Public Suffix List: https://publicsuffix.org/list/public_suffix_list.dat · DuckDNS: https://www.duckdns.org/ · Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https · Caddy reverse_proxy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy · Next.js compress: https://nextjs.org/docs/app/api-reference/config/next-config-js/compress
- WebAuthn Level 3 editor's draft (RP ID scope; https or localhost; domain-only hosts): https://w3c.github.io/webauthn/
- FISCO BCOS v3.17.1 release assets (linux-aarch64): https://github.com/FISCO-BCOS/FISCO-BCOS/releases/tag/v3.17.1
- OpenAI Terms of Use (effective 1 Jan 2026): https://openai.com/policies/row-terms-of-use/ · OpenAI prepaid billing: https://help.openai.com/en/articles/8264644 · OpenAI pricing: https://developers.openai.com/api/docs/pricing · supported countries: https://developers.openai.com/api/docs/supported-countries
- Anthropic spend limits: https://platform.claude.com/docs/en/api/rate-limits · pricing: https://platform.claude.com/docs/en/about-claude/pricing · structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs · supported countries: https://www.anthropic.com/supported-countries
- Groq Responses API: https://console.groq.com/docs/responses-api · rate limits: https://console.groq.com/docs/rate-limits · structured outputs: https://console.groq.com/docs/structured-outputs · Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
