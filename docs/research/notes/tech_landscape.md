# Tech landscape (Oct 2026) for a 72-hour "AI agent as a financial participant" in cross-border and student finance

Research date: 16 Oct 2026. Context: Fintechathon 2026 International Track, Topic C, judged by WeBank experts and finance scholars.

Labels used on every claim:
- **[V] verified fact**: checked this session against a primary source (official repo via the GitHub API, official docs, a standards body or a regulator page). Repo numbers (stars, last push, latest release) were pulled live from the GitHub API on 16 Oct 2026.
- **[S] secondary**: reported by trade press, vendor blogs or aggregators, and not confirmed against a primary source.
- **[E] estimate**: setup-time or effort estimate for a 3–4 person student team using AI coding assistants.
- **[I] inference**: my reasoning from the cited facts.

Method note: the shared web-search budget ran out partway through this research. Everything after that point was checked through the GitHub API (repos, READMEs, licence files, release notes) and direct fetches of official pages. A few topics therefore rest on secondary sources only, and they are labelled [S] and listed under Gaps: Mastercard Agent Pay, the Visa Intelligent Commerce portal, TrueLayer, OPA governance and the 2026 status of mBridge.

---

## 1. Agent frameworks and protocols: which framework for a 72-hour build, and the 2026 status of MCP and A2A

### Takeaway
All four frameworks are alive and shipping weekly. **LangGraph** (MIT) is the safest choice for a deterministic, auditable financial agent because it has explicit state, checkpoints and human-approval interrupts. **Google ADK** (Apache-2.0) is the natural choice if the idea builds on AP2, because the AP2 samples are written in ADK. MCP is now governed by the Linux Foundation's Agentic AI Foundation (AAIF), with a major stateless spec revision on 2026-07-28. A2A reached v1.0 in March 2026.

