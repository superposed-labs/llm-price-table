---
name: update-model-prices
description: >-
  Refresh the LLM price tables in this repo (model_prices.json, plan_prices.json)
  by pulling current prices from the official provider pricing pages (Anthropic,
  OpenAI, Google Gemini). Use this whenever someone wants to update, check, or
  verify model prices; suspects a price is stale, wrong, or too high/low; says a
  provider changed prices or a new model version shipped; or asks "are these
  prices still right" — even if they don't name the file. It fetches the official
  pages (rendering OpenAI's JS-heavy page via the browser), reads per-model
  prices, and proposes reviewed edits that follow SCHEMA.md. It never auto-writes
  or commits — the human approves and merges.
---

# Update model prices

This repo holds a hand-maintained price table. There is no official pricing API,
and tools run models newer than any public price list, so prices are refreshed by
a person running this procedure on demand (a few times a year) — **not** by a
scheduled scraper. Read [SCHEMA.md](../../SCHEMA.md) first; it defines the file
format and the rate fields.

Your job is the judgment-heavy part a cron can't do: render the pages, read the
numbers semantically, decide how each model maps into the table, and hand the
human a clear, correct proposal.

## The one hard rule

**Propose, never auto-apply.** A wrong number silently corrupts every downstream
cost estimate, so a human must verify before anything lands. Produce a clear
summary of proposed changes and stop. Only edit the files if the user explicitly
approves the specific numbers, and **never** `git commit` — committing is the
user's call. Git history is the price-change log; it must stay human-authored.

## Prerequisites

- **Network access** to fetch the pricing pages.
- **A browser tool** (e.g. a browser MCP): OpenAI's pricing page is a JS-rendered
  shell — a plain fetch returns an empty page, so render it in a real browser and
  read the text. Anthropic and Google serve prices in plain HTML, so `curl` /
  fetch is enough for those.

## Procedure

### 1. Audit what's there

```bash
python scripts/audit_prices.py
```

Lists every entry with its `effective_date` age and flags stale ones — your
baseline for the diff.

### 2. Fetch the official pages

| Provider | URL | How |
|---|---|---|
| Anthropic | https://docs.claude.com/en/docs/about-claude/pricing (redirects to platform.claude.com) | plain fetch (server-rendered) |
| Google Gemini | https://ai.google.dev/gemini-api/docs/pricing | plain fetch (server-rendered) |
| OpenAI | https://platform.openai.com/docs/pricing (redirects to developers.openai.com) | **browser** — navigate, then read page text |

### 3. Read prices semantically

Read the rendered page yourself and pull each model's **standard, short-context**
tier: input, cached input (→ `cr`), output. Ignore batch/flex/priority tiers, the
long-context (>200k) tier, and free-tier columns. Note deprecated vs current
models — price the live one, not the deprecated one. For Anthropic also read the
**Fast mode** premiums (→ `fast` section) and the prompt-caching multipliers
(5-min → `cw`, 1-hour → `cw1h`).

### 4. Decide family vs exact — the key judgment

- **Family** when a whole tier shares one price across versions (e.g. Anthropic
  Opus 4.5–4.8 are all $5/$25 → the `opus` family covers them, and a future
  `opus-4-9` resolves without an edit).
- **Exact model** when versions are repriced (e.g. Gemini **3** Flash $0.50/$3 vs
  Gemini **3.5** Flash $1.50/$9 — same "flash" word, different price). Pin the
  diverging versions in `models`; let the family track the current one. Always
  spot-check: did a newer version change price? If so it needs an exact entry.

### 5. Mind the gotchas

- **Word-boundary matching**: family keys match on a boundary, not raw substring
  ("mini" ⊂ "ge**mini**"). Keep family keys unambiguous.
- **Resolution order**: families are tried in file order — `flash-lite` before
  `flash` before `gemini`.
- **Short-context only**: one tier; don't mix in long-context prices.

### 6. Record changes correctly

See [SCHEMA.md → Recording a change](../../SCHEMA.md#recording-a-change-important).
A price **changed** → ADD a dated entry (don't overwrite). Unchanged → leave it,
maybe bump `updated_at`. New version the family misprices → add an exact `models`
entry.

### 7. Present the proposal and stop

Show a compact summary: for each change, the model/family, old → new numbers, the
source, and the `effective_date`. Call out anything uncertain (e.g. a model not on
the page → which fallback applies). Ask whether to apply. Apply only approved
edits; leave the commit to the user.

## Verify after applying (only once approved)

```bash
python -c "import json; json.load(open('model_prices.json')); json.load(open('plan_prices.json')); print('JSON OK')"
python scripts/audit_prices.py
```

Confirm the JSON parses and the audit looks right. Downstream consumers re-test
resolution in their own codebases.

## Example: a price change done right

> Opus drops from $5/$25 to $4/$20 on 2026-10-01.

Add (don't overwrite) to the `opus` family list:

```json
{ "effective_date": "2026-10-01", "observed": "2026-10-01", "in": 4.0, "out": 20.0, "cw": 5.0, "cw1h": 8.0, "cr": 0.4, "source": "Anthropic docs" }
```

Usage before Oct 1 keeps pricing at $5/$25; on/after, at $4/$20 — consumers that
honor `effective_date` reflect both periods automatically.
