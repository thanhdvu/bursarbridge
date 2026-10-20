# Execution evidence

Start with the [fresh submission-branch verification](submission_main_20261020/README.md). It records 271 API tests, 80 scripted conversations, 20/20 keyless HTTP journeys and 20/20 native FISCO/Watchman journeys run from this repository's `main` checkout on 20 October 2026.

The family, bank, university, visa evidence, transfers and refunds are synthetic. The FISCO transactions are real commitments on four team-operated local nodes; they do not prove that a real bank or university moved money. The simulated family clock starts on 12 January 2027, which is separate from the test-run date.

## Check the current run

| Evidence | What it contains |
|---|---|
| [Scenario results](submission_main_20261020/fisco/scenario_results.json) and [human-readable report](submission_main_20261020/fisco/scenario_report.md) | T01–T20, scripted dialogue, native Watchman and fresh SQLite sandbox per journey. |
| [Sandbox operations](submission_main_20261020/fisco/sandbox_ops.jsonl) | MOCK bank and bursar actions attributed by run ID. |
| [Audit entries](submission_main_20261020/fisco/agent_audit.jsonl) | Hash-chained decisions, grouped by run ID. |
| [Anchor hashes](submission_main_20261020/fisco/anchors.csv) and [registry records](submission_main_20261020/fisco/registries.csv) | FISCO transaction hashes, block numbers, contract addresses and explicitly off-chain rows. |
| [Independent verification result](submission_main_20261020/fisco/audit_verification.txt) | 20 audit chains, 163 entries and 37 FISCO anchors checked against the RPC used for this run. |
| [Run manifest](submission_main_20261020/fisco/manifest.json) | Generated time, runtime modes, contracts and file inventory for the new evidence. |

For an offline check of the committed evidence bytes, run from `services/api`:

```powershell
uv run --frozen python scripts/verify_audit.py --evidence ../../evidence/submission_main_20261020/fisco
```

This reports **offline hashes/Merkle only**. To check receipts and contract roots, the operator needs the RPC of the same team-operated chain that produced the hashes:

```powershell
uv run --frozen python scripts/verify_audit.py --evidence ../../evidence/submission_main_20261020/fisco --rpc http://127.0.0.1:8545
```

A fresh chain has different transaction hashes. Follow the [local setup guide](../docs/deploy/local.md) to reproduce new receipts. Hosted-model evaluation was not part of this new run; [earlier hosted conversation records](hosted_conversation_review.md) are separate and should not be read as current 80-case hosted validation.
