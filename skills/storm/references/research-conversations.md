# Simulated research conversations (Stage 1b detail)

This is the depth engine of STORM. Read it before spawning per-perspective research
subagents. Hand each subagent the protocol below, specialized to its perspective.

## The protocol

Each perspective is researched as a short multi-turn dialogue between two roles played by
one subagent:

- **Writer** — a curious Wikipedia author working *from a specific perspective*. Asks one
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

Use whatever web tools are available in the environment.
- **Search:** in this user's setup, `tinyfish search query "<query>"` (fall back to native
  WebSearch only if tinyfish is rate-limited).
- **Read a page:** jina-reader, WebFetch, or `curl -sL` on raw/static pages. Actually read
  the source before citing it — don't cite from a search snippet alone for non-trivial
  claims.

## What each subagent returns

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

Spawn one per perspective, substituting `{TOPIC}` and `{PERSPECTIVE}`:

```
You are researching the topic "{TOPIC}" from one specific perspective: "{PERSPECTIVE}".

Run a simulated conversation between a curious Wikipedia WRITER (who asks questions from
the {PERSPECTIVE} angle) and a topic EXPERT (who answers ONLY from web sources it reads).

Loop 3–5 times:
1. WRITER asks one focused question from the {PERSPECTIVE} angle.
2. EXPERT searches the web (use `tinyfish search query "..."`, fall back to WebSearch),
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

## If you can't spawn subagents

Run the same protocol yourself, one perspective at a time, keeping a running findings list
per perspective. Say out loud that you're going sequential — don't quietly skip the
conversation structure and collapse into a single flat search, which would discard STORM's
depth mechanism.
