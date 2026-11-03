# ADR-0001: Brieflet v2 architecture — personal AI briefing (Streamlit + Discord)

**Status:** Proposed
**Date:** 2026-11-01
**Deciders:** Andrew Tan

## Context

### Goal
Brieflet should give me a **daily briefing of news and papers on things I care about**:

- **Pushed to Discord** every morning (WhatsApp later, maybe).
- **Viewable and editable in a deployed Streamlit app**: today's digest, past digests, and my preferences.
- **Preferences in natural language.** I write "I'm into LLM agents, AI security, F1, and anything about Singapore tech, but no crypto". An AI turns that into a profile and suggests what I should be following.
- **Bring your own model or agent.** I plug in my own LLM key, a local model, or my own agent instead of a hard-wired provider.

### Where v1.0p is today
| Area | v1.0p | Gap |
|---|---|---|
| Sources | One hardcoded feed (`rss.arxiv.org/rss/cs.ai`) | No news, and no per-user sources |
| Preferences | Comma-separated keywords typed on each visit | Not saved, no NL, no suggestions |
| Matching | Whole-word regex (+5 title, +2 description) | Misses synonyms, plurals, and anything semantic |
| Output | Top 5 computed live on every Streamlit rerun | No stored digest, no history, no summaries |
| Scheduling | macOS `launchd` on my laptop | Doesn't run when the Mac is asleep or off. One network error kills the run (see `collect.stderr.log`) |
| Storage | SQLite file committed to git | Doesn't work on a cloud host, and it pollutes the repo |
| Delivery | None | No Discord |
| Code shape | One `script.py` (fetch + store + score + format) | Hard to add sources or providers |

### Constraints and assumptions
- **Single user (me)** for now. The design shouldn't block a few more users later.
- **Near-zero budget.** Free tiers plus a few cents a day of LLM usage.
- **Python only.** It's my stack, and Streamlit is already in.
- **Daily cadence.** Real time isn't needed. A batch at about 07:30 is fine.
- **Volume:** roughly 500–3,000 candidate items/day across sources, and about 10–15 items worth showing.

---

## Decision 1 (the main one): how searching works

### Option A — Pull and filter (extend v1)
Collect from a fixed list of feeds/APIs, then rank locally against my interests: keywords, upgraded to embeddings.

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | ~Free (local embeddings) |
| Coverage | Limited to the feeds I've configured. Can't find things outside them |
| Reliability | High. Deterministic and easy to debug |
| Quality | Good recall, but weak at "is this actually interesting?" |

**Pros:** cheap, predictable, works offline, and the current code already does half of it.
**Cons:** I have to curate sources by hand, which defeats "just type my preferences". There's no reasoning about novelty or importance.

### Option B — Agentic search
Each day an LLM agent takes my profile, calls web-search tools (Tavily/Exa/Brave/etc.), reads pages, and writes the briefing.

| Dimension | Assessment |
|---|---|
| Complexity | Medium to build, high to make reliable |
| Cost | High and unpredictable (many tool calls, long contexts, paid search APIs) |
| Coverage | Excellent. Can find anything |
| Reliability | Low. Non-deterministic, can repeat yesterday's items, can hallucinate summaries or links, and is hard to test |
| Quality | Very good on good days |

**Pros:** maximum flexibility, and it matches the "AI figures it out" vision.
**Cons:** cost grows with topics × days. It doesn't remember what I already saw, and it's hard to debug "why did I get this?". The whole digest depends on the LLM being up.

### Option C — Hybrid: an AI-planned query plan, deterministic collection, AI ranking (**recommended**)
The LLM is used where it adds the most value: **understanding me** (once, when preferences change) and **judging a short list** (once a day). Everything in between is cheap and deterministic.

