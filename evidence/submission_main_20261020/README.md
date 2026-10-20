# Submission-branch verification — 20 October 2026

This report records a fresh run from the submission repository's `main` checkout on Windows with WSL Ubuntu. Dependencies were installed from the committed lockfiles. The family, bank, bursar and accounts are synthetic. No hosted model evaluation or real-money transfer was performed.

| Check | New result | Evidence |
|---|---:|---|
| Complete API pytest suite | 271 passed; one upstream deprecation warning | [pytest output](pytest.txt) |
| Scripted conversation evaluation | 80/80 passed | [conversation report](conversations.json) |
| Production web build | Passed with pnpm 10.33.2; TypeScript and 17 static-page generation steps completed | [frozen install](web_install.txt), [build output](web_build.txt) |
| Keyless HTTP journeys | T01–T20 passed; local commitments and synthetic screening | [offline report](judge_offline/scenario_report.md) |
| Native full-stack HTTP journeys | T01–T20 passed with four FISCO BCOS nodes and native Watchman | [full-stack report](fisco/scenario_report.md) |
| Independent audit verification | 20 runs, 163 entries, 37 FISCO anchors; receipts and roots checked against this run's RPC | [verification result](fisco/audit_verification.txt), [transaction hashes](fisco/anchors.csv) |

The full-stack runner used scripted dialogue, a new signer and contracts, and fresh SQLite state per scenario. [Sandbox operation logs](fisco/sandbox_ops.jsonl), [audit entries](fisco/agent_audit.jsonl), [credential registry records](fisco/registries.csv) and the [run manifest](fisco/manifest.json) are retained. The scenario's simulated date starts on 12 January 2027; the run itself was performed on 20 October 2026.

The first native attempt exposed Windows CRLF conversion of shell scripts. A repository `.gitattributes` rule now keeps `*.sh` at LF. The successful full-stack run followed that fix; it did not require a hosted key. The FISCO nodes share one laptop and are not independent production validators. Real bank settlement, university approval, physical passkeys, public-host acceptance and hosted-model accuracy are outside these checks.
