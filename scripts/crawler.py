from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from scripts.utils import normalize_ws

_PRICE_RE = re.compile(r"([0-9][0-9,\.]*)")

@dataclass
class CrawlResult:
    price: Optional[float]
    sizes_available: List[str]
    raw_price_text: str
    ok: bool
    error: Optional[str] = None


def _read_url(url: str, timeout: int = 20) -> str:
    """
    Read HTML from a URL.
    Supports:
      - http(s)://...
      - file://relative/path (relative to repo root)
    """
    parsed = urlparse(url)

    if parsed.scheme in ("http", "https"):
        # Keep it simple for PoC. Respect sites' ToS/robots, and avoid aggressive crawling.
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "deal-tracker-poc/0.1 (+https://example.invalid)"})
        resp.raise_for_status()
        return resp.text

    if parsed.scheme == "file":
        # file://samples/store1.html  (relative path)
        rel_path = parsed.path.lstrip("/")
        # In many environments urlparse turns "file://samples/store1.html" into netloc="samples" path="/store1.html"
        # Handle both forms.
        if parsed.netloc and rel_path:
            rel_path = f"{parsed.netloc}/{rel_path}"
        elif parsed.netloc and not rel_path:
            rel_path = parsed.netloc

        repo_root = os.getcwd()
        file_path = os.path.join(repo_root, rel_path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    raise ValueError(f"Unsupported URL scheme: {url}")


def _extract_number(text: str) -> Optional[float]:
    if not text:
        return None
    m = _PRICE_RE.search(text.replace(" ", ""))
    if not m:
        return None
    # Remove commas
    num = m.group(1).replace(",", "")
    try:
        return float(num)
    except ValueError:
        return None


def crawl_price_and_sizes(
    url: str,
    selectors: Dict[str, str],
) -> CrawlResult:
    """
    Crawl a product page and extract:
      - price (float)
      - sizes_available (list of strings)
    selectors:
      - "price": CSS selector for the price element (text)
      - "sizes": CSS selector for size option elements (text)
    """
    try:
        html = _read_url(url)
        soup = BeautifulSoup(html, "html.parser")

        # Price
        price_sel = selectors.get("price", "")
        price_el = soup.select_one(price_sel) if price_sel else None
        price_text = normalize_ws(price_el.get_text(" ", strip=True)) if price_el else ""
        price = _extract_number(price_text)

        # Sizes
        sizes_sel = selectors.get("sizes", "")
        size_els = soup.select(sizes_sel) if sizes_sel else []
        sizes: List[str] = []
        for el in size_els:
            t = normalize_ws(el.get_text(" ", strip=True))
            if not t:
                continue
            # Very basic "sold out" filtering for PoC samples.
            if "sold out" in t.lower() or "품절" in t:
                continue
            # Remove parenthetical notes
            t = re.sub(r"\(.*?\)", "", t).strip()
            if t:
                sizes.append(t)

        return CrawlResult(price=price, sizes_available=sizes, raw_price_text=price_text, ok=(price is not None), error=None)

    except Exception as e:
        return CrawlResult(price=None, sizes_available=[], raw_price_text="", ok=False, error=str(e))
