# Simulated research conversations (Stage 1b detail)

Read this protocol for each researched perspective, whether working sequentially
or using authorized subagents. Delegation is optional and does not change the method.

## The protocol

Each perspective is researched as a short multi-turn dialogue between two roles played by
the current researcher:

- **Writer** — a curious Wikipedia author working _from a specific perspective_. Asks one
  focused question at a time. Does **not** answer from memory.
- **Expert** — answers the writer's question, but **only** from search results it fetches
  for that question. Grounds every claim in a source. If sources don't cover it, says so.

The loop (3–5 turns is usually enough; stop when follow-ups stop yielding new ground):

1. Writer poses a question from its perspective.
2. Expert searches the web for that question, reads the most relevant 1–3 results, and
   answers in 2–4 sentences, attaching the source URL(s) behind each claim.
3. Writer reads the answer and asks a **follow-up that builds on it** — drilling into a
   gap, a surprising detail, a named entity, or a disagreement the answer surfaced. Not a
   pre-planned next question; a reaction to what was just learned.
4. Repeat until the perspective is well covered or follow-ups go stale.

The reaction step is the whole point — it's what makes this deeper than a flat query list.

## Tools

Use the tools available in the current environment, respecting the user's choices.

- **Search:** use the configured search capability. Do not assume tinyfish or any
  other CLI is installed; if a selected tool fails, use an available permitted fallback.
- **Read a page:** jina-reader, WebFetch, or `curl -sL` on raw/static pages. Actually read
  the source before citing it — don't cite from a search snippet alone for non-trivial
  claims.

## Research notes for each perspective

Return structured notes, not prose. A list of findings; each finding is a concrete,
citable fact with its source(s). Example shape:

```
PERSPECTIVE: limitations & criticism

FINDINGS:
- Claim: {concrete fact or claim, one sentence}
  Sources: [https://...]
  Quote: "{short supporting quote or paraphrase from the source}"
- Claim: ...
  Sources: [https://..., https://...]
  Quote: "..."

CONFLICTS / UNCERTAINTY:
- {any place sources disagreed, or a claim you couldn't ground}
```

Keep findings atomic (one fact each) so the orchestrator can dedupe across perspectives
and assign stable citation numbers. Always include the real URL — a finding with no
source is useless to a grounded article and should be dropped or flagged.

## Subagent prompt template

Only when delegation is authorized and useful, pass this prompt to a researcher,
substituting `{TOPIC}` and `{PERSPECTIVE}`:

```
You are researching the topic "{TOPIC}" from one specific perspective: "{PERSPECTIVE}".

Run a simulated conversation between a curious Wikipedia WRITER (who asks questions from
the {PERSPECTIVE} angle) and a topic EXPERT (who answers ONLY from web sources it reads).

Loop 3–5 times:
1. WRITER asks one focused question from the {PERSPECTIVE} angle.
2. EXPERT searches the web using the currently available, permitted tools,
   opens the best 1–3 results and actually reads them, then answers in 2–4 sentences with
   the source URL(s) behind each claim.
3. WRITER asks a FOLLOW-UP that reacts to what was just learned — drill into a gap, a
   named entity, a surprising or contested detail. Don't pre-plan it.

Then stop and return ONLY structured findings in this format:

PERSPECTIVE: {PERSPECTIVE}
FINDINGS:
- Claim: <one concrete, citable fact>
  Sources: [<url>, ...]
  Quote: "<short supporting quote/paraphrase>"
- ...
CONFLICTS / UNCERTAINTY:
- <disagreements between sources, or claims you couldn't ground>

Rules: ground every claim in a source you actually read; never answer from memory; keep
findings atomic (one fact each); aim for 8–15 solid findings; drop anything you can't
source. Your returned text IS the data — no preamble, no conclusion.
```

## Sequential execution

Run the same protocol yourself, one perspective at a time, keeping a running findings list
per perspective. No delegation approval is needed for this mode. Preserve the
conversation structure instead of collapsing it into a single flat search.
