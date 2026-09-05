---
name: storm
license: MIT
description: 使用 STORM 的多视角追问方法研究主题，交付带来源引用的百科式长文；用于系统综述或百科写作请求。
---

# STORM — Wikipedia-style article generation from scratch

This skill reproduces the **method** behind Stanford's STORM system (Synthesis of Topic
Outlines through Retrieval and Multi-perspective Question Asking) as a native agent
workflow. Use the current agent and available search/page-reading tools; no separate STORM
package or external model process is required.

The output is a single Markdown article: Wikipedia-style, hierarchically structured,
with **inline numbered citations `[n]`** and a **References** section at the end.

## Why STORM works (read this — it shapes every step)

STORM's one big bet: **the hard part of researching a topic from scratch is asking good
questions, not writing the prose.** Two mechanisms make the questions good, and if you
skip them you collapse back into a shallow one-pass web summary:

1. **Perspectives give breadth.** A single viewpoint asks repetitive, surface questions.
   So before researching, _discover several distinct angles_ a knowledgeable person would
   take on this topic, and research each one separately. Diverse angles → non-overlapping
   coverage → an article that actually feels complete.

2. **Simulated conversation gives depth.** A flat list of pre-written questions stays
   shallow because it can't react. Instead, simulate a dialogue between a _curious writer_
   and a _topic expert grounded in search results_: the expert's answer updates the
   writer's understanding, which produces a sharper **follow-up** question. Depth comes
   from this answer→follow-up loop, not from asking more questions up front.

Then: **outline before writing** (organize what you collected, don't free-associate), and
**ground every claim honestly**. Groundedness is the whole value, and honesty is part of
it: a non-obvious statement cites a real source you actually retrieved (never a guessed or
half-remembered URL), and where sources _disagree_ you show the disagreement instead of
silently picking one number. A confident single figure that hides a real conflict is worse
than two figures with their sources — STORM's known failure mode is exactly this kind of
over-smooth, plausible-but-shaky claim, so prefer transparency over false tidiness.

Keep these in mind as the _reason_ behind the stages below. If a step feels mechanical,
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

Goal: 3–5 _distinct_ angles that together cover the topic without much overlap. Don't
invent them from a vacuum — **survey how the topic is actually framed**:

- Run 1–2 broad searches to see how authoritative/encyclopedic sources break the topic
  down (section headings, recurring sub-themes, the way experts in different fields talk
  about it).
- From that, name perspectives. Good perspectives are _roles or lenses_, not just
  subtopics. Examples by topic type:
  - A technology → _how it works (technical)_ · _history & origin_ · _applications &
    industry_ · _limitations & criticism_ · _comparison to alternatives_
  - A person → _early life & background_ · _major work/contributions_ · _impact &
    legacy_ · _controversies & criticism_
  - A controversy/event → _what happened (timeline)_ · _each side's position_ ·
    _causes_ · _consequences & aftermath_ · _expert/scholarly analysis_

Adapt — don't force a template. State the chosen perspectives to the user in one line.

### 1b. Research each perspective via simulated conversation

For each perspective, run a grounded **writer ↔ expert conversation** (typically 3–5
turns): the writer asks a question _from that perspective_, the expert answers _only from
real search results it just read_, and each answer seeds the next, sharper question.

Read `references/research-conversations.md` for the conversation protocol. Research
perspectives sequentially by default; when authorized and useful, delegate independent
perspectives and provide each researcher with the relevant protocol.

Each perspective produces structured research notes: a list of findings, where every finding
is a concrete fact/claim paired with the **source URL(s)** and a short supporting quote.

Keep the answer-to-follow-up loop in either execution mode; do not replace it with a
flat list of searches.

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
   loosely to perspectives but _merged and reorganized_, not one-section-per-perspective),
   each with sub-sections.
2. Sanity-check against the registry: does each section have sources? Cut sections you
   can't ground; add ones the research surfaced that you didn't anticipate.
3. Keep it Wikipedia-shaped: lead first, specific/technical middle, then impact /
   reception / criticism / see-also toward the end.

Briefly show the evidence-backed outline and continue writing within the agreed scope.
Wait only if a material scope question remains unresolved or the user requested outline
approval. Silence or elapsed time is not approval.

---

## Stage ③ Article Generation

Write the article section by section, each section grounded in the registry.

- **Cite as you write.** Every non-obvious factual claim ends with `[n]` pointing at the
  source that supports it. Multiple sources → `[2][5]`. If you can't cite a claim, either
  find a source or cut the claim — don't assert ungrounded facts in a STORM article, the
  groundedness _is_ the product.
- **Synthesize, don't stitch.** Combine what multiple sources say into clean prose in your
  own words; never paste source text. Where sources disagree, present the disagreement
  (“According to X… whereas Y argues…[3][7]”) instead of flattening it.
- **Match Wikipedia register:** neutral, encyclopedic, third-person; no “I/we”, no hype,
  no hedging filler. Lead with a crisp definitional opening paragraph.
- Long articles: when delegation is authorized, independent sections may be written by subagents,
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
- **Red-herring check:** STORM's other known failure is _plausible-but-irrelevant_
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
is primarily _adversarial fact-checking of specific claims_ rather than building an
article, a dedicated deep-research/verification flow fits better; STORM's edge is coverage
and structure via perspectives, not claim-by-claim verification.
