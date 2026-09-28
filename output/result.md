# Research Digest

Keywords: AI, Security, Database, Concerns
Generated: 28 Sep 2026, 13:39

## Matching Arcticle: 
#### 1. Evolutionary Safety of Recursive Self-Improving AI: Taxonomy, Risk Discovery, and Evaluation

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.31186)

**Description** : arXiv:2609.31186v1 Announce Type: new 
Abstract: Artificial intelligence is advancing rapidly, with increasingly capable systems taking larger roles in reasoning, decision-making, scientific discovery, and autonomous development. As AI begins to participate in its own improvement, from model training and experience accumulation to agent evolution and automated AI development, the prospect of recursive self-improvement (RSI) is becoming increasingly relevant. This transition raises a fundamental safety question: how can safety be maintained when the system, its accumulated experience, and even the process producing its successors continue to change?
  We introduce Evolutionary Safety as a perspective for studying safety under persistent and recursive self-improvement. It concerns not only whether an AI system is safe at a particular moment, but how safety properties change, persist, accumulate, and propagate throughout evolution. We characterize recurring manifestations, including intent drift, error accumulation, experience contamination, safety-property erosion, evaluator drift, and risk propagation. We then develop a taxonomy spanning persistent agent state, model state, evaluation and environmental feedback, computational substrate, and meta-level update mechanisms. Building on this taxonomy, we examine how evolutionary risks can be discovered and evaluated across states, updates, trajectories, and lineages, and derive governance principles for modification, selection, authorization, provenance, and recovery. Finally, we outline open problems toward maintaining safety guarantees as AI systems become increasingly persistent, adaptive, and recursively self-improving. Project resources and proposed evaluation systems are available at https://chaunceykung.github.io/evolutionary-safety-rsi.

**Matches** : ai, concerns in description; ai in title

#### 2. A Framework for Identifying, Categorizing, and Explaining Bias in AI-Generated Code

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.30642)

**Description** : arXiv:2609.30642v1 Announce Type: cross 
Abstract: As Large Language Models (LLMs) become integrated into software development workflows, concerns regarding unintentional biases in AI-generated code. Although evidence suggests these biases exist, limited research has systematically identified, categorized, and explained them. This study investigates bias in AI-generated code and evaluates whether LLMs can reliably identify and explain it through a taxonomy-driven framework. We extended an existing dataset of biased AI-generated Python code and manually annotated snippets with bias categories and human-authored justifications to establish a ground-truth dataset. Using this dataset, we evaluated proprietary and open-source LLMs as automated bias detection and justification systems through ICL. Finally, we analyzed similarity between LLM-generated explanations and human-authored justifications using structured justification and code identification metrics.
  Our findings demonstrate that LLMs can effectively support code bias identification and explanation. Gemini achieved 80.14% classification accuracy, with 84.0% precision and 95.7% recall, while the best open-source alternative, Qwen3-coder, achieved 82.45% accuracy, 68.64% precision, and 80.22% recall. Additionally, the models achieved justification similarity scores of 80.4% and 80.14%, respectively, relative to human-authored reasoning, and code identification similarity scores of 86.0% and 87.82%. These results suggest that LLMs can detect biased logic in generated Python code and produce explanations that substantially align with expert interpretations.

**Matches** : ai, concerns in description; ai in title

#### 3. Resource-Optimized and Energy-Aware Agentic AI Framework Anchored on Blockchain for Secure Software Supply Chains

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.31282)

**Description** : arXiv:2609.31282v1 Announce Type: cross 
Abstract: This paper proposes a blockchain-backed agentic security framework designed to safeguard the complete software development lifecycle (SDLC) while also securing the agentic AI components responsible for monitoring it. The framework coordinates a set of specialised security agents, covering source integrity, dependency and SBOM analysis, CI configura tion auditing, artifact verification, and runtime policy evaluation, each supported by a large language model (LLM) that interprets artefacts, reasons over tool outputs, and produces structured security reports. To ensure agent trustworthiness, every agent generates a cryptographically signed attestation that is recorded in a permissioned blockchain via smart contracts, including an agent registry, an immutable attestation log, and an enforceable release-policy module. Communication among agents and with blockchain nodes is secured using a consortium-operated certificate authority, ensuring authenticated and tamper-resistant interactions. A detailed use-case and sequence flow demonstrate how a source code security agent performs analysis, anchors its attestation on-chain, and triggers a verifiable allow/block deployment decision. The proposed framework of fers decentralised integrity transparent provenance, uninterrupted security assurance and a generalisable architecture to incorporate the agentic AI into the modern software supply chain security.

**Matches** : security, ai in description; ai in title

#### 4. AgentXploit: Autonomous Repository-to-Runtime Red-Teaming for AI Agents

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2609.31318)

**Description** : arXiv:2609.31318v1 Announce Type: cross 
Abstract: AI agents combine language models with external data and tools that can modify files, call APIs, or execute code. Security failures can arise when adversarial content changes an agent's tool use or when the surrounding software contains vulnerabilities such as path traversal or command injection. We study authorized white-box pre-deployment auditing, where the auditor has access to the target repository and a controlled runtime, but successful attacks must still act through the task-defined attacker interface and be confirmed by an external verifier. We present AgentXploit, a two-role auditing system that separates repository-level attack-path discovery from runtime exploitation. The Analyzer Agent traces attacker-controlled inputs to sensitive operations and records code-supported candidate attack paths; the Exploiter Agent turns these paths into concrete attacks and revises them using runtime feedback. We also introduce AgentXploit-Bench, containing 72 reproducible vulnerabilities across 12 open-source AI-agent systems and frameworks. Across three runs, AgentXploit reaches 59.3% end-to-end success, compared with 38.4% for Codex. Under a token-budget-matched comparison, Codex reaches 46.3%. On AgentDojo, where injection points are provided, the Exploiter Agent reaches 79.2% attack success versus 52.7% for AgentVigil. These results highlight repository discovery and runtime exploitation as distinct challenges in end-to-end agent security auditing.

**Matches** : security, ai in description; ai in title

#### 5. An AI Agent Execution Environment to Safeguard User Data

**Score** : 9
**Source** : arxiv
**Published** : 28 Sep 2026

[Read the arcticle](https://arxiv.org/abs/2604.19657)

**Description** : arXiv:2604.19657v3 Announce Type: replace-cross 
Abstract: AI agents promise to serve as general-purpose personal assistants for their users, which requires them to have access to private user data (e.g., personal and financial information). This poses a serious risk to security and privacy: an AI model may hallucinate or make mistakes, and adversaries may attack it (e.g., via prompt injection) to exfiltrate user data. This paper presents GAAP (Guaranteed Accounting for Agent Privacy), an execution environment for AI agents that guarantees confidentiality for private user data. Crucially, GAAP provides this guarantee deterministically, without trusting the agent with private user data, and without requiring any AI model or the user prompt to be free of attacks. Through dynamic and directed user prompts, GAAP collects permission specifications from users describing how their private data may be shared. GAAP then enforces that the agent's data disclosures comply with these specifications by tracking how the AI agent accesses and uses private user data. GAAP augments Information Flow Control with novel persistent data stores and annotations that enable tracking the private information flow both across steps of a single task and over multiple separate tasks. Our evaluation confirms that GAAP blocks all data disclosure attacks, including those that make other state-of-the-art systems disclose private user data to untrusted parties, with only a small impact on agent utility.

**Matches** : security, ai in description; ai in title

