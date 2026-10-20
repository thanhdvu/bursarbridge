# Judge lens: FinTechathon 2026 International Track (Topic C) — WeBank / Tsinghua priorities, China's on-chain stance, and how to frame the entry

Research date: 16 Oct 2026. Labels: **[Fact]** = verified in a primary or directly fetched source; **[Fact, secondary]** = from a news/aggregator summary that I could not open in full; **[Estimate]**; **[Inference]**.

Method note: fintechathon.g-ican.com is a JavaScript app, so a normal page fetch returns only the title. I downloaded its JS bundles and submission templates and read the text from them. That is where the official 2026 rules below come from (app bundle `app.83e69cd7.js`, rules bundle `chunk-4516c2dd.7f79eeba.js`, and the `/templates/` files). Web search ran out partway through, so a few items stay as gaps (listed per section).

---

## 1. What the official site says beyond the basic rules (judging, bonus scope, tech, deliverables)

### Takeaway
The official rules confirm the 40/30/30 rubric for all six international topics. **The 0–5 bonus is officially a "challenge / real-world implementation bonus" (挑战/落地加分), not an "on-chain" bonus.** It applies to the whole International Track and rewards "advanced topics *or* demonstrated real-world deployment". Topic choice alone does not change the base score. For Topics A–E, task completion is judged on scripted tasks in a simulated environment; only Topic F is judged on real on-chain transaction hashes. The deadline is **20 Oct 2026, 24:00 UTC+8, four days from today**.

### Cited Findings
- **[Fact]** International Track rubric, shared by all six topics: Task Completion 40%, "completion of scripted tasks in a simulated environment for non-on-chain topics; Topic F is evaluated using on-chain transaction hashes." Security & Compliance 30%: defence against induced transfers, data extraction, privilege escalation and prompt injection, and "serious security failures trigger substantial deductions." Innovation & Interaction 30%: scenario novelty, real-world value, dialogue efficiency, clarification, correction and fallback. — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)
- **[Fact]** Bonus wording, English: "A capped 0–5 point challenge/implementation bonus rewards advanced topics or demonstrated real-world deployment. Topic choice itself does not affect the base score." Chinese: 设置0—5分"挑战/落地加分"（封顶），奖励主动挑战高阶方向或实现真实落地的团队. Appeals can be filed within 3 business days of results. The site states that all six topics "use the same core judging dimensions" (Chinese: 确保跨方向可比, i.e. comparable across topics). — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)
- **[Fact]** The domestic AI track uses the same 40/30/30 weights with more detailed wording. Security covers induced transfers, information extraction, privilege escalation, prompt injection, plus **"confirmation and risk warnings for sensitive operations."** Interaction covers dialogue efficiency, clarification, error recovery, colloquial input, and (Chinese) 超范围兜底, out-of-scope fallback. This shows how WeBank judges read the same headings. — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)
- **[Fact]** Official Topic C text: "Cross-border / International Student Finance Assistant: Multi-currency, exchange rates, remittances and multilingual service." The Chinese version adds **（APEC 特色）, "APEC feature."** Topic F reads "Agent Wallet: An AI-owned wallet that can spend on-chain"; the Chinese adds 实现真实链上花钱 (real on-chain spending). A–E are new or expanded this year, and F is "the original Agent Wallet." — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
- **[Fact]** Overall brief, in the organisers' own vocabulary: "Select one direction and deliver a working financial Agent that demonstrates **intent understanding, task planning, safe execution, user control and measurable value** in a financial scenario." The Chinese brief says to build an agent that can 理解、规划、安全执行 (understand, plan, execute safely). — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
- **[Fact]** The site intro ties the international upgrade to **the 2026 APEC Summit taking place in Shenzhen.** — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
- **[Fact]** International deliverables:
  - Required: technical document, deck (≤10 min), demo video (≤5 min).
  - Optional: source code, security self-assessment, and "execution evidence."
  - All in English. Ten finalists are picked at online review. — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)
