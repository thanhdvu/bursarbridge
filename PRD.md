# BursarBridge — Product Requirements

Status: v1, 16 Oct 2026. Product review informed by a student reviewer based in Seoul.
Competition: Fintechathon 2026 International Track (PBCSF × WeBank), Topic C "Cross-border & Student Finance Assistant", theme "AI as a Financial Participant".
Submission closes **20 Oct 2026 23:59 Beijing (22:59 Vietnam)**. Internal target: product done 18 Oct night, package done 20 Oct 18:00 VN.
Research behind every claim here: [docs/research/topic-c-research-report.md](docs/research/topic-c-research-report.md).

## 1. One line

BursarBridge is an AI agent that pays an international student's tuition from the family's home-country bank, pays only payees the university has cryptographically vouched for, and gets the money back to the parents if the visa is refused.

## 2. Why it matters

- Families pay tuition **before** they know the visa outcome, and refusals are at record highs (Canada 59% of new study permits Jan–Sep 2025, UK ~13% Q1 2026, Australia 21.8% FY2025-26).
- Refunds after refusal are slow (3–10 weeks), conditional and lossy (re-converted at the refund-day rate, fees, retentions); most Australian complaints come from missed 28-day refund deadlines.
- The payment path is where students and parents get scammed: fake "discount" invoices with a new account, "refund agents", fake police/embassy demands for "proof-of-funds deposits".
- Every transfer from Vietnam/China needs a home-country paperwork pack (VN Circular 20/2022: amount capped by the school's fee notice; CN: USD 50k/person/year quota, splitting across relatives is illegal structuring).
- Nobody owns the unhappy path end to end: Flywire/Wise own "pay", banks own generic scam warnings. No product or hackathon project automates refusal → refund → back to the payer.

## 3. Who it is for

| Persona | Context | What they need |
|---|---|---|
| **Minh** (parent, payer) | Shop owner in Đà Nẵng, pays from a VND account, Vietnamese only, on a phone, nervous about large transfers abroad | To know the money goes to the real university, what it costs all-in, and that he can get it back. Approve with one confident tap, never fill bank forms |
| **Linh** (student) | 19, admitted to a Seoul university (D-2 visa), forwards invoices and letters, chats in VI/EN/KO slang | Not to be the bottleneck between school and parents; to see where the money is; one place to handle "visa refused, now what" |
| **Lan** (mother, co-signer) | Trusted contact at home | To co-sign only when something looks risky, never for routine payments |
| **Wang family** (mirror, CN→KR) | Chengdu parents, CNY account, FX quota | Same flow under China's rules; the agent refuses to help split payments across relatives |
| **Judge / auditor** | WeBank engineer or PBCSF scholar | To see that the agent is safe by construction: tiers, mandates, tamper-evident evidence, reproducible scenarios |

The primary corridor is **Vietnam → Korea** (the student product reviewer's real context; Vietnam and China are the two largest sources of international students in Korea [U: verify]). Mirror corridor **China → Korea**. Australia is kept in the rules table as the destination with a legal 28-day refund deadline, cited in the pitch.

## 4. The experience (what good feels like)

The family experiences **one calm, trustworthy money concierge**, not a banking app and not a chatbot. The parent opens the app only to say yes or no to something precise; everything else (reading invoices, paperwork, chasing the bursar, chasing the refund) happens without them. Every screen answers three questions at a glance: *where is the money, is it safe, what do I need to do (usually nothing)*.

The core journey (demo order):

1. **Set the boundary.** Minh creates a tuition mandate in Vietnamese: purpose tuition, payee must be verified by the university, up to the invoice amount, until a date, Lan as co-signer. Signs with a passkey (Face ID / fingerprint). This is the "humans set goals and boundaries" moment.
2. **Student forwards the invoice.** Linh drops the PDF (or says "ba ơi chuyển tiền học kỳ 1 cho con nha"). The agent reads it, verifies the university's payee credential, checks the corridor rules, gets a quote, builds the outbound paperwork pack.
3. **Approve the exact action.** Minh gets one approval card: amount in VND and KRW, rate vs mid-market, fees, amount received, verified payee (issuer, account match, name match), paperwork ready, 30-minute cancel right. Passkey signs exactly this. Payment executes; bursar shows PAID; reconciliation matches.
4. **The attack.** A "15% early-payment discount, new account" email arrives. The agent extracts it, sees the account is not vouched for by the university and that the parameters came from an untrusted document, and shows a clear red card with the reasons. Nothing moves.
5. **Visa refused.** Linh uploads the refusal letter. The agent files the refund claim with the university, starts the deadline timer, chases on schedule (simulated clock, labelled). A "refund agent" asks to redirect the refund to a new account: hard deny. Refund lands back in Minh's VND account with a line-by-line FX loss statement.
6. **Prove it.** Audit viewer: every decision hash-chained and anchored on a FISCO BCOS permissioned chain. Someone edits one byte of the log; Verify pinpoints the entry. Restore; Verify passes.
7. **Routine autonomy (L2).** Monthly rent to a name-checked landlord, under a cap, executes without asking, with a notification and a cancel window.

How the agent learns the visa outcome: from the decision/refusal letter the student uploads (every country issues one, and every university requires it for a refund). The agent never queries immigration portals (CEAC has CAPTCHA, VEVO needs organisational registration). Verification is the university's job (mocked in the MVP). A forged letter gains nothing because refunds go only to the original payer.

## 5. Scope

**P0 (must ship, never cut)**
- Permission tiers L0–L3 + L-X never-list, enforced by a deterministic policy engine outside the LLM (Section 7 of the research report).
- Mandates signed with passkeys (WebAuthn); consent hash with dynamic linking; single-use grant token.
- Payee verification: university-issued PayeeCredential (VC-JWT, did:key) + registry status on chain + account-hash match + name check.
- Invoice / letter ingestion (PDF) with field-level provenance; injected or tainted parameters can never become a payee.
- First tuition payment end to end on the mock home bank → mock university bursar, with all-in disclosure and cancel window.
- Visa refusal → refund claim → deadline timers (simulated clock) → refund to original payer only → FX reconciliation.
- Hash-chained audit log, Merkle anchoring on FISCO BCOS, verifier with tamper demo.
- Kill switch (parent/student Freeze; circuit breaker).
- Scenario harness: `make judge` runs the scripted tests (T01–T20 in the research report §11.4) and prints a pass/fail table; same via HTTP for the UI.
- Web app: landing page, parent app, student app, agent chat, approvals, payments/refund timeline, trust center (audit + chain), judge console. **i18n EN / KO / ZH / VI, dark mode, mobile-first.**
- All six submission deliverables.

**P1** — Rent mandate (L2 auto-execute); CN→KR corridor with anti-structuring; virtual-kidnapping scam scenario with co-sign + cooling-off; Watchman sanctions screening in the path; MandateGuard contract; public deployment; user test with 5–10 real students (the student product reviewer's network).

**P2 (finals)** — Rafiki/Open Payments rail; graduation mode (departure agent); payment-history credential; SD-JWT selective disclosure; checker model; HK corridor.

**Out of scope** — real banks, real money, stablecoins or any value on chain, querying immigration systems, investment advice, credit scoring.

## 6. Requirements that judges score

- **Task completion (40%)**: scripted tasks in a simulated environment → every scenario runnable headless, deterministic with a fixed seed, evidence written for each.
- **Security & compliance (30%)**: defence against induced transfers, data extraction, privilege escalation, prompt injection; "serious security failures trigger substantial deductions". The LLM proposes, the engine decides; the LLM never holds credentials. Map controls to NFRA's five agent risks, MAS SAFR, FSB, OWASP Agentic Top 10.
- **Innovation & interaction (30%)**: dialogue efficiency, clarification, correction, fallback; multilingual (APEC tag). The refusal-refund path and payee proof are the novelty.
- **Bonus (0–5)**: compliant on-chain exploration (permissioned evidence chain, no tokens) + real-deployment evidence (public URL, real student test).

## 7. Hard lines

- No real money, no real bank credentials, no personal data on chain, no tokens or stablecoins.
- Mocked parts are labelled "MOCK" in the UI and listed in the real-vs-mocked table. Never imply a regulator node or public network.
- No real organisation's branding: universities and banks in the demo are fictional (e.g. "Hanbit University", "Lotus Home Bank").
- Personal data redacted (last 4 digits) before any LLM call; no secrets in Git.
- Third-party code/data properly licensed; `THIRD_PARTY_LICENSES.md` kept current. OpenSanctions bulk data excluded (CC BY-NC).
- English is the submission language; the product is multilingual.

## 8. Success criteria (acceptance)

- A first-time parent completes "approve first tuition payment" on a phone in under 60 seconds without help, in Vietnamese.
- Every P0 scenario passes from a clean clone with one command; evidence package regenerates from the deployed stack.
- The demo story (Section 4) runs live in under 5 minutes without a cut.
- A judge reading any screen can tell what is real and what is mocked.
- the student product reviewer, as a real student, says the flow matches what she actually went through, or we change it.

## 9. Decision ledger

| Date | Decision | Why | Protects | Trades away |
|---|---|---|---|---|
| 16 Oct | BursarBridge (verified-payee tuition + refund-on-refusal) over KinSign / departure agent | 91 vs 81 vs 72 on the rubric; refusal-refund path has no prior art; payee proof is a real security primitive | Novelty + 30% security case | Allowance and departure ideas move to finals |
| 16 Oct | Primary corridor VN→KR, mirror CN→KR, AU kept in rules | the student product reviewer studies in Seoul: real insight beats a generic Melbourne persona; KR's top sources are VN and CN | Authentic user story, i18n relevance | Australia's legal 28-day rule becomes a cited rule, not the main demo |
| 16 Oct | Chain carries evidence only (FISCO BCOS, hashes) | China's Yin Fa [2026] No. 42 bans stablecoins/RWA; WeBank's own stack | Bonus without red flags | No programmable money |
| 16 Oct | Agent learns visa outcome from the uploaded letter, not immigration portals | Works in every country, legal, robust; refunds go only to original payer so forgery gains nothing | Demo reliability, compliance | No "automatic status check" wow |
| 16 Oct | Python backend (FastAPI + LangGraph), VC-JWT in Python instead of Veramo | One backend language for a 3-day build | Speed | Veramo's ecosystem |
| 16 Oct | Next.js web app, i18n EN/KO/ZH/VI, dark mode | Owner wants world-class UX; parents read Vietnamese, students KO, Chinese mirror family ZH | Real users and judges | More copy to translate |

