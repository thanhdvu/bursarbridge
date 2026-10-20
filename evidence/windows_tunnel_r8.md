# Round 8: Windows named-tunnel preparation and local verification

**Activation blocked pending PO main integration.** The deployment gate requires
a clean main checkout that includes Round 8's explicit local-proxy opt-in. At this
verification, origin/main is `943092d`, still the older v2 seed without that guard.
The PO merge request is pending. No live public API/web/Caddy or real hostname,
phone or public passkey acceptance is claimed. The owner's tunnel service/config,
port 8317/Hermes, Zalo and dev API were not changed or restarted.

Prepared: separate main checkout `D:/BursarBridge-live`, restricted private env/state
`D:/BursarBridge-live-state`, frozen control files and Node/Caddy executables,
Next production/live build, three actual dedicated FISCO contract deployments,
and demand-start Task Scheduler supervisor. Optional owner-logon startup is not
enabled. The VM recipe retains its dedicated HTTPS API-key requirement; the
temporary Windows opt-in allows exactly the owner proxy on 8318.

Use the [Windows guide](../docs/deploy/windows-tunnel.md) for start/stop/update/check commands,
ports, state, logs and the single owner dashboard route. After main includes the
current backend, update/rebuild/activate, then route the hostname and do PO phone
acceptance. The operator controller never pushes main or patches a deployment overlay.

## Checkable results

- **191 pytest tests**, ruff; six targeted tests keep the HTTP proxy opt-in narrow
  and keep API/other credentials out of the web environment.
- **49/49 scripted** and a new complete **49/49 hosted** conversation evaluation.
  [First](conversation_eval_hosted_r8_initial.json) and
  [second](conversation_eval_hosted_r8_second.json) raw hosted runs each scored
  48/49 only because C34 required the literal word “you”. Both correctly told
  Minh “Please sign…”. The existing `containsAny` criterion
  now accepts these direct polite imperatives, while retaining the exclusions for
  “your father/parent” and every policy/amount/effect assertion. No prompt,
  provider money authority, denial or consent rule was relaxed. The
  [new complete run](conversation_eval_hosted_r8.json) is not stitched retries or
  fallback counted as hosted success. Bounded lexical checks still do not prove
  unrestricted dialogue quality.
- **T01-T20 20/20** in an isolated explicit local-chain/synthetic-screening run:
  [raw outputs](windows_local_scenarios_r8/scenario_results.json). No chain hashes
  are fabricated. Existing root T01-T20/anchor evidence remains the earlier real
  Round 7 run and is not relabelled as a Round 8 real-chain run.
- [Actual Caddy edge drill](windows_tunnel_edge_r8.json): two independent cookie
  contexts on one simulated shared-network IP; bootstrap before four concurrent
  persona logins; cross-sandbox token rejection; caller-only reset; separate visitor
  message limits; canonical Cf IP buckets and ignored forged XFF. Controlled
  delayed adapter, local chain/screening and small HTML upstream isolate edge
  behavior. First step **40.9 ms**, reply **2064.3 ms**, exhausted two-call budget
  produces labelled `scripted_fallback / hosted_budget_exhausted` without freeze.
  **130.45-second** otherwise quiet event stream, **130** comments, maximum gap
  **1.03 seconds**; disconnect releases its stream slot and servers exit cleanly.
  No compression; `Cache-Control:no-store,no-transform`. Caddy's native SSE flush
  replaces negative flush intervals so upstream cancellation is preserved.
  This is a simulated tunnel, not a real Cloudflare/phone test.
  A [final short drill](windows_tunnel_final_config_r8.json) repeats the assertions
  against the final template and actual `/demo` path (43.8 ms step, clean teardown).
- [Infrastructure/build isolation](windows_tunnel_isolation_r8.json): separate
  actual genesis and signer; three real contract bytecodes and signer survive
  dedicated infrastructure stop/start; dev chain and API remain available.
  **729** production-build files checked against the actual nontrivial LLM key
  value, no match; no frontend dotenv file. Contract addresses/receipts are real
  on the distinct live chain. A temporary pinned-Node production server returned HTTP 200 for `/demo`,
  with the API rewrite bound to 18000 and Next compression disabled.
  Initial invalid hyphenated chain ID was caught
  before deployment; pre-ledger files retained, corrected to `chain8`, and bootstrap
  now verifies Web3 RPC/government-list readiness instead of trusting start-script
  exit status. No existing ledger or approved record was rewritten.
- [Task Scheduler probe](windows_scheduler_probe_r8.json): a one-shot owner-token
  task completed after its invoking tool command exited, and a Windows job closed
  its child in 12 seconds rather than its 60-second sleep. The probe task was removed.
  The actual supervisor is registered but not activated through the release gate.
  This proves scheduler execution/job cleanup, not a forced shutdown of a Codex job,
  pre-login boot availability, host sleep tolerance or an end-to-end public run.

Limits: Windows public PDFs remain bundled-sample-only (or bounded synthetic UTF-8
text); arbitrary compressed PDF isolation remains the Linux worker's responsibility.
The owner must stay logged in/awake for the passwordless interactive WSL task.
Different devices do not join one real family; browser sandboxes remain independent.
The proxy, host, shared WSL VM and administrator remain availability dependencies.
Public budgets count calls, not token/dollar spend. No real money or bank credentials.

