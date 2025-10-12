from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def get_positions(self):
        pass
