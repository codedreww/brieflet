# Research Digest

Keywords: AI, Security
Generated: 13 Oct 2026, 16:32

## Matching Arcticle: 
#### 1. Trust, but Validate the Instrument: Auditing AI-Generated RTL Verification Plans on Authored Security-Regression Proxies

**Score** : 14
**Source** : arxiv
**Published** : 12 Oct 2026

[Read the arcticle](https://arxiv.org/abs/2609.19844)

**Description** : arXiv:2609.19844v2 Announce Type: replace-cross 
Abstract: AI-generated RTL verification plans can satisfy a provider schema yet fail at the boundary to trusted execution. We present SecTB-RTL, an auditable framework covering 31 tasks and 124 authored hardware-security regressions. A deterministic non-AI baseline killed 36, 75, and 78 mutants at increasing resource limits. The first confirmatory run (C1-R2) failed before model execution because the provider rejected its response schema. After a schema-only repair made without viewing outcomes, a separately frozen follow-up run (C1-R3) completed 1,860 calls. The provider accepted 1,857 responses, but only nine passed the production semantic validator. The generation and execution rules did not match. We therefore preserve the run as an instrument-validation incident and report no prompt-effect estimate. This incident shows that provider or schema acceptance does not establish execution validity. Compilation and coverage are only diagnostics; the exact saved artifact must pass the full production path. A subsequent follow-up is excluded because it did not satisfy the preregistered evidence-completeness gate and is treated only as future work. We release the benchmark, failure-preserving contract, incident provenance, and governance controls needed to prevent infrastructure behavior from being misreported as model behavior.

**Matches** : security, ai in description; security, ai in title

#### 2. ArapaiSecure: An Autonomous AI Security Agent for Banking: Multi-Vector Fraud and AML Detection Across Retail and Corporate Accounts

**Score** : 14
**Source** : arxiv
**Published** : 08 Oct 2026

[Read the arcticle](https://arxiv.org/abs/2606.17555)

**Description** : arXiv:2606.17555v3 Announce Type: replace-cross 
Abstract: Banks face two threat families with fundamentally different detection requirements: signature-based fraud (card- not-present attacks, account takeover, ATM cloning) and behavioural financial crime (structuring, layering, mule networks, business email compromise). Static rule engines catch high-velocity events but remain blind to BEC payment redirection, session hijacking, and laundering layering, which are engineered to resemble legitimate activity at the individual level. This paper presents ArapaiSecure, an autonomous AI security agent for retail and corporate banking using a three-component fusion architecture across two parallel event streams: transactions (card fraud, ACH/wire fraud, AML) and sessions (account takeover, hijacking, SIM-swap, insider abuse). Each stream combines an LSTM sequence model of per-account behaviour, a statistical ve- locity/threshold monitor, and a graph module capturing account-counterparty patterns (fan-in, fan-out, pass-through ratio) for laundering detection. Experiments on a synthetic log of 237,669 transactions and 113,508 sessions across 13 threat categories and 3,470 accounts show that ArapaiSecure achieves an overall F1 of 0.787 (transaction) and 0.867 (session), versus 0.562/0.733 for a rule-based baseline and 0.655/0.713 for an LSTM-only baseline. ArapaiSecure also incorporates a customer-facing verification chatbot (96.6% identity accuracy, 86.8% mass-reset detection) and an analyst case-summary assistant (99.3% action recommendation F1), with Critical-tier response latency under 0.43 ms at the 95th percentile.

**Matches** : security, ai in description; security, ai in title

#### 3. Defensive Sufficiency in a Stackelberg Model of AI Security

**Score** : 12
**Source** : arxiv
**Published** : 08 Oct 2026

[Read the arcticle](https://arxiv.org/abs/2610.09892)

**Description** : arXiv:2610.09892v1 Announce Type: cross 
Abstract: Feedback from automated testing, human red teaming, and incident response can strengthen an AI system's defenses when discovered failures lead to effective repairs. We study when this feedback process provides sufficient protection and when investing in it is economically worthwhile. We begin by showing that an attack surface composed of finite number of inputs is defended with probability 1 if every unresolved attack has a persistent chance of discovery, repairs are effective, and subsequent updates preserve earlier protection. We derive completion-time bounds and extend the analysis to growing attack surfaces, repairs that generalize across related attacks, and multiple discovery mechanisms. These results distinguish eventual protection against each fixed attack from complete protection at a single time. We then formulate a defender-led Stackelberg game in which the defender invests in proactive discovery and reactive repair, anticipating the attacker's choice of search effort. We characterize the least-cost allocation that deters attack and the equilibrium regimes in which the defender funds neither capability, one capability, or both. Numerical experiments illustrate these regimes and show how faster repair can reduce compromise duration without reducing compromise probability.unified theory of performance limits in generative language models.

**Matches** : ai in description; security, ai in title

#### 4. A Local Agentic AI Framework to Generate Edge Case Scenarios for Safety Assurance

**Score** : 9
**Source** : arxiv
**Published** : 12 Oct 2026

[Read the arcticle](https://arxiv.org/abs/2610.13479)

**Description** : arXiv:2610.13479v1 Announce Type: new 
Abstract: Generating edge case scenarios is crucial for training, testing and safety assuring autonomous systems. This identifies hazardous failures to increase system reliability and robustness, ensures the system can still function safely on the boundaries of its operational design domain and learns the expected system behaviour for these edge cases. The rapid advancement in the generation and analysis capabilities of language models (LMs) has expanded their applicability and recent work has investigated LM scenario generation. However, many recent approaches rely on human-in-the-loop or rule-based strategies. This restricts the LM's ability to generate diverse and edge case scenarios; the long tail of the distribution. Our work uses local LMs in a laptop-based agentic AI framework for adaptive scenario generation. This is cheap, fully-controlled, ensures data privacy and security. It uses think, act, observe, update, and continue loops with lightweight JSON encoding to generate scenarios. We use the system requirements, system description and environment description as knowledge bases in contextual prompts for an LM to ensure scenario realism. A second, independent LM critiques each scenario using domain specific criteria so it can be refined. The refined scenarios are run in simulation and evaluation metrics collected. These metric scores are analysed and similar scenarios are created for edge cases (exploitation) or novel scenarios are generated to explore the scenario space. Post-hoc clustering using metric scores and thematic-type analysis of the rich-text scenario descriptions produced by the LM pinpoints functional gaps and their triggering conditions. This creates traceable evidence for the safety assurance case. Our work highlights the potential of a flexible and adaptive local agentic AI framework for automating edge case generation and producing traceable safety assurance evidence.

**Matches** : security, ai in description; ai in title

#### 5. AI-Mediation in Retail Markets: Revenue Effects and Assortment Optimization

**Score** : 7
**Source** : arxiv
**Published** : 12 Oct 2026

[Read the arcticle](https://arxiv.org/abs/2610.12917)

**Description** : arXiv:2610.12917v1 Announce Type: new 
Abstract: AI shopping assistants increasingly influence which products consumers consider. We study retail assortment planning under AI mediation, where a retailer chooses a catalog, an AI intermediary forms a customer-facing shortlist, and the customer chooses from that shortlist according to a multinomial logit model. We consider both deterministic mediation, in which the AI follows a fixed segment-specific ranking, and stochastic mediation based on the Plackett-Luce model.
  Empirically, we construct a dataset of product rankings from leading AI models, estimate Plackett-Luce ranking models, and evaluate their predictive performance on held-out assortments. Combining these estimates with synthetic customer preferences, we find that accounting for AI mediation can materially change optimal assortments and revenue. Across the tested capacity configurations, ignoring mediation yields mean revenue losses between 2.52% and 11.37% relative to the PL optimum. A much simpler deterministic plug-in, based only on the ordering of fitted AI utilities, performs substantially better, with mean losses of at most 0.53%.
  Motivated by this performance, we study assortment optimization under deterministic mediation. We characterize its computational complexity and show that, for any fixed number of customer segments, the problem admits a fully polynomial-time approximation scheme.

**Matches** : ai in description; ai in title