- **[Fact]** Template sections the judges will read:
  - [Technical document template](https://fintechathon.g-ican.com/templates/international-technical-document-en.docx): Project Overview; System Architecture (models, tools, data sources, external services); Agent Design (intent understanding, planning, tool use, state management, evaluation approach); Security Design ("tiered permissions and confirmation for sensitive actions"; protection against prompt injection, privilege escalation, privacy leakage); Deployment and Testing (test cases, known limitations).
  - [Security self-assessment template](https://fintechathon.g-ican.com/templates/international-security-self-assessment-en.docx): permission model (roles, permission boundaries, "confirmation, verification and rollback"); security tests (prompt injection, social engineering, privilege escalation, failure recovery); data and privacy ("provenance, consent, minimisation, storage and deletion"); known risks.
  - [Execution evidence template](https://fintechathon.g-ican.com/templates/international-execution-evidence-en.docx): asks for simulated account or sandbox logs (or transaction hashes for Topic F), with timestamp, action and result, plus "steps required for judges to reproduce or verify the evidence."
  - [Demo video guide](https://fintechathon.g-ican.com/templates/demo-video-guide-en.docx): end-to-end core scenario, then "safety mechanisms, innovation and results"; 16:9, 1080p, English subtitles.
- **[Fact]** Official international timeline:
  - Registration and submission: 31 Aug–20 Oct, 24:00 UTC+8.
  - Compliance screening: 21 Oct.
  - Online review: 22–23 Oct.
  - Finalists and invitations: 31 Oct.
  - English defence at WeBank, Shenzhen: 22 Nov.
  - Source: [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js). The [IEEE CIS Shenzhen announcement](https://r10.ieee.org/shenzhen-cis/blog/2026/06/17/2026-shenzhen-international-fintech-competition-international-track/) gives slightly different dates (online review 23–28 Oct; check-in and WeBank HQ visit 20 Nov; final 21–23 Nov). Treat the official site as current.
- **[Fact]** Rules that matter for an on-chain component:
  - "The International Track is governed by the laws of the People's Republic of China."
  - Third-party data, code, APIs and open-source components "must be legally authorised and comply with applicable open-source licences and data-use terms."
  - Source: [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)
- **[Fact]** Organisers per the official site:
  - Strategic guidance: Shenzhen Municipal Local Financial Administration, Shenzhen University, WeBank.
  - Host: Shenzhen University–WeBank Institute of FinTech.
  - Organisers: iCAN Future (Beijing) Technology Co. (the "g-ican" domain) and GouXiongHui.
  - Technical advisers: CCF Technical Committee on Digital Finance, **Tsinghua Institute of Financial Technology (THUIFR)**, IEEE CIS Singapore and Shenzhen chapters.
  - Prize pool: RMB 250k per track (Domestic AI, International AI, Data Analytics), RMB 750k total.
  - Source: [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
- **[Fact, secondary]** Third-party listings describe the International Track as "hosted by Tsinghua University's PBC School of Finance in collaboration with WeBank." They also mention a "PBCSF Appendix 2" PDF with full rules. — [ITS Global Engagement repost](https://www.its.ac.id/international/2026/10/06/2026-shenzhen-fintechathon-international-track-a-fully-funded-international-competition/); [Opportunities Corners](https://opportunitiescorners.com/?p=27537). THUIFR's website sits on the PBCSF domain (thuifr.pbcsf.tsinghua.edu.cn), consistent with THUIFR being part of PBCSF. — [THUIFR site](https://thuifr.pbcsf.tsinghua.edu.cn/english/Events_and_Exchange1/International_Visits/Japan/All.htm)
- **[Fact]** Aggregator pages attach the "0–5 challenge bonus" or "extra consideration for ambitious solutions" to Topic F only. — [Opportunities Corners](https://opportunitiescorners.com/?p=27537); [IEEE CIS Shenzhen](https://r10.ieee.org/shenzhen-cis/blog/2026/06/17/2026-shenzhen-international-fintech-competition-international-track/). The official site places it track-wide (see above).
- **[Fact]** Recommended tech for the 2026 International Track: none named on the official site. No chain, testnet, LLM or sandbox is specified. — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)

### Inferences
- **[Inference]** For Topic C there are two routes to the bonus: (a) "advanced direction," where a real, verifiable on-chain element is the obvious reading because F is the on-chain topic; or (b) **"real-world deployment" (落地)**, such as a live deployment, real users or pilots, or integration with real (sandbox) financial APIs. Route (b) carries no regulatory risk and may be worth as much as (a). The strongest bonus pitch combines a modest, compliant on-chain element with deployment evidence.
- **[Inference]** "Scripted tasks in a simulated environment" means judges will likely run or read concrete test scripts, such as "send 500 USD to my landlord in Vietnam", "pay the spring tuition invoice", "what's my best FX timing". Task Completion (40%) rewards an agent that reliably finishes multi-step scripted tasks with correct tool calls. The optional Execution Evidence (sandbox logs plus reproduction guide) is effectively how a Topic C team proves Task Completion, so submit it even though it is optional.
- **[Inference]** Because the site says topic choice does not affect the base score, picking Topic C costs nothing against F teams. Topic C also has an official "APEC feature" hook that F lacks.
- **[Inference]** With PRC law governing the track, any on-chain feature that would be illegal for mainland users (crypto or stablecoin rails, token issuance) is a direct compliance problem under the 30% Security & Compliance criterion.

### Gaps
- I could not access the "PBCSF Appendix 2" PDF that the ITS page references. It might use the "on-chain exploration" bonus wording the user quotes. If the team has it, its wording should override mine.
- The official site does not say whether organisers supply a simulated environment or test scripts for Topics A–E, or which chain or testnet Topic F uses.
- No 2026 judge names are published. The [IEEE CIS page](https://r10.ieee.org/shenzhen-cis/blog/2026/06/17/2026-shenzhen-international-fintech-competition-international-track/) lists an Academic Advisory Board: Shouyang Wang (CAS), Qiang Yang (WeBank Chief AI Advisor), Jianqing Li (Shenzhen University) and others. It does not say they judge.

---

## 2. Past editions, winners, judges

### Takeaway
FinTechathon is WeBank's university competition, running since 2019. 2026 is the 8th edition and the first with an international track. Winners consistently pair a **real financial pain point** with WeBank's own technology identity: federated learning/FATE, privacy-preserving computation, and FISCO BCOS consortium chains used for **traceability, evidence and regulator-friendly ("supervisable") data sharing**. No winner had tokens or speculation. Recent AI winners (2025) are multi-agent LLM systems that stress trusted reasoning, hallucination control and on-device privacy.

### Cited Findings
- **[Fact]** History: started 2019 as "FinTechathon WeBank University FinTech Technology Competition," rebranded in 2022. Eight editions, "thousands" of works, nearly 10,000 students. — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js); [ifeng, Sep 2026](https://tech.ifeng.com/c/8wJG9eH2KFs); [CLS, Sep 2026](https://www.cls.cn/detail/2471634)
- **[Fact]** 2026 domestic track: "AI Banking Agent," built around smart transfers, bill analysis, wealth operations, card management, subscription and auto-debit management, and cross-scenario linkage. Required capabilities: tiered permissions, hallucination and prompt-injection defence, intent understanding and task planning. Review combines automated evaluation with expert blind review. Winners get a WeBank fast-track ("green channel") interview. — [CLS](https://www.cls.cn/detail/2471634); [ifeng](https://tech.ifeng.com/c/8wJG9eH2KFs)
- **[Fact] 2025 (7th, final 5–7 Dec 2025, Shenzhen; guided by Shenzhen Local Financial Administration).** Source: [Official app bundle, past2025 module](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
  - AI track:
    - 1st prize: 灵操盘 (HKUST-Guangzhou). Zero-code quant engine that turns natural-language investment ideas into back-testable strategies. Multi-agent architecture, financial knowledge graph, "trusted reasoning" and hallucination filtering.
    - 2nd: 易金经 (Capital University of Economics and Business). LLM plus knowledge graph for investment.
    - 3rd: FinAgent (HKUST-GZ). Multi-agent finance and investment assistant using Qwen3-VL for bill capture with on-device privacy protection, built on WeBank user bill data.
    - Best Creativity: EchoPolis (Nanjing University). DeepSeek-driven "digital twin" of Gen-Z financial behaviour.
  - Data-analytics track:
    - 1st: scalable mixture-of-experts AML/fraud detection (Peking University).
    - 2nd: interpretable SME credit scorecard.
- **[Fact] 2024 edition (site module `past2024`).** Source: [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
  - 1st prizes:
    - AI: One-shot SSVFATE, a personalised self-supervised **vertical federated credit-assessment** system built on FATE.
    - Blockchain: AIGC-model trusted supervision and transaction-traceability platform (Beijing Institute of Technology).
    - Product-manager track: **成长盈 (Shenzhen University), a savings, financial-education and AIGC-advisor platform for university students**, with a "graduation fund" and "career fund" to bridge the job transition.
  - Other awards: CipherBridge verifiable multi-party ciphertext computation (HKUST, blockchain 2nd); FATE-LLM financial digital-human assistant for the elderly (AI 3rd).
- **[Fact] 2023 edition (site module `past2023`).** Source: [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
  - AI 1st: OncoFed (FATE-based federated tumour diagnosis).
  - Blockchain 1st: AI4C, an AIGC copyright platform deployed on **FISCO BCOS** with trusted hardware for privacy computing.
  - PM 1st: a conversational LLM "digital butler" for the WeBank app.
  - Others: ESG report generator on LangChain + FATE-ChatGLM3-6B; federated-learning platform on FISCO BCOS; supply-chain carbon-footprint chain with on-/off-chain hybrid storage.
- **[Fact] 2020–2021 blockchain winners.** Source: [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
  - 2020: a volunteer "time bank" on chain; an accounting consortium chain on FISCO BCOS using UTXO plus homomorphic encryption.
  - 2021: 医链, privacy-preserving medical data sharing with proxy re-encryption, zero-knowledge proofs and aggregate signatures; 安产链, "supervisable, privacy-preserving" safety-production oversight; a charity crowdfunding chain against fraudulent fundraising.
- **[Fact, older: 2019–2020 content still in the site bundle]**
  - 2019: 178 teams; AI and Blockchain tracks.
  - Judges: **AI chair Yang Qiang** (then WeBank Chief AI Officer and HKUST Chair Professor); **Blockchain chair Ma Zhitao** (WeBank VP and CIO); WeBank's Fan Lixin (Chief Scientist of AI) and Zhang Kaixiang (Chief Architect of Blockchain); professors from HKUST, NTU, Tsinghua (Tang Jie), Beihang, Fudan and others.
  - The blockchain track required FISCO BCOS plus WeBASE, WeCross, **WeIdentity** (distributed identity) and WeEvent. Reference topics stressed acting "under the condition of legal compliance," with issuing, distribution, redemption, "clearing and supervision on the chain."
  - Source: [Official site legacy bundle lang-en-US-home](https://fintechathon.g-ican.com/js/lang-en-US-home.e7c9e6aa.js)
- **[Fact, older 2019]** PBCSF and THUIFR co-ran a separate "First Chinese University Fintech Case Competition" (Aug 2019, Beijing; 160+ teams). It was judged on case reports and on-site defence by finance professors (including PBCSF's Wang Zhengwei) and fintech CEOs. — [PBCSF English site](https://eng.pbcsf.tsinghua.edu.cn/info/1072/1332.htm)

### Inferences
- **[Inference]** The judges come from a WeBank engineering and research culture. They have rewarded FATE and federated learning, privacy-preserving computation, and FISCO BCOS consortium chains used for evidence, traceability and "supervisable" sharing. An on-chain element framed as **"consortium chain + verifiable evidence + regulator view"** matches eight years of winners. A token-economy framing matches none of them.
- **[Inference]** Student-finance precedent exists: 成长盈 (2024 PM 1st prize) won with a student-savings and financial-education product. Judges have rewarded the student-finance pain point before. A Topic C entry should go beyond it with real cross-border execution, i.e. remittance, tuition payment and FX.
- **[Inference]** Several winners used WeBank-relevant data or scenarios, such as FinAgent on WeBank bill data and the WeBank-app digital butler. Mapping Topic C onto WeBank's real cross-border infrastructure (Section 3) should resonate with the WeBank judges.

### Gaps
- No published judges' comments or scoring sheets from past editions were found.
- There was no international track before 2026, so there are no international precedents.
- Exact year mapping for some winner lists comes from module names in the site bundle (`past2023`, `past2024`). I did not cross-check them against press releases.

---

## 3. WeBank in 2025–2026: strategy, AI, cross-border, open source

### Takeaway
WeBank calls itself an **"AI-native bank."** It runs 800+ agents and 70–80+ "digital employees," and its executives describe the model as "AI-led execution" where humans set goals, boundaries and oversight. Its cross-border work is very relevant to Topic C. It designed the Shenzhen–Hong Kong and Guangdong–Macao **cross-border data verification platforms**, which cover credit reports, bank statements and **university admission letters**. It is also expanding into SE Asia through WeBank Technology. Its inclusion story centres on thin-file borrowers.

### Cited Findings
- **[Fact, secondary]** Strategy shift from "digital-native" to an "AI原生银行" (AI-native bank). By end-2025: AI compute up 3.5x year on year; daily AI calls up from 41,000 to 2.4 million; **70+ digital employees and 800+ agents across 1,000+ scenarios**; 400B+ tokens a year; credit-bond review cut from days to about 10 minutes. — [Shanghai Securities News via 10jqka, 27 May 2026](https://news.10jqka.com.cn/20260527/c677024296.shtml)
- **[Fact, secondary]** Cross-border: WeBank is the overall solution designer and technical supporter of the **Guangdong–Macao and Shenzhen–Hong Kong cross-border data verification platforms**. The Shenzhen–HK platform covers 11 verification scenarios, including personal and enterprise credit reports, **bank statements and university admission letters**, and connects 19+ institutions. Hong Kong-based subsidiary WeBank Technology has entered **Indonesia, Malaysia and Thailand.** — [10jqka](https://news.10jqka.com.cn/20260527/c677024296.shtml)
- **[Fact, secondary]** Inclusion: 440M+ individual customers; **about 20% of WeLend borrowers are "first-time borrowers" with no prior PBOC credit record**; 7.6M+ enterprises have applied for WeBiz loans, almost all private firms; 6.5M visits from hearing- or visually-impaired and elderly customers in 2025. — [10jqka](https://news.10jqka.com.cn/20260527/c677024296.shtml)
- **[Fact]** July 2026: WeBank won The Asian Banker's first "Best AI-Driven Bank of the Year in Asia Pacific".
  - AI Engineering Platform: elastic compute, low-code tools, knowledge bases, **an MCP plugin marketplace and reusable Skills for building agents**; more than 20B tokens a day.
  - 80+ "digital teammates" that go through onboarding and performance reviews; anti-fraud case handling cut from 3 days to 5 minutes.
  - Chief AI Architect Eason Wang: the bank is moving from human-led execution with AI help to "AI-led execution," where humans "define objectives, set boundaries and provide oversight."
  - Source: [PR Newswire via Webull, 21 Jul 2026](https://www.webull.com/news/15264219198792704)
- **[Fact, secondary]** 2025 results (disclosed 30 Apr 2026): total assets RMB 766.29B (+17.57%), revenue RMB 36.28B (−4.84%), net profit RMB 11.01B (+1.00%). — search summary of [Jiemian](https://www.jiemian.com/article/14835776.html) / [10jqka](https://news.10jqka.com.cn/20260527/c677024296.shtml); annual report not opened.
- **[Fact]** Yang Qiang is listed as "WeBank Chief AI Advisor" on the 2026 competition's Academic Advisory Board. — [IEEE CIS Shenzhen](https://r10.ieee.org/shenzhen-cis/blog/2026/06/17/2026-shenzhen-international-fintech-competition-international-track/)
- **[Fact]** Open source, FISCO BCOS: actively maintained. v3.16.4 (Jan 2026) is "Latest"; v3.17.0/3.17.1 (Aug–Sep 2026) are security-hardening pre-releases after audit findings. Recent work covers **Web3 RPC (Ethereum-style JSON-RPC, WebSocket, eth_subscribe)** with continued Solidity/EVM support. — [FISCO-BCOS GitHub releases](https://github.com/FISCO-BCOS/FISCO-BCOS/releases)
- **[Fact]** FATE-LLM ("Federated Learning for LLMs"): federated parameter-efficient fine-tuning and privacy-preserving inference such as InferDPT. It lists a 2026 ACL paper. — [FATE-LLM GitHub](https://github.com/FederatedAI/FATE-LLM)
- **[Fact]** The WeBankFinTech GitHub org's most recently updated repos (2025–26) are mostly infrastructure: fes-design, Schedulis, Prophecis ML platform, DeFiBus. No public agent framework appears on page 1. — [WeBankFinTech GitHub](https://github.com/orgs/WeBankFinTech/repositories?type=all&sort=updated)
- **[Fact, older]** WeBank's blockchain stack as presented to competitors: FISCO BCOS, WeBASE middleware, **WeIdentity (distributed identity / verifiable credentials)**, WeCross cross-chain, WeEvent. — [Official site legacy bundle](https://fintechathon.g-ican.com/js/lang-en-US-home.e7c9e6aa.js)

### Inferences
- **[Inference]** The vocabulary that will land with WeBank judges: *AI-native*, *agents / digital employees*, *Skills*, *MCP tools*, *humans set objectives and boundaries, AI executes*, *inclusive finance / first-time borrowers (首贷户)*, *cross-border data verification*, *privacy-preserving computation*, *federated learning*, *consortium chain*.
- **[Inference]** The strongest Topic C hook: international students are a cross-border thin-file group, much like WeLend's "first-time borrowers." Their key documents (admission letter, bank statement, credit report) are exactly what WeBank's Shenzhen–HK verification platform verifies. Framing the agent's credential layer as compatible in spirit with that infrastructure, e.g. W3C-style verifiable credentials or a WeIdentity-like DID, ties the idea to something WeBank already runs.
- **[Inference]** WeBank's SE Asia expansion (Indonesia, Malaysia, Thailand) and the APEC framing suggest demo corridors such as China↔ASEAN or within APEC (e.g. a Vietnamese or Indonesian student in Shenzhen or Hong Kong). These will read as strategically relevant.
- **[Inference]** Building tools as MCP servers or "Skills" mirrors WeBank's own platform language.

### Gaps
- I found no 2025–2026 public talk by Yang Qiang specifically on agentic AI, and no newer status for WeIdentity or WeDPR (search budget ran out).
- I found no named WeBank retail product built on a customer-facing AI agent. Agent use described publicly is mainly internal: risk, anti-fraud, operations, R&D, marketing.

---

## 4. PBCSF (Tsinghua) priorities and links to PBOC thinking

### Takeaway
PBCSF's public 2025–2026 fintech agenda centres on **CBDC/e-CNY serving the real economy, regtech, "AI+finance," and payments**. Its framing comes from national policy, especially the "five major articles" of finance. It hosts forums with PBOC's Digital Currency Research Institute. In 2026 it partnered with Huawei on payments and regtech, including "AI and intelligent agents" and cryptographic security.

### Cited Findings
- **[Fact]** Sept 2025 Bund Summit: PBCSF, through its **Research Center for Financial Development and Regtech**, hosted a forum on new fintech applications and CBDC innovation.
  - Speakers: **Mu Changchun (Director, PBOC Digital Currency Research Institute)**, Chen Wenhui (former CBIRC vice-chair) and PBCSF Vice Dean Zhang Xiaoyan, who framed it as contributing to the finance "five major articles" (五篇大文章).
  - Released a report on blockchain plus e-CNY enabling industrial digitalisation (《智链融合·数字人民币赋能产业数字化研究报告》).
  - Roundtable theme: CBDC innovation "serving the real economy."
  - Source: [Tsinghua News, 17 Sep 2025](https://www.tsinghua.edu.cn/info/1180/121368.htm)
- **[Fact]** Dec 2025: PBCSF hosted the Tengchong Scientists Forum "Technology + Finance" session, themed **"AI+金融：技术赋能与价值创造"** (AI+Finance: technology empowerment and value creation). Keynote by Tian Xuan (Dean, Tsinghua National Institute of Financial Research; PBCSF Vice Dean); welcome by PBCSF Dean Jiao Jie; former CBIRC vice-chair Liang Tao spoke. — [Tsinghua News, 9 Dec 2025](https://www.tsinghua.edu.cn/info/1177/123118.htm)
- **[Fact]** May 2026: PBCSF and Huawei's Central Bank business unit co-hosted a National Payment & RegTech Roundtable. Planned collaboration areas: **AI and intelligent agents, cryptographic security, cloud and big data analytics.** — [PBCSF Global Finance Forum site](https://en.gff.pbcsf.tsinghua.edu.cn/en2026/info/1021/2974_1.htm)
- **[Fact, secondary]** Tian Xuan, Mar 2025 interview: AI is spreading into trading, product design, operations and risk management, and finance education should combine AI and finance skills. — search summary of [Tsinghua media pages](https://www.tsinghua.edu.cn/info/1182/117470.htm)
- **[Fact]** THUIFR is a technical guidance unit of the 2026 competition. — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)

### Inferences
- **[Inference]** PBCSF-side judges will listen for **policy fit and financial-stability awareness**: serving the real economy, inclusive and digital finance, compliance with capital-account and AML rules, and a regtech or supervisory view. A one-slide "policy alignment" frame (inclusive finance plus digital finance, cross-border payment efficiency, regulator-friendly design) should resonate.
- **[Inference]** If the pitch touches future rails, name **e-CNY / mBridge as the policy-endorsed path for cross-border payment efficiency** (see Section 5), not stablecoins.

### Gaps
- No PBCSF statement specific to international-student finance or remittances was found.
- No 2026 PBCSF publication on AI agents was found, beyond the Huawei collaboration areas.
- The ITS-referenced "PBCSF Appendix 2" was not accessible.

---

## 5. China's 2025–2026 stance on crypto, stablecoins, e-CNY and permissioned chains, and how to frame an on-chain component

### Takeaway
Mainland policy **tightened further**. A Nov 2025 multi-agency meeting flagged stablecoins as an enforcement focus, and **Yin Fa [2026] No. 42 (6 Feb 2026)** replaced the 2021 crypto notice and extended the ban to stablecoins and unapproved RWA tokenisation. Hong Kong runs a separate licensing regime: Stablecoins Ordinance from 1 Aug 2025, first two licences (HSBC, Anchorpoint) on 10 Apr 2026. Beijing's endorsed cross-border path is **e-CNY / mBridge**. Permissioned blockchain for evidence and traceability remains legitimate, subject to CAC filing. A student team should make the chain an **audit and verification layer, never a money or token layer.**

### Cited Findings
- **[Fact, secondary]** 28 Nov 2025: after a 13-agency coordination meeting, the PBOC said crypto speculation had resurfaced, made **stablecoins an enforcement focus**, and argued they cannot currently meet customer-identification and AML requirements. HK-listed crypto stocks fell. — [SCMP](https://www.scmp.com/economy/china-economy/article/3334675/chinas-central-bank-vows-stamp-out-illegal-activities-trading-stablecoins); [PaymentExpert](https://paymentexpert.com/2025/12/01/chinas-central-bank-tightens-stance-as-stablecoins-pulled-into-crypto-clampdown/); [Malay Mail](https://www.malaymail.com/news/money/2025/12/01/hong-kong-crypto-stocks-slide-after-china-flags-stablecoin-crackdown/200315) (search summaries; full articles not opened)
- **[Fact, secondary]** **Yin Fa [2026] No. 42.** Source: [CryptoSlate summary](https://cryptoslate.com/crypto-laws/china-pboc-virtual-currency-rwa-notice-no-42-2026/); [PYMNTS](https://www.pymnts.com/cryptocurrency/2026/china-extends-crypto-ban-to-stablecoins-and-tokenized-assets/). The official PBOC text was not opened.
  - Issuers: PBOC with NDRC, MIIT, MPS, SAMR, NFRA, CSRC and SAFE. Effective 6 Feb 2026; repeals Yin Fa [2021] No. 237.
  - Bitcoin, Ether, Tether and similar assets have no legal-tender status. Exchange, matching, information intermediation, pricing and token-issuance financing in the mainland are illegal financial activity.
  - **No RMB-pegged stablecoin may be issued, onshore or offshore, without authorities' agreement.**
  - **RWA tokenisation is illegal onshore unless approved and run through specified financial infrastructure.**
  - Banks and payment institutions may not provide account, clearing or settlement services for these activities. Internet platforms may not host or promote them.
  - Offshore entities may not unlawfully serve mainland residents.
- **[Fact, secondary]** Ant Group and JD.com shelved Hong Kong stablecoin plans in Oct 2025 after regulators ordered a halt. — [Forbes, 9 Aug 2026](https://www.forbes.com/sites/digital-assets/2026/08/09/the-yuan-stablecoin-is-not-coming-beijing-has-already-said-so/) (search summary; page returned 403)
- **[Fact]** Hong Kong: the Stablecoins Ordinance (Cap. 656) took effect **1 Aug 2025**, and issuing fiat-referenced stablecoins requires a licence. — [HKMA stablecoin page](https://www.hkma.gov.hk/eng/key-functions/international-financial-centre/stablecoin-issuers/). **First two licences granted 10 Apr 2026 to Anchorpoint Financial Limited and HSBC.** HKMA Chief Executive Eddie Yue called it "an important milestone." HKMA urged the public to use stablecoins only through regulated channels and to beware of scams. — [HKMA press release, 10 Apr 2026](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/04/20260410-4/)
- **[Fact, secondary]** e-CNY:
  - The PBOC's 2026 line is to 稳步发展数字人民币 (develop the e-CNY steadily).
  - From 1 Jan 2026, a new management framework (e-CNY app 2.0) took effect, and **real-name wallet balances at the six large state banks earn interest at the demand-deposit rate.**
  - The international operation centre runs in Shanghai.
  - mBridge, as of end-Nov 2025: 4,047 cross-border payments worth about RMB 387.2B equivalent, with e-CNY about 95.3% of value.
  - Provincial 2026 priorities include e-CNY border-trade QR payments with Vietnam and Laos (Yunnan).
  - Source: [10jqka, 20 Jan 2026](https://news.10jqka.com.cn/20260120/c674140165.shtml)
  - Related: Bank of Communications and Malaysian partners showed an e-CNY cross-border solution at the 2026 China International Financial Expo — [Xinhua](https://www.xinhuanet.com/fortune/20260617/d297cdab324548a3ab840ed40fe4cad8/c.html) (search summary).
- **[Fact]** CAC Provisions on Blockchain Information Services (in force since 15 Feb 2019):
  - Providers must file with the CAC within 10 working days of launching (Art. 11).
  - Users' real identities must be verified (Art. 8).
  - New products and features need a security assessment (Art. 9).
  - Source: [CAC](http://www.cac.gov.cn/2019-01/10/c_1123971164.htm)
- **[Fact]** WeBank's consortium-chain stack (FISCO BCOS) is actively maintained and adds Ethereum-compatible Web3 RPC. — [FISCO-BCOS releases](https://github.com/FISCO-BCOS/FISCO-BCOS/releases). PBCSF's 2025 report explicitly pairs blockchain with e-CNY for industrial digitalisation. — [Tsinghua News](https://www.tsinghua.edu.cn/info/1180/121368.htm)

### Inferences
- **[Inference]** Legitimate "on-chain" uses in the current Chinese policy climate:
  - Permissioned/consortium chains for **evidence, traceability, verifiable credentials and supervisory access.**
  - CBDC/mBridge for cross-border payments.
  - In Hong Kong only, licensed stablecoins.

  Red-zone uses: public-chain crypto and stablecoins as payment rails for mainland users, token issuance, yield or RWA tokens.
- **[Inference]** Safest framing for Topic C's on-chain part, in order:
  1. **Tamper-evident audit trail.** Hash-anchor the agent's decision trace, risk checks, user confirmations and consent receipts on a permissioned chain such as FISCO BCOS. Keep raw PII off-chain and store only hashes and salts. Give an auditor or regulator node read access. This mirrors the "supervision on the chain" wording from WeBank's own past briefs.
  2. **Verifiable credentials for student documents.** Admission letter, enrolment proof, tuition invoice and remittance-purpose declaration issued as VCs, WeIdentity-style DID or W3C VC. The agent verifies them before preparing a tuition payment. This links to WeBank's real Shenzhen–HK cross-border verification platform, which already covers admission letters and bank statements.
  3. **Smart-contract policy guardrails**, optional: spending limits, allow-listed payees (verified university accounts) and a two-party confirmation rule recorded on chain. The rules are enforced, but no value moves on chain.
- **[Inference]** If the team wants to mention payment rails, present **e-CNY/mBridge as a future-interoperability option** and Hong Kong-licensed stablecoins only as a jurisdiction-specific note for HK users. Never present stablecoins as a remittance rail for mainland users. Do not claim a live e-CNY integration.
- **[Inference]** Use the wording "permissioned / consortium chain," "evidence anchoring," "verifiable credential," "regulator node," "no tokens, no value on chain." Avoid "crypto," "Web3 wallet," "token," "DeFi," "yield," "airdrop," "USDT."
- **[Estimate]** Even with no public-chain assets, a public testnet reads more "crypto-ish" to this audience than FISCO BCOS. If the team already has EVM tooling, FISCO BCOS's Web3 RPC compatibility (per release notes) may let it reuse Solidity and ethers-style code. This compatibility was not tested.

### Gaps
- The official PBOC text of No. 42 was not opened, so the wording relies on secondary summaries. PaymentExpert, SCMP and Forbes pages were blocked or paywalled.
- I could not verify by search, so these are background only, not cited facts: the current SAFE individual FX quota (widely cited as USD 50,000 a year), PIPL cross-border personal-data transfer rules, and BSN's current status.
- I did not find which currencies the two HK licensees will issue, or when they launch.

---

## 6. How Chinese regulators and banks talk about AI agents in finance (2025–2026)

### Takeaway
The key 2026 document is the **NFRA Guidelines on the Safe Development and Application of AI in Banking and Insurance (18 Jun 2026)**. It treats **fund transactions, credit approval, underwriting and claims, and risk management as high-risk**. In those areas it requires human supervision and intervention at key steps, explainability limits, AI-content labelling, and a ban on using personal data to train generative models. It names agent-specific risks: **data leakage, memory contamination, identity privilege abuse, tool misuse, runaway operation**. Banks themselves describe 2026 as the year agents became the main vehicle for AI.

### Cited Findings
- **[Fact]** NFRA guidelines, 18 Jun 2026. Source: [The Paper](https://www.thepaper.cn/newsDetail_forward_33409946); document number 金发〔2026〕8号 per search summary of [BBT News](https://www.bbtnews.com.cn/2026/0618/596754.shtml)
  - Structure: 32 items covering governance, development, data, compute, risk management, capability building and supervision.
  - Board-level committee responsible for AI.
  - **Human supervision and intervention at key steps of high-risk applications** (在高风险应用关键环节建立人工监督和干预机制).
  - High-risk uses include fund trading, asset valuation, credit approval, underwriting and claims, and risk management. They need risk-committee approval.
  - **Names, ID, phone and bank-card numbers may not be used to train or optimise generative models.**
  - Insufficiently explainable AI may only be an auxiliary tool in high-risk scenarios.
  - AI-generated content must be prominently labelled and explained to consumers.
  - **Agents: guard against data leakage, memory contamination, identity privilege abuse, tool misuse and runaway operation** (防范数据泄露、记忆污染、身份越权、工具滥用、运行失控).
  - External models need strict internal evaluation; generative models must be filed with the CAC.
- **[Fact, secondary]** Industry framing: 2025 was the "first year" of bank LLM deployment, and by H1 2026 agents had become the core vehicle for bank AI. — search summary of [Xinhua](https://www.news.cn/fortune/20250910/ec64e5bf15454f75929b2ac438d2973c/c.html) / [CNFIN](https://www.cnfin.com/hb-lb/detail/20260903/4464405_1.html)
- **[Fact]** WeBank: "humans define objectives, set boundaries and provide oversight" while AI executes. Digital employees handle anti-fraud, operations and R&D. — [PR Newswire via Webull](https://www.webull.com/news/15264219198792704)
- **[Fact]** The competition's own security criteria mirror these risks: induced transfers, information extraction, privilege escalation, prompt injection, plus confirmation and risk warnings for sensitive operations. — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js)

### Inferences
- **[Inference]** Topic C's core actions (remittance, tuition payment, FX conversion) fall under "fund trading," which is high-risk in NFRA terms. The design should show:
  - tiered permissions: read-only → draft → execute-with-confirmation;
  - mandatory human confirmation, with step-up verification above thresholds;
  - payee allow-lists;
  - velocity and amount limits;
  - cooling-off and rollback where possible;
  - an explainable "why this route / fee / rate" card;
  - AI-content labelling;
  - no PII in model training;
  - a red-team table covering the five NFRA agent risks.

  Quoting NFRA's own five agent-risk terms in the security self-assessment is a low-cost, high-signal move.
- **[Inference]** Scams targeting international students (fake tuition invoices, impersonation of universities or officials, "urgent fee" pressure) give a natural, judge-relevant **social-engineering test suite**. They map directly to "induced transfers."

### Gaps
- No PBOC-specific guidance on AI agents or "agent payments" (智能体支付) was found before search ran out.
- No source found for whether State Council "AI+" action-plan items specific to finance apply.

---

## 7. What will likely impress or annoy these judges (all inference), plus checklist and on-chain recommendation

### Takeaway
**[Inference]** Winning Topic C entries will look like a **safe, deployable, inclusion-oriented cross-border agent** that WeBank could imagine piloting in the Greater Bay Area or APEC corridors. They will be scored mostly on reliable scripted task completion and visible security engineering. The on-chain element should be a small, compliant trust layer (evidence plus credentials), and the bonus pitch should also cite real-deployment evidence.

### Cited Findings
- Rubric, bonus and deliverables — [Official rules bundle](https://fintechathon.g-ican.com/js/chunk-4516c2dd.7f79eeba.js); [templates](https://fintechathon.g-ican.com/templates/international-execution-evidence-en.docx)
- Past winners' patterns (FATE/federated, FISCO BCOS evidence chains, multi-agent with trusted reasoning, student finance) — [Official app bundle](https://fintechathon.g-ican.com/js/app.83e69cd7.js)
- WeBank's cross-border verification platform and inclusion metrics — [10jqka](https://news.10jqka.com.cn/20260527/c677024296.shtml)
- NFRA agent-risk terms — [The Paper](https://www.thepaper.cn/newsDetail_forward_33409946)
- Stablecoin and RWA restrictions — [CryptoSlate](https://cryptoslate.com/crypto-laws/china-pboc-virtual-currency-rwa-notice-no-42-2026/); [HKMA](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/04/20260410-4/)

### Inferences

**Judge resonance checklist (Topic C)**
1. **Use the organisers' words.** Structure the deck and tech doc around "intent understanding → task planning → safe execution → user control → measurable value." Pitch it as "AI as a financial participant" with humans setting goals and boundaries.
2. **Make Task Completion provable.** Write 10–20 scripted Topic C tasks: remit to a family member, pay a tuition invoice, convert currencies at the best quoted time, set up a recurring rent payment, build a credit file. Run them in a realistic sandbox and include logs plus a reproduction guide in the Execution Evidence doc.
3. **Tiered permissions and confirmation for every money movement.** Read, draft and execute tiers; thresholds with step-up confirmation; payee allow-lists; limits; rollback or cancel windows. NFRA treats fund transactions as high-risk.
4. **A red-team table.** Prompt injection (including injected text inside documents and invoices), induced transfers via fake tuition-invoice and impersonation scams, information extraction, privilege escalation, out-of-scope requests. For each: test, result, mitigation. Use NFRA's five agent-risk terms.
5. **Inclusion story with numbers.** International students as thin-file, cross-border customers, like WeBank's ~20% first-time borrowers. Show measurable value: fees and FX spread saved versus a bank wire, time to pay tuition, a credit-building path.
6. **Tie in WeBank's real cross-border infrastructure.** Verifiable admission letter, enrolment and bank-statement credentials, consistent with the Shenzhen–HK cross-border data verification scenarios.
7. **Privacy-by-design.** Data minimisation, consent receipts, no PII in model training, on-device or redacted processing of passports and statements. Optionally reference federated or privacy-preserving computation (FATE or FATE-LLM ideas) for credit features without centralising student data.
8. **APEC and multilingual.** Demo at least one non-English, non-Chinese user flow, e.g. Vietnamese or Indonesian to English or Chinese, in an APEC corridor (China/HK ↔ ASEAN). Show colloquial input, clarification questions and graceful fallback.
9. **Explainability and labelling.** Every recommendation shows rate source, fee breakdown and risk warning, labelled as AI-generated. No hallucinated FX rates: rates come from a tool call with a timestamp.
10. **A real-deployment angle for the bonus.** A live demo URL, a pilot or user test with real international students (even 10–20), or integration with real sandbox APIs (bank, FX or payment provider test environments). Put it in a "Deployment & Testing" section with known limitations stated honestly.

**Red flags to avoid**
1. **Crypto or stablecoins as the remittance rail for mainland users**, token issuance, yield, trading, "DeFi" or "Web3 wallet" language. This conflicts with Yin Fa [2026] No. 42, and the rules say PRC law governs.
2. **Tokenising tuition, loans or receivables (RWA)** or anything resembling an RMB stablecoin. Both are illegal onshore without approval.
3. **Helping users get around FX or capital controls**, e.g. splitting remittances to stay under quotas, or routing via informal channels. Judges will read this as AML or structuring.
4. **An agent that moves money autonomously** with no confirmation, limits or audit trail. Also "the LLM decides" credit or eligibility with no explanation.
5. **Vague compliance claims** ("we will comply with KYC/AML") with no concrete KYC flow, sanctions or AML screening step, consent handling or data-retention policy. The security self-assessment template asks for specifics.
6. **Careless PII handling.** Passports, I-20/CAS or admission letters, bank statements sent raw to third-party LLMs, used for training, or written on chain.
7. **Slideware.** A polished deck without reproducible execution evidence, or a demo where FX rates or fees are invented by the model.
8. **Unlicensed data or APIs**, or unclear open-source licences. The rules require legal authorisation.

**Safest way to earn the challenge bonus with an on-chain element**
- **[Inference]** Officially the bonus rewards "advanced topics *or* demonstrated real-world deployment." Pursue both, with a compliant chain component as the "advanced" part:
  1. **Run a small permissioned FISCO BCOS chain** (WeBank's own consortium-chain project, actively maintained in 2026) as a **tamper-evident audit and consent ledger.** Each confirmed agent action (quote shown, user confirmation, risk check passed, payment instruction sent to the sandbox) produces a hashed record anchored on chain. PII and amounts stay off-chain or salted. An auditor or regulator node can verify integrity.
  2. **Issue and verify student credentials as verifiable credentials** (WeIdentity-style DID or W3C VC): admission or enrolment proof from a mock university issuer, tuition invoice from a mock bursar. The agent refuses tuition payments to unverified payees. This doubles as anti-scam security, so it scores under Security & Compliance too.
  3. **Optional smart-contract guardrails**: payee allow-list and limit rules on chain. **No tokens and no value transfer on chain.**
  4. Put the block hashes, transaction hashes and a verification script in the Execution Evidence doc. In the deck, label the chain "permissioned evidence layer," and mention e-CNY/mBridge only as a future interoperability path.
- **[Estimate]** Given the 20 Oct deadline, this layer is realistic only if it is kept to hash-anchoring plus one VC flow. If time is too short, a clean audit-hash design with a working local chain, plus strong deployment evidence, is better than a rushed, fragile on-chain feature. Security failures carry "substantial deductions" that would outweigh a 0–5 bonus.

### Gaps
- No judges' scoring sheets or comments are public, so the checklist is inference from the rubric, past winners, and WeBank and regulator vocabulary.
- I could not confirm whether the "PBCSF Appendix 2" document defines the bonus as "on-chain exploration." If it does, the on-chain plan above becomes the primary bonus route rather than one of two.
