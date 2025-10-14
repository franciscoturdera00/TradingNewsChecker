import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from typing import List, Dict

from logging_config import get_logger


logger = get_logger(__name__)


class GoogleNewsRSSFetcher:
    BASE = "https://news.google.com/rss/search"

    def __init__(self, hl: str = "en-US", gl: str = "US", ceid: str = "US:en", timeout: int = 10):
        self.hl, self.gl, self.ceid, self.timeout = hl, gl, ceid, timeout

    def _url(self, query: str) -> str:
        params = {"q": query, "hl": self.hl, "gl": self.gl, "ceid": self.ceid}
        return f"{self.BASE}?{urlencode(params)}"

    def get_news(self, symbol: str, company: str | None = None, max_results: int = 12) -> List[Dict]:
        """
        Returns: [{"title": str, "link": str}, ...]
        """
        # A tiny query boost: include company name if you have it (e.g., from SnapTrade description).
        # You can also add operators like "symbol stock" to reduce noise.
        terms = [f'"{symbol}"']
        if company:
            terms.append(f'"{company}"')
        query = " OR ".join(terms)

        try:
            url = self._url(query)
            logger.debug("Requesting Google News RSS for %s (query=%s)", symbol, query)
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.exception("Failed to fetch RSS for %s: %s", symbol, e)
            return []

        items: List[Dict] = []
        seen_titles = set()

        try:
            root = ET.fromstring(resp.content)

            # RSS 2.0
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link or title in seen_titles:
                    continue
                seen_titles.add(title)
                items.append({"title": title, "link": link})
                if len(items) >= max_results:
                    break

            # Atom fallback (some locales)
            if not items:
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall(".//atom:entry", ns):
                    title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
                    link_el = entry.find("atom:link", ns)
                    link = link_el.get("href", "").strip() if link_el is not None else ""
                    if not title or not link or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    items.append({"title": title, "link": link})
                    if len(items) >= max_results:
                        break

        except ET.ParseError:
            logger.exception("Failed to parse RSS XML for %s", symbol)
            return []

        logger.info("Parsed %d news items for %s", len(items), symbol)
        return items

    def get_news_for_tickers(self, tickers: Dict[str, str] | List[str], max_results: int = 12) -> Dict[str, List[Dict]]:
        """
        tickers:
          - dict form: {"TSM": "Taiwan Semiconductor Manufacturing", "NVDA": "NVIDIA"}
          - or list form: ["TSM", "NVDA"]  (company name optional)
        """
        out: Dict[str, List[Dict]] = {}
        if isinstance(tickers, dict):
            for sym, name in tickers.items():
                arts = self.get_news(sym, company=name, max_results=max_results)
                if arts:
                    out[sym] = arts
        else:
            for sym in tickers:
                arts = self.get_news(sym, company=None, max_results=max_results)
                if arts:
                    out[sym] = arts
        return out
