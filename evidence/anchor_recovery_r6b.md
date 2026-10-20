# Round 6 follow-up: anchoring, freeze and conversation regression

The frontend's seven-scene LIVE run exposed two unaudited freeze paths. Both were
removed: background anchor failure and a chat-time availability probe. Periodic
anchoring now records safe-code-only `anchor_deferred`, retries with capped real-time
backoff and emits family-scoped `anchor_updated`. Recovery catches up pending entries,
records `anchor_recovered`, and retries ready recorded tuition intent. No receipt/hash
is fabricated. A new outage does not require a parent's unfreeze or suspend mandates.

Persistent safety freezes use one helper with audit, reason, family event and explicit
parent-passkey recovery. `/me` and session user expose `frozenReason`; legacy unknown
causes are labelled `LEGACY_FREEZE`, not guessed or automatically cleared.

Validation: **169 pytest tests**, ruff, **43/43 scripted** and **43/43 fresh hosted**
conversation evals; **20/20 T01-T20** on the existing real four-node FISCO chain and
native government-only Watchman. See [scenario results](scenario_results.json),
[hosted transcripts](conversation_eval_hosted_r6b.json), and
[scripted transcripts](conversation_eval_scripted.json). The provider is the owner's
private local gpt-6.1-sol proxy, not a public deployment/provider validation.

[Targeted recovery tests](../services/api/tests/test_anchor_recovery.py) simulate
DomainError and unexpected anchor failures, ensure no cross-family freeze, verify
backoff and catch-up roots, prove chain-down approvals leave balance/approval intact,
check the bank boundary directly, exercise every persistent freeze reason/event,
and resume a ready pending tuition request after recovery. They also verify automatic
continuation speaks to Linh as the requester. These failures are injected in isolated
HTTP test stores, not by stopping the team's live FISCO nodes.
The refusal-specific regression uploads a refusal offline and prepares the claim,
while proving its signature waits and no refund/payment moves.

The engine now supplies rent's actual payment status/cancel availability and the
thread reader's server-derived role/name. Held and matched rent evals verify distinct
wording and one debit for repeated requests. Scripted continuation uses third-person
signer wording rather than calling out to the father. Money authority, taint, consent,
original-payer refund and cap rules are unchanged. `screeningMode` remains in health.

All banking/bursar activity and authentication assertions in headless runs remain
labelled MOCK/DEMO. No real money, public VM, hardware-passkey or native-speaker claim.
The previous Round 6 readiness report records its original baseline; scenario bundles
and the manifest now represent this follow-up rerun on the existing chain, not a reset.

The first hosted run was 42/43: C39 answered correctly, but a single greeting was
misclassified by its old blanket ban as an unrelated denial. The complete initial
raw report is retained as conversation_eval_hosted_r6b_initial.json. Vietnamese greeting
checks now allow at most one across a conversation, matching the existing occasional
warmth policy; wrong-language greetings, unrelated denials and factual assertions stay.
The unconditional name-use prompt was removed; reader identity is context for audience,
not a required salutation. Final hosted evidence is a new complete run, not merged retries.
The second raw 41/43 run is retained in conversation_eval_hosted_r6b_second.json:
C35 incorrectly used the elder-to-child address `con`; C43's correct settled wording
`支付成功` was missing from the lexical assertion. Restored the student's Vietnamese
name convention without a required greeting and accepted that valid settlement phrase;
engine state and duplicate-debit assertions were retained.
