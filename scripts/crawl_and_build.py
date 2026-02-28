from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on PYTHONPATH so `import scripts...` works when running as a file.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import json
import os
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional

from scripts.crawler import crawl_price_and_sizes
from scripts.utils import utc_now_iso


# REPO_ROOT already defined above
CONFIG_PATH = REPO_ROOT / "config" / "targets.json"
HISTORY_PATH = REPO_ROOT / "data" / "history.json"
DEALS_OUT = REPO_ROOT / "docs" / "data" / "deals.json"


def _load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _offer_key(t: Dict[str, Any]) -> str:
    # Unique per seller+url
    return f"{t.get('seller','')}\n{t.get('url','')}"


def _append_history(history: Dict[str, Any], offer_key: str, price: float, sizes: List[str], fetched_at: str, max_points: int):
    offers = history.setdefault("offers", {})
    series = offers.setdefault(offer_key, [])
    series.append({
        "price": price,
        "sizes": sizes,
        "fetched_at": fetched_at,
    })
    # Trim
    if len(series) > max_points:
        offers[offer_key] = series[-max_points:]


def _baseline_price(target: Dict[str, Any], series: List[Dict[str, Any]], rules: Dict[str, Any]) -> float:
    # Strategy: use config baseline if provided else median of last N
    cfg = target.get("baseline_price")
    if isinstance(cfg, (int, float)) and cfg > 0:
        return float(cfg)

    n = int(rules.get("median_last_n", 14))
    prices = [p["price"] for p in series[-n:] if isinstance(p.get("price"), (int, float))]
    if prices:
        return float(median(prices))
    # Fallback to 0 to avoid division errors
    return 0.0


def main() -> int:
    cfg = _load_json(CONFIG_PATH, default={})
    targets = cfg.get("targets", [])
    rules = cfg.get("rules", {}) or {}
    max_points = int(rules.get("max_history_points", 60))

    history = _load_json(HISTORY_PATH, default={"offers": {}})
    fetched_at = utc_now_iso()

    # Crawl all targets
    crawled: List[Dict[str, Any]] = []
    for t in targets:
        url = t["url"]
        selectors = t.get("selectors", {}) or {}
        res = crawl_price_and_sizes(url, selectors)

        item = {
            "product_id": t.get("product_id"),
            "brand": t.get("brand"),
            "model": t.get("model"),
            "seller": t.get("seller"),
            "url": t.get("display_url") or url,
            "source_url": url,
            "currency": t.get("currency", "KRW"),
            "ok": res.ok,
            "error": res.error,
            "price": res.price,
            "sizes_available": res.sizes_available,
            "raw_price_text": res.raw_price_text,
            "fetched_at": fetched_at,
            "discount_threshold": float(t.get("discount_threshold", 0.10)),
            "baseline_price": t.get("baseline_price"),
        }
        crawled.append(item)

        # Update history only if OK
        if res.ok and isinstance(res.price, (int, float)):
            _append_history(history, _offer_key(t), float(res.price), res.sizes_available, fetched_at, max_points)

    _save_json(HISTORY_PATH, history)

    # Build deals
    deals: List[Dict[str, Any]] = []
    # For simplicity: evaluate each crawled offer independently as a "deal".
    for item in crawled:
        if not item["ok"] or item["price"] is None:
            continue
        if not item["sizes_available"]:
            continue

        offer_key = f"{item.get('seller','')}\n{item.get('url','')}"
        series = history.get("offers", {}).get(offer_key, [])
        baseline = _baseline_price(item, series, rules)
        if baseline <= 0:
            # If no baseline, skip deal logic in PoC
            baseline = float(item["price"])

        price = float(item["price"])
        discount_rate = (baseline - price) / baseline if baseline else 0.0
        threshold = float(item.get("discount_threshold", 0.10))

        if discount_rate >= threshold:
            deals.append({
                "id": f"{item['product_id']}::{item['seller']}",
                "product_id": item["product_id"],
                "brand": item["brand"],
                "model": item["model"],
                "seller": item["seller"],
                "url": item["url"],
                "currency": item["currency"],
                "price": int(price) if price.is_integer() else price,
                "baseline_price": int(baseline) if float(baseline).is_integer() else baseline,
                "discount_rate": round(discount_rate, 4),
                "discount_percent": round(discount_rate * 100, 1),
                "sizes_available": item["sizes_available"],
                "last_seen_at": item["fetched_at"],
                "rule": f">= {int(threshold*100)}% off",
            })

    # Sort: biggest discount first, then price
    deals.sort(key=lambda d: (-d.get("discount_rate", 0), d.get("price", 0)))

    out = {
        "generated_at": fetched_at,
        "count": len(deals),
        "deals": deals,
        "notes": [
            "PoC output. Replace config/targets.json with real product pages & selectors.",
            "Respect each site's ToS/robots. Avoid aggressive crawling.",
        ]
    }
    _save_json(DEALS_OUT, out)

    print(f"Wrote {DEALS_OUT} with {len(deals)} deals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())