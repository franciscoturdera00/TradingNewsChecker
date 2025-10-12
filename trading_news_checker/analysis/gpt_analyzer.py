from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class GptAnalyzer:

    client: OpenAI

    def __init__(self):
        self.client = OpenAI()
        self.client.api_key = os.getenv("OPENAI_API_KEY", "")

        if self.client.api_key == "":
            raise ValueError("OPENAI_API_KEY environment variable is not set.")

    def analyze(self, symbol, articles):
        prompt = f"Here are some news articles about {symbol}:\n\n"
        for article in articles:
            prompt += f"- {article['title']}\n"
        prompt += "\nPlease provide a summary of the news and a sentiment analysis (positive, negative, or neutral)."

        response = self.client.responses.create(
            model="text-davinci-003",
            input=prompt,
        )

        return response.output_text
