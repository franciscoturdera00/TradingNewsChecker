from portfolio_provider import SnapTradeProvider
from news_fetcher.google_news_fetcher import GoogleNewsRSSFetcher as NewsFetcher
from analysis.gpt_analyzer import GptAnalyzer
from reporting.email_reporter import EmailReporter
from reporting.html_report_builder import (
    build_portfolio_html_report,
    build_plaintext_fallback,
)

def main():
    provider = SnapTradeProvider()
    news = NewsFetcher()
    analyzer = GptAnalyzer()  # e.g., gpt-4o-mini
    reporter = EmailReporter()

    # Get & normalize positions
    raw = provider.get_positions()
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
        html = build_portfolio_html_report([], {})
        reporter.send_report(html, is_html=True, plain_fallback="No positions found.")
        return

    # Build {ticker: [{title, link}, ...]} with RSS fetcher
    items = {}
    for t in sorted(tickers):
        arts = news.get_news(t, max_results=12)
        if arts:
            items[t] = arts

    # Batch analysis
    analysis = analyzer.analyze_batch(items) if items else {}

    # Render & send
    html = build_portfolio_html_report(positions, analysis)
    text = build_plaintext_fallback(positions, analysis)
    reporter.send_report(html, is_html=True, plain_fallback=text)

if __name__ == "__main__":
    main()
