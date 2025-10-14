from abc import ABC, abstractmethod
from typing import Dict
from logging_config import get_logger

logger = get_logger(__name__)


class BaseProvider(ABC):
    @abstractmethod
    def get_positions(self):
        """Return list of normalized positions. Implementations should log successes and failures."""
        pass
