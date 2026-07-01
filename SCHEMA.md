# Schema

Two JSON files, both hand-maintained. All token rates are **USD per 1,000,000
tokens**. These are *estimates* — see the disclaimer in [README.md](README.md).

## `model_prices.json` — per-token API rates

```jsonc
{
  "version": 1,
  "updated_at": "YYYY-MM-DD",   // last time the table was reviewed
  "note": "...",                 // free-text conventions (JSON has no comments)
  "models":    { "<exact-model-id>": { "provider": "...", "rates": [ <rate> ] } },
  "fast":      { "<id-or-family>":   { "rates": [ <rate> ] } | [ <rate> ] },
  "families":  { "<family-key>":     [ <rate> ] },
  "providers": { "<provider-key>":   [ <rate> ] }
}
```

### Resolution (how a model id → a rate)

For a given `(provider, model_id, date, is_fast)`:

1. If `is_fast`, try **`fast`** first: exact id, then family (word-boundary).
   Falls through to the standard tables if no fast rate exists.
2. **`models`** — exact model id. Use for versions that diverge in price.
3. **`families`** — case-insensitive **word-boundary** substring of the id
   (e.g. `opus`, `sonnet`, `haiku`, `mini`, `nano`, `flash-lite`, `flash`,
   `gemini`). Word-boundary (not raw substring) so `mini` doesn't match inside
   `ge`**`mini`**. Families are tried **in file order**, so put more specific
   keys first: `flash-lite` before `flash` before `gemini`.
4. **`providers`** — coarse per-provider fallback.
5. Otherwise **$0** (local/unknown models — surfaced as "uncosted", not hidden).

### The `<rate>` object

A dated list; each entry is the price effective from a date:

```jsonc
{ "effective_date": "YYYY-MM-DD", "observed": "YYYY-MM-DD",
  "in": 0.0, "out": 0.0, "cw": 0.0, "cw1h": 0.0, "cr": 0.0, "source": "..." }
```

- `in` / `out` — input / output price.
- `cw` — cache **write**, 5-minute TTL (Anthropic ≈ 1.25× input). Providers with
  **no** per-token cache-write fee (OpenAI, Google) set `cw = in`.
- `cw1h` — cache **write**, 1-hour TTL (Anthropic = 2× input). **Optional**;
  omit when there's no distinct 1h rate and the consumer falls back to `cw`.
- `cr` — cache **read** / "cached input" (≈ 1/10th of input).
- `effective_date` — when this price took effect *as far as known*. Use the
  provider's announced date if any; else a best-effort floor = first-observed
  day. **This is the only field that affects cost.** A consumer prices each unit
  of usage at the rate whose `effective_date` is the latest on/before its date,
  so a recorded change splits history by period.
- `observed` — the day the number was read off the source. Provenance only.
- `source` — short note on where the number came from.

#### Optional: `context_pricing`

Models whose official page has distinct short/long context tiers can keep the
short tier in the top-level fields and attach the full tier split here:

```jsonc
{
  "effective_date": "YYYY-MM-DD",
  "observed": "YYYY-MM-DD",
  "in": 2.5, "out": 15.0, "cw": 2.5, "cr": 0.25,
  "context_pricing": {
    "metric": "input_tokens_total",
    "short_max": 272000,
    "short": { "in": 2.5, "out": 15.0, "cw": 2.5, "cr": 0.25 },
    "long":  { "in": 5.0, "out": 22.5, "cw": 5.0, "cr": 0.5 }
  }
}
```

- `metric` — currently `input_tokens_total`, meaning the consumer should choose
  the tier from the request's original billed input before any cache-read split.
- `short_max` — inclusive threshold for the short tier (`<= short_max` = short;
  `> short_max` = long).
- `short` / `long` — complete rate objects for each tier. Consumers should use
  these leaf values when the block is present, not the top-level `in/out/cw/cr`.

The top-level `in/out/cw/cr` should mirror the short tier so older consumers
that ignore `context_pricing` still get a conservative result instead of a null.

### Recording a change (important)

- Price **changed** → **ADD** a new entry with the new `effective_date`. **Do not
  edit an existing entry's numbers** — overwriting erases the period split and
  re-prices all history at the new number.
- Price **unchanged** → leave it; at most bump top-level `updated_at`.
- New version the family **misprices** → add an exact `models` entry.

### Conventions

- Record only the **standard** on-demand tier. Don't mix in batch/flex/priority.
- If a model has short/long context tiers, record both via `context_pricing`.
- **`fast`** holds premium overrides (e.g. Anthropic Fast mode); same shape as
  `models`/`families`.

## `plan_prices.json` — subscription list prices

Display-only; for framing token cost against a flat monthly plan. Never affects
token cost.

```jsonc
{
  "version": 1,
  "updated_at": "YYYY-MM-DD",
  "note": "...",
  "plans": {
    "<provider>": { "<plan-label>": <monthly_usd> }   // label matched case-insensitively
  }
}
```

The `<plan-label>` is matched against whatever the consumer detects for the
account (e.g. `pro`, `plus`, `max-20x`, `google ai pro`). Unknown label → the
consumer omits the comparison rather than guessing.
