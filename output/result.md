# Research Digest

Keywords: AI, Database, Security
Generated: 28 Sep 2026, 13:32

## Matching Arcticle: 
#### 1. Resource-Optimized and Energy-Aware Agentic AI Framework Anchored on Blockchain for Secure Software Supply Chains

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.31282)

**Description** : arXiv:2609.31282v1 Announce Type: cross 
Abstract: This paper proposes a blockchain-backed agentic security framework designed to safeguard the complete software development lifecycle (SDLC) while also securing the agentic AI components responsible for monitoring it. The framework coordinates a set of specialised security agents, covering source integrity, dependency and SBOM analysis, CI configura tion auditing, artifact verification, and runtime policy evaluation, each supported by a large language model (LLM) that interprets artefacts, reasons over tool outputs, and produces structured security reports. To ensure agent trustworthiness, every agent generates a cryptographically signed attestation that is recorded in a permissioned blockchain via smart contracts, including an agent registry, an immutable attestation log, and an enforceable release-policy module. Communication among agents and with blockchain nodes is secured using a consortium-operated certificate authority, ensuring authenticated and tamper-resistant interactions. A detailed use-case and sequence flow demonstrate how a source code security agent performs analysis, anchors its attestation on-chain, and triggers a verifiable allow/block deployment decision. The proposed framework of fers decentralised integrity transparent provenance, uninterrupted security assurance and a generalisable architecture to incorporate the agentic AI into the modern software supply chain security.

**Matches** : 'security' in description; 'ai' in title; 'ai' in description

#### 2. AgentXploit: Autonomous Repository-to-Runtime Red-Teaming for AI Agents

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.31318)

**Description** : arXiv:2609.31318v1 Announce Type: cross 
Abstract: AI agents combine language models with external data and tools that can modify files, call APIs, or execute code. Security failures can arise when adversarial content changes an agent's tool use or when the surrounding software contains vulnerabilities such as path traversal or command injection. We study authorized white-box pre-deployment auditing, where the auditor has access to the target repository and a controlled runtime, but successful attacks must still act through the task-defined attacker interface and be confirmed by an external verifier. We present AgentXploit, a two-role auditing system that separates repository-level attack-path discovery from runtime exploitation. The Analyzer Agent traces attacker-controlled inputs to sensitive operations and records code-supported candidate attack paths; the Exploiter Agent turns these paths into concrete attacks and revises them using runtime feedback. We also introduce AgentXploit-Bench, containing 72 reproducible vulnerabilities across 12 open-source AI-agent systems and frameworks. Across three runs, AgentXploit reaches 59.3% end-to-end success, compared with 38.4% for Codex. Under a token-budget-matched comparison, Codex reaches 46.3%. On AgentDojo, where injection points are provided, the Exploiter Agent reaches 79.2% attack success versus 52.7% for AgentVigil. These results highlight repository discovery and runtime exploitation as distinct challenges in end-to-end agent security auditing.

**Matches** : 'security' in description; 'ai' in title; 'ai' in description

#### 3. An AI Agent Execution Environment to Safeguard User Data

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2604.19657)

**Description** : arXiv:2604.19657v3 Announce Type: replace-cross 
Abstract: AI agents promise to serve as general-purpose personal assistants for their users, which requires them to have access to private user data (e.g., personal and financial information). This poses a serious risk to security and privacy: an AI model may hallucinate or make mistakes, and adversaries may attack it (e.g., via prompt injection) to exfiltrate user data. This paper presents GAAP (Guaranteed Accounting for Agent Privacy), an execution environment for AI agents that guarantees confidentiality for private user data. Crucially, GAAP provides this guarantee deterministically, without trusting the agent with private user data, and without requiring any AI model or the user prompt to be free of attacks. Through dynamic and directed user prompts, GAAP collects permission specifications from users describing how their private data may be shared. GAAP then enforces that the agent's data disclosures comply with these specifications by tracking how the AI agent accesses and uses private user data. GAAP augments Information Flow Control with novel persistent data stores and annotations that enable tracking the private information flow both across steps of a single task and over multiple separate tasks. Our evaluation confirms that GAAP blocks all data disclosure attacks, including those that make other state-of-the-art systems disclose private user data to untrusted parties, with only a small impact on agent utility.

**Matches** : 'security' in description; 'ai' in title; 'ai' in description

#### 4. TiAb Review Plugin: A Browser-Based Tool for AI-Assisted Study Selection in Systematic Reviews

**Score** : 9
**Source** : arxiv
**Published** : 24 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2604.08602)

**Description** : arXiv:2604.08602v2 Announce Type: replace-cross 
Abstract: Server-based screening tools impose subscription costs, while open-source alternatives require coding skills, and full-text screening has remained outside the scope of no-code open-source tools. We developed TiAb Review Plugin, an open-source Chrome browser extension that provides no-code, serverless artificial intelligence (AI)-assisted study selection covering both title and abstract (T&amp;A) screening and full-text screening. It uses Google Sheets as a shared database and Google Drive as a PDF store, and users supply their own large language model (LLM) API key. For T&amp;A screening, it offers manual review, LLM batch screening, and machine learning (ML) active learning. For full-text screening, it retrieves open-access PDFs from PubMed Central, Europe PMC, Unpaywall, OpenAlex, and publisher pages, supports blinded dual review with structured exclusion reasons and adjudication, optionally obtains an LLM judgment with page-anchored evidence, and computes PRISMA 2020 flow counts. We re-implemented the default ASReview algorithm (TF-IDF with Naive Bayes) in TypeScript and compared it with the Python original using 10-fold cross-validation on six datasets. For LLM T&amp;A screening, we compared 16 parameter configurations on a benchmark dataset, validated the best (Gemini 3.0 Flash, low thinking budget, TopP 0.95) on five public datasets (1,038 to 5,628 records; 0.5% to 2.0% prevalence), and benchmarked nine further models from four developers. The TypeScript classifier produced top-100 rankings identical to ASReview on all six datasets. LLM T&amp;A screening achieved recall of 94% to 100% with precision of 2% to 15%, and work saved over sampling at 95% recall (WSS@95) of 46.3% to 89.3%. No additional model exceeded the 96.1% recall of the reference configuration; the most recent models traded recall for precision. The classification accuracy of the full-text stage has not yet been evaluated.

**Matches** : 'ai' in title; 'ai' in description; 'database' in description

#### 5. Bringing AI to Autonomous Systems -- From Cognition to Collective Intelligence

**Score** : 7
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.30291)

**Description** : arXiv:2609.30291v1 Announce Type: new 
Abstract: The purpose of this article is to highlight the central role of autonomous systems as the ultimate stage in the development of AI, to explain the underlying technical challenges that require a combination of connectionist AI and symbolic AI, and to integrate AI and systems engineering. We present a comprehensive framework for the design and evaluation of autonomous systems, based on a generic agent architecture that characterizes their behavior as the composition of cognitive functions organized around a long-term memory containing the agent's evolving knowledge. We address the challenges posed by the implementation of the fundamental features of the agent architecture, in particular the link between sensory data and structured data stored in memory, decision-making related to the achievement of the agent's goals and their planning, as well as the coordination of agents to combine individual and collective intelligence. We explain that agent trustworthiness, unlike that of traditional systems, is not limited to behavioral properties. It includes an essential dimension related to cognitive properties, the validity of which depends on how the agent uses its knowledge in decision-making. We present avenues for the development of methods for evaluating agent trustworthiness. We conclude with a critical assessment of the substantial gap between the aspirational vision of autonomous multi-agent systems and the current state of the art.

**Matches** : 'ai' in title; 'ai' in description

