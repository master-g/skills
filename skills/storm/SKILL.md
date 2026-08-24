---
name: storm
license: MIT
description: >-
  Generate a comprehensive, citation-grounded, Wikipedia-style article on any topic
  from scratch using Stanford's STORM method: discover multiple perspectives, run
  simulated expert conversations to research each one, build an outline from what was
  collected, then write the article section-by-section with inline citations. Use this
  whenever the user wants a deep, structured, long-form write-up of a topic — "写一篇关于X的
  文章/百科条目", "系统梳理一下X", "给我一份关于X的综述/研究报告", "从零帮我写一篇维基式长文", "整理X的来龙去脉",
  "write a comprehensive article on X", "deep dive / explainer on X". Especially strong
  when the topic benefits from several angles (technical / historical / economic / social /
  controversy) and a clean hierarchical structure. Prefer STORM over a quick web summary
  whenever the user wants breadth + structure + sources rather than a one-paragraph answer.
  Not for: fact-checking a single claim, simple lookups, or rewriting existing prose.
---

# STORM — Wikipedia-style article generation from scratch

This skill reproduces the **method** behind Stanford's STORM system (Synthesis of Topic
Outlines through Retrieval and Multi-perspective Question Asking) as a native agent
workflow. You — Claude — *are* the language model STORM needs, you have web search, page
reading, and subagents. So you run STORM yourself; no external package or API keys.

The output is a single Markdown article: Wikipedia-style, hierarchically structured,
with **inline numbered citations `[n]`** and a **References** section at the end.

## Why STORM works (read this — it shapes every step)

STORM's one big bet: **the hard part of researching a topic from scratch is asking good
questions, not writing the prose.** Two mechanisms make the questions good, and if you
skip them you collapse back into a shallow one-pass web summary:

1. **Perspectives give breadth.** A single viewpoint asks repetitive, surface questions.
   So before researching, *discover several distinct angles* a knowledgeable person would
   take on this topic, and research each one separately. Diverse angles → non-overlapping
   coverage → an article that actually feels complete.

2. **Simulated conversation gives depth.** A flat list of pre-written questions stays
   shallow because it can't react. Instead, simulate a dialogue between a *curious writer*
   and a *topic expert grounded in search results*: the expert's answer updates the
   writer's understanding, which produces a sharper **follow-up** question. Depth comes
   from this answer→follow-up loop, not from asking more questions up front.

