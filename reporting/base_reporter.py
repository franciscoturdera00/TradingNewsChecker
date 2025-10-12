from abc import ABC, abstractmethod

class BaseReporter(ABC):
    @abstractmethod
    def send_report(self, report):
        pass
