import os
import logging
from typing import Any
from datetime import datetime, timezone
import inspect

import os
import logging
from typing import Any
from datetime import datetime, timezone
import inspect

try:
    from notion_client import Client as NotionClient
except Exception:
    NotionClient = None  # optional dependency

logger = logging.getLogger(__name__)


class NotionReporter:
    """Saves a basic record for each report into a Notion database.

    Requires environment variables:
      - NOTION_API_KEY
      - NOTION_DATABASE_ID
    """

    def __init__(self, notion_api_key: str | None = None, database_id: str | None = None):
        notion_api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if NotionClient is None:
            raise RuntimeError("notion_client package is not installed")
        if not notion_api_key or not database_id:
            raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID must be set to use NotionReporter")

        self.client = NotionClient(auth=notion_api_key)
        self.database_id = database_id

    def save_report(self, tickers: list[str] | None = None, analysis: dict | None = None) -> Any:
        """Create a page in the configured Notion database with basic fields.

        The method now generates its own subject and date. `tickers` should be
        a list of ticker strings. Returns the created page response (or an
        awaitable if using an async Notion client).
        """
        tickers = tickers or []
        try:
            date_val = datetime.now(timezone.utc).isoformat()
            subject = f"Trading News Report — {', '.join(tickers) if tickers else 'Portfolio'} — {date_val.split('T',1)[0]}"

            properties: dict[str, Any] = {
                "Name": {"title": [{"text": {"content": subject}}]},
                "Date": {"date": {"start": date_val}},
            }

            # Assume the database defines `Tickers` as a multi-select and
            # always send a multi_select payload (empty list when no tickers).
            properties["Tickers"] = {"multi_select": [{"name": t} for t in tickers]} if tickers else {"multi_select": []}

            # Create children from analysis
            children: list[dict] = []

            # If analysis is provided, build structured Notion blocks from it.
            if analysis and isinstance(analysis, dict):
                results = analysis.get("results") or analysis.get("items") or []
                if isinstance(results, dict):
                    # If results keyed by ticker, convert to list
                    results = list(results.values())

                for item in results:
                    try:
                        symbol = item.get("symbol") or "Unknown"
                        sentiment = (item.get("sentiment") or "").lower()

                        # sentiment badge emoji
                        emoji_map = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}
                        badge = emoji_map.get(sentiment, "")

                        # Heading (symbol) with sentiment badge as a separate paragraph
                        children.append({
                            "object": "block",
                            "type": "heading_2",
                            "heading_2": {"text": [{"type": "text", "text": {"content": str(symbol)}}]},
                        })
                        if sentiment:
                            children.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {"text": [{"type": "text", "text": {"content": f"{badge} {sentiment.capitalize()}"}}]},
                            })

                        # Build left column: News Analysis (bullets)
                        left_blocks: list[dict] = []
                        left_blocks.append({
                            "object": "block",
                            "type": "heading_3",
                            "heading_3": {"text": [{"type": "text", "text": {"content": "News Analysis"}}]},
                        })
                        for b in item.get("summary_bullets", []) or []:
                            left_blocks.append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {"text": [{"type": "text", "text": {"content": str(b)}}]},
                            })

                        # Build right column: compact summary and overall sentiment
                        reasons = item.get("reasons") or []
                        summary_bullets = item.get("summary_bullets", []) or []
                        summary_short = ", ".join([s for s in summary_bullets[:3]])

                        right_blocks: list[dict] = []
                        right_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"text": [{"type": "text", "text": {"content": "Summary:"}}]},
                        })
                        right_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"text": [{"type": "text", "text": {"content": summary_short}}]},
                        })
                        overall = f"Overall sentiment: {sentiment.capitalize()}"
                        if reasons:
                            overall += f" (because: {reasons[0]})"
                        right_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"text": [{"type": "text", "text": {"content": overall}}]},
                        })

                        # Column list combining left and right
                        children.append({
                            "object": "block",
                            "type": "column_list",
                            "column_list": {
                                "children": [
                                    {"object": "block", "type": "column", "column": {"children": left_blocks}},
                                    {"object": "block", "type": "column", "column": {"children": right_blocks}},
                                ]
                            }
                        })

                        # Divider between symbols
                        children.append({"object": "block", "type": "divider", "divider": {}})
                    except Exception:
                        logger.exception("Failed to build Notion blocks for analysis item: %s", item)
            # No plaintext fallback: if analysis missing, children will be empty

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children,
            )

            # The Notion client may return a plain dict (sync) or an awaitable
            # (async client). We avoid attempting to synchronously resolve an
            # awaitable here because that can conflict with an existing event
            # loop and causes type-checker issues. If an awaitable is returned
            # we log and return it; callers running inside an async context can
            # await it themselves.
            if inspect.isawaitable(page):
                logger.info("Notion client returned awaitable result; returning awaitable to caller")
                return page

            # Synchronous dict response
            if isinstance(page, dict):
                page_id = page.get("id")
                if page_id:
                    logger.info("Saved report to Notion: %s", page_id)
                else:
                    logger.info("Saved report to Notion (no id available)")
            else:
                logger.info("Saved report to Notion (unexpected response type: %s)", type(page))

            return page
        except Exception:
            logger.exception("Failed to save report to Notion")
            raise
