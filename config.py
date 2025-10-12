import os
from dotenv import load_dotenv

load_dotenv()

# Robinhood credentials
ROBINHOOD_USERNAME = os.getenv("ROBINHOOD_USERNAME")
ROBINHOOD_PASSWORD = os.getenv("ROBINHOOD_PASSWORD")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# News API Key
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# SnapTrade API Key
SNAPTRADE_CLIENT_ID = os.getenv("SNAPTRADE_CLIENT_ID")
SNAPTRADE_CONSUMER_KEY = os.getenv("SNAPTRADE_CONSUMER_KEY")
SNAPTRADE_USER_ID = os.getenv("SNAPTRADE_USER_ID")

PORTFOLIO_PROVIDER = os.getenv("PORTFOLIO_PROVIDER", "robinstocks")
