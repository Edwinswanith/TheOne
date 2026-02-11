from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))


def dedupe_sources(sources: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    for source in sources:
        normalized = normalize_url(source["url"])
        existing = by_url.get(normalized)
        if not existing:
            item = deepcopy(source)
            item["normalized_url"] = normalized
            item.setdefault("snippets", [])
            by_url[normalized] = item
            continue

        merged_snippets = list(dict.fromkeys([*existing.get("snippets", []), *source.get("snippets", [])]))
        existing["snippets"] = merged_snippets
        existing["quality_score"] = max(existing.get("quality_score", 0), source.get("quality_score", 0))
        if not existing.get("title") and source.get("title"):
            existing["title"] = source["title"]

    deduped = list(by_url.values())
    deduped.sort(key=lambda x: x["normalized_url"])
    return deduped
