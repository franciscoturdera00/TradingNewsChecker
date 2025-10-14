from portfolio_provider import SnapTradeProvider
from news_fetcher.google_news_fetcher import GoogleNewsRSSFetcher as NewsFetcher
from analysis.gpt_analyzer import GptAnalyzer
from reporting.email_reporter import EmailReporter
from reporting.html_report_builder import (
    build_portfolio_html_report,
    build_plaintext_fallback,
)

from logging_config import setup_logging, get_logger


logger = get_logger(__name__)


def main():
    setup_logging()
    logger.info("Starting TradingNewsChecker main")

    try:
        provider = SnapTradeProvider()
    except Exception as e:
        logger.exception("Failed to initialize portfolio provider: %s", e)
        raise

    news = NewsFetcher()
    analyzer = GptAnalyzer()  # e.g., gpt-4o-mini
    reporter = EmailReporter()

    # Get & normalize positions
    try:
        raw = provider.get_positions()
        logger.info("Fetched positions: count=%d", len(raw or []))
    except Exception:
        logger.exception("Error while fetching positions from provider")
        raw = []

    positions, tickers = [], set()
    for p in raw or []:
        if p.get("cash_equivalent"):
            continue
        sym = (p.get("symbol") or {}).get("symbol") or {}
        ticker = sym.get("raw_symbol") or sym.get("symbol")
        if not ticker:
            continue
        tickers.add(ticker)
        positions.append({
            "ticker": ticker,
            "qty": float(p.get("units") or p.get("fractional_units") or 0),
            "avg_cost": p.get("average_purchase_price"),
            "last_price": p.get("price"),
            "account_id": p.get("account_id"),
        })

    if not positions:
        logger.info("No positions found; sending empty report")
        html = build_portfolio_html_report([], {})
        try:
            reporter.send_report(html, is_html=True, plain_fallback="No positions found.")
            logger.info("Sent empty report successfully")
        except Exception:
            logger.exception("Failed to send empty report")
        return

    # Build {ticker: [{title, link}, ...]} with RSS fetcher
    items = {}
    for t in sorted(tickers):
        try:
            arts = news.get_news(t, max_results=12)
            logger.info("Fetched news for %s: %d items", t, len(arts or []))
        except Exception:
            logger.exception("Error fetching news for %s", t)
            arts = []
        if arts:
            items[t] = arts

    # Batch analysis
    try:
        analysis = analyzer.analyze_batch(items) if items else {}
        logger.info("Completed GPT analysis for %d tickers", len(analysis or {}))
    except Exception:
        logger.exception("GPT analysis failed")
        analysis = {}

    # Render & send
    html = build_portfolio_html_report(positions, analysis)
    text = build_plaintext_fallback(positions, analysis)
    try:
        reporter.send_report(html, is_html=True, plain_fallback=text)
        logger.info("Report sent successfully")
    except Exception:
        logger.exception("Failed to send report")


if __name__ == "__main__":
    main()
