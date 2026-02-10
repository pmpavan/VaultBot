from abc import ABC, abstractmethod
from typing import Optional

class MessagingProvider(ABC):
    """
    Abstract interface for messaging providers.
    Decouples application logic from specific 3rd party integrations (e.g., Twilio).
    """
    
    @abstractmethod
    def send_message(self, to: str, body: str, from_: Optional[str] = None) -> None:
        """
        Send a message to a recipient.
        
        Args:
            to: Recipient identifier (e.g., phone number).
            body: The message content.
            from_: Optional sender identifier. If None, uses default.
        """
        pass
