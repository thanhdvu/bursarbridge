# Competitive landscape and hackathon prior art: international-student and cross-border finance (as of 16 Oct 2026)

Labels used on every claim: **[Fact]** = stated by a primary or credible secondary source; **[Company claim]** = self-reported by the company, not independently checked; **[Single-source]** = only one source found; **[Unverified]** = conflicting or weak source; **[Older]** = pre-2025 information; **[Inference]** = my reasoning.

Method note: research ran on 16 Oct 2026 using web search (the session's search budget ran out near the end), page fetches, and Devpost's public project-search JSON endpoint (`devpost.com/software/search.json?query=...`). That endpoint matches projects containing ALL the keywords anywhere in their text. Counts are therefore noisy upper bounds, not concept counts. I read titles and taglines to find true near-duplicates. Devpost project pages returned HTTP 403, so for those projects I have only taglines (no hackathon name, date or prize).

---

## Q1. Incumbents and startups: what they do, fees, 2025–2026 AI or agentic features, where users still suffer

### Takeaway
No major cross-border or student-payments incumbent has shipped a consumer AI agent that completes a cross-border or student finance task end to end. The 2025–2026 AI launches are in-app assistants at neobanks: Revolut AIR in April 2026, and Starling's assistant with Scam Intelligence in June 2026. Network-level agentic rails also arrived (Visa and Mastercard live agentic transactions in 2026, Ant International's AMP protocol). Remittance firms use AI internally, or as a WhatsApp chat front end in Félix's case. The money layer is shifting to stablecoins (Western Union USDPT, MoneyGram's USDC app, Félix, Remitly's stablecoin wallet). In reviews, users still suffer most from opaque holds, account closures, KYC loops, refund delays and support that is "entirely AI". The biggest student lender, MPOWER, reportedly collapsed in October 2026.

### Cited Findings

