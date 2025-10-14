from abc import ABC, abstractmethod
from logging_config import get_logger

logger = get_logger(__name__)


class BaseReporter(ABC):
    @abstractmethod
    def send_report(self, report):
        """Send the provided report. Implementations should log attempts and results."""
        pass
