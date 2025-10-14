from abc import ABC, abstractmethod
from logging_config import get_logger

logger = get_logger(__name__)


class BaseFetcher(ABC):
    @abstractmethod
    def get_news(self, symbol):
        """Return a list of news dicts for symbol.

        Implementations should log successes and failures.
        """
        pass
