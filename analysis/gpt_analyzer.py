from openai import OpenAI
import os, json
from typing import Dict, List
import time

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
        logger.debug("Prepared sections for GPT analysis:\n %s", sections)

        # Build compact instruction (JSON-only response)
        parts = []
        for s in sections:
            hlines = "\n".join(f"- {h}" for h in s["headlines"])
            extra = ("\nTop sources:\n" + "\n".join(f"- {u}" for u in s["links"])) if s["links"] else ""
            parts.append(f"### Ticker: {s['symbol']}\nHeadlines:\n{hlines}{extra}\n")

        prompt = (f"""
            "You are a financial news analyst. Treat each ticker independently.\n"
            "Your task: ONLY return valid JSON. DO NOT include explanations, markdown, or any text outside the JSON.\n"
            "The JSON **must strictly follow** this schema (NEVER return anything other than this JSON schema):\n"
            "Return ONLY valid JSON exactly matching this structure:
            {{
            "results": [
                {{
                "symbol": "TICKER",
                "summary_bullets": ["..."],
                "sentiment": "positive|neutral|negative",
                "reasons": ["..."]
                }}
            ]
            }}
            "For EVERY ticker, do BOTH:\n"
            "  1) Summarize the likely impact in 3-5 concise bullets\n"
            "  2) Provide overall sentiment as one of {{positive|neutral|negative}} with 1-2 brief reasons.\n\n"
            "Return ONLY valid minified JSON (no code fences, no commentary, no explanations).\n\n"
            "SECTIONS:\n {'\n'.join(parts)}""".strip()
        )

        logger.debug("Constructed GPT prompt %s", prompt)

        try:
            logger.info("Sending GPT analysis request for %d sections", len(sections))
            resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
            max_output_tokens=2000,  # keep bounded
            )

            # Use the SDK JSON mode output directly if supported
            raw = getattr(resp, "output_text", "") or getattr(resp, "output_json", "") or ""
            logger.debug("Raw GPT response length=%d", len(raw))
            logger.debug("Raw GPT response: %s", raw.strip())

            # Parse JSON strictly
            data = json.loads(raw.strip())

        except json.JSONDecodeError as e:
            logger.error("JSON parsing failed: %s", e)
            logger.debug("Fallback raw response: %s", raw)
            data = {}

        except Exception:
            logger.exception("GPT request failed")
            data = {}


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