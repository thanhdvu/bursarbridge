# API runbook

BursarBridge helps a family pay verified tuition and recover a visa-refusal refund to the original payer. The bank, university and accounts are MOCK. Start with the [root README](../../README.md) for the family story, or the [local setup guide](../../docs/deploy/local.md) for API and production web commands.

## Start and check

Run from `services/api`:

```powershell
uv sync --frozen
uv run --frozen python -m bursarbridge.cli dev --offline
```

Keyless mode forces scripted dialogue, local commitments and synthetic screening. For native FISCO/Watchman, use `cli dev` without `--offline` after following the full setup guide. `--port 8001` selects another API port; `--wsl-distro Ubuntu-24.04` selects the WSL distro. The default is the user's default distro. Use one API worker.

The API base is `http://127.0.0.1:8000/api`. `/api/docs` serves Swagger; `/api/openapi.json` is the generated contract. `/api/health` reports `llmProvider`, `chainMode`, `screeningMode` and `llm.status/lastError`. A configured provider name alone does not prove a successful hosted reply. Inspect each reply's `source`; `scripted_fallback` includes a safe fallback reason. Planner failures keep conversation available in both dev and public modes.

Private configuration belongs in `.env`, loaded only from this directory. Process env wins. [.env.example](.env.example) documents the settings; never commit its populated copy.

| Setting | Operator choice |
|---|---|
| `LLM_PROVIDER` | `auto` selects Anthropic if keyed, then OpenAI, otherwise scripted. Set `scripted` for deterministic runs. |
| `OPENAI_BASE_URL`, `OPENAI_MODEL` | Official `/v1` root by default. Owner's test proxy: `http://127.0.0.1:8318/v1`, model `gpt-6.1-sol`; strict Responses output was checked. |
| `OPENAI_TIMEOUT_SECONDS` | Default 60; bounded 5-120 seconds. Failures fall back visibly; no automatic paid retry. |
| `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN` | Default `localhost`; exact HTTP origins on 3000 and 3700. Public deployment derives the fixed HTTPS origin and hostname. |
| `CHAIN_MODE`, `SCREENING_MODE` | Full launcher discovers FISCO; Watchman uses native government OFAC. `--offline` overrides both to local/synthetic. |
| `DATABASE_URL`, `DATA_DIR` | Keep each serving instance's SQLite state, issuer key, bank state and deployment/signing files together and private. |
| `PUBLIC_DEMO` | `1` selects visitor sandboxes, durable budgets and public admission controls; use the deployment controller. |

## Operate the family journey

Create a persona session with `POST /session`, retain the returned bearer token, and use the [API contract](../../docs/API.md). Public clients must retain the bootstrap cookie before parallel persona logins. Every browser has its own family; reset never resets another visitor.

The clock starts at 12 January 2027, inside the first signed tuition window. The judge can advance it with `/clock/advance`; public jumps are capped at 31 days per request. A payment is `sent` during its 30-minute simulated hold and matches after the clock passes it. The refusal promise is 16 March, relative to classes starting 2 March. Dorm/NHIS are external obligations, not part of the tuition refund.

Freeze cancels cancellable outgoing holds, pauses outgoing approvals and suspends valid signed mandates temporarily. Incoming claims/refunds continue. Parent passkey Unfreeze restores valid signed limits, without replaying cancelled transfers or reviving revoked/expired authority. A refusal before payment cancels pending tuition intent and notifies Dad within the family app; it opens no refund.

For a slow chain, inspect `/chain/status`, the `frozenReason` field on `/me`, and audit/events. Reset commits locally and returns registration/anchor status; background work retries. Money remains closed until required chain checks recover. Never replace missing receipts with local-looking transaction hashes.

## Verify and regenerate

```powershell
uv run --frozen pytest -q
uv run --frozen python -m bursarbridge.cli conversation-eval --provider scripted --output runtime/conversations.json
uv run --frozen python -m bursarbridge.cli judge --offline --output runtime/judge-offline
```

`make judge` from the repository root runs the full FISCO/Watchman journeys. `make evidence` regenerates the package on a fresh chain: stop any API using that checkout and run only in an isolated verification environment. It resets local chain state. Then verify with `uv run --frozen python scripts/verify_audit.py --rpc http://127.0.0.1:8545`. See the [test catalogue](../../docs/deliverables/test-cases.md) and [evidence index](../../evidence/README.md) for current results and what the logs prove.

Regenerate OpenAPI with `uv run --frozen python -m bursarbridge.cli openapi`. Generate fixture PDFs with `cli fixtures`; the evidence build also writes them to `evidence/fixtures/`.

## Serving instances and recovery

Local development uses port 8000. The public Windows instance uses a separate checkout/runtime, production Next, loopback Caddy and dedicated FISCO/Watchman. Operate it through the [Windows controller](../../docs/deploy/windows-tunnel.md); never run dev tests, evidence resets or ad hoc upgrades inside the serving checkout. Logs live under `D:\BursarBridge-live-state\logs`.

For a local failure, inspect your redirected server log and health first. Preserve the private database/runtime before reset. Do not delete chain signer/deployment files while keeping the ledger, or point a ledger at a replacement chain and claim old receipts still verify. Follow the [Ubuntu VM guide](../../docs/deploy/ubuntu-vm.md) for systemd logs and public deployment limits.

Implementation history is recorded in the [API Changelog](../../docs/API.md#changelog); this file describes current operation.

