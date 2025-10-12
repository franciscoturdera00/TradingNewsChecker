import requests
from bs4 import BeautifulSoup
from .base_fetcher import BaseFetcher

class GoogleNewsFetcher(BaseFetcher):
    def get_news(self, symbol):
        url = f"https://news.google.com/search?q={symbol}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        for article in soup.find_all("article"):
            title = article.find("a").text
            link = article.find("a")["href"]
            articles.append({"title": title, "link": link})
        return articles
