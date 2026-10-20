# Frontend round 6 acceptance

Completed early Monday, 19 October 2026 (Vietnam time), on `feat/web`. Functional implementation: `4bf41d2`; merged main: `ef90f45`. The final copy also says “outgoing” on the landing page. [Run the web](../../README.md).

Used Chromium at **375 × 812**, through the family apps and all seven `/demo` scenes, in both modes. Live used the existing API on port 8000, with OpenAI dialogue, FISCO and Watchman reporting ready. There were **nine live chat sends** across the normal story, hold cancellation and unpaid-refusal branch; switches, signatures and clock moves used their normal API actions.

| Requirement | Mock | Live |
| --- | --- | --- |
| Freeze reverses a held payment; balance and allowance return; valid signed limit resumes; cancelled payment stays cancelled | Pass | Pass |
| Incoming refund can be signed and received while outgoing payments stay frozen | Pass | Pass |
| Unpaid refusal stops pending tuition, creates no refund, gives admission guidance and Dad's app notice | Pass | Pass |
| Acceptance → certificate → visa processing → payment window; certificate PDF opens before payment | Pass | Pass |
| Reset returns without waiting for chain receipts; catching-up state clears after recovery | Pass | Pass |
| Seven scene controls work on a phone; all personas, scams, Lan's check, refund redirect denial, audit tamper/restore and rent | Pass | Pass |
| Plain local/live/mock run instructions | Pass | Pass |

`pnpm lint` (zero warnings), `pnpm typecheck` and `pnpm build` passed. Locale key parity: **1,105** in English, Vietnamese, Korean and Chinese. A final nine-page phone sweep had no horizontal overflow or browser runtime errors. After combining event refreshes and removing hidden desktop phone frames on mobile, the live sweep made **70 API requests** without failed API calls (automatic session-renewal 401s excluded). The earlier rapid sweep had reached the existing server limit; its limit was not changed. Activity also stopped making the old oversized judge-only audit request: family payments, refunds and approvals stay visible, but the API does not provide family blocked-audit history.

The paid-refusal case returned **132,551,176.98 VND** to the original **•••• 4821** account in both modes, with the family still frozen and a final balance of **996,887,220.88 VND**. The refund is tuition only; dormitory and health insurance remain separate. Mock repeat-payment replies were also checked during a hold and after settlement; they do not claim receipt early or create another payment. Rent wording describes the bank hold. Send waits until the conversation is ready. An extra temporary mock fixture checked pending/cooling approvals, an incoming claim, expired and revoked limits; their statuses and consent hashes stayed intact, and expired/revoked limits were not revived. That fixture was restored after the check.

Live reset responses were observed at about **61–129 ms**, reporting registration/anchoring pending. Actual `anchor_updated` pending and ready events were read after reset and `/chain/status` eventually reported both ready. Recovery has no asserted time bound. For a repeatable slow-chain **display** check, the browser temporarily overrode the live status response; mock used a pending query fixture. Both showed the calm notice and cleared it after recovery. No chain service was stopped, and no receipt was invented.

The stage's certificate was also opened through its actual PDF button in both modes. Its family data uses the selected student's session; the judge session cannot read `/study-plan`. Mobile scene cues preserve both attachments and draft text without sending. Desktop loads two phone frames; mobile loads none.

These are local acceptance results with fictional people, banks and funds. Signatures used the explicitly labelled demo authenticator. This is not hardware WebAuthn acceptance, a public deployment or a public-link load test. The local demo was reset afterwards for recording; no Monday-noon blocker remains.

[Structured results](acceptance.json) contain selected synthetic API observations, without session tokens or credentials. Screenshots:

| View | Mock | Live |
| --- | --- | --- |
| Certificate before payment | [Mock](screenshots/mock-admission-before-payment.png) | [Live](screenshots/live-admission-before-payment.png) |
| Held payment cancelled | [Mock](screenshots/mock-frozen.png) | [Live](screenshots/live-frozen.png) |
| Refusal before payment | [Mock](screenshots/mock-unpaid-linh.png) | [Live](screenshots/live-unpaid-linh.png) |
| Refund home while frozen, Vietnamese | [Mock](screenshots/mock-minh-vi-final.png) | [Live](screenshots/live-minh-vi-final.png) |
| Catching-up notice | [Mock](screenshots/mock-chain-catching-up.png) | [Live](screenshots/live-chain-catching-up.png) |
| Hao's rent, Chinese | [Mock](screenshots/mock-hao-rent.png) | [Live](screenshots/live-hao-rent.png) |

[Desktop stage](screenshots/live-demo-desktop-final.png).
