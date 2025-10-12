from abc import ABC, abstractmethod
from typing import Dict

class BaseProvider(ABC):
    @abstractmethod
    def get_positions(self):
        pass
