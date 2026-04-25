from abc import ABC, abstractmethod
from typing import Dict, Tuple


class NotificationStrategy(ABC):

    """Strategy interface for all notification channels """

    @abstractmethod
    def send_reminder(self, recipient: str, name: str, class_info: Dict) -> Tuple[bool, str]:
        """ send reminder notifications"""

        pass