```
            (on preference change)                         (daily batch)
NL prefs ──► Profile Compiler (LLM) ──► Interest Profile ──► Source Plan
                                         (topics, weights,     │
                                          exclusions, queries,  ▼
                                          arXiv cats, feeds)   Collectors (deterministic)
                                                                arXiv · RSS · HN · Reddit · news/search API
                                                                │
                                                                ▼
                                                        Normalize + dedupe ──► items store
                                                                │
                                         Stage 1: recall  ──────┤  embeddings vs each interest  (~2000 → 60)
                                         Stage 2: filter  ──────┤  recency, exclusions, already-sent
                                         Stage 3: rerank  ──────┤  LLM scores + "why" + 2-line summary (60 → ~12)
                                         Stage 4: diversify ────┘  cap per topic/source (MMR)
                                                                │
                                                                ▼
                                                         Digest (stored) ──► Discord · Streamlit · MCP
                                                                ▲
                                                 👍/👎 feedback ─┘ (adjusts interest weights and examples)
```

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | Low and bounded: 1 rerank call/day over about 60 short items (≈15–25k tokens). Cents per day on a small model, $0 on a local model |
| Coverage | Broad. The compiler proposes feeds/queries, and a search API slot can cover the long tail |
| Reliability | High. If the LLM fails, fall back to embedding score alone and still send a digest |
| Quality | High. Semantic recall plus LLM judgement, and it improves with feedback |

**Pros:** the AI suggests sources and queries but stays out of the hot loop. Cost is predictable, every item has a traceable score and reason, it's testable, and it degrades gracefully. It reuses the v1 collection and SQLite work.
**Cons:** more moving parts than A. I need an embedding model and vector search. It's less able than B to "go read 10 pages and synthesize".

### Trade-off analysis
The real question is **where the LLM sits**. In B it's in the hot path for everything. That's expensive and hard to trust, and it repeats work daily that only needs doing when preferences change. In A it's absent, so the system can't understand natural-language preferences. C puts it at the two points where judgement matters (translating me → a plan, and choosing the final 12) and uses cheap vector math for the 2,000 → 60 funnel.

C also leaves room for B later. An optional **"deep dive" agent** step can run on demand (from a Discord command or a Streamlit button) for one topic, without the daily digest depending on it.

**Decision: Option C.**

### How each stage works
1. **Profile Compiler (LLM, structured output).** Input: my free-text preferences plus current feedback stats. Output: a validated Pydantic `InterestProfile`:
   ```json
   {
     "interests": [
       {"name": "LLM agents", "description": "tool use, planning, multi-agent systems, agent evals",
        "weight": 1.0, "kind": ["paper", "news"],
        "arxiv_categories": ["cs.AI", "cs.CL", "cs.MA"],
        "queries": ["LLM agent", "tool-use benchmark"],
        "feeds": ["https://hnrss.org/newest?q=agents"]}
     ],
     "exclude": ["crypto", "NFT"],
     "suggestions": ["You might also like: AI red-teaming (overlaps with AI security + agents)"]
   }
   ```
   It shows a **diff and suggestions** in Streamlit. I accept or edit, then it saves as a new profile version. It never silently changes what I get.