Then: **outline before writing** (organize what you collected, don't free-associate), and
**ground every claim honestly**. Groundedness is the whole value, and honesty is part of
it: a non-obvious statement cites a real source you actually retrieved (never a guessed or
half-remembered URL), and where sources *disagree* you show the disagreement instead of
silently picking one number. A confident single figure that hides a real conflict is worse
than two figures with their sources — STORM's known failure mode is exactly this kind of
over-smooth, plausible-but-shaky claim, so prefer transparency over false tidiness.

Keep these in mind as the *reason* behind the stages below. If a step feels mechanical,
re-read this section: you're optimizing for breadth, depth, structure, and groundedness.

## The four stages

```
① Knowledge Curation  → discover perspectives, research each via simulated conversation
② Outline Generation  → organize collected knowledge into a hierarchical outline
③ Article Generation  → write section-by-section, grounded with inline citations
④ Polishing           → lead section, dedup, citation hygiene, reference list
```

Before starting, briefly tell the user your plan: the topic as you understand it, the
perspectives you'll research, and the rough shape of the article. One short paragraph —
then proceed. If the topic is ambiguous (e.g. an acronym, a common name), ask one
clarifying question first; otherwise don't stall.

---

## Stage ① Knowledge Curation

This is where STORM lives. Two sub-steps: discover perspectives, then research each.

### 1a. Discover perspectives

Goal: 3–5 *distinct* angles that together cover the topic without much overlap. Don't
invent them from a vacuum — **survey how the topic is actually framed**:

- Run 1–2 broad searches to see how authoritative/encyclopedic sources break the topic
  down (section headings, recurring sub-themes, the way experts in different fields talk
  about it).
- From that, name perspectives. Good perspectives are *roles or lenses*, not just
  subtopics. Examples by topic type:
  - A technology → *how it works (technical)* · *history & origin* · *applications &
    industry* · *limitations & criticism* · *comparison to alternatives*
  - A person → *early life & background* · *major work/contributions* · *impact &
    legacy* · *controversies & criticism*
  - A controversy/event → *what happened (timeline)* · *each side's position* ·
    *causes* · *consequences & aftermath* · *expert/scholarly analysis*

Adapt — don't force a template. State the chosen perspectives to the user in one line.

### 1b. Research each perspective via simulated conversation

For each perspective, run a grounded **writer ↔ expert conversation** (typically 3–5
turns): the writer asks a question *from that perspective*, the expert answers *only from
real search results it just read*, and each answer seeds the next, sharper question.

**Run perspectives in parallel with subagents** — one subagent per perspective. This is
both faster and truer to STORM (independent experts). The detailed subagent prompt and
conversation protocol are in `references/research-conversations.md` — read it before
spawning, and pass it (or its substance) to each subagent.

Each subagent returns structured research notes: a list of findings, where every finding
is a concrete fact/claim paired with the **source URL(s)** and a short supporting quote.

> If you can't spawn subagents in your current context, **say so** and run the
> perspectives yourself, sequentially. Don't silently drop the conversation structure and
> degrade to one flat search — that throws away the depth mechanism that makes this STORM.

### 1c. Build the source registry

Merge all findings. Deduplicate sources by URL into a single numbered **source registry**
(`[1] = url`, `[2] = url`, …). Every citation in the article will reference these numbers,
so freeze this list now and reuse it across all sections — consistent numbering matters.
Drop low-quality sources (content farms, contradicted claims). Note conflicts between
sources explicitly; you'll surface them in the article rather than silently picking one.

Check **source diversity** before moving on: if most of your findings trace back to one or
two sources (a single Wikipedia page, one news recap), the research was too shallow — that
breadth-of-perspectives is the entire reason for the conversation step. Go widen it: pull
primary sources (papers, filings, official statements) and independent reporting so no
single source dominates the article's grounding.

---

## Stage ② Outline Generation

Now organize — **outline from what you collected, not from the bare topic.** A topic-only
outline guesses at structure; a knowledge-grounded one reflects what the sources actually
support and where the material is rich vs thin.

1. Draft a hierarchical outline: a lead/overview, then top-level sections (often mapping
   loosely to perspectives but *merged and reorganized*, not one-section-per-perspective),
   each with sub-sections.
2. Sanity-check against the registry: does each section have sources? Cut sections you
   can't ground; add ones the research surfaced that you didn't anticipate.
3. Keep it Wikipedia-shaped: lead first, specific/technical middle, then impact /
   reception / criticism / see-also toward the end.

Show the outline to the user before writing the full article — it's cheap to course-correct
here and expensive later. Proceed once it looks right (or after a brief pause for input).

---

## Stage ③ Article Generation

Write the article section by section, each section grounded in the registry.

- **Cite as you write.** Every non-obvious factual claim ends with `[n]` pointing at the
  source that supports it. Multiple sources → `[2][5]`. If you can't cite a claim, either
  find a source or cut the claim — don't assert ungrounded facts in a STORM article, the
  groundedness *is* the product.
- **Synthesize, don't stitch.** Combine what multiple sources say into clean prose in your
  own words; never paste source text. Where sources disagree, present the disagreement
  (“According to X… whereas Y argues…[3][7]”) instead of flattening it.
- **Match Wikipedia register:** neutral, encyclopedic, third-person; no “I/we”, no hype,
  no hedging filler. Lead with a crisp definitional opening paragraph.
- Long articles: sections are independent enough to **write in parallel via subagents**,
  each given the outline, its section's slice of the registry, and the citation rules.
  Keep the shared registry numbering authoritative.

---

## Stage ④ Polishing

A final pass over the assembled draft:

- **Lead section:** ensure the opening summarizes the whole article (what/why-it-matters),
  readable standalone.
- **Deduplicate:** STORM's known failure mode is repeating the same fact across sections
  (perspectives overlap). Remove redundancy; keep each fact in its most natural home.
- **Citation hygiene:** every `[n]` resolves to a registry entry; no orphan numbers, no
  uncited claims in body text. Renumber to be contiguous if needed. Every reference must
  carry a real, well-formed URL you actually retrieved — no missing URLs, no placeholders,
  and never invent a plausible-looking link to fill a gap. If a source has no findable URL,
  drop the claim or label it clearly rather than fabricating one.
- **Red-herring check:** STORM's other known failure is *plausible-but-irrelevant*
  connections and tangents. Cut anything that's true but doesn't serve the topic.
- **References section:** append a numbered list, `[n] Title — URL`, matching the registry.

Then deliver the final Markdown.

## Output format

Save and return one Markdown file:

```markdown
# {Topic}

{Lead paragraph — standalone summary, defines the topic, why it matters.}

## {Section}
{Prose with inline citations [1][2].}

### {Sub-section}
...

## References
[1] {Source title} — {URL}
[2] {Source title} — {URL}
...
```

Tell the user where you saved it. If they later want it typeset (PDF/HTML) or dropped into
a notes vault, hand off to the appropriate skill — STORM's job ends at the cited Markdown.

## When to use this vs. a plain web search or deep-research

Use STORM when the user wants a **structured, multi-perspective, encyclopedic article**
with an outline and sources — breadth + structure are the point. For a single fact, a
quick lookup, or rewriting text the user already has, just answer directly. If the request
is primarily *adversarial fact-checking of specific claims* rather than building an
article, a dedicated deep-research/verification flow fits better; STORM's edge is coverage
and structure via perspectives, not claim-by-claim verification.