**Agentic and AI features (2025–2026)**
- [Fact] Revolut launched its in-app assistant "AIR" on 9 Apr 2026 in the UK. It covers spending insights, investment tracking, subscription management, card controls and travel help, including eSIM purchase. Sensitive actions require biometric approval. Revolut says AIR only accesses data the customer already sees and uses zero data retention with third-party AI providers — [FintechWeekly](https://www.fintechweekly.com/news/revolut-air-ai-assistant-uk-customers-launch-2026); [Revolut newsroom](https://www.revolut.com/news/revolut_enters_new_era_of_money_intelligence_with_launch_of_ai_assistant/). (The Revolut page returned 403 when fetched; details come via FintechWeekly and search summaries.)
- [Fact] Starling launched "Scam Intelligence" in Oct 2025, where users upload images of marketplace listings or seller messages for AI fraud checks. Starling claims it raised marketplace-payment cancellation rates by 300% [Company claim]. On 24 Jun 2026 it became an agent inside Starling Assistant covering romance scams and 10+ other fraud types. The agent asks probing questions, such as why a new partner can't pay for their own flight, then recommends contacting the bank — [Starling press release](https://www.starlingbank.com/news/scam-intelligence-launch/); [Crowdfund Insider, Jun 2026](https://www.crowdfundinsider.com/2026/06/287477-uks-starling-bank-introduces-ai-enabled-solution-to-combat-romance-scams-and-other-frauds/); [FStech](https://www.fstech.co.uk/fst/Starling_Expands_AI_Assistant_To_Detect_10_Types_Of_Fraud.php)
- [Fact, Older] In Feb 2024 Revolut launched AI scam detection that sends high-risk payments into a "scam intervention flow" — [UKTN](https://www.uktech.news/fintech/revolut-ai-scam-detection-20240215)
- [Fact] I found no Wise consumer AI-agent launch. Wise published a March 2026 piece predicting multi-step agentic AI in business, with "more pressure for oversight" where errors carry financial or regulatory weight — [eCommerceNews](https://ecommercenews.com.au/story/wise-predicts-agentic-ai-shift-in-business-by-2026)
- [Fact] Flywire's AI plans are forward-looking only. A post by its Chief Product Officer (updated 6 Jan 2026) lists AI in Student Financial Software that is planned, not shipped: market detection, personalised payment plans, automated outreach and predictive risk. On the Q1 2026 call, management said it is "rearchitecting" systems for an agentic future — [Flywire 2026 predictions](https://www.flywire.com/zh/resources/2026-payment-predictions); [Q1 2026 call transcript (StatementDog)](https://statementdog.com/analysis/FLYW/earnings_calls/312993)
- [Fact] Remitly: record Q2 2026 revenue of $495.2M (+20% YoY). AI is described mainly as an internal efficiency tool. New products include the Remitly Global Card, a stablecoin wallet, Flex, Remitly Business and Remitly One. I found no named customer AI assistant — [Remitly IR Q2 2026](https://remitly.gcs-web.com/news-releases/news-release-details/remitly-reports-record-second-quarter-results-and-raises-full); [Quartr summary](https://quartr.com/events/remitly-global-inc-rely-q2-2026_ojEZaby1)
- [Fact] Félix Pago runs an AI chatbot on WhatsApp for US→LatAm remittances. The user chats, then pays via a secure link, with USDC on Stellar as the settlement rail. Stripe's case study headline cites $3B in payment volume [Company claim] — [Stripe customer story](https://stripe.com/ie/customers/felix). Funding reports conflict [Unverified]: $200M Series B announced 1 Sep 2026 (a16z $87M equity plus $113M General Catalyst credit) per [Forkast](https://forkast.news/felix-pagos-200m-series-b-a16z-validates-stablecoin-rails-for-latam-immigrants/), versus a $75M Series B in Apr 2025 per [Briter](https://www.briter.co/companies/felix-pago).
- [Fact] Ant International is rolling out about 100 "AI-native" products across Alipay+, Antom, WorldFirst and Bettr through H2 2026. It also introduced AMP (Agentic Mobile Protocol), described as an open-sourced agentic payment framework for wallets and super apps. Performance figures are company-reported — [SCMP](https://www.scmp.com/tech/tech-trends/article/3367998/ant-international-embeds-ai-agents-across-all-platforms-biggest-ever-product-upgrade); [Fintech Futures press release](https://www.fintechfutures.com/press-releases/expanding-infrastructure-for-the-age-of-ai-commerce-ant-international-connects-over-150-million-merchants-with-more-than-2-billion-consumers); [Crowdfund Insider Sep 2026](https://www.crowdfundinsider.com/2026/09/311541-ant-international-says-merchants-using-ai-for-payment-integration-quadrupled/)
- [Fact, mostly vendor or aggregator sources] Network agentic rails went live in 2026:
  - Visa launched an "Agentic Ready" programme in Europe in Mar 2026.
  - Santander and Visa completed the first live LatAm agentic transactions on 12 Mar 2026.
  - Mastercard (Agent Pay, launched 2025) made its first live agentic payment in Hong Kong in late Mar 2026.
  - I found no documented live cross-border agentic consumer transaction.
  Sources: [IBS Intelligence](https://ibsintelligence.com/ibsi-news/visa-launches-agentic-payments-programme-in-europe/); [Stellagent (Santander/Visa)](https://stellagent.ai/insights/santander-visa-latam-agentic-payments); [Stellagent (Visa/MC)](https://stellagent.ai/insights/visa-mastercard-agentic-commerce-strategy)

**Stablecoin and remittance players**
- [Fact] Western Union launched USDPT, a USD stablecoin issued by Anchorage Digital Bank on Solana, around 4–5 May 2026. It serves as a 24/7 settlement asset, starting in the Philippines and Bolivia. A consumer product, "Stable by Western Union", is planned for 40+ countries later in 2026, with Fireblocks and Crossmint as infrastructure — [The Block](https://theblock.co/post/399890/western-union-launches-usdpt-stablecoin-anchorage-solana); [Sumsub](https://sumsub.com/media/news/western-union-launches-usd-backed-stablecoin-on-solana/); [Decrypt](https://decrypt.co/346433/western-union-launch-usdpt-stablecoin-solana)
- [Fact] In the UK (autumn 2025), Western Union marketed student transfers with no fee on the first online send. These are plain transfers with no spending controls — [Yorkshire Post (sponsored)](https://www.yorkshirepost.co.uk/recommended/western-union-student-money-transfer-gap-year-money-transfer-5300369)
- [Fact] MoneyGram launched a stablecoin-based app in Colombia in Sep 2025. It holds a USD balance in USDC on Stellar, with Crossmint wallets and cash-out at MoneyGram locations — [Blockworks](https://blockworks.co/news/moneygram-stablecoin-app-colombia); [Cointelegraph](https://cointelegraph.com/news/moneygram-app-launch-colombia-stablecoin-savings)
- [Fact] Aspora (Sequoia-backed, Indian diaspora) launched bill pay in Nov 2025, covering 22,000+ Indian billers via BBPS with no fee. It raised a $50M Series B at a $500M valuation in Jun 2025 and reports 800k customers and $4B in transactions [Company claim]. It has no family or purpose controls — [TechCrunch](https://techcrunch.com/2025/11/17/sequoia-backed-fintech-aspora-will-let-indian-diaspora-pay-bills-back-home)

**Tuition-payment specialists**
- [Fact] Flywire acquired Cohort Go (agent-channel tuition payments) and StudyLink (Australian agent and admissions software), and won Penn State in 2026 — [Crowdfund Insider](https://www.crowdfundinsider.com/?p=193704); [TipRanks press release](https://www.tipranks.com/news/press-releases/flywire-acquires-studylink-to-accelerate-expansion-in-the-australian-higher-education-market)
- [Company claim] Convera says 900+ educational institutions use it, including "8 out of 10 top-ranked universities" — [Convera](https://convera.com/solutions/international-payments-educational-institutions/). [Fact] At the University of Alberta, both Convera and PayMyTuition payments post in 3–5 business days — [UAlberta](https://www.ualberta.ca/en/admissions-programs/tuition/international-tuition-payment-options/index.html). University of Houston caps Convera wires: total under $10,000, and no more than $1,000 above the amount due — [UH](https://www.uh.edu/one-stop/financial/payment/method-payment/wire-transfer/). Convera's sanctions policy restricts some countries — [ANU](https://study.anu.edu.au/accept-your-offer/international-students-accept-decline-or-change-preference/international-students)
- [Fact] PayMyTuition has an unclaimed Trustpilot profile with zero reviews, so there is no public review signal — [Trustpilot](https://www.trustpilot.com/review/paymytuition.com)
- [Fact, Older 2024] Pay4Me offers same-day tuition payments and cites a survey in which 57%+ of international students face payment complexity [Company claim] — [Boise State Venture College](https://www.boisestate.edu/venturecollege/2024/07/26/boise-startup-ensures-international-students-stay-enrolled-with-fast-tuition-payment-app/). Pax Credit offers local-currency tuition payment with flat fees — [IBS Intelligence](https://ibsintelligence.com/ibsi-news/cross-border-payments-for-international-students-interview-with-abhinov-balagoni-ceo-founder-of-pax-credit)
- [Company claim] Crebit offers stablecoin FX for tuition. Its founders say they have processed "over a million dollars" in tuition — [Credit Union Connection](https://thecreditunionconnection.com/sending-money-across-borders-should-be-as-easy-as-sending-a-text/)
- [Fact] Mastercard (2025) says most mid-tier and smaller banks in China and India lack efficient outbound cross-border payment for tuition — [Mastercard insight](https://www.mastercard.com/mt/en/news-and-trends/insights/2025/Cracking-the-code-on-international-tuition-payments.html)
- [Fact] China-side tuition rails:
  - Tencent's "微汇款" mini-program supports paying overseas tuition with WeChat Pay — [ifeng](https://finance.ifeng.com/c/87vOSbakV7C)
  - Alipay offers a "快速缴费" (quick payment) flow for UK tuition — [XDF blog](https://liuxue.xdf.cn/blog/blog_7875772.shtml)
  - 易思汇 (Easy Transfer) is a study-abroad payment platform — [36Kr PitchHub](https://pitchhub.36kr.com/project/2072053463597062)
- [Fact] Hong Kong–Mainland "Payment Connect" (FPS↔IBPS) launched 22 Jun 2025 for small real-time remittances, with tuition named among target uses. Limits: HKD 10,000 per day per institution and HKD 200,000 per year for HK residents. Mainland residents remain under the USD 50,000 annual FX quota — [HKMA](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/06/20250620-4/); [Fintech News HK](https://fintechnews.hk/34467/payments/payment-connect-launch-hk-mainland/); [Payment Expert](https://paymentexpert.com/2025/06/24/china-and-hong-kong-launch-cross-border-payment-link/)

**Lenders, credit and newcomer banking**
- [Single-source, serious] MPOWER Financing has reportedly largely shut down. Per a 7 Oct 2026 Bloomberg report relayed by PYMNTS:
  - ABS investor demand fell after Zimbabwe was added to a US travel-ban list in 2025.
  - A sale attempt failed and most staff were cut, including CEO Manu Smadja.
  - About $400M+ in ABS is outstanding.
  - Its website says it is "temporarily unable to offer new loans for 2026."
  Sources: [PYMNTS](https://www.pymnts.com/?p=4286606); [MPOWER school list page](https://www.mpowerfinancing.com/schoollist). Only five months earlier (May 2026) it reported $1B+ tuition funded for 25,000+ students from 183 countries — [BusinessWire](https://www.businesswire.com/news/home/20260529877989/en/MPOWER-Financing-Releases-2026-Social-Impact-Report-Over-%241-Billion-in-Tuition-Funded-and-12x-Income-Growth-for-International-Students)
- [Unverified, guide site] Prodigy Finance covers 1,700+ schools. Example Fall 2026 APR is 13.26% (8.50% fixed spread plus SOFR). The guide frames it as the main remaining no-cosigner graduate option — [CollegeHelpGuide](https://www.collegehelpguide.com/blog/mpower-financing-collapses-international-student-loans-2026/)
- [Fact] Nova Credit:
  - Raised a $35M Series D (Oct 2025, Socium Ventures) — [Pulse 2.0](https://pulse2.com/nova-credit-35-million-series-d-raised-to-advance-growth-of-cash-flow-underwriting-platform)
  - Partnered with Seen Finance for cash-flow underwriting (Jan 2026) — [Crowdfund Insider](https://www.crowdfundinsider.com/2026/01/258853-seen-finance-nova-credit-partner-to-improve-credit-access-by-using-cash-flow-data/)
  - JPMorgan Chase is reported to use Cash Atlas plus Credit Passport (date unconfirmed) — [CardRates](https://www.cardrates.com/news/jpmorgan-to-tap-new-markets-with-cash-flow-underwriting/)
  - [Older] Credit Passport is embedded in Earnest (2023) and Prodigy (2022) loans — [Nova blog](https://www.novacredit.com/corporate-blog/earnest-and-nova-credit-launch-international-private-student-loans); [Nova/Prodigy](https://novacredit.com/blog/nova-credit-and-prodigy-finance-partner)
- [Fact] I found no 2026 AI announcement from Zolve. Its pages promote a scholarship and list MPOWER as financing partner (loans $2,001–$100,000), now a risky dependency — [Zolve blog](https://zolve.com/blog/how-does-zolve-empower-your-us-college-transition/); [Zolve scholarship](https://zolve.com/scholarship)
- [Unverified, conflicting guide sites] German blocked-account fees:
  - Expatrio: €119 or €149 setup, plus €5 per month.
  - Fintiba: €159 or €89 setup, plus €9.90 per month.
  - Coracle: €99, with "operational status" described as uncertain.
  - The 2026 required amount is €11,904 (€992 per month).
  Sources: [GlobalScholarsGuide](https://globalscholarsguide.com/blocked-account-germany-providers-expatrio-fintiba-coracle/); [MyGermanUniversity](https://www.mygermanuniversity.com/articles/Fintiba-vs-Expatrio-blocked-account)
- [Fact] ApplyBoard projects an 18% decline in US F-1 visas in 2025 — [ApplyBoard 2026 trends via Macau Business](https://macaubusiness.com/applyboards-2026-trends-report-reveals-how-global-education-is-being-rebuilt/)

**Where users still suffer (Trustpilot 1-star themes, sampled 16 Oct 2026)**
- [Fact] Flywire has a TrustScore of 3.9 from about 3,200 reviews, 16% of them 1-star. Among 20 recent 1-star reviews (Aug–Oct 2026):
  - About 11 cite unresponsive support, including an AI chatbot that can't resolve issues: "support was unresponsive and entirely AI." (15 Sep 2026)
  - About 9 cite stuck or cancelled payments: "left me completely stranded for 23 days" (14 Oct 2026)
  - About 5 cite refund delays.
  - About 2 cite duplicate charges.
  - About 2 cite FX or fees.
  Source: [Trustpilot Flywire 1-star](https://www.trustpilot.com/review/www.flywire.com?stars=1); a third-party analysis also flags refund delays and high FX — [Kimola](https://kimola.com/reports/flywire-feedback-analysis-insights-actions-trustpilot-en-us-147378)
- [Fact] Wise has a TrustScore of 4.3 from about 303,074 reviews, 9% of them 1-star. Recurring 1-star themes:
  - Account closures and withheld funds: "closed my account without any previous email, no reason" (15 Oct 2026)
  - Repeated identity or residency-permit verification
  - Scripted support
  - Transfer limits and delays
  Source: [Trustpilot Wise 1-star](https://www.trustpilot.com/review/wise.com?stars=1)
- [Fact] Remitly has a TrustScore of 4.6 from about 122,698 reviews. Recurring 1-star themes:
  - Held or delayed transfers
  - Unexplained suspensions
  - Repeated ID checks per transfer
  - Refunds taking 7–10 days
  - Unhelpful support
  Source: [Trustpilot Remitly 1-star](https://www.trustpilot.com/review/remitly.com?stars=1)

### Inferences
- [Inference] Users' main pain is neither the fee nor finding the cheapest route; comparison tools already handle that. It is the black-box state of a payment: held, under review, refund pending, account closed, with no one to explain it. The same complaint appears across Flywire, Wise and Remitly. An agent that proactively tracks, explains and escalates a payment's state, with evidence, addresses a demonstrated pain. Several reviewers say current AI support makes this worse, which is a warning to build an agent that acts rather than a chatbot.
- [Inference] MPOWER's reported collapse (Oct 2026) and US visa or travel-ban volatility make "visa outcome risk" a live financial risk for students, lenders and payers. This strengthens seeds (b), refund on refusal, and (f), portable credit. It is very fresh, so judges may not have seen many projects on it.
- [Inference] The stablecoin rail is now mainstream among incumbents (WU, MoneyGram, Remitly, Félix). A hackathon project that is "just stablecoin tuition or remittance" will look commoditised. Stablecoins should be a back-end choice, not the pitch.
- [Inference] WeBank (co-organiser) runs the Shenzhen–HK Cross-Boundary Data Validation Platform (see Q2). Judges will know cross-border verifiable data well, which is an advantage if the idea builds on it and a risk if it merely re-invents it.

### Gaps
- I retrieved no verified current fee schedules for Wise, Remitly, Flywire, Convera or PayMyTuition this session. Search results gave only qualitative FX and fee complaints.
- Not researched or not found: Sprintax and Taxback product or AI updates, Leap Finance 2025–26 news, Coracle's current operating status, Cohort Go post-acquisition, Bitso and Circle-based consumer apps.
- The Revolut AIR "13 million UK customers" figure comes from a headline only. Its expansion beyond the UK is unconfirmed.
- I could not independently confirm the MPOWER shutdown beyond PYMNTS relaying Bloomberg plus MPOWER's own "unable to offer new loans" notice.

---

## Q2. Seed (a): proof-of-funds agent issuing a privacy-preserving verifiable credential

### Takeaway
The cryptographic building blocks exist and are production-grade in Web3: zkTLS or "web proofs" such as Reclaim Protocol, with bank-balance-above-threshold as the canonical example. Bank-issued verifiable documents are also appearing in government practice (Bangladesh Bank QR-verifiable visa statements; WeBank's Shenzhen–HK DVP validating bank statements and credit reports by hash). I found no embassy or immigration authority that accepts a ZK or VC proof of funds. At least one hackathon project already pitches exactly "ZK proof-of-funds credential for students applying to visas" (Devpost "proofvault-zk"). The concept is therefore not novel to hackathons, but it is still far from real-world adoption.

### Cited Findings
- [Fact] An IACR ePrint paper (2026/2187) uses "proof of solvency" as the canonical zkTLS example: the user proves a bank balance exceeds a threshold without revealing credentials, account number or exact balance. It notes existing zkTLS schemes lack a common security model — [IACR ePrint 2026/2187](https://eprint.iacr.org/2026/2187.pdf)
- [Fact] Many zkTLS implementations are "web proofs" or TLS attestations rather than true ZK. The emphasis is verifiability first, privacy second — [BlockEden, Feb 2026](https://blockeden.xyz/blog/2026/02/23/zktls-verifiable-offchain-data-https/)
- [Company claim, third-party figures] Reclaim Protocol uses an attestor node plus a client-side ZK circuit, e.g., to prove a bank balance exceeds a threshold. It reportedly has 4M+ verifications and covers 29,000+ universities and payroll systems (ADP, Workday, etc.). I found no regulator or bank endorsement as a KYC substitute — [Reclaim blog](https://blog.reclaimprotocol.org/posts/what-is-reclaim-protocol); [Solana Compass](https://solanacompass.com/projects/reclaim-protocol)
- [Fact] Bangladesh Bank ordered banks to add QR codes to bank statements and solvency certificates issued for visa purposes. Embassies scan the code to verify account name, number, balances and statement date. Banks have 90 days to implement and records must stay verifiable for 6+ months. The stated reason is embassies' difficulty verifying authenticity instantly. The circular's exact date was not captured — [The Daily Star](https://thedailystar.net/business/economy/news/banks-asked-use-qr-verification-visa-documents-4174256); [Bangladesh Monitor](https://www.bangladeshmonitor.com.bd/en/bangladesh-bank-orders-qr-codes-on-bank-statements-for-visa-applications)
- [Fact] Some banks sell paper "certificates of finance" for visas, e.g., SCB Thailand at 100 baht per document — [SCB](https://scb.co.th/en/personal-banking/other-services/certificate-of-finance/certificate-of-finance-applying-for-visa.html)
- [Fact] Shenzhen–HK Cross-Boundary Data Validation Platform (DVP):
  - Piloted May 2024, using hash-based verification plus blockchain, so originals don't cross the border.
  - WeBank Technology Services provides the architecture and co-operates it.
  - Mainland providers supply personal and corporate credit reports and bank statements for validation.
  - Over 10 entities use it; Fusion Bank says it approved HKD 100M+ of loans using it [Company claim].
  - ICBC (Asia) plans to verify Mainland individuals' central-bank credit reports for newly arrived talent-scheme residents (TTPS/QMAS).
  - Nova Credit was a phase-1 trial participant.
  Sources: [WeBank press release, Jul 2025](https://kyodonewsprwire.jp/release/202507292857); [HKMA May 2024](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2024/05/20240506-4/); [SCMP](https://amp.scmp.com/tech/article/3261620/greater-bay-area-hong-kong-shenzhen-begin-cross-border-credit-checks-pilot-trial-data-transfer); [HK Digital Policy Office](https://www.digitalpolicy.gov.hk/en/our_work/success_stories/shenzhen_hongkong_cross_boundary_data_validation_platform/)
- [Fact, secondary] EU Digital Identity Wallet pilots: the EWC consortium ran 49 bank-led production payment transactions using the wallet for authentication. EWC RFC007 defines a "Payment Wallet Attestation". The WE BUILD pilot (Sep 2025, 200+ organisations, 28 countries) is testing bank-issued payment credentials. These cover payments and attestations, not visa proof of funds — [Dock.io recap](https://www.dock.io/post/eudi-wallet-payments-what-the-large-scale-pilots-revealed); [EWC RFC007](https://www.weboftrust.org/standard/ewc_rfc007:_payment_wallet_attestation-72); [iGrant WE BUILD](https://docs.igrant.io/docs/ecosystem-engagements/we-build-consortium/)
- [Fact] Proof-of-funds rules are rising and fragmented. Canada requires CAD 23,448 for a single applicant from 1 Sep 2026. Since the Student Direct Stream closed, a GIC is optional, alongside bank statements, loan letters and bank drafts — [CIC News](https://www.cicnews.com/?p=79805); [Prodigy Finance blog](https://prodigyfinance.com/resources/blog/canada-study-permit-2026-cap-gic-standard-stream/). Germany requires €11,904 in a blocked account for 2026 [Unverified guide] — [GlobalScholarsGuide](https://globalscholarsguide.com/blocked-account-germany-providers-expatrio-fintiba-coracle/)
- [Fact] Prior art (hackathon or demo):
  - Devpost "proofvault-zk": "Prove your funds. Reveal nothing. A zero-knowledge proof-of-funds credential for students applying to visas, universities…" — [Devpost](https://devpost.com/software/proofvault-zk)
  - ETHGlobal Cannes "ProofOfFunds": an Android app that proves crypto-balance thresholds — [ETHGlobal](https://ethglobal.com/showcase/proofoffunds-zczod)
  - zkRemit Guard: a Noir reserve-threshold proof that gates escrow on Stellar — [DEV.to](https://dev.to/cypriantinasheaarons/i-built-a-payment-gate-that-never-sees-your-balance-4egg)
  - Visa-document helpers on Devpost: "FormBridge" (finds conflicting details in visa forms and bank statements), "Dossier — UK Visa Case Partner", "DIY Visa", "VisaCurator" (winner) — [FormBridge](https://devpost.com/software/formbridge-spqc8r); [Dossier](https://devpost.com/software/dossier-uk-visa-case-partner); [VisaCurator](https://devpost.com/software/visacurator)

### Inferences
- [Inference] "ZK proof of funds for visas" by itself is now a known hackathon trope, with at least 1 direct Devpost duplicate and several ZK-balance demos. Judges at a WeBank-backed event may also see it as a re-skin of WeBank's own DVP. The open space is the agentic and longitudinal part that no project shows:
  - continuous monitoring of the visa balance rule over the required window (e.g., the UK's 28-day rule, Germany's blocked amount, Canada's annual update);
  - assembling multi-source evidence (bank, sponsor, loan letter, scholarship);
  - issuing a verifier-checkable credential that relies on issuer-signed data (bank-signed or DVP-style hash), not on embassies trusting zkTLS.
- [Inference] The compliance story is stronger if the credential is bank-issued and bank-signed (Bangladesh QR model, DVP model) than if it rests on cryptography the embassy has never accepted. That fits the 30% security and compliance weight.

### Gaps
- I found no evidence that any embassy, consulate or immigration authority (IRCC, UKVI, German missions, US consulates) has piloted or accepted a digital verifiable proof of funds beyond QR-verifiable statements.
- I could not open the proofvault-zk Devpost page (403), so its hackathon, date, prize and implementation depth are unknown.

---

## Q3. Seed (b): tuition-payment autopilot (route and timing, execution, reconciliation, refund if visa refused)

### Takeaway
Paying tuition cross-border is crowded: Flywire, Convera, PayMyTuition, Cohort Go, WeChat and Alipay rails, stablecoin startups, and many hackathon clones. The unsolved part is after the payment: reconciliation (amount, reference, overpayment caps) and especially refunds after a visa refusal. Rules there are set by schools and regulators, and Flywire's 1-star reviews and the Australian Ombudsman show refunds as a top complaint. I found no product or hackathon project that automates "visa refused → evidence → refund request → FX-aware repatriation".

### Cited Findings
- [Fact] Australian law requires providers to refund most fees within 28 days after a visa refusal, and the Ombudsman says most complaints arise because that deadline is missed — [Commonwealth Ombudsman media release](https://www.ombudsman.gov.au/__data/assets/pdf_file/0027/315846/Media-Release-Visa-Refusal-Refunds.pdf)
- [Fact] School policies vary. Example (Older, 2022): a full refund minus the application fee if the refusal letter is submitted — [Sir Wilfrid Laurier SB](https://bilingualtraining.ca/wp-content/uploads/2022/02/Modalites-de-paiement-et-de-remboursement.pdf). Another refunds the deposit only if requested within 30 days of the program start — [Augustana](https://augie.edu/international-student-payments)
- [Fact] Flywire 1-star themes include refunds unissued for weeks, payments held, and "duplicate charges" (see Q1) — [Trustpilot Flywire](https://www.trustpilot.com/review/www.flywire.com?stars=1)
- [Fact] Universities impose reconciliation constraints: Convera wire caps at UH, no overpayments at Texas Tech, and 3–5 business days for posting — [UH](https://www.uh.edu/one-stop/financial/payment/method-payment/wire-transfer/); [Texas Tech](https://www.depts.ttu.edu/studentbusinessservices/international-payments/); [UAlberta](https://www.ualberta.ca/en/admissions-programs/tuition/international-tuition-payment-options/index.html)
- [Fact] Home-country outbound rules are part of the job. India raised the LRS TCS threshold from ₹7 lakh to ₹10 lakh from 1 Apr 2025 and exempted education remittances funded by loans from specified institutions. Other sources dispute the exemption's status [Unverified] — [Business Standard](https://www.business-standard.com/amp/budget/news/tcs-on-foreign-remittances-up-to-rs-10-lakh-none-on-foreign-education-loan-125020100857_1.html); [Bajaj Finserv](https://www.bajajfinserv.in/tcs-on-foreign-remittance). Mainland Chinese residents have a USD 50,000 annual FX quota — [Payment Expert](https://paymentexpert.com/2025/06/24/china-and-hong-kong-launch-cross-border-payment-link/)
- [Fact] China (Older, 2022–23): a Chengdu e-CNY smart-contract prepaid-tuition pilot auto-refunded fees for missed classes. This is a rare instance of programmable refunds for education — [Forkast](https://forkast.news/china-to-speed-up-expand-digital-yuan-smart-contracts-pboc-official-says); [Unlock-BC](https://www.unlock-bc.com/?p=90750)
- [Fact] Hackathon and startup clones of "cheaper or faster tuition payment":
  - Intuipay, a stablecoin tuition project entered at multiple HackQuest hackathons (EDU Chain Semester 3, Pharos Builder Base Camp). It claims to cut fees "from 5–8% to 0.5–3%" [Company claim] — [HackQuest](https://hackquest.io/projects/Intuipay); [EDU Chain entry](https://hackquest.io/vi/projects/EDU-Chain-Hackathon-Semester-3-Intuipay)
  - Remintify, an Edinburgh testnet prototype — [FinTech Scotland](https://www.fintechscotland.com/?p=10934)
  - ReMiT, AI-timed FX conversion for remittances — [HackQuest](https://hackquest.io/projects/ReMiT)
  - Devpost "Rex" ("pay international college tuition with no fees") — [Devpost](https://devpost.com/software/rex)
  - Devpost "Fintech Fanatics" (XRPL campus wallet) — [Devpost](https://devpost.com/software/fintech-fanatics)
  - Devpost "LADTransfer" — [Devpost](https://devpost.com/software/ladtransfer)
- [Fact] Devpost keyword counts (16 Oct 2026): "international student tuition" 53; "tuition visa" 20; "tuition refund" 4. None of the 4 "tuition refund" hits is about visa-refusal refunds (they are a PayPal free-trial refunder, a budgeting app, a micro-credential project and a study chatbot) — [Devpost search](https://devpost.com/software/search?query=tuition%20refund)

### Inferences
- [Inference] Pitching "pick the cheapest route and time" will be seen as a clone, since incumbents and dozens of hackathon projects already do it. The defensible and judge-friendly angle is an agent that owns the whole lifecycle, including the unhappy paths:
  - payment-state tracking;
  - university reconciliation (reference matching, over- or under-payment);
  - a visa-refusal refund playbook that knows the jurisdiction's rule (e.g., Australia's 28 days) and school policy, files the request with the refusal letter, chases the deadline and repatriates funds to the original payer under home-country FX rules.
  This maps cleanly to "task completion" scoring and to real complaints.
- [Inference] Refund-to-original-payer and source-of-funds traceability is also a compliance feature (AML/FX rules), which helps the 30% security and compliance score.

### Gaps
- I did not find how Flywire, Convera or PayMyTuition handle visa-refusal refunds operationally (timelines, FX rate used, who bears FX loss).
- I found no data on refund volumes or average refund delay for international students.

---

## Q4. Seed (c): purpose-bound family allowance (programmable, purpose-limited money plus home-country outbound compliance)

### Takeaway
Pieces exist separately:
- programmable money in central-bank pilots (MAS Purpose Bound Money trials including "learning accounts"; e-CNY smart-contract prepaid education);
- diaspora "pay the bill instead of sending cash" products (Aspora, EcoCash Diaspora Wallet, MoneyHive, T-Plus);
- old parent-controlled student cards (SideKick, 2020).
I found no live product where parents in one country fund a child's study-abroad life with purpose limits (tuition, rent, living) and an agent also handles the home-country outbound FX paperwork. On the hackathon side, "programmable spending limits or mandates" is heavily cloned, though almost always for AI agents rather than families. Family-allowance projects exist but are few (XRPay, St4bl.com).

### Cited Findings
- [Fact, Older 2023] MAS Purpose Bound Money (Project Orchid) attaches conditions (expiry, eligible merchants) to digital money via a smart-contract "wrapper". Trials include government vouchers, payouts and "managing learning accounts" — [Vulcan Post explainer](https://vulcanpost.com/807649/explainer-purpose-bound-money-singapore/); [ZDNet](https://www.zdnet.com.au/finance/banking/singapore-explores-programmable-digital-currency-use-cases-with-industry-trials/)
- [Fact, Older 2022–23] In Chengdu, an e-CNY smart contract let parents prepay for classes with automatic refunds for missed classes. It was framed as protecting funds if an institution's accounts were frozen — [Forkast](https://forkast.news/china-to-speed-up-expand-digital-yuan-smart-contracts-pboc-official-says); [Unlock-BC](https://www.unlock-bc.com/?p=90750)
- [Fact, Older 2020] SideKick Card (Canada) is a parent-funded student card with category budgets (education, food, entertainment) — [The PIE News](https://thepienews.com/news/sidekick-card-launched-in-canada/)
- [Fact] Diaspora bill-pay products:
  - Aspora: 22,000+ Indian billers, free. TechCrunch mentions no family or purpose controls — [TechCrunch](https://techcrunch.com/2025/11/17/sequoia-backed-fintech-aspora-will-let-indian-diaspora-pay-bills-back-home)
  - EcoCash Diaspora Wallet: pay school fees, utilities and groceries in Zimbabwe — [Business Times ZW](https://businesstimes.co.zw/ecocash-launches-diaspora-wallet-to-ramp-up-remittances/)
  - MoneyHive (UK→Nigeria): rent and school fees; pre-launch at the time [Company claim] — [BusinessDay NG](https://businessday.ng/?p=1087921)
  - T-Plus (Somali diaspora) — [MWM](https://mwm.ai/apps/t-plus/1300716879)
- [Fact] Outbound-compliance context the agent would handle:
  - India's LRS and TCS rules for education remittances — [Business Standard](https://www.business-standard.com/amp/budget/news/tcs-on-foreign-remittances-up-to-rs-10-lakh-none-on-foreign-education-loan-125020100857_1.html)
  - China's USD 50k annual quota, and HK–Mainland Payment Connect limits naming tuition as a use — [HKMA](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/06/20250620-4/); [Payment Expert](https://paymentexpert.com/2025/06/24/china-and-hong-kong-launch-cross-border-payment-link/)
- [Fact, Older 2013] Hackathon precedent: Banga (UC Berkeley Play Hackathon winner) was a remittance app where senders set spending controls for family in developing countries — [Berkeley iSchool](https://www.ischool.berkeley.edu/news/2013/i-school-teams-sweep-play-hackathon-awards)
- [Fact] Devpost family-allowance and remittance-rules projects:
  - "XRPay — Instant allowances across borders" — [Devpost](https://devpost.com/software/xrpay-gc8kiz)
  - "St4bl.com", at least 4 submissions: recipients request support, senders pre-authorise rules, AI routes the cheapest channel — [Devpost](https://devpost.com/software/st4bl-com); [variant](https://devpost.com/software/st4bl-com-troc8z)
  - "SigmaPay": XRPL remittances with "conditional escrow payments" — [Devpost](https://devpost.com/software/sigmapay)
- [Fact] Agent spending-limit and mandate projects are very common:
  - Devpost: "Nexus Pay" (5 separate submissions with programmable spending limits for AI agents) and "Midnight Mandate" — [Devpost Nexus Pay](https://devpost.com/software/nexus-pay); [Midnight Mandate](https://devpost.com/software/d-5sh1iv)
  - ETHGlobal Tokyo 2026 showcase snapshot: "DSAP Protocol" (spending limits for AI agents), "Proviso" (shopping agent bound by approval rules), "My Agent Ohana" (revocable consent), "Agent PayGuard", "Izanagi" — [ETHGlobal showcase](https://ethglobal.com/showcase?search=remittance)
- [Fact] Devpost keyword counts: "allowance programmable" 14; "parents abroad money" 19 (mostly noise); "family remittance" 40; "stablecoin remittance" 19 — [Devpost search](https://devpost.com/software/search?query=allowance%20programmable)

### Inferences
- [Inference] "Spending rules or mandates for an AI agent" is now saturated in Web3 and agentic hackathons, so framing (c) as "programmable wallet with limits" will look familiar. What remains open:
  - Two-country, two-party compliance: the sender's outbound FX or LRS paperwork plus the receiver's purpose evidence (rent contract, tuition invoice).
  - Paying purpose-bound obligations directly to the landlord or university instead of handing cash to the student.
  - Explainable, auditable release for parents.
  This combination is still rare.
- [Inference] e-CNY or PBM framing could resonate with a Tsinghua PBCSF and WeBank jury. However, cross-border e-CNY for students is not live in what I found, so present it as a design that could later run on PBM or e-CNY, with today's rails underneath.

### Gaps
- I found no 2025–2026 MAS PBM or e-CNY updates specific to education or cross-border allowances (sources are 2022–2023).
- I could not verify whether WeChat Pay's family card (亲属卡) or Alipay's family card work for overseas students' spending abroad; this was not researched.
- No pricing data for diaspora bill-pay beyond Aspora's free bill pay.

---

## Q5. Seed (d): payment guardian or AI co-signer against scams targeting international students

### Takeaway
Scams aimed at international students are well documented in 2025 (fake ICE/USCIS/DHS officers, fake police or embassy video calls, AI voice cloning of family). Banks now ship strong generic defences: Starling's agentic Scam Intelligence, Revolut's intervention flow, and Singapore's "money lock". Scam-detection apps are the most saturated hackathon category I measured. Even the international-student-specific version already exists (Devpost "VisaShield": fake ICE/USCIS calls and fake OPT). A pure scam detector would be a clone. The thinner space is a consent or co-signer step on the payment itself, an agent that holds or verifies a payment before money leaves, especially for cross-border payments, plus university-verified payee directories.

### Cited Findings
- [Fact, aggregator relaying FBI] The FBI Atlanta warned in May 2025 that impersonators of DHS/HSI/USCIS were extorting international students with deportation threats. The scams exploited visa-cancellation confusion — [Geebo summary](https://blog.geebo.com/2025/05/22/visa-scam-targets-foreign-students/). The FBI Seattle noted spoofed law-enforcement numbers and payment by wire, crypto or gift cards — [FOX13 Seattle](https://www.fox13seattle.com/news/fbi-scam-immigration-foreign-students)
- [Fact] University of Manchester (Oct 2025) reported rising scams: fake police or embassy calls, including video calls with fake uniforms, fake UKVI messages, and AI voice cloning used against families — [Manchester student news](https://studentnews.manchester.ac.uk/2025/10/27/be-careful-dont-be-a-victim-of-fraud/). IRCC (Dec 2024) warned that students had transferred thousands to fake immigration agents — [Study International](https://studyinternational.com/news/scam-international-students-canada/). Guidance from [Stanford Bechtel](https://bechtel.stanford.edu/navigate-international-life/fraud-alert-scams-targeting-international-students-and-scholars) and [UMN ISSS](https://isss.umn.edu/scams-and-identity-theft)
- [Fact] Bank defences:
  - Starling Scam Intelligence (Oct 2025) and its agent version (Jun 2026) — [Starling](https://www.starlingbank.com/news/scam-intelligence-launch/); [Crowdfund Insider](https://www.crowdfundinsider.com/2026/06/287477-uks-starling-bank-introduces-ai-enabled-solution-to-combat-romance-scams-and-other-frauds/)
  - Revolut scam intervention flow (2024) — [UKTN](https://www.uktech.news/fintech/revolut-ai-scam-detection-20240215)
  - Revolut AIR requires biometric approval for sensitive actions (2026) — [FintechWeekly](https://www.fintechweekly.com/news/revolut-air-ai-assistant-uk-customers-launch-2026)
- [Fact, Older 2023–24] Singapore money lock: DBS digiVault (Nov 2023, extended to all accounts Feb 2024) needs an in-branch, identity-verified unlock. OCBC Money Lock ringfences funds so they can't be transferred digitally. MAS frames these as limiting losses from malware, phishing and pressured transfers — [DBS newsroom](https://www.dbs.com/newsroom/DBSPOSB_launches_two_new_options_for_customers_to_lock_up_their_funds_empowering_them_with_greater_control_over_their_funds_security); [Fintech News SG](https://fintechnews.sg/89215/security/dbs-expands-its-money-lock-feature-digivault-to-all-accounts/); [MoneySmart](https://blog.moneysmart.sg/budgeting/bank-money-locking-feature/)
- [Fact] International-student scam prior art on Devpost:
  - "VisaShield": "AI that spots fake ICE/USCIS calls and fake OP[T]…" — [Devpost](https://devpost.com/software/visashield)
  - "SafeRoute AI" (newcomers and international students in Canada) — [Devpost](https://devpost.com/software/saferoute-ai-35u4rw)
  - "Landed" (remote-job scams for newcomers) — [Devpost](https://devpost.com/software/landed-sr152o)
  - "RentEscrow" (blockchain escrow against rent scams for international students) — [Devpost](https://devpost.com/software/rentescrow)
  - "RentSpiracy" — [Devpost](https://devpost.com/software/rentspiracy)
  - "Mi Casita" ("catches scams" for Latino immigrants) — [Devpost](https://devpost.com/software/latinos-x-ai-fdt)
- [Fact] General scam and payment-guardian prior art:
  - Guardião won "Europe's largest AI hackathon" (Feb 2026), an on-device agent that screens calls and texts in about 2 seconds — [NOVA FCT](https://www.fct.unl.pt/en/news/2026/02/nova-fct-alumna-wins-europe-s-largest-ai-hackathon-app-against-scams)
  - Devpost: ScamShield v4 (AI plus a "STOP" delay), ElderShield, Safebook — [ScamShield v4](https://devpost.com/software/scamshield-v4); [ElderShield](https://devpost.com/software/eldershield); [Safebook](https://devpost.com/software/winhacks2024)
  - Devpost payment-side guardians: "PayPause" (checks "new bank details, pay today" emails against payment history), "Interdict.ai" (freezes vendor payments after bank-detail changes) — [PayPause](https://devpost.com/software/paypause); [Interdict.ai](https://devpost.com/software/interdict-ai)
  - ETHGlobal Tokyo 2026 "Meigi": "Confirmation of Payee for stablecoins and AI agents" — [ETHGlobal showcase](https://ethglobal.com/showcase?search=remittance)
- [Fact] Devpost keyword counts: "scam payment" 444; "scam elderly" 251; "scam student" 177; "scam international student" 23 — [Devpost search](https://devpost.com/software/search?query=scam%20payment)

### Inferences
- [Inference] This is the most saturated seed. Scam detection on messages, calls or screenshots is a high-density hackathon cliché, already specialised to international students, and banks now ship agentic versions. Judges will likely have seen many.
- [Inference] The remaining space is narrow and should be treated as a feature, not the core idea. One version is a guardian embedded in a payment-executing agent (seeds b, c or e) that:
  - checks the payee against an authoritative directory (university bursar accounts, government fee endpoints);
  - enforces a cooling-off period or second approval from a trusted contact, e.g., parents in the home country, for first-time cross-border payees;
  - refuses "government fine" payment patterns.
  This makes security a scored property of the main agent rather than a separate app.

### Gaps
- Not verified this session: the EU Verification of Payee mandate (believed to be Oct 2025 under the Instant Payments Regulation), the UK APP-fraud reimbursement regime and Australia's Scam Prevention Framework. The EPC page returned 403 and the search budget ran out.
- I found no commercial startup that offers a scam guardian specifically for international students' cross-border payments.

---

## Q6. Seed (e): departure or offboarding agent (deposits, tax or pension refunds, account closure, repatriation, credit-history export)

### Takeaway
This is the least-served seed. What exists is fragmented: university checklists (Japan, Germany), bank advice, single-purpose refund agencies (German pension refunds, which are explained widely and offered by intermediaries; US and Australian tax or super refund agencies were not researched in depth), and deposit-return processes. Hard constraints make it a real multi-step task:
- some banks can't be closed from abroad;
- some can't receive international remittances;
- German pension refunds have a 24-month wait;
- deposits take 3–4 weeks.
I found almost no hackathon prior art.

### Cited Findings
- [Fact] Japan: accounts generally must be closed in person before leaving. Universities describe proxy closure, and selling or giving away a bankbook or cash card is illegal. Kyoto University (2026 handbook) and Osaka University provide departure procedures. A Shizuoka University page warns one regional bank (Suruga Bank) "does not accept international remittances", so money can't be sent back in after departure — [Kyoto University notice](https://kuiso.oc.kyoto-u.ac.jp/filesdir/files/life/notice_on_bank-accounts_en.pdf); [Osaka University](https://www.osaka-u.ac.jp/en/international/support_office/japan_life/leaving); [Shizuoka University](https://www.suoic.shizuoka.ac.jp/english/international/returningprocess/)
- [Fact] Bank of China (Canada), Jul 2026, advises students who finish their studies to close accounts in person before departure, and warns about fees and security risks on dormant accounts — [BOC Canada](https://www.boc.cn/ca/en/bocinfo/bi1/202607/t20260729_25682247.html)
- [Fact] Germany: a student-housing deposit is refunded after inspection, which takes 3–4 weeks, so students are advised to keep the German account open a month after leaving and then transfer the remainder home — [Ostfalia ISO departure](https://ostfalia.de/cms/en/iso/iso_international-students/iso_exchange-students/iso_departure). The University of Münster publishes a dedicated "offboarding" handbook section — [Uni Münster PDF](https://www.uni-muenster.de/imperia/md/content/wwu/auslandsamt/international_office-handbook-section-offboarding_en.pdf)
- [Fact, commercial guides] German pension refunds:
  - Non-EU/EEA/Swiss leavers can reclaim only the employee half of contributions.
  - Typically 24 months after leaving.
  - Working students pay pension contributions even under the Werkstudent privilege.
  - Intermediary services file on the leaver's behalf.
  Sources: [Simple Germany](https://www.simplegermany.com/german-pension-refund/); [WorkingStudentJobs](https://www.workingstudentjobs.de/blog/german-pension-refund-students); [Feather](https://feather-insurance.com/blog/a-complete-guide-to-getting-your-german-pension-back); [iamexpat](https://www.iamexpat.de/expat-info/german-expat-news/leaving-germany-dont-leave-your-money-behind)
- [Fact] Devpost keyword counts: "pension refund" 3 and "tax refund international student" 3. All are noise or tangential: "Exchange Treasurer" checks whether students' "money lasts until the flight home"; "CivicFlow AI" is a generic government-form agent. "moving abroad" has 141 hits, mostly arrival or relocation assistants — [Exchange Treasurer](https://devpost.com/software/exchange-treasurer); [CivicFlow AI](https://devpost.com/software/civicflow-ai); [Devpost search](https://devpost.com/software/search?query=pension%20refund)
- [Fact] Arrival or onboarding assistants for newcomers are heavily represented on Devpost. Examples: ArrivalOS, Arrival Quest, ArrivalMate, LandingMate AI, NewLife AI, AbroadOS, F1-Finance1, Clear-Path, Arrive, 49th (winner), Homie (winner), Talk To Canada, LifePilot, FreddyBuddy. Counts: "newcomer bank" 22; "international student bank account" 39 — [ArrivalOS](https://devpost.com/software/arrivalos); [Homie](https://devpost.com/software/homie-1d28pr); [49th](https://devpost.com/software/hack-canada-2026)

### Inferences
- [Inference] Departure is a clear white space: the arrival side is saturated, while the departure side has near-zero hackathon prior art and no integrated commercial product in what I found. It is also a natural "AI completes real financial tasks" story. The agent sequences deadlines (deposit inspection, final payroll, tax filing, the 24-month pension window), keeps the account alive just long enough, closes it correctly, and repatriates the balance with the right FX route. It can also export a credit-history or "good payer" credential, linking to seed (f). Each step produces verifiable artefacts for scoring task completion.
- [Inference] The compliance angle is rich: identity re-verification from abroad, proxy rules (e.g., Japan's ban on transferring cash cards), source-of-funds for repatriation, and protection against "refund agency" scams. The 24-month pension delay means a demo must use simulated time or mock APIs, which is acceptable at a hackathon if disclosed.

### Gaps
- Not researched in depth because the search budget ran out: Taxback, Sprintax (US FICA and nonresident tax refunds), Australia DASP or super-refund agencies, and their fees and AI features.
- I found no commercial "relocation offboarding" startup, but absence of search hits is weak evidence. A targeted search for terms like "leaving Germany service", "Abmeldung app" and "Japan nenkin lump-sum agent" is recommended.

---

## Q7. Seed (f): portable credit identity from home-country and alternative data with privacy-preserving computation

### Takeaway
Commercially this is Nova Credit's core (Credit Passport, cash-flow underwriting, a $35M Series D in Oct 2025). The China–HK corridor already has a regulated cross-border credit-verification platform built by WeBank (DVP). Hackathons are moderately saturated with "credit builder or alternative score for immigrants" and "ZK credit score" projects. The remaining gap is narrower: a student-held, consented, privacy-preserving credit credential that a landlord, lender or bank can verify without receiving raw data. US lending to international students also just lost its biggest specialist lender, MPOWER.

### Cited Findings
- [Fact] Nova Credit: Credit Passport (foreign bureau data translated into a US-equivalent score), Cash Atlas cash-flow underwriting, and partners including Seen Finance (Jan 2026) and reportedly JPMorgan Chase. It raised a $35M Series D in Oct 2025 — [Pulse 2.0](https://pulse2.com/nova-credit-35-million-series-d-raised-to-advance-growth-of-cash-flow-underwriting-platform); [Crowdfund Insider](https://www.crowdfundinsider.com/2026/01/258853-seen-finance-nova-credit-partner-to-improve-credit-access-by-using-cash-flow-data/); [CardRates](https://www.cardrates.com/news/jpmorgan-to-tap-new-markets-with-cash-flow-underwriting/)
- [Fact] The Shenzhen–HK DVP validates personal credit reports cross-border by hash. ICBC (Asia) plans to use it for newly arrived Mainland talent-scheme residents, and Nova Credit and Baihang were trial participants — [WeBank release](https://kyodonewsprwire.jp/release/202507292857); [SCMP](https://amp.scmp.com/tech/article/3261620/greater-bay-area-hong-kong-shenzhen-begin-cross-border-credit-checks-pilot-trial-data-transfer)
- [Single-source] MPOWER, the largest no-cosigner international student lender, reportedly collapsed in Oct 2026 — [PYMNTS](https://www.pymnts.com/?p=4286606)
- [Company claim] Reclaim Protocol lists "proving a credit score without revealing bank account details" as a use case — [Reclaim blog](https://blog.reclaimprotocol.org/posts/what-is-reclaim-protocol)
- [Fact] Hackathon prior art:
  - ShellHacks 2024 "Prospera" (raises immigrants' FICO by analysing income and spending) — [ShellHacks 2024 gallery](https://shellhacks2024.devpost.com/project-gallery)
  - Devpost "Alt-C" (carry credit history across borders) — [Devpost](https://devpost.com/software/alt-c)
  - Devpost "Dasa Gang/TrustBridge" (alternative credit score for migrants) — [Devpost](https://devpost.com/software/trustbridge)
  - Devpost "Lazo" (turns remittances into a credit history) — [Devpost](https://devpost.com/software/lazo)
  - Devpost "Ruta AI" (WhatsApp assistant to send money and build credit) — [Devpost](https://devpost.com/software/ruta-ai)
  - Devpost "ArriveAI" and "Anchor" (credit coaches) — [ArriveAI](https://devpost.com/software/arriveai); [Anchor](https://devpost.com/software/anchor-jlgsk0)
  - Devpost "CrediPro" and "ZKredit" (ZK creditworthiness for DeFi) — [CrediPro](https://devpost.com/software/credipro); [ZKredit](https://devpost.com/software/zkredit)
  - Devpost "MoveMate" (renter history for students) — [Devpost](https://devpost.com/software/movemate-1wck8u)
  - Event-level evidence: the ShellHacks 2023 idea list included immigrant credit-building — [ShellHacks 2023](https://shellhacks-2023.devpost.com/). A USAII 2026 example project targeted international students' financial-aid and credit gaps — [USAII 2026 gallery](https://usaii-global-ai-hackathon-2026.devpost.com/project-gallery)
- [Fact] Devpost keyword counts: "credit immigrant" 57; "credit score international student" 21; "bank balance zero knowledge" 93; "zktls" 36 (mostly unrelated authenticity demos) — [Devpost search](https://devpost.com/software/search?query=credit%20immigrant)

### Inferences
- [Inference] A plain "credit builder or alternative credit score for immigrants" is medium-high saturation. "Portable credit" is credible but well covered commercially (Nova Credit) and, for this jury, institutionally (WeBank's DVP). It would need a sharp twist to read as innovative, such as a student-held verifiable credential produced as a by-product of seeds (b) or (e): an on-time tuition, rent and allowance payment record, exported at departure and verifiable by a landlord or lender in the next country.
- [Inference] With MPOWER gone, "who underwrites international students now" is a fresh, topical question. A privacy-preserving, consented credential could be pitched as an input to lenders rather than as a lender.

### Gaps
- I found no evidence of a production ZK or MPC credit score accepted by a regulated lender.
- 2025–26 Experian, Equifax or TransUnion cross-border products were not researched.

---

## Q8. Hackathon prior art: what has been built and how common each concept is

### Takeaway
Across Devpost, HackQuest and ETHGlobal, the crowded concepts are:
- AI "co-pilot" or onboarding assistants for international students or newcomers;
- scam or fraud detectors (including international-student variants);
- stablecoin remittance or tuition rails;
- credit builders for immigrants;
- spending-limit or mandate layers for AI agents (dominant at 2026 Web3 hackathons).
Rare or absent: visa-refusal tuition refunds and reconciliation, departure or offboarding finance, and two-country purpose-bound family allowances with outbound compliance. ZK proof of funds for student visas has at least one direct clone. I found no list of past Fintechathon (WeBank / Tsinghua) winning projects.

### Cited Findings
- [Fact] Devpost keyword counts (16 Oct 2026; AND-match; noisy upper bounds) — [Devpost project search](https://devpost.com/software/search?query=remittance):

| Query | Count | Note |
|---|---|---|
| remittance | 208 | |
| remittance agent | 40 | Many are B2B accounts-payable agents |
| family remittance | 40 | |
| stablecoin remittance | 19 | |
| remittance student | 6 | |
| international student tuition | 53 | |
| tuition visa | 20 | |
| tuition refund | 4 | None relevant |
| proof funds visa | 13 | 1 direct hit: proofvault-zk |
| visa bank statement | 19 | |
| zktls | 36 | |
| scam payment | 444 | |
| scam elderly | 251 | |
| scam student | 177 | |
| scam international student | 23 | |
| credit immigrant | 57 | |
| credit score international student | 21 | |
| allowance programmable | 14 | |
| newcomer bank | 22 | |
| international student bank account | 39 | |
| pension refund | 3 | All noise |
| tax refund international student | 3 | Noise or tangential |
| cosigner agent | 2 | Both noise |

- [Fact] ETHGlobal Tokyo 2026 showcase snapshot (33 projects on the page fetched; it appears to be the default recent listing, not a filtered "remittance" result). Agent payment-control projects dominate: DSAP Protocol, Proviso, My Agent Ohana, Agent PayGuard, Izanagi, Axis (asks a World ID-verified human before large moves) and Meigi (Confirmation of Payee for stablecoins and agents) — [ETHGlobal showcase](https://ethglobal.com/showcase?search=remittance)
- [Fact] ETHGlobal sponsor prize framing often includes remittances, e.g., a PayPal USD prize at ETHGlobal New York 2025 — [ETHGlobal NY 2025 prizes](https://ethglobal.com/events/newyork2025/prizes). ETHGlobal "ProofOfFunds" (Cannes) — [ETHGlobal](https://ethglobal.com/showcase/proofoffunds-zczod)
- [Fact] Agentic payments hackathons in 2026:
  - HackMoney 2026 had an Arc track (155 teams built on Arc Testnet) including "Best Agentic Commerce App" — [Arc blog](https://www.arc.io/blog/meet-the-arc-track-winners-from-the-hackmoney-2026-hackathon-and-what-we-learned)
  - lablab.ai "Agentic Commerce on Arc" (Jan 2026, $20k USDC prizes) — [lablab.ai](https://lablab.ai/ai-articles/agentic-commerce-on-arc)
  - MERGE "Agent Pay" hackathon (Madrid, Sep–Nov 2026) — [MERGE](https://www.mmerge.io/hackathon-2026)
- [Fact] HackQuest has repeated stablecoin-tuition entries (Intuipay across several hackathons) and AI-FX remittance (ReMiT) — [Intuipay](https://hackquest.io/projects/Intuipay); [ReMiT](https://hackquest.io/projects/ReMiT)
- [Fact, Older] Remitly sponsored Technica 2022 with a "Best Hack Project That Benefits Immigrants Or International Students" prize — [Mammoth Times / GlobeNewswire](https://business.mammothtimes.com/mammothtimes/article/gnwcq-2022-10-13-remitly-to-sponsor-technica-2022-hackathon). Banga, a remittance app with sender spending controls, won at Berkeley in 2013 — [Berkeley iSchool](https://www.ischool.berkeley.edu/news/2013/i-school-teams-sweep-play-hackathon-awards)
- [Fact] Scam-agent winners: Guardião won Europe's largest AI hackathon (Feb 2026) — [NOVA FCT](https://www.fct.unl.pt/en/news/2026/02/nova-fct-alumna-wins-europe-s-largest-ai-hackathon-app-against-scams)
- [Fact] Fintechathon / Shenzhen International FinTech Competition:
  - The 2025 edition ran 5–7 Dec 2025, co-hosted by the Shenzhen University–WeBank FinTech College and WeBank, with 1,700+ students and an AI-track hackathon. The winners list was not in coverage found — [China.com](https://m.tech.china.com/redian/2025/1209/122025_1778234.html)
  - The 2023 edition had 300+ teams and 1,500+ students — [SZU WeBank FinTech College](https://swift.szu.edu.cn/en/info/1051/1655.htm)
  - [Unverified, aggregator] The 2026 International Track (Tsinghua PBCSF × WeBank) has an RMB 250,000 prize pool (1st prize RMB 100,000; best innovation RMB 20,000) and a 20 Oct 2026 deadline on fintechathon.g-ican.com — [Opportunities Corners](https://opportunitiescorners.com/?p=27537); [ScholarshipBob](https://www.scholarshipbob.com/scholarship/tsinghua-university-shenzhen-fintech-competition-2026-in-china)
  - The official site rendered only a title when fetched — [fintechathon.g-ican.com](https://fintechathon.g-ican.com)

### Inferences
- [Inference] Density ranking, most to least saturated:
  1. Scam detection (very high, including student-specific).
  2. AI financial co-pilot or onboarding assistant for international students or newcomers (very high).
  3. Agent spending limits or mandates (high, especially Web3 2026).
  4. Stablecoin remittance or tuition (high).
  5. Credit builder or alternative score for immigrants (medium-high).
  6. ZK proof of funds or creditworthiness (medium; one direct student-visa clone).
  7. Family allowance with sender rules (low-medium).
  8. Tuition reconciliation and visa-refusal refund (low).
  9. Departure or offboarding finance (very low).
- [Inference] Judges reward task completion (40%). The rare concepts (b-refunds, e) are also the most naturally multi-step and agentic, which favours them over the saturated ones.

### Gaps
- I could not access DoraHacks BUIDL search, Encode Club, Hack the North or MLH galleries in a countable way. The ETHGlobal search parameter did not appear to filter.
- Devpost project pages (hackathon name, date, prize) were blocked (403). Winner flags came only from the search JSON: e.g., VisaCurator [winner], Dispatch [winner], Reach RBC [winner], 49th [winner], Homie [winner].
- I found no past Fintechathon winning-project list, from 2025 or the International Track, to check for duplicates against this specific jury.
- The 20 Oct 2026 deadline comes from aggregators only. If correct, it leaves 4 days, so it should be checked on the official site immediately.

---

## Q9. Saturated vs underserved: synthesis and saturation table

### Takeaway
Avoid leading with scam detection, a generic "AI assistant for international students", cheapest-route remittance, stablecoin tuition, or standalone ZK proof of funds. These are the concepts judges have most likely seen. The clearest white space is the unhappy-path, end-of-cycle financial work:
- visa-refusal refund and reconciliation;
- departure or offboarding with repatriation and credit-history export;
- two-country purpose-bound family funding where an agent completes the home-country outbound compliance.
Guardian and co-signer checks and verifiable credentials work best as built-in safety and compliance layers in those agents rather than as the product.

### Cited Findings
- Evidence for each row is cited in Q1–Q8 above. Key anchors:
  - Flywire, Wise and Remitly 1-star themes — [Trustpilot Flywire](https://www.trustpilot.com/review/www.flywire.com?stars=1); [Trustpilot Wise](https://www.trustpilot.com/review/wise.com?stars=1); [Trustpilot Remitly](https://www.trustpilot.com/review/remitly.com?stars=1)
  - Australian visa-refusal refund complaints — [Ombudsman](https://www.ombudsman.gov.au/__data/assets/pdf_file/0027/315846/Media-Release-Visa-Refusal-Refunds.pdf)
  - WeBank DVP — [WeBank release](https://kyodonewsprwire.jp/release/202507292857)
  - Devpost counts — [Devpost search](https://devpost.com/software/search?query=remittance)

### Inferences

**Saturation table**

| Concept | Existing products and pilots (2025–26 unless noted) | Hackathon prior-art density | Remaining white space |
|---|---|---|---|
| (a) Proof-of-funds verifiable credential | Bangladesh Bank QR-verifiable visa statements; WeBank Shenzhen–HK DVP (hash-validates bank statements and credit reports); bank "certificates of finance" (SCB); zkTLS stacks (Reclaim, etc.); Canada GIC / Germany blocked accounts as standardised proof; no embassy accepts ZK/VC yet | **Medium**: a direct clone (Devpost proofvault-zk) plus ETHGlobal ProofOfFunds, zkRemit Guard, ZK credit demos, visa-doc assistants (FormBridge, Dossier, VisaCurator [W]) | Agentic monitoring of balance rules over the required window; multi-source evidence assembly; issuer-signed (bank or DVP-style) credential that verifiers trust; renewal or re-proof. Weak as a standalone pitch to this jury, since it overlaps WeBank's own DVP |
| (b) Tuition autopilot plus visa-refusal refund | Flywire (+Cohort Go, StudyLink), Convera (900+ institutions claimed), PayMyTuition, Pay4Me, Pax Credit, Crebit, WeChat 微汇款, Alipay, 易思汇, HK–Mainland Payment Connect; Chengdu e-CNY auto-refund pilot (Older) | **High** for "cheaper or faster tuition payment" (Intuipay ×n, Rex, Remintify, ReMiT, LADTransfer); **Low** for refund and reconciliation (0 relevant Devpost hits) | End-to-end lifecycle: payment-state tracking, bursar reconciliation, refusal-triggered refund playbook (e.g., Australia's 28-day rule) with repatriation to the original payer and FX/LRS compliance. Strong task-completion story |
| (c) Purpose-bound family allowance plus outbound compliance | MAS PBM trials incl. learning accounts (2023); e-CNY smart-contract prepaid education (2022–23); diaspora bill-pay (Aspora, EcoCash, MoneyHive, T-Plus); SideKick card (2020); Payment Connect limits; India LRS/TCS, China USD 50k quota | **Low-medium** for family allowance (XRPay, St4bl.com ×4, SigmaPay, Banga 2013); **High** for generic agent spending mandates (Nexus Pay ×5, DSAP, Proviso, Midnight Mandate) | Two-country, two-party flow: parent-side outbound paperwork done by the agent, plus purpose-locked direct payment to landlord or university, plus explainable release to parents. Can be framed as PBM/e-CNY-ready |
| (d) Payment guardian / AI co-signer vs scams | Starling Scam Intelligence agent (Jun 2026); Revolut intervention flow and AIR biometric approval; Singapore money lock (DBS digiVault, OCBC); university and FBI warnings | **Very high** (Devpost: "scam payment" 444, "scam student" 177; VisaShield, SafeRoute AI, RentEscrow, Guardião winner, ScamShield, PayPause, Interdict.ai, Meigi) | Narrow: guardian as a built-in layer of a payment-executing agent (authoritative payee directory, trusted-contact co-sign from the home country, cooling-off for first-time cross-border payees). Not a standalone idea |
| (e) Departure / offboarding agent | University checklists (Kyoto, Osaka, Münster offboarding handbook); BOC Canada advice; German pension-refund intermediaries; deposit-return processes; tax or super refund agencies (not researched in depth) | **Very low** (Devpost "pension refund" 3 and "tax refund international student" 3, all noise or tangential; arrival assistants are plentiful) | Largely open. Sequenced, deadline-driven agent: deposit, final pay and tax, account keep-alive then closure (incl. no-remote-closure banks), FX repatriation, pension refund at 24 months, credit/payment-history export. Strong multi-step, verifiable task completion |
| (f) Portable credit identity (privacy-preserving) | Nova Credit (Credit Passport, Cash Atlas; $35M Series D Oct 2025); WeBank DVP cross-border credit-report validation (ICBC Asia for newcomers); Reclaim "prove credit score"; MPOWER collapse (Oct 2026) leaves a lending gap | **Medium-high** (Prospera, Alt-C, TrustBridge, Lazo, Ruta AI, ArriveAI, Anchor, CrediPro, ZKredit, MoveMate) | Student-held, consented credential generated as a by-product of (b) and (e) payment records, verifiable by landlords or lenders in the next country; feeds lenders rather than being one |
| Cross-cutting: generic "AI financial co-pilot for international students" | Revolut AIR, Starling Assistant (generic); Flywire AI planned | **Very high** (F1-Finance1, NewLife AI, AbroadOS, FinMate, Clear-Path, Arrive, ArrivalOS, LandingMate, Homie [W], 49th [W], …) | Avoid as framing; judges score completion of a real task, not advice |

- [Inference] Combinations that may score well and are under-built:
  - (b) and (e) as one "visa-outcome and lifecycle money agent": admission → pay → refuse or arrive → depart. The refund and departure halves are the white space; arrival and pay are commodity.
  - (c) with (d) built in: a purpose-bound family allowance whose guardian layer uses a home-country trusted-contact co-sign, with outbound compliance done by the agent.
  - (a) and (f) as outputs, not products: verifiable proof-of-funds and payment-history credentials issued by the agent, which shows the privacy and compliance competence that carries 30% of the score.
- [Inference] Given WeBank's DVP and its Shenzhen–HK focus, a China–HK student corridor (Payment Connect limits plus the USD 50k quota) is a natural demo setting. A Vietnam-, India- or Africa-origin corridor would differentiate from the jury's own work. This is a judgment call for the team.

### Gaps
- Saturation levels for DoraHacks, Encode Club, Hack the North and MLH are estimated from Devpost, HackQuest and ETHGlobal evidence only.
- Commercial absence findings for (e) and the refund half of (b) rest on a limited number of searches before the search budget ran out. Confirm with 2–3 targeted searches before committing.
