# Round 7: realistic synthetic semester amounts

The signed catalog is now `semester-2027-v3`: tuition **7,174,000 KRW**,
dormitory March-June (four months) **1,500,000**, and fictional bridge insurance
**70,000/month × 4 = 280,000**; total **8,954,000**. Two issuer instalments are
**4,477,000** each. Private rent remains a separate **900,000/month** alternative.
The amount basis is the team-supplied presenter/advisor summary of a Seoul
semester bill. We have not reviewed or copied the original document. No real
university, insurer, credential, account, seal or personal information is included.
Hanbit and all bank/bursar operations/refund terms remain synthetic/MOCK.

No policy threshold was changed. First payment remains L3; the second issuer
instalment remains L2. A 7.2M mandate is deliberately insufficient for the new
bill. See [new regressions](../services/api/tests/test_semester.py),
[signed catalog](../services/api/bursarbridge/catalog.py), and
[pure policy](../services/api/bursarbridge/policy.py).

Validation: **185 tests**, ruff, **49/49 scripted evals**, **49/49 fresh hosted
evals**, and **20/20 T01-T20** on the existing real FISCO/native Watchman services.
The interactive API was paused for CLI signer isolation, then restarted hosted
on port 8000. No chain or interactive-family reset was performed. Old signed
records and explicitly versioned earlier reports retain their old amounts.
Use the explicit demo reset to adopt v3 in an existing sandbox.

The full-semester VND quote includes a MOCK 25,000 VND fee:
**169,318,450.36 VND** debit. The unchanged mock refund formula reconciles
**3,386,369.01** FX loss + **1,693,184.50** fictional policy charge + zero
retention, returning **164,238,896.85 VND** to the original payer. Separate
instalment quotes each debit **84,671,725.18 VND**, including their own fee.
See the exact public-API reconciliation assertions in the
[semester tests](../services/api/tests/test_semester.py), plus the matching
[T13 operations](T13/sandbox_ops.jsonl) and [audit](T13/agent_audit.jsonl).

[Invoice PDF](fixtures/invoice.pdf) and [refund illustration](fixtures/refund.pdf)
derive from the catalog and were rendered/visually checked. The refund document
is expressly an illustration, not a filed claim or settlement receipt; actual
claim amounts resolve from paid bank records. The unchanged fake invoice retains
its extractable hidden injection, and T06/T07/T14 still deny the attacks.

[Fresh hosted run](conversation_eval_hosted_r7.json) is one complete raw run,
not stitched cases or fallback counted as hosted success. The existing grounding,
clarification, audience/kinship, correction, state and incident-continuity assertions
remain intact. No conversation prompt, planner authority or money policy was
relaxed for these amount changes. Native-speaker/video review remains useful.

Reproduce from `services/api` with `uv run --frozen pytest -q`,
`uv run --frozen python -m bursarbridge.cli conversation-eval --provider hosted`,
and `uv run --frozen python -m bursarbridge.cli judge` (pause the API for the
real-chain CLI run). `make evidence` additionally resets the synthetic chain;
this refresh aggregated isolated new scenarios on the existing chain instead.

