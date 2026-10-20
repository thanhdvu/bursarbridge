# Security self-assessment

A parent frightened by a changed invoice or a police impersonator needs an assistant that can stop money leaving without blocking its return. We put that distinction in the engine and the bank, rather than relying on how the model is prompted. This assessment covers the synthetic demo in this repository. It is not an audit opinion or a claim of regulatory approval.

## Permission tiers

| Tier | Allowed behavior | Required authority |
|---|---|---|
| L0 | Explain the family's bill, rates, dates and fictional policies. | Read-only family scope; no payment grant. |
| L1 | Parse evidence, assemble a pack or draft forms. | Tainted inputs remain data; preparing a form does not submit it. |
| L2 | Execute a later tuition instalment or monthly rent within existing authority. | Valid signed purpose/payee/cap/period mandate, verified evidence, current window/quote and all bank checks. A cancel hold and notification follow. |
| L3 | First tuition payment, new/amended mandate, student refund claim or approved recovery letter. | The correct human signs the bound action. The engine can still deny it. |
| L-X | Refund diversion, unverified destination, self-escalation, crypto speculation, credential/data extraction or registry poisoning. | Denied. A parent signature, co-sign or model instruction cannot override the hard boundary. |

The implementation returns `DENY`, `ESCALATE` or `AUTO_EXECUTE`. Cooling-off is a persisted risk disposition, not permission to send to an unsafe account. See [policy.py](../../services/api/bursarbridge/policy.py) and [the API contract](../API.md).

## Who can do what

| Actor | Can | Cannot |
|---|---|---|
| Student | Ask, upload synthetic evidence, prepare tuition requests, Freeze, sign their withdrawal/refund forms and recovery letters. | Spend the parent's money without the parent's authority, change a bank-held destination, fetch a parent's raw document or unfreeze alone. |
| Parent | Sign/revoke purpose-specific limits, approve first tuition, cancel a held transfer, Freeze and passkey-authorize Unfreeze. | Approve around a cap, sanctions denial or unverified payee; redirect a refund. |
| Co-signer | Record the required household check on a cooling case. | Replace parent consent, skip cooling or make an unsafe destination payable. |
| Judge persona | Advance the simulated clock, reset/tamper/restore/verify within its sandbox and run scenarios. | Reset another visitor or move real money. Judge identity itself is demo-only. |
| Agent / LLM | Propose intent/scope, ask for missing information and explain allowlisted facts. | Supply payment amount/payee/destination, hold bank credentials, create a grant, sign for a human or amend the trust registry. |
| MOCK bank | Re-derive authority, debit once, hold/cancel, match and credit original-payer refunds. | Accept a model's monetary fields as authority. It is code in the same trust domain, not an independently operated bank. |
| MOCK issuer / bursar | Issue signed synthetic tuition/payee records, define Hanbit's fictional terms and simulate receipt/refund progress. | Represent a real university or establish a real visa outcome. The team controls the issuer key and simulated records. |

Public persona selection is intentionally available to a tester in their own browser sandbox. It is not authentication of a real Minh or Linh. Separate browsers cannot currently join one family's consent flow.

## Hard-never rules

There is no real-money rail, real bank credential or token/stablecoin in this demo. The model never supplies payee, amount or destination. Document/email/chat text cannot establish those fields. Refunds only credit the original payer's bank record. Caps and payee rules cannot be waived by approval. Keys and private env files stay outside Git; personal data stays off chain. Use fictional documents only. Dependencies and government-list sources are recorded in [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md); no OpenSanctions bulk data is used.

## Risks, controls and remaining gaps

All test-file references below are covered by the [271-test submission-branch result](../../evidence/submission_main_20261020/pytest.txt). Scenario references link through the [catalogue](test-cases.md) to execution logs.

