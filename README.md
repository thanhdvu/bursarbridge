# BursarBridge

Fintechathon 2026, PBCSF × WeBank. Topic C. Theme: "AI as a Financial Participant".

Minh is in Vietnam. His daughter Linh has been accepted by a university in Seoul, and her tuition is due while her D-2 visa is still being processed. He wants to pay the right account. If her visa is refused, he needs help getting the money home.

BursarBridge follows that whole request. It checks an issuer-signed tuition bill, asks Minh to sign the spending limit and first payment, and pays only the university-attested tuition account. After a refusal, it prepares Linh's withdrawal and refund forms, watches the school's promise date, and reconciles the return to Minh's original account. A missed promise produces a dated, student-approved follow-up and then a complaint pack for manual submission. It cannot make a university pay.

Try the family journey at [bursarbridge.pages.dev](https://bursarbridge.pages.dev). It is a synthetic demo: use the supplied fictional personas and PDFs, never real personal documents. Each browser has a separate sandbox. Switch personas within that browser to act as the family; two phones do not join one shared family. The simulated date moves through the judge's clock controls.

The current Hanbit University invoice is **7,174,000 KRW tuition**, payable in two 3,587,000 KRW instalments. Dormitory and health insurance are separate obligations, outside this payment and refund. The [technical guide](docs/deliverables/technical.md) explains the dates and authority behind the bill.

## What runs, and what is MOCK

| Runs in code | Scope and limit |
|---|---|
| FastAPI, streamed progress, SQLite ledger, policy engine and refund timers | Real execution over synthetic accounts and a simulated clock. |
| Ed25519 issuer credentials, WebAuthn verification, consent hashes and single-use grants | Real cryptographic checks. The issuer is team-controlled; labelled demo assertions are available in `DEMO=1`. Persona login is demo identity. |
| Four-node FISCO BCOS and native Watchman | Real commitments, receipts and government OFAC matching in the full stack. Nodes share one host. Keyless mode uses local hashes and synthetic screening, clearly labelled. |
| Hosted conversation with scripted fallback | The model proposes intent and writes explanations from redacted facts. It cannot supply a payee, amount or destination. No key is needed for judging. |
| University, bank, identity checks, visa evidence, transfers and refunds | **MOCK**. No real bank, immigration service, university portal, insurance integration or external message delivery. VND/KRW is a labelled MOCK board rate. |

Freeze cancels outgoing MOCK transfers still inside their 30-minute hold and pauses further outgoing authority. It leaves incoming refunds running. Unfreezing restores valid signed limits without resending cancelled payments.

## Run a keyless copy

Install Git and [uv](https://docs.astral.sh/uv/) with Python 3.12 support. From a fresh clone:

```powershell
git clone https://github.com/thanhdvu/bursarbridge.git
cd bursarbridge/services/api
uv sync --frozen
uv run --frozen python -m bursarbridge.cli dev --offline
```

The API is at `http://127.0.0.1:8000/api`, with interactive documentation at `/api/docs`. `--offline` forces scripted dialogue, local commitments and synthetic screening, even if a private env file exists. Dependency installation needs network access; the resulting API needs neither a hosted key nor WSL.

To use the family screens, install Node.js and pnpm, then follow the second-terminal commands in the [local setup guide](docs/deploy/local.md). They build the web in live mode on port 3700 against your local API. The same guide covers native FISCO and Watchman in WSL2 Ubuntu; no Docker is required.

Run all twenty scripted journeys without a key or chain installation:

```powershell
uv run --frozen python -m bursarbridge.cli judge --offline --output runtime/judge-offline
```

From the repository root with Make installed, the equivalent is `make judge-offline`. Full-stack reproduction uses `make judge`; `make evidence` rebuilds the full package on a fresh team chain and must run in an isolated verification checkout, away from a serving demo.

## Read and check the submission

| Document | What to look for |
|---|---|
| [Technical guide](docs/deliverables/technical.md) | Request flow, seven core algorithms, authority and chain commitments. |
| [Security self-assessment](docs/deliverables/security.md) | Permission tiers, actor powers, attacks checked and remaining risks. |
| [Test catalogue](docs/deliverables/test-cases.md) | T01-T20, security tests, 80 conversation cases and reproduction commands. |
| [Execution evidence](evidence/README.md) | Sandbox operations, audit logs, actual chain receipts, verifier and current results. |
| [API runbook](services/api/README.md) | Configuration, normal operation, recovery and evidence safety. |
| [API contract and Changelog](docs/API.md) | Public fields, events and visible changes. |
| [Windows tunnel hosting](docs/deploy/windows-tunnel.md) | The public test link's independent checkout and runtime. |
| [Ubuntu VM recipe](docs/deploy/ubuntu-vm.md) | Later fixed-hostname deployment; cloud acceptance remains to be performed. |

The [submission-branch verification](evidence/submission_main_20261020/README.md) passed 271 API tests, all 80 scripted conversation evaluations, T01-T20 offline and T01-T20 with native FISCO/Watchman. The full-stack evidence includes real FISCO receipts for a team-operated development chain. Physical passkey acceptance, real banking and native-speaker review remain separate checks. Dependency notices are in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