### Cited Findings
- [V] LangGraph: 43.4k stars, MIT, last push 2026-10-16, latest release 1.2.15 (2026-10-12), so it is on the 1.x line — [GitHub langchain-ai/langgraph](https://github.com/langchain-ai/langgraph/releases)
- [V] OpenAI Agents SDK (Python): 30.1k stars, MIT, v0.24.0 released 2026-10-15. The JS/TS SDK is @openai/agents 0.20.0 (2026-10-08), MIT — [openai-agents-python](https://github.com/openai/openai-agents-python), [openai-agents-js](https://github.com/openai/openai-agents-js)
- [V] Google ADK Python: 21.9k stars, Apache-2.0, v2.0.0 on 2026-05-19, latest v2.12.0 on 2026-10-13 (v1.0.0 was 2025-05-20). ADK for JS/TS is at v2.3.0 (2026-10-13) — [google/adk-python](https://github.com/google/adk-python/releases), [google/adk-js](https://github.com/google/adk-js)
- [V] CrewAI: 59.8k stars, MIT, release 1.15.28 on 2026-10-14 — [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
- [V] The AP2 reference samples are built on ADK and need a Gemini key (`GOOGLE_API_KEY` from AI Studio) or Vertex AI. The README says the protocol itself does not depend on ADK or Gemini — [google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2)
- [S] The Linux Foundation announced the Agentic AI Foundation on 9 Dec 2025. Anthropic donated MCP as a founding project, alongside Block's goose and OpenAI's AGENTS.md — [OpenSourceForU](https://opensourceforu.com/2025/12/anthropic-openai-block-move-agentic-ai-infrastructure-to-open-source-governance-under-linux-foundation/), [WorkOS](https://workos.com/blog/the-linux-foundation-launches-the-aaif)
- [V] MCP spec: the stable revision `2026-07-28` was released 2026-07-28 (RC on 2026-05-29; previous stable 2025-11-25) — [modelcontextprotocol releases](https://github.com/modelcontextprotocol/modelcontextprotocol/releases)
- [V] What 2026-07-28 changed in MCP:
  - It is now stateless. The `initialize` handshake and `Mcp-Session-Id` are gone, and every request carries its version and capabilities in `_meta`. There is a new `server/discover` method.
  - Tasks moved into an official extension.
  - A Multi Round-Trip Requests pattern replaces server-initiated elicitation and sampling.
  - OpenTelemetry trace-context propagation in `_meta` is documented.
  - Roots, Sampling and Logging are deprecated, and so is Dynamic Client Registration (in favour of Client ID Metadata Documents).
  - Source: [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [V] A2A: repo `a2aproject/A2A` has 26.2k stars, Apache-2.0, v1.0.0 on 2026-03-12 and v1.0.1 on 2026-05-28 — [a2aproject/A2A](https://github.com/a2aproject/A2A/releases)
- [S] A2A was handed to the Linux Foundation on 23 June 2025. Sources disagree on whether it sits inside AAIF or is a separate LF project — [blckalpaca](https://blckalpaca.at/en/knowledge-base/ai-agents/a2a-protocol-basics/linux-foundation-aaif-bedeutung), [agentic-ai readthedocs](https://agentic-ai.readthedocs.io/en/latest/Standards/agentic-ai-foundation/)

### Inferences
- [I] Best fit for 72 hours: **LangGraph (Python) for the core agent, plus a Next.js/TS UI**. A finance agent needs explicit states (draft → policy check → human approval → execute → receipt), and LangGraph's graph, checkpointer and `interrupt` map directly onto permission tiers and approval logs. That gives judges inspectable evidence for the 30% security and compliance score.
- [I] Pick **ADK** instead if the team reuses AP2 sample code (same framework, A2A built in). Avoid **CrewAI** for the money-moving path: role-play multi-agent orchestration is harder to make deterministic and auditable. It is fine for a research or explanation sub-agent.
- [I] The OpenAI Agents SDK has built-in guardrails, handoffs and tracing and is a solid alternative if the team already uses OpenAI models. I did not verify its non-OpenAI model support this session.
- [I] Expose the bank and payment tools as an **MCP server**. That is idiomatic in 2026: Watchman already ships an experimental MCP, and AP2's x402 sample uses MCP agents. Target spec 2026-07-28 or use an SDK that handles version negotiation; SDK support for the brand-new stateless revision may lag.
- [E] Setup: LangGraph or ADK agent with 3–5 tools and a basic UI takes 3–6 h. Running an AP2 sample end to end takes 1–3 h if a Gemini key is available.

### Gaps
- I did not verify how fast the MCP SDKs (Python, TS) adopted 2026-07-28. Check the SDK changelogs before relying on stateless features.
- A2A's exact governance home (inside AAIF or separate) is unconfirmed.

---

## 2. Agent payment and mandate protocols: AP2, x402, ACP, Visa, Mastercard, KYA, UCP. What can students use in test mode?

### Takeaway
Students can really use two of these: **AP2**, open source with runnable Python, Go and Android samples including an x402 flow, and **x402**, an open spec with a free public testnet facilitator on Base Sepolia and other testnets. **ACP** is an open spec (beta, Apache-2.0), but Stripe's Shared Payment Token test helpers are documented as private preview. **Visa TAP** has a sample repo under Visa developer terms. **Mastercard Agent Pay** needs partner onboarding. KYA is a set of competing early efforts (DIF KYA-OS, ERC-8004, Skyfire KYAPay) that are good to cite and borrow ideas from, not to integrate.

### Cited Findings
**AP2 (Google, Agent Payments Protocol)**
- [V] Repo `google-agentic-commerce/AP2`: Apache-2.0, 3.2k stars, v0.1.0 on 2025-09-16, **v0.2.0 on 2026-04-28** ("focuses on providing Human Not Present flows"), last push 2026-06-17 — [AP2 releases](https://github.com/google-agentic-commerce/AP2/releases)
- [V] Spec v0.2 replaced v0.1's Intent and Cart mandates with **Checkout Mandate + Payment Mandate**, each "open" (constraints pre-approved by the user) or "closed" (bound to one checkout), plus signed receipts usable as dispute evidence. The Human Not Present flow works like this: the user approves open mandates and the agent later presents agent-signed closed mandates — [AP2 spec](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md), [flows.md](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/flows.md), [glossary](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/glossary.md)
- [V] Mandate credential format: **SD-JWT VCs (`dc+sd-jwt`, ES256) presented over OpenID4VP**. ISO mDocs are mentioned as an alternative. Mandate types are `mandate.checkout.1`, `mandate.checkout.open.1`, `mandate.payment.1` and `mandate.payment.open.1` — [agent_authorization.md](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/agent_authorization.md), [checkout_mandate.md](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/checkout_mandate.md), [payment_mandate.md](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/payment_mandate.md)
- [V] There are five roles: Shopping Agent, Credential Provider, Merchant, Merchant Payment Processor and **Trusted Surface** (the UI that captures user consent). AP2 is "designed explicitly to be compatible with" UCP — [AP2 spec](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md)
- [V] Samples:
  - Python: human-present and human-not-present, each with cards and x402.
  - Go: human-present cards.
  - Android: digital payment credentials.
  - The Python HNP x402 sample is an autonomous purchase triggered by a mock price drop, built from Shopping Agent, Merchant (MCP), x402 Payment Processor (MCP) and x402 Credentials Provider (MCP) agents.
  - Source: [AP2 HNP x402 sample](https://github.com/google-agentic-commerce/AP2/tree/main/code/samples/python/scenarios/a2a/human-not-present/x402)

**x402 (HTTP 402 payments)**
- [V] The x402 Foundation launched under the Linux Foundation on **2 April 2026**, and Coinbase completed its contribution of the protocol. There were 40 members at launch, and the premier members are AWS, American Express, Cloudflare, Coinbase, Google, Mastercard, Shopify, Solana Foundation, Stripe and Visa — [Coinbase CDP docs](https://docs.cdp.coinbase.com/x402/support/x402-foundation)
- [V] Repo `x402-foundation/x402`: 6.7k stars, Apache-2.0, pushed 2026-10-15. SDKs are TypeScript, Python and Go (`github.com/x402-foundation/x402/go/v2`) — [x402-foundation/x402](https://github.com/x402-foundation/x402)
- [V] The public x402.org facilitator is testnet-only and is the default in the x402 packages. It supports:
  - Base Sepolia `eip155:84532`, with USDC `0x036CbD53842c5426634e7929541eC2318f3dCF7e` using EIP-3009 `transferWithAuthorization`
  - Solana Devnet
  - Stellar, Aptos, Hedera and XRPL testnets
  - Source: [x402 network & token support](https://docs.x402.org/core-concepts/network-and-token-support)
- [V] The README warns not to treat the public facilitator as the production path for mainnet — [x402 README](https://github.com/x402-foundation/x402)
- [S] Adoption: 169M cumulative transactions on Base by July 2026, but Artemis estimates about 50% are artificial or wash activity — [Forkast](https://forkast.news/?p=127425)

**ACP (OpenAI + Stripe Agentic Commerce Protocol)**
- [V] Repo `agentic-commerce-protocol/agentic-commerce-protocol`: Apache-2.0, 1.6k stars, status **Beta**, maintained by OpenAI and Stripe. Spec versions are 2025-09-29, 2025-12-12, 2026-01-16, 2026-01-30 and 2026-04-17 (cart, feed, orders, authentication, MCP) — [ACP repo](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol)
- [S, from Stripe docs snippets] Stripe has test helpers that create a granted Shared Payment Token from a test PaymentMethod (`pm_card_visa`) with a currency cap, maximum amount and expiry, and `SharedPaymentGrantedToken` / `SharedPaymentIssuedToken` objects were added 2026-04-22. The docs mark this area as **private preview** — [Stripe agentic commerce testing](https://docs.stripe.com/agentic-commerce/testing), [SPT concepts](https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens), [changelog](https://docs.stripe.com/changelog/dahlia/2026-04-22/shared-payment-granted-token)
- [S] Joining Instant Checkout requires contacting Stripe, so it is not self-serve — [Stripe blog](https://stripe.com/ae/blog/developing-an-open-standard-for-agentic-commerce)

**UCP (Universal Commerce Protocol)**
- [V] Repo `Universal-Commerce-Protocol/ucp`: Apache-2.0, 3.4k stars, latest release v2026-08-25 — [UCP repo](https://github.com/Universal-Commerce-Protocol/ucp)
- [S] Google launched UCP in January 2026 with Shopify, Etsy, Wayfair, Target and Walmart. It is compatible with AP2 and integrates over APIs, A2A and MCP — [The New Stack](https://thenewstack.io/shopify-walmart-endorse-googles-new-open-commerce-protocol/), [i-programmer](https://www.i-programmer.info/news/105-artificial-intelligence/18597-google-launches-open-source-standard-for-agentic-commerce.html)

**Visa and Mastercard**
- [V] `visa/trusted-agent-protocol`: 213 stars, last push 2025-10-28. Its licence is the **Visa Developer Center Terms of Use plus TAP Product Terms, not an OSI licence**. TAP has agents sign each request (timestamp, session id, key id, algorithm), bound to the merchant domain and the operation — [visa/trusted-agent-protocol](https://github.com/visa/trusted-agent-protocol)
- [S] Visa and Mastercard both require agents to register public keys in a well-known directory and to sign requests with HTTP Message Signatures. Cloudflare implements this "Web Bot Auth" style verification — [Cloudflare blog](https://blog.cloudflare.com/secure-agentic-commerce/)
- [S] Mastercard Agent Pay opened to developer preview in October 2025, with agentic tokens via the Mastercard Token Service — [paz.ai](https://www.paz.ai/glossary/visa-trusted-agent-protocol), [atxp.ai](https://atxp.ai/blog/visa-trusted-agent-protocol-explained)

**KYA (Know Your Agent)**
- [S, from DIF's own blog] Vouched donated its KYA specification to DIF in March 2026, where it is now "KYA-OS", an identity and delegation standard across agentic protocols — [DIF blog](https://blog.identity.foundation/kya-os/)
- [V] **ERC-8004 "Trustless Agents"**: status Draft, created 2025-08-13. It defines three registries: Identity (ERC-721 agentId pointing to a registration file that can link an A2A Agent Card and an MCP endpoint), Reputation (signed feedback) and Validation (0–100 validator scores via re-execution, zkML or TEE) — [EIP-8004](https://eips.ethereum.org/EIPS/eip-8004)
- [S] ERC-8004 registries went live on Ethereum mainnet on 29 Jan 2026, and Skyfire's KYAPay signed-token approach has been submitted as an IETF draft — [BlockEden](https://blockeden.xyz/blog/2026/04/26/kya-know-your-agent-new-kyc-a16z-skyfire-fatf-compliance-battleground/)

### Inferences
- [I] **Usable in test mode within 72 hours:**
  - AP2: run the samples, or re-implement open and closed mandates as SD-JWT VCs in your own agent.
  - x402 on Base Sepolia or Solana Devnet with faucet USDC, which yields real testnet transaction hashes and so qualifies for the on-chain bonus.
  - Stripe test mode for ordinary PaymentIntents. SPT helpers only if the account has preview access.
  - ACP and UCP as specs to model the checkout JSON on.
- [I] **Not usable:** Visa Intelligent Commerce and Mastercard Agent Pay production or sandbox APIs (onboarding or partner approval). Teams can still copy the TAP pattern of signed agent requests with HTTP Message Signatures using their own keys.
- [I] The strongest narrative for "AI as a financial participant" is the AP2 v0.2 open/closed mandate split. A student sets an *open* mandate once, for example "pay up to CNY 6,000 rent to landlord X monthly; tuition only to university Y". The agent produces *closed* mandates per transaction, and each one is verified against the open mandate before execution. That is directly demonstrable and maps onto the security and compliance criterion.
- [I] With the EIP-3009 flow, the x402 client only signs an authorisation and the facilitator submits the transaction. The agent wallet therefore needs testnet USDC and does not need ETH for gas. This follows from the x402 design; confirm when testing.
- [E] Setup: x402 paywalled API plus agent client on Base Sepolia takes 2–4 h. AP2 sample run takes 1–3 h. A self-built mandate layer (SD-JWT VC issue/verify plus constraint check) takes 4–8 h.

### Gaps
- Official Mastercard Agent Pay and Visa Intelligent Commerce developer pages returned 404 or 403, so sandbox terms are unverified.
- Reclaim, x402 and Circle facilitator rate limits are not documented.
- I could not confirm whether Stripe SPT test helpers are callable from a standard test account without preview enrolment.

---

## 3. Interledger Open Payments / Rafiki and Mojaloop as a local cross-border sandbox

### Takeaway
**Rafiki's Local Playground** is the best free, local "two banks plus cross-border-style payment" sandbox. It runs two peered mock account servicers in Docker, and Open Payments gives a third-party agent **grant-based consent**: outgoing payments require interactive user approval and return a scoped access token. That is exactly the "AI as participant with delegated authority" story. **Mojaloop** has a docker-compose core test harness, but it is heavier and less agent-oriented.

### Cited Findings
- [V] `interledger/rafiki`: Apache-2.0, 360 stars, latest v2.4.5 (2026-07-16), pushed 2026-10-14. `interledger/open-payments`: Apache-2.0, pushed 2026-10-15 — [rafiki](https://github.com/interledger/rafiki), [open-payments](https://github.com/interledger/open-payments)
- [V] The Local Playground runs Cloud Nine Wallet (primary) and Happy Life Bank (secondary) via `pnpm localenv:compose up`, with TigerBeetle or Postgres as the ledger. A Bruno collection walks through wallet-address lookups, then grants for incoming payments, quotes and outgoing payments. **Outgoing payments need interactive consent**: you follow the redirect, the user approves, and you call `continue` to get the access token. Prerequisites are Docker and pnpm — [Rafiki Local Playground](https://rafiki.dev/integration/playground/overview)
- [V] The hosted **Interledger Test Network** has a Test Wallet at wallet.interledger-test.dev and a test e-commerce shop at boutique.interledger-test.dev. The repo is Apache-2.0, v1.3.0 (2026-10-12) — [interledger/testnet](https://github.com/interledger/testnet)
- [S] Rafiki is intended for regulated account servicing entities, not individual developers, for production use — [interledger.org Rafiki](https://interledger.org/tech/rafiki)
- [V] Mojaloop `ml-core-test-harness`: v2.15.1 (2026-02-03), pushed 2026-08-19. Start it with `docker-compose --profile all-services --profile ttk-provisioning --profile ttk-tests up`. It includes the Testing Toolkit and a live sequence-diagram UI. Mojaloop files are Apache-2.0 per the TTK licence — [ml-core-test-harness](https://github.com/mojaloop/ml-core-test-harness), [ml-testing-toolkit LICENSE](https://github.com/mojaloop/ml-testing-toolkit)
- [V] `mojaloop/mini-loop` was last pushed 2024-10, and the main `mojaloop/mojaloop` docs repo 2025-03. Both are stale — [mini-loop](https://github.com/mojaloop/mini-loop)
- [S] Mojaloop docs describe the core test harness as a minimal single-node docker-compose stack without production components — [Mojaloop deployment tools](https://docs.mojaloop.io/product/features/tools.html)

### Inferences
- [I] **Rafiki is the more natural fit.** Open Payments grants (GNAP-style, with interactive consent and limits) are a real, standards-based form of "agent spending authority". Judges see a mock bank asking the student to approve the agent's grant, and the grant and payment logs serve as the "sandbox operation logs" evidence.
- [I] I could not verify cross-currency (for example CNY→USD) between the two playground instances. The safe framing is that the team's FX quote service, using Frankfurter rates, prices the transfer while Rafiki moves the asset.
- [E] Rafiki playground: 1–3 h on Linux, macOS or WSL2, more on native Windows. Agent integration via the Open Payments Node SDK: another 4–6 h. Mojaloop harness: 3–6 h and RAM-hungry, so only worth it if the idea is explicitly about an instant-payment switch.

### Gaps
- Multi-asset or cross-currency support in the playground, and the RAM and time footprint of the Mojaloop harness, are not documented in the sources I read.

---

## 4. Verifiable credentials and DIDs: W3C VC 2.0 status and libraries

### Takeaway
VC 2.0 has been a W3C Recommendation family since May 2025. The live, permissively licensed (Apache-2.0) libraries in Oct 2026 are **Veramo** (TS, now under DIF), **walt.id identity** (Kotlin/JVM with REST services) and **Credo-ts** (OpenWallet Foundation). **SpruceID didkit is archived.** AP2 already uses SD-JWT VCs, so SD-JWT VC is the pragmatic format.

### Cited Findings
- [V] The W3C `vc-data-model` repo (spec "Verifiable Credentials v2.0") shows `previousPublishDate: "2025-05-15"`. The repo is now an Editor's Draft for maintenance, pushed 2026-10-15 — [w3c/vc-data-model](https://github.com/w3c/vc-data-model). (The w3.org TR page returned 403 to my fetch. The Recommendation status on that date is from my background knowledge and is consistent with the publish date.)
- [V] Veramo: Apache-2.0, now at `decentralized-identity/veramo` (redirected from `uport-project`), release @veramo/utils 7.0.2 on 2026-09-23, pushed 2026-10-15 — [decentralized-identity/veramo](https://github.com/decentralized-identity/veramo)
- [V] walt.id `waltid-identity`: Apache-2.0, v1.2.0 on 2026-10-15 — [walt-id/waltid-identity](https://github.com/walt-id/waltid-identity)
- [V] Credo-ts: Apache-2.0, OpenWallet Foundation, v0.7.2 on 2026-10-01 — [openwallet-foundation/credo-ts](https://github.com/openwallet-foundation/credo-ts)
- [V] `spruceid/didkit` was **archived** (last push 2025-07-10). `spruceid/ssi` (Rust) is still active (pushed 2026-10-15) — [spruceid/didkit](https://github.com/spruceid/didkit), [spruceid/ssi](https://github.com/spruceid/ssi)
- [V] AP2 mandates use SD-JWT VCs over OpenID4VP — [AP2 agent_authorization.md](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/agent_authorization.md)
- [V] WeIdentity (WeBank's DID/VC stack) is effectively dormant; see section 13 — [WeBankBlockchain/WeIdentity](https://github.com/WeBankBlockchain/WeIdentity)

### Inferences
- [I] For a TS/Python team, use **Veramo (TS)** or a plain SD-JWT library to issue three credentials: "Enrolled student at University Y", "Proof of funds ≥ X" and "Agent mandate". Use **walt.id** only if someone is comfortable with the JVM or Docker REST services.
- [I] Anchoring credential status or revocation hashes on FISCO BCOS is a natural way to involve WeBank tech without depending on dormant WeIdentity code (section 13).
- [E] Issuing and verifying an SD-JWT VC or JWT-VC with did:key in Veramo: 2–4 h. Adding a status list or revocation anchored on a chain: another 2–3 h.

### Gaps
- I did not fetch the official W3C TR page (403), so the list of companion Recommendations (Data Integrity, VC-JOSE-COSE, Bitstring Status List, Controlled Identifiers) is from memory and unverified this session.

---

## 5. zkTLS and ZK proofs over web data: can a team prove "balance ≥ X" or "tuition paid" from a (mock) bank page in 72 hours?

### Takeaway
**Feasible only as a stretch goal, and only against a mock site the team controls.** TLSNotary is open source (MIT or Apache-2.0) but explicitly alpha ("should not be used in production"), and its browser JS package was archived. Reclaim is the most turnkey but relies on Reclaim's hosted infrastructure and providers. zkPass and Opacity are vendor networks with mostly secondary documentation. A selective-disclosure "balance ≥ X" proof is a credible demo; real bank sites are not.

### Cited Findings
- [V] `tlsnotary/tlsn`: dual MIT/Apache-2.0, latest **v0.1.0-alpha.15** (2026-05-21), pushed 2026-10-15. The README says the project is "under active development and should not be used in production. Expect bugs and regular major breaking changes" — [tlsnotary/tlsn](https://github.com/tlsnotary/tlsn)
- [V] `tlsnotary/tlsn-js` (browser bindings) was **archived** (last release alpha.12, June 2025) — [tlsnotary/tlsn-js](https://github.com/tlsnotary/tlsn-js)
- [V] The official quick start offers four Rust examples (Basic Verification, Proxy Verifier, Simple Attestation with a Notary, and ZK age verification with Noir) plus a browser-extension plugin tutorial. It is an Ethereum Foundation project — [TLSNotary quick start](https://tlsnotary.org/docs/quick_start/)
- [S] The PSE roadmap lists 1.0 "Production Ready Protocol" as next. TLS 1.3 support and the web/mobile SDK are in progress. The Chrome extension v0.1.0.1501 (June 2026) notes it is not independently audited — [PSE master map](https://pse.dev/mastermap/tlsnotary), [Chrome listing mirror](https://www.chromeboard.com/extension/tlsnotary-gnoglgpcamodhflknhmafmjdahcejcgg)
- [V] Reclaim:
  - Developers build providers with an AI agent or the devtool (dev.reclaimprotocol.org) "for any website whose logged-in data you want to verify".
  - SDKs exist for Node/web, Flutter, React Native, Kotlin and Swift. No Python SDK is listed.
  - Verification takes 2–30 s, and results go to the app's backend.
  - zkFetch proves API calls without a user login.
  - Source: [Reclaim docs](https://docs.reclaimprotocol.org/)
- [V] The `reclaimprotocol/reclaim-js-sdk` repo has no licence file detected and was pushed 2026-10-12 — [reclaim-js-sdk](https://github.com/reclaimprotocol/reclaim-js-sdk)
- [S] Reclaim's free tier is 25 verifications per month — [madeonsol](https://madeonsol.com/compare/reclaim-protocol-vs-crossmint)
- [V] zkPass `Transgate-JS-SDK` repo: no licence detected, pushed 2026-10-08 — [zkPassOfficial/Transgate-JS-SDK](https://github.com/zkPassOfficial/Transgate-JS-SDK)
- [S] zkPass uses VOLE-based ZK. The TransGate extension supports 200+ schemas from 70+ sources — [Paragraph](https://paragraph.xyz/@jordan981/zktls-unlocking-crypto-consumer-apps), [BlockEden](https://blockeden.xyz/blog/2026/03/19/zktls-zero-knowledge-transport-layer-security-privacy-preserving-identity-web3/)
- [S] Opacity Network does MPC-TLS built on TLSNotary, plus TEEs and EigenLayer AVS slashing — [BlockEden](https://blockeden.xyz/blog/2026/03/19/zktls-zero-knowledge-transport-layer-security-privacy-preserving-identity-web3/)
- [V] The OpacityLabs GitHub org's recent repos include `dcap-verify` (Intel SGX DCAP quote verifier) and `react-native-opacity`, which fits a TEE-heavy design — [OpacityLabs](https://github.com/OpacityLabs)

### Inferences
- [I] A realistic 72-hour zkTLS demo looks like this:
  1. Stand up a **mock bank web page or API over TLS 1.2** (since TLS 1.3 support is still in progress).
  2. Run TLSNotary's Rust attestation example with a local notary.
  3. Selectively disclose only `balance` and `currency`.
  4. Derive the "≥ X" predicate in the verifier, or with the Noir example pattern, to issue a "Proof of funds" VC.
- [I] Present it honestly as "privacy-preserving proof-of-funds for visa and tuition, demo against a mock bank". Proving data from real bank sites is out of scope: alpha software, unaudited, likely to hit TLS 1.3, and bank ToS issues.
- [I] Reclaim needs the target site reachable by Reclaim's attestor infrastructure and a login flow, so a localhost mock bank will probably not work without public hosting. That is an inference; their docs don't cover mock sites.
- [E] TLSNotary Rust example running locally: 3–6 h, including the Rust toolchain build. Adapting it to a custom mock-bank JSON and verifier service: another 6–10 h. Total roughly 1 person-day, high risk.

### Gaps
- No primary source on Reclaim pricing or limits, or on zkPass and Opacity developer onboarding. No independent audits for any of the four.

---

## 6. Programmable and purpose-bound money: MAS PBM, e-CNY programmability, stablecoin testnets, ERC-4337 smart accounts with spending policies

### Takeaway
**ERC-7291 (Purpose Bound Money, from MAS Project Orchid) is a Final ERC with a reference implementation.** It is the cleanest open blueprint for "tuition or living-allowance money that can only be spent for its purpose", and its Solidity runs on Base Sepolia or FISCO BCOS. e-CNY smart contracts are real but not open to outside developers. **Circle testnet USDC and faucets are free and instant.** ERC-4337 tooling is mature, while permission standards (ERC-7715/7710) are still Draft.

### Cited Findings
- [V] **ERC-7291 Purpose Bound Money**:
  - Status **Final**, created 2023-06-24, authors Orchid-Dev et al.
  - An ERC-1155 PBM wrapper holds an ERC-20-compatible "sovToken" (for example a stablecoin) and releases it only when conditions are met.
  - Business rules sit in core logic plus plugins and hooks.
  - A token manager handles token types, and a compliance guard keeps merchant whitelists and blacklists.
  - A reference implementation is linked under `/assets/eip-7291/`.
  - Source: [EIP-7291](https://eips.ethereum.org/EIPS/eip-7291)
- [S] The PBM pilot involved Grab, StraitsX, the Singapore Tourism Board, MAS and local banks. Reviewers noted discrepancies between the whitepaper, the definitions and the sample implementation — [Ethereum Magicians](https://ethereum-magicians.org/t/eip-7291-purpose-bound-money/14973)
- [S] ERC-7994 extends PBM to ERC-20 with multi-condition unlocking — [ERC-7994](https://eips.ethereum.org/EIPS/eip-7994)
- [S] e-CNY smart contracts are used for government subsidies, retail marketing and prepaid-fund management. The PBOC reviews and registers contract templates, and contracts must pass compliance reviews and tests before becoming templates — [Forkast](https://forkast.news/china-to-speed-up-expand-digital-yuan-smart-contracts-pboc-official-says), [The Block (whitepaper)](https://www.theblock.co/amp/post/111648/china-digital-yuan-whitepaper-smart-contract-programmability)
- [S] A Frankfurt School working paper (May 2026) says the e-CNY rollout is still in a pilot phase, and the PBOC introduced interest-bearing e-CNY wallet balances from 2026 — [SGC WP 09](https://sgc.frankfurt-school.de/wp-content/uploads/2026/05/SGC-WP-09_May-2026.pdf)
- [S, from Circle docs snippets] Circle's public faucet (faucet.circle.com) needs no account and gives 10 USDC per request, once per 24 h per testnet. The Developer Console faucet gives 20 USDC per request for Circle wallets and needs a free developer account. Networks include Base Sepolia, Ethereum Sepolia, Arbitrum Sepolia, Avalanche Fuji, Solana Devnet and more — [Circle faucet docs](https://developers.circle.com/wallets/developer-console-faucet), [fund a testnet wallet](https://developers.circle.com/wallets/fund-a-testnet-wallet)
- [S] CCTP V2 (Standard Transfer, Fast Transfer, Hooks) runs on testnets including Base Sepolia (domain 6). V2 contracts share addresses across EVM chains via CREATE2 — [Circle supported domains](https://developers.circle.com/cctp/supported-domains), [eth_defi constants](https://web3-ethereum-defi.readthedocs.io/api/cctp/_autosummary_cctp/eth_defi.cctp.constants.html)
- [V] `circlefin/evm-cctp-contracts`: Apache-2.0, last release 2025-10-01 — [evm-cctp-contracts](https://github.com/circlefin/evm-cctp-contracts)
- [V] ERC-4337 reference `eth-infinitism/account-abstraction`: **GPL-3.0**, v0.9.0 (2025-11-16) — [account-abstraction](https://github.com/eth-infinitism/account-abstraction)
- [V] `pimlicolabs/permissionless.js`: MIT, v0.5.0 (2026-10-15) — [permissionless.js](https://github.com/pimlicolabs/permissionless.js)
- [V] `MetaMask/delegation-framework` (ERC-7710 delegations): Apache-2.0, pushed 2026-10-16 — [delegation-framework](https://github.com/MetaMask/delegation-framework)
- [V] `erc7579/erc7579-implementation` (modular accounts): MIT — [erc7579-implementation](https://github.com/erc7579/erc7579-implementation)
- [V] **ERC-7715**: Draft, created 2024-05-24. It defines `wallet_requestExecutionPermissions` (plus get-supported, get-granted and revoke), with permission types such as `native-token-allowance` and `erc20-token-allowance` and an `expiry` rule — [EIP-7715](https://eips.ethereum.org/EIPS/eip-7715)
- [S] Session keys are usually bounded by a spend cap, a contract allowlist, function selectors and an expiry. MetaMask, Biconomy, Rhinestone and Alchemy ship implementations, but interoperability is limited — [Eco](https://eco.com/support/en/articles/15254038-erc-7715-session-keys-2026-granular-permissions-explained)

### Inferences
- [I] The most natural programmable-money demo is **"Purpose-Bound Tuition and Allowance"**:
  - Parents or a sponsor wrap testnet USDC into a PBM that can be redeemed only by whitelisted payees (university, landlord, insurer), with optional expiry and monthly caps.
  - The agent can trigger redemptions within those rules but cannot divert funds.
  - On-chain transaction hashes provide the bonus evidence.
- [I] Simplify ERC-7291 to a single ERC-20 wrapper with a whitelist, caps and an expiry rather than the full ERC-1155 design.
- [I] ERC-4337 session keys are an alternative "agent spending policy" mechanism. On public testnets they need a bundler and paymaster (Pimlico or ZeroDev free tiers, not verified this session), which adds risk. A plain smart-contract allowance or PBM is more robust in 72 hours.
- [I] e-CNY programmability can only be *referenced* (as the conceptual analogue judges know). There is no public developer sandbox.
- [E] Simplified PBM in Solidity (Foundry or Hardhat), deployed to Base Sepolia or FISCO BCOS: 4–8 h. Faucet funding: 10 min. A 4337 session-key wallet with permissionless.js: 6–12 h, medium-high risk.

### Gaps
- I did not open the ERC-7291 reference implementation's README, so its licence and completeness are unchecked.
- I found no public e-CNY developer API or sandbox, and none is believed to exist.
- Pimlico and ZeroDev free-tier limits are unverified.

---

## 7. Regulation context (brief): GENIUS Act, Hong Kong stablecoin licensing, mBridge, Project Nexus

### Takeaway
GENIUS Act rules are still being finalised (OCC final rule promised by November 2026, Act effective no later than 18 Jan 2027). Hong Kong's regime is live, with the first two licences issued on 10 Apr 2026. mBridge continues without the BIS, and its 2026 status is unclear. Nexus now has an operating company and targets go-live in 2027.

### Cited Findings
- [S] The statutory deadline for final GENIUS Act rules was 18 July 2026, and coordinated final rules were not visible by then. The Act takes effect on the earlier of 18 Jan 2027 or 120 days after final rules. Treasury's AML and sanctions NPRM was published 10 Apr 2026 (comments closed 9 June). The FDIC proposed its rule in April 2026 — [Chapman GENIUS tracker](https://www.chapman.com/publication-genius-act-rulemaking-tracker), [Stablecoin Insider](https://stablecoininsider.org/the-genius-act-july-18-rulemaking-deadline-has-arrived-the-rules-are-not-ready/)
- [S] OCC Comptroller Gould said in August that the OCC "will have a final rule out by November", with issuer application processing from 2027 — [LCX](https://lcx.com/en/cryptonews/occ-head-promises-final-genius-rules-by-november)
- [V] The HKMA granted the **first stablecoin issuer licences on 10 April 2026** to Anchorpoint Financial Ltd and HSBC under the **Stablecoins Ordinance (Cap. 656)**, effective that day, with launches "in the coming few months" — [HKMA press release](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/04/20260410-4/)
- [S] Anchorpoint is a joint venture of Standard Chartered HK, HKT and Animoca Brands. 36 applications were reviewed. The Ordinance took effect on 1 Aug 2025 — [Charltons](https://www.charltonslaw.com/hkma-issues-first-stablecoin-issuer-licences/), [Stablecoin Insider](https://stablecoininsider.org/hkma-stablecoin-issuer-licenses/)
- [S] The BIS "graduated out" of mBridge in late 2024. The participating central banks (China, Hong Kong, Thailand, UAE, plus Saudi Arabia from June 2024) continue on their own. A claim that Saudi Arabia has since exited is unverified — [Cointelegraph](https://cointelegraph.com/news/bis-exits-project-mbridge-amid-sanctions-concerns), [MNI](https://marketnews.com/mni-brief-mbridge-project-to-move-forward-despite-bis-exit)
- [S] The central banks of India, Indonesia, Malaysia, the Philippines, Singapore and Thailand incorporated **Nexus Global Payments** in 2025, and the BIS handed over the project. A PayNet–NETS joint venture is the technical operator, development started in early 2026, and **go-live is targeted for 2027** — [The Asian Banker](https://www.theasianbanker.com/press-releases/nexus-appoints-paynet-nets-joint-venture-as-technical-operator-for-global-instant-payments-network), [BIS Nexus](https://www.bis.org/project/nexus)

### Inferences
- [I] For the pitch, keep regulation to one compliance slide: the agent only moves *test* assets; a production version would use licensed stablecoin issuers (HK Cap. 656, US GENIUS) or licensed remittance partners; and cross-border instant-payment rails like Nexus (2027) are the future connection point. Do not claim integration with mBridge or Nexus.

### Gaps
- No primary-source confirmation of GENIUS final rules as of 16 Oct 2026, and no 2026 primary source on mBridge's status.

---

## 8. Sandboxes and data: Plaid, TrueLayer, Wise, Stripe test mode, Circle sandbox, free FX APIs, mock and open-banking simulators

### Takeaway
Instantly usable for free: **Plaid Sandbox**, **Stripe test mode**, **Circle faucets and testnets**, **Frankfurter FX** (MIT, ECB and other central-bank sources, public API or self-hosted), **Rafiki playground** and the **Interledger Test Wallet**. **Wise** gives a personal sandbox account with email and password, but partner API credentials require a partnership. **TrueLayer** reportedly has free sandbox sign-up (unverified).

### Cited Findings
- [V] Plaid Sandbox is a "free and fully-featured environment". Keys come from the Plaid Dashboard, and the test login is `user_good` / `pass_good`. Auth, Identity, Transactions, Investments, Liabilities, Assets, Statements, Signal and Transfer are testable, plus custom test users and `/sandbox/public_token/create`. UK and EU Payment Initiation may need special enablement — [Plaid Sandbox docs](https://plaid.com/docs/sandbox/)
- [S] Plaid's free real-data Trial plan is limited to US and Canada teams created on or after 15 Apr 2026, capped at 10 Production Items — [Plaid support](https://support.plaid.com/hc/en-us/articles/16110110883479-How-are-Sandbox-Production-Trial-plan-and-Limited-Production-different)
- [S, from Wise docs and help snippets] Partners receive sandbox Client ID and Secret only once a partnership begins, and personal tokens "are not meant to be used for partner integrations". Individual developers can create a sandbox account with email and password, but generating a personal API token needs 2-step verification. The sandbox API is at `api.wise-sandbox.com` (with an mTLS variant). The sandbox doesn't support all currency routes, and Sandbox v2 tokens expire every 12 h — [Wise environments](https://docs.wise.com/guides/developer/environments), [Wise getting started](https://docs.wise.com/guides/developer), [Wise help](https://wise.com/uk/help/articles/2958107/getting-started-with-the-api)
- [S] TrueLayer and Yapily offer free sandbox sign-up, according to a competitor's comparison — [Finexer blog](https://blog.finexer.com/open-banking-sandbox/)
- [S] Stripe test mode covers standard payments. Agentic Shared Payment Token test helpers exist but are in private preview — [Stripe agentic testing](https://docs.stripe.com/agentic-commerce/testing)
- [S] Circle faucets: see section 6 — [Circle faucet](https://developers.circle.com/wallets/developer-console-faucet)
- [V] **Frankfurter**: MIT, repo now `lineofflight/frankfurter` (2.0k stars, v2.6.1 on 2026-10-02). It is "an open-source currency data API that tracks daily exchange rates from central banks and official sources". The v2 API has `/v2/coverage`, `/v2/currencies` and provider filters (for example `providers=BIS`), a public endpoint at `api.frankfurter.dev`, and Docker self-hosting — [lineofflight/frankfurter](https://github.com/lineofflight/frankfurter)
- [V] Interledger Test Wallet and Test E-Commerce are publicly hosted — [interledger/testnet](https://github.com/interledger/testnet)

### Inferences
- [I] Best combination for a cross-border student scenario with no KYB:
  - **Plaid Sandbox** as the "home bank" data source (balances and transactions for a proof-of-funds check).
  - **Frankfurter** for FX quotes and fee transparency.
  - **Rafiki playground** as the payment-execution rail, or **Base Sepolia USDC** for the on-chain leg.
  - **Stripe test mode** to simulate paying tuition or a deposit by card.
  - A **self-built mock bank** (FastAPI) for anything else, such as a mock "PBOC-style" CNY account or a mock bank web page for zkTLS.
- [I] Skip Wise unless a personal sandbox token works on the first try. Its partner-only features (quotes and transfers for third parties) are what a remittance demo would need.
- [E] Plaid sandbox link plus balance pull: 1–2 h. Frankfurter: 15 min. Stripe test PaymentIntent: 1 h. Mock bank API: 2–3 h.

### Gaps
- TrueLayer's sandbox terms are not verified from TrueLayer's own docs (my fetch returned 404).
- I did not find an independent maintained "open banking simulator" (for example Berlin Group or UK OBIE mocks) to recommend over a self-built mock.

---

## 9. Compliance open source: Moov Watchman, OpenSanctions, Marble, other AML and fraud engines

### Takeaway
**Moov Watchman** (Apache-2.0, one Docker command, OFAC/EU/UK/UN lists, experimental MCP server) is the obvious sanctions-screening tool. **OpenSanctions data is CC BY-NC 4.0**, so it is free for non-commercial hackathon use. **Marble is Elastic License 2.0** (source-available, not OSI): usable for a demo, but say "source-available". Tazama (Apache-2.0) and Jube (AGPL-3.0) are active alternatives for transaction monitoring.

### Cited Findings
- [V] Moov Watchman:
  - Apache-2.0, v1.2.2 (2026-10-13), 513 stars.
  - Its own README calls it "an open-source **sanctions screening engine**. One Docker command downloads OFAC (and EU, UK, UN, and related lists), indexes them in memory, and scores each customer or counterparty", with a 0–1 score.
  - Lists: OFAC SDN and Non-SDN, US CSL, FinCEN 311, EU, UK, UN, OpenSanctions Senzing files, plus CSV.
  - Interfaces: HTTP API, Go client, browser UI and an **experimental MCP** server.
  - Quick start: `docker run -p 8084:8084 -e INCLUDED_LISTS=us_ofac moov/watchman`.
  - Source: [moov-io/watchman](https://github.com/moov-io/watchman)
- [V] OpenSanctions data is licensed CC BY-NC 4.0. Internal screening in an organisation, redistribution in products and hosted per-query screening require a paid licence. Bulk data is "open for download" — [OpenSanctions licensing](https://www.opensanctions.org/licensing/)
- [V] The OpenSanctions code repo is MIT, and `yente` (its screening API) is MIT, v5.5.0 (2026-06-23) — [opensanctions/opensanctions](https://github.com/opensanctions/opensanctions), [opensanctions/yente](https://github.com/opensanctions/yente)
- [V] **Marble**:
  - Licence file is **Elastic License 2.0**. v1.11.0 on 2026-10-08, 616 stars.
  - Features: real-time transaction monitoring, sanctions/PEP screening, case manager, AI-assisted investigations, and "searchable and unalterable audit logs".
  - Quick start is Docker Compose, needing 4 GB RAM and 10 GB disk.
  - Source: [checkmarble/marble](https://github.com/checkmarble/marble), [LICENSE](https://github.com/checkmarble/marble/blob/main/LICENSE)
- [V] Tazama (`tazama-lf` org): Apache-2.0 repos active, for example rule-executer v4.0.0 (2026-07-23), tazama-helm and a configuration studio pushed in Oct 2026 — [tazama-lf](https://github.com/tazama-lf)
- [V] Jube AML/fraud transaction monitoring: **AGPL-3.0**, pushed 2026-10-16 — [jube-home/aml-fraud-transaction-monitoring](https://github.com/jube-home/aml-fraud-transaction-monitoring)

### Inferences
- [I] For 72 hours, use **Watchman (sanctions) plus about 10 hand-written, explainable AML and fraud rules** in the agent's policy layer. Examples: velocity, new payee plus large amount, structuring just under thresholds, mismatched names, high-risk corridor. Show the rule hit in the decision log.
- [I] Marble is impressive but heavy (4 GB RAM) and ELv2. Use it only if the idea is "fraud guardian" and someone owns its setup.
- [I] Tazama's background as a Linux Foundation and Gates Foundation-funded project is from memory and unverified this session; describe it only as an Apache-2.0 alternative.
- [E] Watchman: 15–30 min. Custom rules engine: 3–5 h. Marble: 2–4 h to run, plus 4–8 h to model data and rules.

### Gaps
- OpenSanctions' "free and non-commercial use" page (the exact eligibility wording for students and hackathons) was not retrieved.

---

## 10. Guardrails and policy: NeMo Guardrails, Llama Guard, Guardrails AI, OPA, AWS Cedar, OpenFGA. Which fits a permission-tier engine?

### Takeaway
Split the problem. For **authorization tiers** ("may this agent move CNY 5,000 to a new payee without step-up?"), use a deterministic policy engine. **Cedar** (Apache-2.0, CNCF Sandbox, analysable policies) or **OPA** (Apache-2.0, CNCF Graduated) both fit, and **OpenFGA** suits relationship-based "who can act for whom". For **LLM content safety and prompt injection**, use NeMo Guardrails or Llama Guard 4. Llama Guard 4 has a "Specialized Advice (financial)" category, but it is a gated 12B model.

### Cited Findings
- [V] **Cedar**: Apache-2.0, v4.13.0 (2026-09-15); **CNCF Sandbox, accepted 2025-10-08** — [cedar-policy/cedar](https://github.com/cedar-policy/cedar), [CNCF landscape.yml](https://github.com/cncf/landscape/blob/master/landscape.yml)
- [V] **OPA**: Apache-2.0, v1.21.2 (2026-10-12), 12.4k stars; **CNCF Graduated** — [open-policy-agent/opa](https://github.com/open-policy-agent/opa), [CNCF landscape.yml](https://github.com/cncf/landscape/blob/master/landscape.yml)
- [V] **OpenFGA**: Apache-2.0, v1.22.0 (2026-10-06); CNCF Incubating since 2025-10-28 — [openfga/openfga](https://github.com/openfga/openfga), [CNCF landscape.yml](https://github.com/cncf/landscape/blob/master/landscape.yml)
- [V] **NeMo Guardrails**: now at `NVIDIA-NeMo/Guardrails`, Apache-2.0, v0.24.1 (2026-09-16), 7.3k stars — [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)
- [V] **Guardrails AI**: Apache-2.0, v0.11.0 (2026-08-14), 7.5k stars — [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails)
- [V] **Llama Guard 4**:
  - 12B, natively multimodal safety classifier.
  - Hazard categories S1–S14 follow the MLCommons taxonomy, with **S6 "Specialized Advice" covering financial, medical and legal advice** and S14 code-interpreter abuse.
  - Licensed under the Llama 4 Community License (700M MAU threshold, "Built with Llama").
  - **Gated**: the access form asks for legal name, date of birth and organisation.
  - It pairs with Llama Prompt Guard 2 for prompt attacks.
  - Source: [HF meta-llama/Llama-Guard-4-12B](https://huggingface.co/meta-llama/Llama-Guard-4-12B)
- [V] The PurpleLlama repo (4.4k stars, pushed 2026-10-12) README still lists only Llama Guard 1–3, Prompt Guard and Code Shield, so the docs lag the models — [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama)

### Inferences
- [I] Recommended **permission-tier engine** design:
  - Cedar or OPA policies take inputs `{agent, principal(student), action(pay/convert/quote), amount, currency, payee_risk, corridor, mandate_id}`.
  - They return one of four tiers: T0 auto-execute, T1 notify, T2 step-up approval by the student in the UI, T3 deny and escalate.
  - The policy files are short, readable and testable. That gives judges concrete evidence for the 30% security score.
- [I] Choose **Cedar** for its readability and formal-analysis story (schema validation), or **OPA/Rego** if a team member knows it. OpenFGA adds value only if delegation graphs matter (parent → student → agent).
- [I] Use NeMo Guardrails (or simple input and output classifiers) for prompt injection, since the agent reads untrusted documents and web pages. Gated Llama Guard 4 needs a GPU or hosted inference, so treat it as optional.
- [E] Cedar or OPA policies plus tests: 2–4 h. NeMo Guardrails basic rails: 2–3 h. Llama Guard via a hosted API: 1–2 h, if access is granted.

### Gaps
- I did not verify (search budget exhausted) the reported 2025 move of core OPA maintainers to Apple or how it affected OPA governance. The repo itself is active (release 2026-10-12).

---

## 11. Document AI: Docling, PaddleOCR, Marker, MinerU for bank statements, admission letters and invoices

### Takeaway
**Docling (MIT, LF AI & Data)** and **PaddleOCR (Apache-2.0; strong on Chinese text, seals and tables)** are the licence-safe defaults. **Marker's code moved to Apache-2.0**, but its model weights are a modified OpenRAIL-M (free for research, personal use and startups under $5M). **MinerU 4.0** uses a custom "Apache-2.0 plus terms" licence with an attribution duty for online services.

### Cited Findings
- [V] **Docling**: MIT, v2.140.0 (2026-10-16), 69k stars, hosted by **LF AI & Data**, supports VLMs such as GraniteDocling-258M — [docling-project/docling](https://github.com/docling-project/docling)
- [V] **PaddleOCR**: Apache-2.0, v3.7.0 (2026-06-11), 91k stars.
  - PaddleOCR-VL-1.6 (0.9B) document VLM reports 96.3% on OmniDocBench v1.6 and handles seals and charts.
  - PP-StructureV3 converts PDFs and images to Markdown or JSON with cell coordinates.
  - PP-OCRv6 adds +4.6% detection and +5.1% recognition over v5.
  - Source: [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [V] **Marker**: repo `datalab-to/marker`, v2.0.0 (2026-07-20). "Our code is licensed under **Apache 2.0**… Our model weights use a modified AI Pubs Open Rail-M license (free for research, personal use, and startups under $5M funding/revenue)" — [datalab-to/marker](https://github.com/datalab-to/marker)
- [V] **MinerU 4.0**: release 4.0.12 on 2026-10-11, 82k stars.
  - The "MinerU Open Source License" is Apache-2.0 plus extra terms: a commercial licence is needed above 100M MAU or USD 20M monthly revenue, and online services must prominently attribute MinerU.
  - The default install runs CPU ONNX plus a llama.cpp VLM.
  - Source: [opendatalab/MinerU](https://github.com/opendatalab/MinerU), [LICENSE.md](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md)

### Inferences
- [I] Flag for the team: older write-ups and forks list **Marker as GPL-3.0** and **MinerU as AGPL-3.0**. Both changed (per current licence files), so cite the current licences in the README.
- [I] For Chinese admission letters, bank statements with seals (公章) and invoices (发票), **PaddleOCR (PP-StructureV3 or PaddleOCR-VL)** is the strongest licence-clean choice. For English PDFs and simple pipelines, **Docling** is the fastest to integrate.
- [I] Pair either one with an LLM extraction step into a strict JSON schema (amount, currency, issuer, date, account-holder name). Then cross-check extracted values against Plaid or mock-bank data as an anti-forgery check.
- [E] Docling or PaddleOCR pipeline into JSON: 1–3 h on CPU. With a VLM model: 2–4 h, faster on a GPU.

### Gaps
- No head-to-head benchmark on bank statements specifically.

---

## 12. Observability and audit: Langfuse, OpenTelemetry for agents, tamper-evident logs

### Takeaway
**Langfuse** (MIT core, self-host via Docker Compose; part of ClickHouse since Jan 2026) gives agent traces in minutes. **OpenTelemetry GenAI semantic conventions**, now in their own repo, include MCP and agent spans. MCP 2026-07-28 also standardises trace-context propagation. For tamper evidence, use a **hash-chained audit log whose periodic Merkle root is anchored on-chain** (FISCO BCOS or Base Sepolia). That is cheap, and it lines up with the "sandbox operation logs plus transaction hashes" requirement.

### Cited Findings
- [V] **Langfuse**: v4.62.0 (2026-10-16), 35.9k stars. The LICENSE is MIT except `ee/` directories, with copyright "© 2023-2026 ClickHouse, Inc.". The README says "since January 2026 we're part of ClickHouse" and "Run Langfuse on your own machine in 5 minutes using Docker Compose" — [langfuse/langfuse](https://github.com/langfuse/langfuse), [LICENSE](https://github.com/langfuse/langfuse/blob/main/LICENSE)
- [V] The OTel GenAI semantic conventions **moved to `open-telemetry/semantic-conventions-genai`** (created 2026-05-05, pushed 2026-10-14). It covers GenAI client spans, metrics, events, **MCP** and provider-specific conventions. The old pages in `semantic-conventions` are marked "Moved" — [semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai), [old agent-spans page](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-agent-spans.md)
- [V] OpenLLMetry (OTel instrumentation for LLMs): Apache-2.0, 0.62.4 (2026-09-29) — [traceloop/openllmetry](https://github.com/traceloop/openllmetry)
- [V] MCP 2026-07-28 documents propagating `traceparent`, `tracestate` and `baggage` in `_meta` — [MCP changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [V] Marble advertises "unalterable audit logs" as a feature, which shows the market expects tamper-evident audit — [checkmarble/marble](https://github.com/checkmarble/marble)

### Inferences
- [I] Audit design to show judges:
  1. Every agent step (intent, policy decision with tier, mandate id, tool call, result) goes into an append-only JSONL record with `prev_hash` → `hash`.
  2. Every N minutes or each session, the Merkle root is written to a FISCO BCOS "Evidence" contract (or Base Sepolia) and the transaction hash is shown in the UI.
  3. A "Verify log integrity" button recomputes the chain.
- [I] This one component serves three judging criteria: security and compliance (auditability), the on-chain bonus, and the required sandbox logs.
- [E] Langfuse self-host plus SDK instrumentation: 1–2 h. Hash-chain logger plus anchoring contract plus verify UI: 3–5 h.

### Gaps
- None material.

---

## 13. WeBank's own open source: FATE, FISCO BCOS, WeIdentity, WeDPR and newer AI projects. Natural uses and realistic setup times

### Takeaway
**FISCO BCOS is the only WeBank project that is clearly alive and practical in 72 hours.** It is v3.17.1 (Sept 2026), Apache-2.0, supports Solidity and an **Ethereum-compatible Web3 JSON-RPC since v3.9.0** (MetaMask, Remix, Hardhat), and starts locally as a 4-node chain with one script. WeBank's own **FinTechathon blockchain track has required FISCO BCOS in past years**. FATE and FATE-LLM have had no release since mid-2024 (FATE core has no commits since Nov 2024). WeIdentity has had no code commits since March 2024. WeDPR was rebuilt as a privacy-computing platform (v3.0.0, Dec 2024), and its components were last updated in March 2026. I found no new WeBank open-source AI agent framework.

### Cited Findings
**FISCO BCOS**
- [V] `FISCO-BCOS/FISCO-BCOS`: Apache-2.0, 2.6k stars, pushed 2026-10-16.
  - Releases: **v3.17.1 (2026-09-15)**, v3.17.0 (2026-08-24), v3.16.4 (2026-01-14), v3.16.3 (2025-11-29).
  - v3.17.0 is a security-hardening release merging fixes from a code security audit, 130+ PRs across consensus, txpool, sync, EVM and gateway.
  - v3.17.1 fixes Web3 RPC issues among other things.
  - Source: [FISCO-BCOS releases](https://github.com/FISCO-BCOS/FISCO-BCOS/releases)
- [V] Web3 JSON-RPC has been supported since **3.9.0**:
  - Enable it with `[web3_rpc] enable=true` on port 8545 and set `web3_chain_id` (for example 20200).
  - Enable `feature_balance` to use MetaMask, Remix, Hardhat and OpenZeppelin.
  - Websocket and CORS support for Web3 RPC arrived in 3.16.0.
  - Source: [FISCO docs: web3_usage.md](https://github.com/FISCO-BCOS/FISCO-BCOS-DOC/blob/master/3.x/zh_CN/docs/develop/web3_usage.md), [v3.16.0 release notes](https://github.com/FISCO-BCOS/FISCO-BCOS/releases/tag/v3.16.0)
- [V] Quick start:
  - `curl -#LO .../v3.17.0/build_chain.sh && bash build_chain.sh -l 127.0.0.1:4 -p 30300,20200` builds a 4-node Air chain (Ubuntu, CentOS or macOS).
  - The `-D` flag builds Docker-mode nodes (`fiscoorg/fiscobcos` image).
  - The interactive console needs Java.
  - Source: [Air installation](https://github.com/FISCO-BCOS/FISCO-BCOS-DOC/blob/master/3.x/zh_CN/docs/quick_start/air_installation.md), [build_chain docs](https://github.com/FISCO-BCOS/FISCO-BCOS-DOC/blob/master/3.x/zh_CN/docs/tutorial/air/build_chain.md)
- [V] SDKs:
  - **Java SDK** v3.8.0 (2024-09), pushed 2026-08 (Apache-2.0).
  - `bcos-c-sdk` pushed 2026-08.
  - **Python SDK** supports 3.x through a wrapper over the C SDK, but only Python 3.6–3.10 ("3.11+ not yet adapted"), with its last commit 2024-10-30 (MIT).
  - **Go SDK** v3.0.2 (2024-09), last push 2024-12.
  - Sources: [java-sdk](https://github.com/FISCO-BCOS/java-sdk), [python-sdk README](https://github.com/FISCO-BCOS/python-sdk), [go-sdk](https://github.com/FISCO-BCOS/go-sdk), [bcos-c-sdk](https://github.com/FISCO-BCOS/bcos-c-sdk)
- [V] The `FISCO-BCOS/hackathon` repo collects **FinTechathon** entries for 2020–2024. For 2022–2024 its README says the blockchain track "要求参赛项目基于FISCO BCOS区块链底层开源平台、微众区块链系列开源技术设计并开发" (projects must be built on FISCO BCOS and WeBank blockchain open-source tech). Entries were still being committed in June 2026 — [FISCO-BCOS/hackathon](https://github.com/FISCO-BCOS/hackathon)
- [V] Related tooling: WeBASE (management console; WeBASE-Doc pushed 2026-09) and an `op-stack-e2e-tests` repo under the FISCO org (pushed 2026-10) — [WeBankBlockchain org](https://github.com/WeBankBlockchain), [FISCO-BCOS org](https://github.com/FISCO-BCOS)

**FATE / FATE-LLM**
- [V] `FederatedAI/FATE`: Apache-2.0, 6.1k stars, latest **v2.2.0 (2024-07-31)**, last commit 2024-11-19. Its README calls it "an open source project hosted by Linux Foundation" — [FederatedAI/FATE](https://github.com/FederatedAI/FATE)
- [V] `FederatedAI/FATE-LLM`: Apache-2.0, latest release v2.2.0 (2024-08-02). Only README and documentation commits since, the latest on 2026-09-04 — [FederatedAI/FATE-LLM](https://github.com/FederatedAI/FATE-LLM)
- [S] Recent FATE-LLM features include FedMKT (federated knowledge transfer between large and small LMs), InferDPT (differentially private inference on black-box LLMs) and FATE-LLM Evaluate. Standalone install needs FATE ≥ v2.2.0 plus FATE-Flow — [FATE-LLM releases](https://github.com/FederatedAI/FATE-LLM/releases/latest)

**WeIdentity**
- [V] `WeBankBlockchain/WeIdentity`: Apache-2.0, 1.15k stars. Latest release **v3.1.0-rc.1 (2023-04-28)**, last code commit **2024-03-13** (repo pushed 2025-04-18). Sibling repos (Build-Tools, Kit, Rest-Service) were last pushed April 2025. It implements W3C DID and VC on FISCO BCOS — [WeIdentity](https://github.com/WeBankBlockchain/WeIdentity), [WeIdentity docs](https://weidentity-en.readthedocs.io), [FISCO doc: Distributed Identity](https://fisco-bcos-30-en-document.readthedocs.io/en/latest/docs/advanced_function/distributed_identity.html)

**WeDPR**
- [V] `WeBankBlockchain/WeDPR` (new platform): Apache-2.0, v3.0.0 (2024-12-16), pushed 2025-03. It is WeBank's multi-party privacy-computing platform:
  - PSI (隐私求交集) and anonymous query (匿踪查询)
  - Private SQL joint analysis
  - Federated LR and LGBM training and prediction
  - Gateway, site and admin consoles
  - Source: [WeBankBlockchain/WeDPR](https://github.com/WeBankBlockchain/WeDPR)
- [V] `WeDPR-Component` and `WeDPR-Lab-Java-SDK` were pushed 2026-03-04. The older `WeDPR-Lab-Core` (Rust crypto: hidden payments, anonymous voting and similar) is at v1.6.0 (2023-01), last push 2024-05 — [WeDPR-Component](https://github.com/WeBankBlockchain/WeDPR-Component), [WeDPR-Lab-Core](https://github.com/WeBankBlockchain/WeDPR-Lab-Core)

**Other WeBank open source**
- [V] The `WeBankFinTech` org's recently active repos are data and ML platform tools, not agent frameworks: Prophecis (cloud-native ML platform, pushed 2026-09), Schedulis, DataSphereStudio, Qualitis, DeFiBus, and the fes.js front-end framework — [WeBankFinTech](https://github.com/WeBankFinTech)
- [V] GitHub orgs named `WeBank`, `webank-ai` and `WeBankAI` do not exist (404) — [GitHub API checks this session]

### Inferences
- [I] **Natural (non-decorative) uses of FISCO BCOS** in a student cross-border agent:
  1. **Consortium evidence chain (存证) for agent actions.** Student, school, bank and remittance provider are consortium members, and the agent's hash-chained decision log is anchored there. That is the canonical FISCO use case and maps onto "operation logs".
  2. **Purpose-bound tuition and allowance contract (PBM-style)** in Solidity, deployed via Web3 RPC with Hardhat or ethers. Unlike a public chain, this is the right model for a *regulated, permissioned* money programme, mirroring e-CNY's template-reviewed smart contracts.
  3. **Credential status registry** (issuer DID → VC hash → revoked?), giving WeIdentity-style DID/VC semantics without the dormant WeIdentity codebase.
  - Because WeBank's own FinTechathon historically required FISCO BCOS for blockchain projects, judges are likely to recognise and value it (inference).
- [I] **Dual-chain framing for the 0–5 on-chain bonus:** FISCO BCOS for the permissioned evidence and PBM layer, plus optionally Base Sepolia (x402 or Circle USDC) for the public testnet settlement leg. Use Web3 RPC so one codebase (ethers or web3.py) talks to both. Avoid the Python SDK, which is limited to Python ≤ 3.10 and stale; use web3.py or ethers against port 8545 instead.
- [I] **FATE**: the natural story is "federated scam and fraud detection across banks in different jurisdictions without sharing raw data". But FATE is dormant since 2024 and a cluster deployment is heavy. At most, run a FATE standalone toy horizontal-LR job (or simulate federated averaging in plain Python) and present FATE as the production path. Do not make it a core dependency.
- [I] **WeDPR**: the natural story is **anonymous query (匿踪查询)**. The agent checks whether a payee is on a partner bank's fraud blacklist without revealing which payee it asked about, or PSI between the student's contacts and a scam-account list. The platform is heavy (site, node and gateway), so implement a lightweight PSI (for example a DH-based PSI in Python) and label it as "the WeDPR pattern". Deploying WeDPR itself is not realistic in 72 hours.
- [I] **WeIdentity**: cite it as the conceptual reference (did:weid on FISCO BCOS). Implement DIDs and VCs with Veramo or SD-JWT and anchor them on FISCO, and say so openly. Do not try to deploy WeIdentity (Java plus build tools, unmaintained since 2024).
- [E] FISCO BCOS 4-node Air chain on Linux, macOS or WSL2: 30–60 min. Enabling Web3 RPC (genesis `web3_chain_id`, `feature_balance`) and deploying a Solidity contract with Hardhat: 1–2 h. Evidence-anchoring plus PBM contracts: 4–8 h. FATE standalone: 2–4 h, low payoff. WeDPR platform: 1–2+ days, so don't. WeIdentity: 1–2 days, so don't.

### Gaps
- I found no WeBank open-source AI-agent or LLM project newer than FATE-LLM (search budget exhausted before a Chinese-language search). The team should check WeBank's latest announcements or the competition brief for any recommended WeBank AI toolkit.
- Whether FISCO BCOS v3.17's Web3 RPC fully supports the EIP-3009 / EIP-712 signatures needed to run x402 against a FISCO-deployed USDC-like token is untested.

---

## 14. Recommended 72-hour stacks (four idea types) and what NOT to attempt

### Takeaway
Every stack shares a common spine:
- LangGraph (or ADK) agent
- Cedar or OPA permission tiers
- Watchman screening
- Hash-chained audit log anchored on FISCO BCOS
- Langfuse traces
- Frankfurter FX

On top of the spine, pick one differentiator: **credentials and proofs**, **mandated payments**, **purpose-bound money** or **fraud guardian**. Everything is free, needs no KYB, and is Apache-2.0, MIT or similarly permissive, apart from the flagged exceptions (Marble ELv2, OpenSanctions CC BY-NC, gated Llama Guard, Visa TAP terms).

### Cited Findings
- [V] Licence and status facts for each component are cited in sections 1–13. The key ones:
  - LangGraph MIT; ADK Apache-2.0
  - Cedar and OPA Apache-2.0; Watchman Apache-2.0
  - FISCO BCOS Apache-2.0 with Web3 RPC; Langfuse MIT core; Frankfurter MIT
  - AP2, x402 and Rafiki Apache-2.0; Veramo Apache-2.0
  - TLSNotary MIT/Apache-2.0 (alpha); Docling MIT; PaddleOCR Apache-2.0
  - ERC-7291 Final; Circle testnet faucets free
  - Sources: see sections above.

### Inferences
**Shared spine (all ideas)**, estimate about 14–20 person-hours:

| Component | Licence | Setup [E] |
|---|---|---|
| LangGraph agent + FastAPI backend + Next.js chat/approval UI | MIT | 6–8 h |
| Cedar (or OPA) permission tiers T0–T3 | Apache-2.0 | 2–4 h |
| Moov Watchman (OFAC/EU/UK/UN) | Apache-2.0 | 0.5 h |
| Frankfurter FX quotes | MIT | 0.25 h |
| Hash-chained audit log + Merkle root anchored on FISCO BCOS (Web3 RPC, Solidity) | Apache-2.0 | 4–6 h incl. chain setup |
| Langfuse self-host traces | MIT core | 1–2 h |
| Mock bank API (FastAPI) and/or Plaid Sandbox | own / free | 2–3 h |

**A. Proof and credential idea: "Student Financial Passport"** (proof of funds, enrolment and tuition-paid for visa, rent and bank onboarding)
- Docling or PaddleOCR (MIT, Apache-2.0) parses the admission letter and bank statement: 2–3 h.
- Veramo (Apache-2.0) issues and verifies SD-JWT or JWT VCs, with a status or revocation registry on FISCO BCOS: 4–6 h.
- Stretch: TLSNotary (MIT/Apache, alpha) proves "balance ≥ X" from a TLS 1.2 mock-bank endpoint: 8–12 h, high risk.
- The agent assembles a minimal-disclosure package for the verifier (landlord, embassy, university).
- Bonus: credential hashes on FISCO BCOS.
- Total about 30–40 person-hours. Risk: medium (high with TLSNotary).

**B. Payments-execution idea: "Mandated Remittance Agent"** (agent pays tuition, rent and top-ups abroad within user-signed limits)
- AP2 v0.2 open/closed Checkout and Payment Mandates as SD-JWT VCs (Apache-2.0; reuse the sample models): 4–8 h.
- Rail option 1: Rafiki Local Playground (Apache-2.0), where Open Payments grants with interactive consent serve as the bank's own approval: 4–8 h.
- Rail option 2: x402 on Base Sepolia with Circle faucet USDC (Apache-2.0), giving real testnet transaction hashes: 2–4 h.
- Stripe test mode for a card-based tuition deposit: 1 h.
- The FX quote with all-in fee disclosure is shown before the student signs the open mandate.
- Total about 30–40 person-hours. Risk: medium. This idea best matches "AI as a financial participant" and the 40% task-completion criterion.

**C. Programmable-money idea: "Purpose-Bound Tuition and Allowance"** (sponsor parents fund money that can only go to whitelisted purposes, and the agent optimises timing and FX within the rules)
- A simplified ERC-7291-style PBM (ERC-20 wrapper with payee whitelist, monthly cap and expiry) in Solidity, deployed on **FISCO BCOS** (permissioned, regulator-style) **and** Base Sepolia with testnet USDC (public): 6–10 h.
- The agent proposes redemptions, Cedar tiers gate them, and the contract enforces them on-chain (defence in depth).
- Optional stretch: an ERC-4337 smart account with session-key spend caps via permissionless.js (MIT): 6–12 h, medium-high risk.
- Narrative link to e-CNY smart-contract "conditional payments" and MAS Orchid.
- Total about 30–40 person-hours. Risk: low to medium. Strongest for the on-chain bonus.

**D. Fraud-guardian idea: "Cross-border Scam and AML Guardian"** (protects students from fake-tuition, rental and "police" scams)
- Watchman plus OpenSanctions (CC BY-NC is fine for non-commercial use) plus about 10 explainable rules (velocity, new payee, structuring, corridor risk): 4–6 h.
- Document forensics with Docling or PaddleOCR (fake admission letters and invoices) and a cross-check against university registry mocks: 3–5 h.
- NeMo Guardrails (Apache-2.0) against prompt injection from scam messages: 2–3 h.
- Optional: Marble (**Elastic License 2.0, source-available**) as the case manager: 4–8 h.
- A "WeDPR-pattern" privacy-preserving blacklist lookup (lightweight PSI or anonymous query in Python, labelled as the pattern rather than WeDPR itself): 4–6 h.
- FATE only as the roadmap slide.
- Total about 30–40 person-hours. Risk: medium.

**Do NOT attempt in 72 hours**
1. Production or partner APIs: Visa Intelligent Commerce, Mastercard Agent Pay, Wise partner API, ACP Instant Checkout, Stripe SPT if the account lacks preview access. All need onboarding or KYB.
2. Real-bank zkTLS proofs (TLSNotary alpha, TLS 1.3 gaps, ToS), or writing ZK circuits from scratch.
3. Real e-CNY smart contracts, or mBridge or Nexus integration. No public sandboxes; mention them only as context.
4. Full Mojaloop (Helm or Kubernetes), Rafiki in production mode, or running your own ERC-4337 bundler.
5. Deploying the WeIdentity stack or the WeDPR platform, or running a multi-party FATE or FATE-LLM cluster or training. Dormant or heavy; use the patterns instead.
6. The FISCO BCOS Python SDK on Python 3.11+. Use web3.py or ethers over Web3 RPC.
7. Mainnet funds, real customer data, or claiming licensed stablecoin issuance or remittance status.
8. Multi-chain CCTP bridging as a core feature (stretch at most). Fine-tuning safety models. Self-hosting gated Llama Guard 4 without a GPU.
9. Building on Marble or MinerU while describing them as "open source (OSI)". State ELv2 and the MinerU custom terms correctly.

### Gaps
- All time estimates are untested, and native Windows will add friction for FISCO BCOS, Rafiki and TLSNotary. Assume WSL2 or a Linux VM.
- Free-tier limits for Gemini or OpenAI API keys, Pimlico and Reclaim were not verified this session.
