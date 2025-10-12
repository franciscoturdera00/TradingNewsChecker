from portfolio_provider.robinhood_provider import RobinhoodProvider
from news_fetcher.google_news_fetcher import GoogleNewsFetcher
from analysis.gpt_analyzer import GptAnalyzer
from reporting.email_reporter import EmailReporter

def main():
    # Initialize providers
    portfolio_provider = RobinhoodProvider()
    news_fetcher = GoogleNewsFetcher()
    analyzer = GptAnalyzer()
    reporter = EmailReporter()

    # Get portfolio
    positions = portfolio_provider.get_positions()

    # Generate report
    report = ""
    for symbol, data in positions.items():
        report += f"--- {symbol} ---\n"
        report += f"Quantity: {data['quantity']}\n"
        report += f"Average Price: {data['average_price']}\n\n"

        # Fetch and analyze news
        articles = news_fetcher.get_news(symbol)
        analysis = analyzer.analyze(symbol, articles)

        report += "News Analysis:\n"
        report += analysis
        report += "\n\n"

    # Send report
    reporter.send_report(report)

if __name__ == "__main__":
    main()
