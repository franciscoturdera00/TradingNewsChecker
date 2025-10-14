from openai import OpenAI
import os, json
from typing import Dict, List

from logging_config import get_logger

logger = get_logger(__name__)


class GptAnalyzer:
    """
    Expects:
      items = { "TSM": [ {"title": "...", "link": "..."}, ... ], "NVDA": [...] }
    Returns:
      { "TSM": {"summary_bullets": [...], "sentiment": "...", "reasons": [...]}, ... }
    """
    def __init__(self, model: str = "gpt-4o-mini", max_titles_per_ticker: int = 12):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_titles = max_titles_per_ticker

    def analyze(self, symbol: str, articles: List[Dict]) -> Dict:
        return self.analyze_batch({symbol: articles}).get(symbol, {
            "summary_bullets": [], "sentiment": "neutral", "reasons": []
        })

    def analyze_batch(self, items: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        # Normalize → sections
        sections = []
        for symbol, arts in (items or {}).items():
            if not symbol or not arts:
                continue
            titles, links = [], []
            for a in arts:
                t = (a.get("title") or "").strip()
                if not t:
                    continue
                titles.append(t)
                if a.get("link"):
                    links.append(a["link"])
                if len(titles) >= self.max_titles:
                    break
            if titles:
                sections.append({
                    "symbol": symbol,
                    "headlines": titles,
                    "links": links[:2],  # small context only
                })
        if not sections:
            return {}
        # Build compact instruction (JSON-only response)
        parts = []
        for s in sections:
            hlines = "\n".join(f"- {h}" for h in s["headlines"])
            extra = ("\nTop sources:\n" + "\n".join(f"- {u}" for u in s["links"])) if s["links"] else ""
            parts.append(f"### Ticker: {s['symbol']}\nHeadlines:\n{hlines}{extra}\n")

        prompt = (
            "You are a financial news analyst. Treat each ticker independently.\n"
            "For EVERY ticker, do BOTH:\n"
            "  1) Summarize the likely impact in 3-5 concise bullets\n"
            "  2) Provide overall sentiment as one of {positive|neutral|negative} with 1-2 brief reasons.\n\n"
            "Return ONLY valid minified JSON (no prose, no code fences) with this shape:\n"
            '{\"results\":[{\"symbol\":\"<TICKER>\",\"summary_bullets\":[\"...\"],'
            '\"sentiment\":\"positive|neutral|negative\",\"reasons\":[\"...\"]}...]}\n\n'
            "SECTIONS:\n" + "\n".join(parts)
        )

        try:
            logger.info("Sending GPT analysis request for %d sections", len(sections))
            resp = self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=0.2,
                max_output_tokens=800,  # keep bounded
            )
            raw = resp.output_text or ""
            logger.debug("Raw GPT response length=%d", len(raw or ""))
            data = self._safe_json_parse(raw)
        except Exception:
            logger.exception("GPT request failed")
            return {}

        # Normalize to dict keyed by symbol
        out: Dict[str, Dict] = {}
        for row in (data.get("results") or []):
            sym = row.get("symbol")
            if not sym:
                continue
            out[sym] = {
                "summary_bullets": row.get("summary_bullets", []),
                "sentiment": row.get("sentiment"),
                "reasons": row.get("reasons", []),
            }
        return out

    @staticmethod
    def _safe_json_parse(s: str) -> Dict:
        """
        Robust JSON extraction: handles accidental prose by trimming to the first '{' and last '}'.
        """
        try:
            return json.loads(s)
        except Exception:
            try:
                start = s.find("{")
                end = s.rfind("}")
                if start != -1 and end != -1 and end > start:
                    snippet = s[start:end+1]
                    logger.debug("Attempting trimmed JSON parse; length=%d", len(snippet))
                    return json.loads(snippet)
            except Exception:
                logger.exception("Failed to parse GPT JSON response")
        return {"results": []}
