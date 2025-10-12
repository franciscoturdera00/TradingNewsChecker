from abc import ABC, abstractmethod

class BaseFetcher(ABC):
    @abstractmethod
    def get_news(self, symbol):
        pass
