import requests
from typing import List, Dict
from logging_config import get_logger

logger = get_logger(__name__)


class RedditFetcher:
    """Lightweight Reddit fetcher using public JSON endpoints.

    This does not require OAuth and fetches recent posts that mention the
    ticker symbol. It's intentionally conservative to avoid rate limits.
    """

    SEARCH_URL = "https://www.reddit.com/search.json"

    def __init__(self, user_agent: str | None = None, timeout: int = 8):
        self.timeout = timeout
        # Reddit requires a User-Agent header; default to an informative one.
        self.headers = {"User-Agent": user_agent or "TradingNewsChecker/0.1 (+https://example.com)"}

    def _query(self, q: str, limit: int = 12) -> List[Dict]:
        params = {"q": q, "sort": "new", "limit": limit}
        try:
            resp = requests.get(self.SEARCH_URL, params=params, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.exception("Reddit search failed for query=%s: %s", q, e)
            return []

        try:
            data = resp.json()
            items = []
            for child in data.get("data", {}).get("children", []) or []:
                d = child.get("data") or {}
                title = d.get("title") or d.get("selftext") or ""
                url = d.get("url") or ""
                subreddit = d.get("subreddit")
                if not title:
                    continue
                items.append({"title": title.strip(), "link": url, "source": f"reddit/{subreddit}"})
                if len(items) >= limit:
                    break
            return items
        except Exception:
            logger.exception("Failed to parse Reddit response for query=%s", q)
            return []

    def get_news(self, symbol: str, max_results: int = 12) -> List[Dict]:
        """Return list of dicts: {title, link, source}

        Searches r/all for the symbol (as a token) and for $TICKER patterns.
        """
        # Query tokens: exact symbol and dollar-prefixed ticker
        queries = [f'"{symbol}"', f'${symbol}']
        out = []
        seen = set()
        per_query = max(3, max_results // len(queries))
        for q in queries:
            items = self._query(q, limit=per_query)
            for it in items:
                t = it.get("title")
                if t in seen:
                    continue
                seen.add(t)
                out.append(it)
                if len(out) >= max_results:
                    return out
        return out
