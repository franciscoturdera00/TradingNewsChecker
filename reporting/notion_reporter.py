import os
import logging
from typing import Dict, Any

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

    def save_report(self, subject: str, html: str, plaintext: str | None = None, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Create a page in the configured Notion database with basic fields.

        Returns the created page response.
        """
        metadata = metadata or {}
        try:
            # Build simple properties. Users should tailor database schema to match these keys.
            properties = {
                "Name": {"title": [{"text": {"content": subject}}]},
                "Date": {"date": {"start": metadata.get("date")}},
                "Tickers": {"rich_text": [{"text": {"content": ",".join(metadata.get("tickers") or [])}}]},
                "Summary": {"rich_text": [{"text": {"content": metadata.get("summary", "")}}]},
            }

            # Create the page with an HTML block as a child if desired
            children = []
            if plaintext:
                children.append({"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": plaintext}}]}})

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children or None,
            )
            logger.info("Saved report to Notion: %s", page.get("id"))
            return page
        except Exception:
            logger.exception("Failed to save report to Notion")
            raise