| Risk | Control and evidence | Residual risk / gap |
|---|---|---|
| Prompt injection in an invoice or email | Envelope-local taint; issuer/bank resolution. T06/T07/T20; [provider tests](../../services/api/tests/test_providers.py) reject model attempts to lift taint. | The fixture recognizer is not a general document authenticity service. |
| Forged payee or changed bank details | Credential signature/status, purpose binding and bank name-check rechecked at debit. T07; `test_revoked_credential_rechecked_at_execution` in [security tests](../../services/api/tests/test_security.py). | Issuer and bank are team-controlled; a real deployment needs independent onboarding and key custody. |
| Consent swapped after signing | Canonical action digest and server re-derivation. `test_changed_consent_cannot_execute` and `test_bank_rederives_changed_action_even_with_matching_hash`. | Consent UI still depends on a trustworthy browser/device. |
| Replay or simultaneous approval | Single-use grant and serialized transaction. T03; `test_concurrent_approval_is_single_debit`. | No real bank idempotency/outbox or crash-recovery settlement protocol has been integrated. |
| Wrong person or another visitor's token | Role/family checks, private cookie sandbox and document ACL. [Public tests](../../services/api/tests/test_public.py), `test_auth_and_cross_family_boundaries`. | Demo persona login is not production identity; two devices have no family invitation protocol. |
| Passkey replay or wrong origin | Actual signed WebAuthn verification with RP/origin/challenge/user-verification checks; [WebAuthn tests](../../services/api/tests/test_webauthn.py). Demo assertions require `DEMO=1`. | Automated cryptographic/browser tests do not prove a physical authenticator on the public hostname. |
| Scam pressure and repeated frightened follow-ups | Persisted cooling case, household co-sign and parent consent; T12 and [incident tests](../../services/api/tests/test_incidents.py). | Risk features are heuristic, not a trained fraud detector; legitimate urgency may also pause a case. |
| Panic button fails or blocks incoming money | Atomic cancellation of outgoing holds, preserved consent and limits, incoming refund exemption. T13/T15; [Round 10 tests](../../services/api/tests/test_round10.py) cover expiry, revocation, rent replay and CN reservations. | Delivered transfers cannot be cancelled; the 30-minute hold is a MOCK bank feature. |
| Refund diversion or false entitlement | Original-payer record, paid-tuition claim and student-signed forms. T13/T14; [refund contract tests](../../services/api/tests/test_refund_contract.py). | Visa proof and school acceptance are simulated. After-term degree refunds require manual assessment. |
| University misses its promise | Clock creates a dated student-approved chaser, then a manual external complaint pack; `test_overdue_refund_creates_consent_bound_chaser_and_manual_pack` in [Round 9 tests](../../services/api/tests/test_round9.py). | No external delivery or power to force repayment; a real wire may incur different costs. |
| LLM outage, hallucinated facts or quota exhaustion | Strict proposals, allowlisted facts, response validation, visible scripted fallback and health degradation. [Provider tests](../../services/api/tests/test_providers.py), [80 scripted conversations](../../evidence/conversation_eval_scripted.json). | Language quality is not proved by factual assertions; hosted output is nondeterministic. Only one focused hosted turn was used this round. |
| Chain outage, late receipt or silent freeze | Retry/catch-up, generation checks, recorded freeze reason, money closed until required state recovers. [Anchor recovery](../../services/api/tests/test_anchor_recovery.py) and [reset regressions](../../services/api/tests/test_round9c.py). | Some chain calls still delay writes; host loss can remove all four validators at once. |
| Operator edits or rewrites records | Hash chain, Merkle commitments, actual receipts and independent verifier; T16. | Team controls nodes and signer. Anchoring proves recorded bytes, not the truth of a MOCK bank event. Before anchoring, local operator trust remains. |
| Sanctions or cross-border compliance missed | Native Watchman OFAC matching with source hash; T11. Versioned corridor rules and ledger-derived family structuring; T10. | OFAC alone is incomplete screening; no real KYC/AML, external-bank visibility or legal compliance determination. |
| Public abuse, shared NAT or crawler capacity | Stateless previews, session-only allocation, idle eviction protections, trusted loopback forwarding, per-IP/visitor caps and durable LLM budgets. [Public tests](../../services/api/tests/test_public.py), [Windows edge tests](../../services/api/tests/test_windows_tunnel.py). | Not DDoS protection; a local administrator is trusted. Count caps do not replace the provider's monetary budget cap. |
| Malicious PDF or private-data leakage | Bounded worker on Linux; Windows public mode accepts bundled PDFs only. [PDF worker tests](../../services/api/tests/test_pdf_worker.py). Redaction and safe provider error codes prevent raw keys/bodies in replies. | Linux worker shares the service UID; no claim of a hardened hostile-document sandbox. Enter only synthetic data. |
| Misleading FX/refund estimate | API-owned estimate and reconciliation, labelled MOCK board/fees, bank balance refreshed on receipt; [refund tests](../../services/api/tests/test_refund_contract.py). | No executable live FX price or guaranteed net return. Intermediaries may charge differently. |

## Deployment and acceptance limits

The public Windows stack is separate from development, with loopback Caddy behind the owner's existing Cloudflare tunnel. It retains durable visitor budgets and labelled fallback. The [VM recipe](../deploy/ubuntu-vm.md) targets a dedicated Linux host; no cloud account was accessed or provisioned here. Keep the API single-worker and keep private ledger/runtime backups together.

The [evidence index](../../evidence/README.md) identifies which results are current, which use a local chain and which include actual FISCO receipts. Native-speaker review, phone/cellular routing, physical passkeys, real issuer governance, real-bank settlement and independent penetration testing remain outside the automated result. The student product reviewer's review informs the synthetic bill and timeline; it is not verification of a real institution's contract.

