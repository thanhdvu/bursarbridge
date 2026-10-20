# Run a local copy

A parent should be able to try the family journey without buying an API key or setting up a chain. Start with the keyless path. The full path adds actual FISCO commitments and native government-list screening; the bank and university remain MOCK in both.

## Keyless API and family screens

Requirements: Git, uv with Python 3.12, Node.js 20+ and pnpm 10 for the web. The recorded check used Python 3.12.11, Node 24.18.0 and pnpm 10.33.2 on Windows. Installing dependencies needs internet access. Make is optional; the commands below also work in PowerShell.

```powershell
git clone https://github.com/thanhdvu/bursarbridge.git
cd bursarbridge/services/api
uv sync --frozen
uv run --frozen python -m bursarbridge.cli dev --offline
```

`--offline` explicitly selects scripted conversation, local hash commitments and synthetic screening. No `.env`, hosted key, WSL or Docker is needed. The API listens on loopback port 8000. Check `http://127.0.0.1:8000/api/health`: expect `llmProvider: scripted`, `chainMode: local`, `screeningMode: synthetic`. Local mode returns no invented chain transaction hashes.

In a second terminal, from the clone's `apps/web` directory:

```powershell
pnpm install --frozen-lockfile
$env:NEXT_PUBLIC_API_MODE='live'
$env:NEXT_PUBLIC_API_URL='/bbapi'
$env:BB_API_ORIGIN='http://127.0.0.1:8000'
$env:NEXT_TELEMETRY_DISABLED='1'
pnpm build
pnpm exec next start -H 127.0.0.1 -p 3700
```

Open `http://localhost:3700`. The production web forwards `/bbapi` to the API; it contains no LLM key. Use the supplied personas and sample PDFs. The default passkey RP ID is `localhost`, with exact origins `http://localhost:3000` and `http://localhost:3700`. `DEMO=1`, selected by the dev launcher, also permits the visibly labelled demo authenticator. Use Ctrl+C in each terminal to stop your own processes.

To use a different API port, append `--port 8001` to `cli dev` and change `BB_API_ORIGIN` accordingly before starting Next. Keep the web at an allowed origin or configure `WEBAUTHN_ORIGIN` and `WEBAUTHN_RP_ID` before starting the API.

## Reproduce the checks

In `services/api`, with no serving process using the same verification state:

```powershell
uv run --frozen pytest -q
uv run --frozen python -m bursarbridge.cli conversation-eval --provider scripted --output runtime/conversations.json
uv run --frozen python -m bursarbridge.cli judge --offline --output runtime/judge-offline
```

The [test catalogue](../deliverables/test-cases.md) states the latest results and limits. Each journey gets its own temporary SQLite state. `runtime/judge-offline` is separate from the committed FISCO evidence.

## Full local stack: native FISCO and Watchman

On Windows, install WSL2 Ubuntu and ensure `python3`, `curl` and `tar` are available in it. Use the distro's normal package manager for missing tools. Git, uv, Node/npm and pnpm must be available on Windows. On a dedicated native Linux host the same launcher runs shell scripts directly. The installers select Linux amd64 or arm64; no Docker is involved.

Use a separate checkout if another demo is running. The default infrastructure uses FISCO Web3 ports 8545-8548 and Watchman 8084/9094, plus the FISCO node ports. Do not start a second set of nodes on those ports.

In `services/api`, copy `.env.example` to `.env` and keep it private. Leave `CHAIN_MODE` unset, use `SCREENING_MODE=watchman`, and choose `LLM_PROVIDER=scripted` for a keyless full stack. Then:

```powershell
uv sync --frozen
uv run --frozen python -m bursarbridge.cli dev --wsl-distro Ubuntu-24.04
```

Omit `--wsl-distro` to use the default WSL distribution. The launcher downloads FISCO 3.17.1, starts four Air nodes, compiles/deploys the contracts and starts native Watchman with the government OFAC list only. First setup can take several minutes. Runtime keys and deployed addresses stay in ignored `services/api/runtime`; retain them with the matching private state. Health should report `fisco` and `watchman`. Complete the web commands above in the second terminal.

If local services already run, reuse their endpoints without bootstrapping another node set. In the new clone, run `npm ci` and `npm run compile` in `contracts`. Back in `services/api`:

```powershell
$env:DEMO='1'
$env:CHAIN_MODE='fisco'
$env:FISCO_RPC='http://127.0.0.1:8545'
$env:SCREENING_MODE='watchman'
$env:LLM_PROVIDER='scripted'
uv run --frozen python scripts/deploy_chain.py
uv run --frozen uvicorn bursarbridge.main:create_app --factory --host 127.0.0.1 --port 8001
```

This deploys a new signer/contracts for that checkout and starts its own ledger. Point Next's `BB_API_ORIGIN` at port 8001. It shares infrastructure availability, so never reset the shared chain while either copy depends on it.

## Conversation keys and safe evidence generation

For hosted conversation, set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `services/api/.env`, choose `LLM_PROVIDER=auto`, and restart. OpenAI defaults to `https://api.openai.com/v1`; an OpenAI-compatible root can be set with `OPENAI_BASE_URL`, alongside `OPENAI_MODEL`. The owner's local test proxy uses `http://127.0.0.1:8318/v1` and `gpt-6.1-sol`. The API uses strict Responses output, a configurable 60-second timeout and labelled scripted fallback. Keep keys out of web env and build arguments. Hosted checks consume the recording link's shared quota; do not run the full hosted suite casually.

`make judge` runs the full native stack's scripted journeys. `make evidence` stops/resets this checkout's FISCO state, redeploys and regenerates the package. Run it only in an isolated verification environment with its serving API stopped. Afterwards, from `services/api`, use `uv run --frozen python scripts/verify_audit.py --rpc http://127.0.0.1:8545`. Regeneration makes new real hashes; it cannot recreate another machine's historical receipts.

## What was actually checked

The submission repository's `main` checkout installed frozen API dependencies and passed 271 tests, 80 scripted conversations, all twenty offline journeys and all twenty native FISCO/Watchman journeys. Fresh contracts and ledger state were used, and an independent verifier checked the new audit receipts. This was not a public tunnel, phone, physical passkey or real-bank test. [Logs and report](../../evidence/submission_main_20261020/README.md).

The public test link has its own checkout, ports and runtime: [Windows tunnel operations](windows-tunnel.md). The later [Ubuntu VM recipe](ubuntu-vm.md) includes Caddy/HTTPS and public budgets; cloud deployment and acceptance still require the operator.
