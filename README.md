# llm-price-table

A small, hand-maintained price table for LLM usage — **per-token API rates**
([`model_prices.json`](model_prices.json)) and **subscription list prices**
([`plan_prices.json`](plan_prices.json)) — meant to be consumed by multiple
projects as a shared override/supplement layer (e.g. on top of LiteLLM, for
models newer than any public price list).

See [SCHEMA.md](SCHEMA.md) for the file format and conventions.

## ⚠️ These are estimates

There is no official pricing API, and the tools that run these models are often
newer than any published price list. Numbers here are read off official pricing
pages by a human (with AI assistance) and **will drift** between updates. They
model only the **standard short-context tier** and exclude batch/flex/priority
discounts and long-context tiers. **Do not treat as billing-accurate.** No
warranty. Check `updated_at` in each file for staleness.

## Using it in a project

Recommended pattern (offline-safe, no hard runtime network dependency — this is
how LiteLLM ships its own table):

1. **Bundle a snapshot.** Commit a copy of `model_prices.json` (and
   `plan_prices.json`) into your project as the always-available fallback.
2. **Refresh opportunistically.** Optionally fetch the latest from the raw URL
   and cache it locally; on any failure, fall back to the bundled snapshot.

```
https://raw.githubusercontent.com/<owner>/llm-price-table/main/model_prices.json
https://raw.githubusercontent.com/<owner>/llm-price-table/main/plan_prices.json
```

Keep the fetch **opt-in** if your project is local-first — never surprise the
user with network calls. Compare `updated_at` to decide whether a refresh is
worth it.

## Contributing a price change

PRs welcome. Follow the discipline that keeps the table trustworthy:

- **Cite the official source** for every number (`source` field).
- A price that **changed** → *add* a dated entry; don't overwrite the old one
  (history must split by period). See [SCHEMA.md](SCHEMA.md#recording-a-change-important).
- Read the **standard short-context** tier; ignore batch/flex/priority/long-context.
- Git history is the price-change log — keep it human-authored and reviewed. A
  wrong number silently corrupts every downstream cost estimate.

The [`update-model-prices`](skills/update-model-prices/SKILL.md) skill captures
the full refresh procedure (which pages to read, family-vs-exact judgment,
gotchas). `python scripts/audit_prices.py` flags stale entries.

## License

[MIT](LICENSE).