2. **Collectors.** One small class per source type behind a common interface (`fetch(plan) -> list[RawItem]`). Each has retries with backoff, and one failing never kills the run. Start with arXiv (API by category, not one RSS feed: the RSS feed only lists the day's announcements and is empty on weekends), generic RSS/Atom, and Hacker News (Algolia API). For sites without a feed, point the RSS collector at an **RSSHub** route (self-hosted or public), which turns many sites into RSS for free. Add Reddit and a news/search API (GNews, NewsAPI, Tavily or Exa) as an optional "long tail" collector that runs the profile's `queries`.
3. **Normalize + dedupe.** Canonical URL (strip tracking params, map arXiv versions `v1/v2` → one id), plus title-embedding near-duplicates (cosine > 0.92). Also strip arXiv's `arXiv:… Announce Type:` prefix.
4. **Recall (embeddings).** Embed each item's `title + abstract/lede` once, at ingest. Embed each interest's `name + description` (plus 👍'd item examples). Score = max over interests of `weight × cosine`. Keep the top ~60. Local model by default (`bge-small-en`/`all-MiniLM` via sentence-transformers, free), or provider embeddings if configured.
5. **Filter.** Recency window (papers ≤ 3 days, news ≤ 1 day), exclusions (embedding + keyword), and never re-send an item already in a past digest.
6. **Rerank + summarize (LLM, one batched call).** Pass the profile plus ~60 items (title + first ~400 chars). It returns `{item_id, score 0–10, interest, why, summary}` as structured JSON. **Only summarize from the text provided** (no browsing), so it can't hallucinate content. Links come from the database, never from the model. Store and **show the numeric score next to the "why"** in Discord and Streamlit, so I can see how confident each pick is and tune thresholds.
7. **Diversify.** Max ~3 per interest and ~4 per source. Papers and news are balanced to my ratio setting.
8. **Feedback.** Discord reactions or Streamlit buttons write `feedback(item_id, +1/-1)`. Learning happens in two tiers:
   - **Tier 1, cold start (from the first vote).** 👍 items become positive examples in that interest's embedding. Repeated 👎 on one interest lowers its weight, and the compiler can propose "drop or narrow this topic?".
   - **Tier 2, a learned preference model (after ≥30 votes, with ≥10 of each kind).** Train a **logistic regression on the embeddings of items I've voted on** (scikit-learn, under a second). Its output `p(like)` becomes a second recall signal, blended as `recall = α · similarity + (1 − α) · p(like)`. Start with α ≈ 0.7 and lower it as votes accumulate. Retrain at the start of each daily run, and keep a held-out 20% of votes to check the model actually beats similarity alone before trusting it. This catches tastes that interest descriptions miss ("I like benchmark papers but not survey papers"). The idea comes from arxiv-sanity-lite (see Prior art).

---

## Decision 2: bring your own model or agent

Two separate things are being asked for here, so the design does both.

### 2a. Bring your own **model** (Brieflet calls the LLM)
- All LLM calls go through **one `LLMProvider` interface** with two methods: `complete_structured(prompt, schema)` and `embed(texts)`.
- Implement it with **LiteLLM**, which gives one API over Anthropic, OpenAI, Gemini, OpenRouter, and **local Ollama**. The model is just config: `BRIEFLET_LLM=anthropic/claude-haiku-...`, `ollama/llama3.1`, etc.
- Keys come from env vars or a secrets store, never the database or git.
- **Caveat:** consumer chat subscriptions (ChatGPT Plus, Claude Pro) generally **don't give API keys**. "Bring your own subscription" in practice means an API key, OpenRouter credits, or a local model. If I want to use the chat subscription itself, that's what 2b is for.
- **No-LLM mode:** if no provider is configured, Brieflet uses embeddings + keywords only, so it still works.

### 2b. Bring your own **agent** (my agent calls Brieflet)
- Expose Brieflet as an **MCP server** (`brieflet-mcp`) with tools such as:
  - `get_digest(date)`
  - `search_items(query, days)`
  - `get_profile()`
  - `propose_profile_update(text)`
  - `give_feedback(item_id, vote)`
- Then Claude Desktop, Claude Code, or any MCP-capable agent can read my briefing, dig deeper, and edit preferences. It runs on that agent's own subscription, so Brieflet pays nothing for the reasoning.
- MCP is the clean answer to "install my own agent": Brieflet supplies the data and tools, and the agent supplies the intelligence.

---

## Decision 3: deployment and runtime

The current launchd-on-laptop setup is the main reliability problem. There are three runtime pieces with different needs:

| Piece | Needs | Recommendation |
|---|---|---|
| **Daily pipeline** (collect → rank → digest → send) | Runs once a day, ~1–3 min | **GitHub Actions cron** (free, logs, retries) to start. Move it into the worker host if one exists |
| **Streamlit app** | Always reachable, light | **Streamlit Community Cloud** (free) |
| **Discord** | Push only → nothing. Interactive (slash commands, reactions) → an always-on process | **Phase 1: Discord webhook** (no bot, no host, one HTTP POST). **Phase 3: discord.py bot** on a small always-on host (Fly.io / Railway / a cheap VPS / a Raspberry Pi) |
| **Database** | Shared by all of the above | **Hosted Postgres with pgvector** (Supabase or Neon free tier). Streamlit Cloud and GH Actions have ephemeral disks, so a local SQLite file won't survive there |

For local dev, run the same code against SQLite (+ `sqlite-vec`) through one repository layer, so switching databases is a config change.

**Alternative considered:** one small VPS running everything (Postgres, cron, Streamlit, bot) in Docker Compose. It's simpler to reason about and has no free-tier limits, but costs ~$5/month and I'd maintain the server myself. It's a fine choice if I'd rather own the box. The code layout below supports both.

---

## Target structure

```
brieflet/
  core/
    models.py         # Pydantic: RawItem, Item, InterestProfile, Digest, Feedback
    db.py             # repository layer (SQLite locally, Postgres in prod)
    llm.py            # LLMProvider (LiteLLM) + no-LLM fallback
    embed.py          # embedding + vector search helpers
    profile.py        # NL prefs -> InterestProfile (compiler + suggestions)
    sources/          # base.py, arxiv.py, rss.py, hackernews.py, search_api.py
    pipeline.py       # collect -> dedupe -> recall -> filter -> rerank -> diversify -> digest
    delivery/         # discord_webhook.py, discord_bot.py, (whatsapp.py later)
  apps/
    web/app.py        # Streamlit: Today, History, Preferences (chat + diff), Sources, Settings
    bot/main.py       # discord.py bot (phase 3)
    mcp/server.py     # MCP server (phase 4)
  cli.py              # `brieflet run-daily`, `brieflet collect`, `brieflet profile "..."`
tests/
.github/workflows/daily.yml
pyproject.toml        # deps pinned; replaces "install streamlit, httpx, feedparser"
.gitignore            # data/, output/, *.db, __pycache__, .env
```

### Data model (minimal)
- `items(id, canonical_url UNIQUE, title, body, source, kind[paper|news], published_at, fetched_at, embedding vector)`
- `profiles(id, version, raw_text, profile_json, created_at, active)`
- `digests(id, date, profile_version, created_at, delivered_at)`
- `digest_items(digest_id, item_id, rank, interest, score, why, summary)`
- `feedback(item_id, vote, source[discord|web|mcp], created_at)`
- `runs(id, started_at, status, stats_json, error)` for "why didn't I get a digest today?"

Retention: keep `items` for 30 days, and keep `digests`/`digest_items`/`feedback` forever (they're small, and that's what makes history and learning work).

---

## Prior art

Similar open-source projects confirm the core choices: embedding recall, cheap LLM scoring, a no-LLM fallback, and scheduled batch runs. They also contribute a few ideas worth borrowing. These were found by search on 2026-11-01. I haven't audited their code, maintenance or licenses, so check those before reusing anything.

| Project | What it does | What Brieflet borrows / where to read it |
|---|---|---|
| [ilonae/research-agent](https://github.com/ilonae/research-agent) (ArXiv-Paper-Digest) | arXiv feeds → skip seen papers → sentence-transformers relevance → Ollama summaries, daily on GitHub Actions | Validates the stack for stages 2–6. **Read before Phase 2 recall** |
| [Pappet/ai_digest](https://github.com/Pappet/ai_digest) | Cheap LLM scores news 0–10, keyword fallback when the LLM is down, Ollama/OpenRouter | Same shape as our rerank stage and no-LLM mode. **Read its scoring prompt before Phase 2 rerank** |
| [AutoLLM/ArxivDigest](https://www.github.com/AutoLLM/ArxivDigest) | Ranks arXiv papers against natural-language interest descriptions, emails a digest | Prior art for describing interests in plain text. OpenAI-only, and its license is unclear |
| arxiv-sanity-lite (Karpathy) | Users tag papers, and a per-tag classifier recommends new ones | **Tier 2 feedback model** (stage 8) |
| [Newscope](https://github.com/joinserve/newscope), [NewsBlur](https://www.stork.ai/en/newsblur) | Feed readers that score items against interests and learn from feedback | Showing the score and "why" (stage 6). Feedback UX ideas for Phase 3 |
| [rundown](https://railway.com/deploy/rundown-1.md), [Discorss](https://tomevault.io/tome/mergd/discorss) | Feed → LLM summary → Discord | Reference for Discord message formatting in Phase 1 |
| RSSHub | Generates RSS feeds for sites that don't publish one | Extends the generic RSS collector (stage 2) |
| [RSSbrew](https://github.com/yinan-c/RSSbrew) | Rule filters (AND/OR/NOT/regex) plus AI digests | Possible syntax for hard exclusions if embedding-based exclusion proves too fuzzy |

**Where Brieflet differs:**
- An AI-made source plan with suggestions, compiled from typed preferences.
- Papers *and* news in one digest.
- An MCP server for bringing your own agent.

None of the projects found combine all three.

**Why build rather than fork:** this is a learning project. Read each reference *after* attempting the matching stage, and compare. Don't copy beforehand.

---

## Consequences

**Easier**
- Adding a source means one collector class. Adding a model means a config change.
- Every recommendation can be explained (embedding score + LLM "why" + profile version).
- Digests are computed once, so Streamlit, Discord, and MCP all show the same thing, and Streamlit loads instantly.
- The daily run survives the laptop being closed and one source failing.

**Harder**
- More infrastructure: a hosted DB, secrets in GH Actions and Streamlit Cloud, and eventually a bot host.
- Embedding models add a dependency (sentence-transformers pulls in torch, so the CI run gets heavier). The provider embeddings option avoids that.
- Prompt and schema drift: the compiler and reranker outputs need validation and tests.
- The Tier 2 preference model adds scikit-learn and a train/evaluate step to every run. With few votes it can overfit, which is why it's gated on vote counts and a held-out check.

**To revisit**
- When it moves to multiple users: auth on Streamlit, `user_id` on profiles/digests/feedback, and per-user schedules.
- Whether to add the on-demand "deep dive" agent (Option B, scoped to one topic).
- WhatsApp (Business API onboarding is heavier than Discord's, so defer it).
- The blend weight α and the Tier 2 vote thresholds, once there's real feedback data.

---

## Action items (phased)

**Phase 0 — Clean the foundation (≈1 evening)**
1. [x] Add `.gitignore`. Untrack `data/storage.db`, `output/*.log`, `__pycache__`, `.DS_Store`, and `cs.AI.txt`.
2. [x] Add `pyproject.toml` with pinned deps. Rename "Pscript" → "Brieflet" in the UI.
3. [x] Split `script.py` into `core/` modules (models, db, sources/arxiv, pipeline) without changing behaviour. Keep the tests green.
4. [x] Add retries/backoff to fetching, and a `runs` table for status.

**Phase 1 — A stored digest delivered to Discord (MVP)**
5. [ ] `digests` + `digest_items` tables. `brieflet run-daily` builds and stores the digest.
6. [ ] Discord webhook delivery (embed per item: title, why, link).
7. [ ] GitHub Actions cron for `run-daily`. Retire launchd.
8. [ ] Streamlit "Today" and "History" pages read stored digests instead of scoring live.

**Phase 2 — Natural-language preferences and semantic ranking**
9. [ ] `LLMProvider` via LiteLLM + no-LLM fallback.
10. [ ] Profile compiler → `InterestProfile`, with a suggestions and diff UI in Streamlit.
11. [ ] Embeddings at ingest plus recall stage. Move to Postgres+pgvector (Supabase/Neon) and deploy Streamlit Cloud.
12. [ ] LLM rerank + summary stage. Diversity caps.
13. [ ] More collectors: arXiv API (replacing RSS), generic RSS (+ RSSHub routes), Hacker News, then an optional search/news API.

**Phase 3 — Feedback and an interactive bot**
14. [ ] discord.py bot on an always-on host: 👍/👎 reactions, `/prefs <text>`, `/more <topic>`.
15. [ ] Tier 1 feedback: interest weights and examples. The compiler proposes topic changes.
16. [ ] Tier 2 feedback: logistic regression on voted item embeddings, blended into recall. Held-out check against similarity alone.

**Phase 4 — Bring your own agent**
17. [ ] MCP server over the same `core/` (digest, search, profile, feedback tools).
18. [ ] Optional on-demand deep-dive agent for a single topic.
