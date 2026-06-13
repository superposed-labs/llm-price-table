#!/usr/bin/env python3
"""Audit the price tables: list every dated rate entry with its age and flag
stale ones. Stdlib only; run from the repo root: `python scripts/audit_prices.py`."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

STALE_DAYS = 120  # entries not re-observed in this long are flagged

ROOT = Path(__file__).resolve().parent.parent


def _iter_rates(data: dict):
    """Yield (section, key, rate) for every rate object in a price file."""
    for section in ("models", "fast", "families", "providers"):
        block = data.get(section) or {}
        for key, val in block.items():
            rates = val.get("rates") if isinstance(val, dict) else val
            if isinstance(rates, list):
                for rate in rates:
                    if isinstance(rate, dict):
                        yield section, key, rate


def _age_days(iso: str) -> int | None:
    try:
        return (date.today() - date.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return None


def audit_model_prices(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n=== {path.name} (updated_at={data.get('updated_at')}) ===")
    stale = 0
    rows = list(_iter_rates(data))
    for section, key, rate in rows:
        observed = rate.get("observed") or rate.get("effective_date") or ""
        age = _age_days(observed)
        flag = ""
        if age is None:
            flag = "  ⚠ no/invalid date"
        elif age > STALE_DAYS:
            flag = f"  ⚠ stale ({age}d)"
            stale += 1
        print(f"  [{section:9}] {key:24} in={rate.get('in')!s:>6} out={rate.get('out')!s:>6} "
              f"observed={observed}{flag}")
    print(f"  {len(rows)} rate entries, {stale} stale (> {STALE_DAYS}d).")
    return stale


def audit_plan_prices(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n=== {path.name} (updated_at={data.get('updated_at')}) ===")
    for provider, plans in (data.get("plans") or {}).items():
        pairs = ", ".join(f"{k}=${v}" for k, v in plans.items())
        print(f"  {provider:14} {pairs}")


def main() -> int:
    mp = ROOT / "model_prices.json"
    pp = ROOT / "plan_prices.json"
    if not mp.exists():
        print(f"missing {mp}", file=sys.stderr)
        return 2
    stale = audit_model_prices(mp)
    if pp.exists():
        audit_plan_prices(pp)
    print(f"\nTip: re-check official pages and bump prices via the update-model-prices skill.")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
